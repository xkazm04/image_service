from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

Base = declarative_base()

# Get Supabase database configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Require Supabase configuration
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    if DATABASE_URL:
        # Use provided DATABASE_URL (for custom PostgreSQL instances)
        engine = create_engine(DATABASE_URL)
        logger.info("Using custom PostgreSQL database")
    else:
        raise ValueError(
            "Supabase configuration required. Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file, "
            "or provide a custom DATABASE_URL for PostgreSQL."
        )
else:
    # Build Supabase connection string
    # Extract host from URL (remove protocol)
    supabase_host = SUPABASE_URL.replace('https://', '').replace('http://', '')
    db_url = f"postgresql://postgres:{SUPABASE_SERVICE_KEY}@{supabase_host}:5432/postgres"
    engine = create_engine(db_url)
    logger.info("Using Supabase PostgreSQL database")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()