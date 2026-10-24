"""Class-style Supabase setup, loaded only when a route needs the database."""
import logging
import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from fastapi import HTTPException
from supabase import Client, create_client

load_dotenv(Path(__file__).resolve().parent / ".env")
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Reuse one client; allow documentation/tests to open without credentials."""
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()
    if not url or not key:
        logger.error("Supabase configuration is missing")
        raise HTTPException(503, "Configure SUPABASE_URL and SUPABASE_KEY in .env")
    try:
        return create_client(url, key)
    except Exception as error:
        # Do not log credentials or a potentially sensitive connection error string.
        logger.error("Supabase client configuration failed (%s)", type(error).__name__)
        raise HTTPException(503, "Supabase configuration is invalid") from error
