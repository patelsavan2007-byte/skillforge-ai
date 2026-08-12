import os
from datetime import datetime
from app.config import settings
from app.database.mongodb import (
    get_database,
    get_users_collection,
    get_resumes_collection,
    get_portfolios_collection,
    get_career_profiles_collection,
    get_learning_paths_collection,
    get_progress_collection,
    get_safe_host_info,
    close_mongodb_connection,
    init_indexes
)

def verify_and_initialize_atlas():
    """Verify MongoDB Atlas/server connection, create required collections by inserting initial data if empty, and print status."""
    print("--- SKILLFORGE AI MONGODB ATLAS INITIALIZATION ---")
    
    # 1. Initialize indexes
    init_indexes()
    
    db = get_database()
    safe_host = get_safe_host_info(db.client)
    
    print(f"Connected to Cluster Host: {safe_host}")
    print(f"Target Database Name: {db.name}")
    
    if db.name != "skillforge":
        print(f"WARNING: Current database is '{db.name}', expected 'skillforge'. Check MONGODB_DATABASE in backend/.env")
    
    # 2. Check collections
    cols = ["users", "resumes", "portfolios", "career_profiles", "learning_paths", "progress"]
    
    # Create initial system document if database is completely empty to force Atlas/Compass UI rendering
    if not db.list_collection_names():
        print("Database is empty on remote Atlas cluster. Inserting system initialization marker...")
        now = datetime.utcnow()
        db["users"].insert_one({
            "system_init": True,
            "message": "SkillForge AI database initialized successfully",
            "createdAt": now
        })
        # Remove initialization marker immediately
        db["users"].delete_many({"system_init": True})

    current_cols = db.list_collection_names()
    print(f"Active Collections in '{db.name}': {current_cols}")
    
    # 3. Print document counts per collection
    print("\n--- COLLECTION DOCUMENT COUNTS ---")
    for col_name in cols:
        count = db[col_name].count_documents({})
        print(f"Collection '{col_name}': {count} documents")

    close_mongodb_connection()
    print("\nInitialization check complete.")

if __name__ == "__main__":
    verify_and_initialize_atlas()
