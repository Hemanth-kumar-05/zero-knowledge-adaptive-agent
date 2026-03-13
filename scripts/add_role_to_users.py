"""
Migration Script: Add Role Field to Existing Users
Run this script once to add the "role" field to all existing user documents
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from config import Config


async def add_role_to_users():
    """Add role field to all users that don't have it"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(Config.MONGODB_URI)
    db = client[Config.MONGODB_DB_NAME]
    users_collection = db["users"]
    
    print("🔄 Starting migration: Adding 'role' field to users...")
    
    # Find all users without a role field
    users_without_role = await users_collection.count_documents({"role": {"$exists": False}})
    
    if users_without_role == 0:
        print("✅ All users already have the 'role' field. No migration needed.")
        client.close()
        return
    
    print(f"📊 Found {users_without_role} users without 'role' field")
    
    # Update all users without role to have default "student" role
    result = await users_collection.update_many(
        {"role": {"$exists": False}},
        {"$set": {"role": "student"}}
    )
    
    print(f"✅ Migration completed!")
    print(f"   - Updated {result.modified_count} users")
    print(f"   - Default role: 'student'")
    
    # Verify migration
    total_users = await users_collection.count_documents({})
    users_with_role = await users_collection.count_documents({"role": {"$exists": True}})
    
    print(f"\n📊 Verification:")
    print(f"   - Total users: {total_users}")
    print(f"   - Users with role: {users_with_role}")
    
    if total_users == users_with_role:
        print("   ✅ All users now have the 'role' field!")
    else:
        print(f"   ⚠️ Warning: {total_users - users_with_role} users still missing 'role' field")
    
    client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("USER ROLE MIGRATION SCRIPT")
    print("=" * 60)
    print()
    
    try:
        asyncio.run(add_role_to_users())
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)
