"""Offline API tests using the real Supabase SDK with mocked HTTP responses.

No test reads real credentials or contacts a Supabase database.
Run: python -m unittest -v test_api
"""
import json
import os
import unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from supabase import create_client, ClientOptions
import main
from database import get_client


class EnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.responses = []
        self.requests = []
        def respond(request):
            self.requests.append(request)
            if not self.responses:
                raise AssertionError('Unexpected database request')
            code, body = self.responses.pop(0)
            return httpx.Response(code, json=body)
        self.transport = httpx.Client(transport=httpx.MockTransport(respond))
        self.db = create_client('https://example.supabase.co', 'test-key',
            options=ClientOptions(httpx_client=self.transport, auto_refresh_token=False,
                                  persist_session=False))
        main.app.dependency_overrides[get_client] = lambda: self.db
        self.client = TestClient(main.app)
        self.addCleanup(main.app.dependency_overrides.clear)
        self.addCleanup(self.transport.close)
        self.addCleanup(self.client.close)
        self.course = {'id':1,'title':'Python Basics','description':'Learn Python'}
        self.enrollment = {'id':5,'student_id':1,'course_id':1}

    def queue(self, *bodies):
        self.responses.extend((200, body) for body in bodies)

    def test_create_course(self):
        self.queue([self.course])
        response=self.client.post('/courses',json={'title':' Python Basics ','description':'Learn Python'})
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json(),self.course)
        request=self.requests[0]
        self.assertEqual(request.method,'POST')
        self.assertEqual(request.url.path,'/rest/v1/courses')
        self.assertEqual(json.loads(request.content),{'title':'Python Basics','description':'Learn Python'})

    def test_list_courses_empty_and_populated(self):
        for body in [[],[self.course]]:
            self.queue(body)
            response=self.client.get('/courses')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json(),body)
        self.assertEqual(self.requests[-1].url.params['order'],'id.asc')

    def test_enroll_checks_records(self):
        self.queue([{'id':1}],[{'id':1}],[self.enrollment])
        response=self.client.post('/enroll',json={'student_id':1,'course_id':1})
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json(),self.enrollment)
        self.assertEqual([r.url.path for r in self.requests],
            ['/rest/v1/student','/rest/v1/courses','/rest/v1/enrollments'])
        self.assertEqual(self.requests[0].url.params['id'],'eq.1')

    def test_missing_student_and_course(self):
        self.queue([])
        response=self.client.post('/enroll',json={'student_id':99,'course_id':1})
        self.assertEqual(response.status_code,404)
        self.assertEqual(response.json()['detail'],'Student 99 not found')
        self.queue([{'id':1}],[])
        response=self.client.post('/enroll',json={'student_id':1,'course_id':99})
        self.assertEqual(response.status_code,404)
        self.assertEqual(response.json()['detail'],'Course 99 not found')
        self.assertTrue(all(r.method=='GET' for r in self.requests))

    def test_duplicate_unique_constraint(self):
        self.queue([{'id':1}],[{'id':1}])
        self.responses.append((409,{'code':'23505','message':'duplicate key','details':None,'hint':None}))
        response=self.client.post('/enroll',json={'student_id':1,'course_id':1})
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.json()['detail'],'Student is already enrolled in this course')

    def test_foreign_key_race(self):
        # A record can disappear after the existence check; the database rejects insert.
        self.queue([{'id':1}],[{'id':1}])
        self.responses.append((409,{'code':'23503','message':'foreign key','details':None,'hint':None}))
        self.assertEqual(self.client.post('/enroll',json={'student_id':1,'course_id':1}).status_code,404)

    def test_student_courses_and_unknown_student(self):
        self.queue([{'id':1}],[{'courses':self.course}])
        response=self.client.get('/students/1/courses')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(),[self.course])
        self.assertEqual(self.requests[-1].url.params['student_id'],'eq.1')
        self.assertEqual(self.requests[-1].url.params['select'],'courses(id,title,description)')
        self.queue([{'id':1}],[])
        self.assertEqual(self.client.get('/students/1/courses').json(),[])
        self.queue([])
        self.assertEqual(self.client.get('/students/999/courses').status_code,404)

    def test_cancel_uses_enrollment_id_and_repeat_missing(self):
        self.queue([self.enrollment])
        response=self.client.delete('/enroll/5')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(),{'message':'Enrollment cancelled','enrollment_id':5})
        request=self.requests[-1]
        self.assertEqual(request.method,'DELETE')
        self.assertEqual(request.url.path,'/rest/v1/enrollments')
        self.assertEqual(request.url.params['id'],'eq.5')
        self.queue([])
        self.assertEqual(self.client.delete('/enroll/5').status_code,404)

    def test_invalid_body_and_path(self):
        for body in [{},{'title':' '},{'title':None},{'title':'x'*101},
                     {'title':'x','description':'x'*501},{'title':'x','id':1}]:
            self.assertEqual(self.client.post('/courses',json=body).status_code,422)
        for value in [0,-1,1.5,True,'1',None]:
            for field in ['student_id','course_id']:
                body={'student_id':1,'course_id':1,field:value}
                self.assertEqual(self.client.post('/enroll',json=body).status_code,422)
        for body in [{},{'student_id':1},{'student_id':1,'course_id':1,'id':3}]:
            self.assertEqual(self.client.post('/enroll',json=body).status_code,422)
        for value in ['0','-1','abc','1.5']:
            self.assertEqual(self.client.get(f'/students/{value}/courses').status_code,422)
            self.assertEqual(self.client.delete(f'/enroll/{value}').status_code,422)
        self.assertEqual(self.requests,[])

    def test_valid_boundaries_and_default(self):
        self.queue([{'id':1,'title':'x'*100,'description':'y'*500}])
        self.assertEqual(self.client.post('/courses',json={'title':'x'*100,'description':'y'*500}).status_code,201)
        self.queue([{'id':2,'title':'x','description':''}])
        self.assertEqual(self.client.post('/courses',json={'title':'x'}).status_code,201)
        self.assertEqual(json.loads(self.requests[-1].content)['description'],'')

    def test_database_and_network_errors(self):
        for code in ['PGRST205','42P01','42501']:
            self.responses.append((400,{'code':code,'message':'private database detail','details':None,'hint':None}))
            response=self.client.get('/courses')
            self.assertEqual(response.status_code,503)
            self.assertNotIn('private database detail',response.text)
        with patch.object(self.db,'table',side_effect=httpx.ConnectError('private connection detail')):
            self.assertEqual(self.client.get('/courses').status_code,503)
        with patch.object(self.db,'table',side_effect=RuntimeError('private detail')):
            response=self.client.get('/courses')
            self.assertEqual(response.status_code,500)
            self.assertEqual(response.json(),{'detail':'Internal server error'})

    def test_missing_config_and_documentation(self):
        main.app.dependency_overrides.clear()
        get_client.cache_clear()
        with patch.dict(os.environ,{'SUPABASE_URL':'','SUPABASE_KEY':''}):
            self.assertEqual(self.client.get('/courses').status_code,503)
            self.assertEqual(self.client.get('/docs').status_code,200)
            paths=self.client.get('/openapi.json').json()['paths']
            self.assertEqual(sum(len(methods) for methods in paths.values()),5)
        get_client.cache_clear()

    def test_malformed_json(self):
        for path in ['/courses','/enroll']:
            self.assertEqual(self.client.post(path).status_code,422)
            self.assertEqual(self.client.post(path,content='{',headers={'Content-Type':'application/json'}).status_code,422)
        self.assertEqual(self.requests,[])


if __name__=='__main__':
    unittest.main()
