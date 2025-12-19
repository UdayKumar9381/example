# app/database.py
"""
Database connection and session management.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.config import get_settings
import sys

# Load settings
settings = get_settings()

# Create database engine with error handling
try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600
    )
except Exception as e:
    print(f"❌ Failed to create database engine: {e}")
    sys.exit(1)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function that provides database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """
    Test database connection and provide helpful error messages.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        return True
    except OperationalError as e:
        error_msg = str(e)
        print(f"❌ Database connection failed!")
        print(f"   Error: {error_msg}")
        
        if "Access denied" in error_msg:
            print("\n🔧 TROUBLESHOOTING:")
            print("   1. Check if your .env file exists in the project root")
            print("   2. Verify DB_PASSWORD is set correctly in .env")
            print("   3. Make sure there are no quotes around the password in .env")
            print("   4. Test your MySQL credentials manually:")
            print(f"      mysql -u {settings.db_user} -p")
        elif "Unknown database" in error_msg:
            print("\n🔧 TROUBLESHOOTING:")
            print(f"   Create the database in MySQL: CREATE DATABASE {settings.db_name};")
        elif "Can't connect" in error_msg:
            print("\n🔧 TROUBLESHOOTING:")
            print("   1. Make sure MySQL server is running")
            print("   2. Check if the host and port are correct")
        
        return False


def init_db():
    """
    Initialize database tables.
    """
    # First test the connection
    if not test_connection():
        print("\n❌ Cannot initialize database. Please fix connection issues first.")
        sys.exit(1)
    
    # Import models to register them with Base
    from app import models  # noqa: F401
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables initialized!")