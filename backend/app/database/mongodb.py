import logging
import urllib.parse
from typing import Optional, List, Dict, Any
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from app.config import settings

logger = logging.getLogger("skillforge.database")

class MongoDBManager:
    client: Optional[MongoClient] = None
    db: Optional[Database] = None

db_manager = MongoDBManager()

def get_safe_host_info(client: MongoClient) -> str:
    """Extract cluster host name safely without exposing credentials."""
    try:
        if client.nodes:
            first_host = list(client.nodes)[0][0]
            if "mongodb.net" in first_host:
                parts = first_host.split(".")
                domain = ".".join(parts[-3:]) if len(parts) >= 3 else first_host
                return f"skillforgeai-0.{domain}"
            return first_host
        elif client.address:
            return f"{client.address[0]}:{client.address[1]}"
    except Exception:
        pass
    return "skillforgeai-0.zw7q1a8.mongodb.net"

def connect_to_mongodb():
    """Establish connection to MongoDB Atlas/server, verify with ping, and build indexes."""
    db_name = settings.MONGODB_DATABASE or "skillforge"
    uri = settings.MONGODB_URI
    
    if not uri:
        print("MONGODB_URI is not set. Falling back to in-memory mongomock.")
        logger.warning("MONGODB_URI is not set. Falling back to in-memory mongomock.")
        try:
            import mongomock
            db_manager.client = mongomock.MongoClient()
            db_manager.db = db_manager.client[db_name]
            init_indexes()
            print("MongoDB mock client initialized successfully")
            return
        except ImportError:
            print("mongomock is not installed. Mock database fallback not available.")
            raise ValueError("MONGODB_URI is empty and mongomock is not installed.")

    try:
        # Create single MongoClient instance (secure TLS — no insecure overrides)
        db_manager.client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        
        # Test connection with ping
        db_manager.client.admin.command("ping")
        
        # Select database
        db_manager.db = db_manager.client[db_name]
        
        # Verify actual database name
        actual_db_name = db_manager.db.name
        safe_host = get_safe_host_info(db_manager.client)
        
        # Safe logging without credentials
        print("MongoDB connected successfully")
        print(f"MongoDB database: {actual_db_name}")
        print(f"MongoDB host: {safe_host}")
        
        logger.info("MongoDB connected successfully to database: %s on host: %s", actual_db_name, safe_host)

        # List existing collections
        existing_cols = db_manager.db.list_collection_names()
        logger.info("Existing collections in %s: %s", actual_db_name, existing_cols)

        # Initialize collections and indexes
        init_indexes()

    except Exception as e:
        err_str = str(e)
        err_type = type(e).__name__

        # Categorize the error clearly without exposing credentials
        if "SSL" in err_str or "TLS" in err_str or "tlsv1" in err_str.lower():
            print("MongoDB connection FAILED — TLS/SSL handshake error.")
            print(">>> Most likely cause: your IP is not in MongoDB Atlas Network Access allowlist.")
            print(">>> Fix: Go to https://cloud.mongodb.com -> Network Access -> Add IP Address")
            logger.error("MongoDB TLS handshake failed — likely Atlas IP allowlist issue: %s", err_type)
        elif "timed out" in err_str.lower() or "ServerSelectionTimeoutError" in err_type:
            print("MongoDB connection FAILED — connection timed out.")
            print(">>> Check: network/firewall, Atlas cluster status, and IP allowlist.")
            logger.error("MongoDB connection timed out: %s", err_type)
        elif "authentication" in err_str.lower() or "auth" in err_str.lower():
            print("MongoDB connection FAILED — authentication error.")
            print(">>> Check: username and password in MONGODB_URI (.env file).")
            logger.error("MongoDB authentication failed: %s", err_type)
        else:
            print(f"MongoDB connection FAILED — {err_type}")
            logger.error("MongoDB connection failed (%s): %s", err_type, err_str[:200])

        try:
            import mongomock
            db_manager.client = mongomock.MongoClient()
            db_manager.db = db_manager.client[db_name]
            init_indexes()
            print("MongoDB mock client initialized (in-memory fallback — data will not persist)")
            logger.warning("Using mongomock in-memory fallback — Atlas connection unavailable")
        except Exception as fallback_err:
            logger.error("Failed to fallback to mongomock: %s", str(fallback_err))
            print("Failed to fallback to mongomock:", str(fallback_err))
            raise e

def close_mongodb_connection():
    """Close MongoClient on FastAPI shutdown."""
    if db_manager.client:
        db_manager.client.close()
        logger.info("MongoDB client connection closed")
        print("MongoDB connection closed")

def get_database() -> Database:
    """Return active PyMongo database instance."""
    if db_manager.db is None:
        connect_to_mongodb()
    return db_manager.db

def get_users_collection():
    return get_database()["users"]

def get_resumes_collection():
    return get_database()["resumes"]

def get_portfolios_collection():
    return get_database()["portfolios"]

def get_career_profiles_collection():
    return get_database()["career_profiles"]

def get_learning_paths_collection():
    return get_database()["learning_paths"]

def get_progress_collection():
    return get_database()["progress"]

def init_indexes():
    """Create exact required MongoDB indexes for all 6 collections and log index names."""
    try:
        db = get_database()
        index_summary = {}

        # 1. users.email -> unique
        idx1 = db["users"].create_index([("email", ASCENDING)], unique=True)
        index_summary["users"] = [idx1]
        
        # 2. resumes.userId
        idx2 = db["resumes"].create_index([("userId", ASCENDING)])
        index_summary["resumes"] = [idx2]
        
        # 3. portfolios.userId
        idx3 = db["portfolios"].create_index([("userId", ASCENDING)])
        index_summary["portfolios"] = [idx3]
        
        # 4. career_profiles.userId
        idx4 = db["career_profiles"].create_index([("userId", ASCENDING)])
        index_summary["career_profiles"] = [idx4]
        
        # 5. learning_paths.userId
        idx5 = db["learning_paths"].create_index([("userId", ASCENDING)])
        index_summary["learning_paths"] = [idx5]
        
        # 6. progress.userId -> unique
        idx6 = db["progress"].create_index([("userId", ASCENDING)], unique=True)
        index_summary["progress"] = [idx6]
        
        logger.info("MongoDB indexes verified successfully: %s", index_summary)
    except Exception as e:
        logger.warning("Error initializing MongoDB indexes: %s", str(e))
        print(f"Warning initializing MongoDB indexes: {e}")
