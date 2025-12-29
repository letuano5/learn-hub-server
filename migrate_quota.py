"""
Migration script to initialize quota for existing users
Run this once to populate quota collection based on existing quizzes and documents
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models.mongo import mongo_database
from datetime import datetime, timezone

# Collections
quizzes_collection = mongo_database['quizzes']
documents_collection = mongo_database['documents']
quota_collection = mongo_database['quota']


async def migrate_user_quotas():
    """Migrate existing data to populate quota collection"""
    
    print("Starting quota migration...")
    print("=" * 60)
    
    # Get all unique user_ids from quizzes
    quiz_users = await quizzes_collection.distinct('user_id')
    print(f"Found {len(quiz_users)} users with quizzes")
    
    # Get all unique user_ids from documents
    doc_users = await documents_collection.distinct('user_id')
    print(f"Found {len(doc_users)} users with documents")
    
    # Combine all unique users
    all_users = set(quiz_users) | set(doc_users)
    print(f"Total unique users: {len(all_users)}")
    print("=" * 60)
    
    migrated = 0
    updated = 0
    
    for user_id in all_users:
        print(f"\nProcessing user: {user_id}")
        
        # Count quizzes for this user
        quiz_count = await quizzes_collection.count_documents({'user_id': user_id})
        print(f"  - Quizzes: {quiz_count}")
        
        # Calculate total storage for this user
        documents = await documents_collection.find({'user_id': user_id}).to_list(length=None)
        total_storage = sum(doc.get('file_size', 0) for doc in documents)
        total_storage_mb = total_storage / (1024 * 1024)
        print(f"  - Documents: {len(documents)}")
        print(f"  - Total storage: {total_storage_mb:.2f} MB ({total_storage} bytes)")
        
        # Check if quota already exists
        existing_quota = await quota_collection.find_one({'user_id': user_id})
        
        if existing_quota:
            # Update existing quota
            await quota_collection.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'total_quizzes': quiz_count,
                        'total_storage': total_storage,
                        'last_updated': datetime.now(timezone.utc)
                    }
                }
            )
            print(f"  ✓ Updated existing quota")
            updated += 1
        else:
            # Create new quota
            await quota_collection.insert_one({
                'user_id': user_id,
                'total_quizzes': quiz_count,
                'total_storage': total_storage,
                'created_date': datetime.now(timezone.utc),
                'last_updated': datetime.now(timezone.utc)
            })
            print(f"  ✓ Created new quota")
            migrated += 1
    
    print("\n" + "=" * 60)
    print("Migration completed!")
    print(f"New quotas created: {migrated}")
    print(f"Existing quotas updated: {updated}")
    print(f"Total users processed: {len(all_users)}")
    print("=" * 60)


async def verify_migration():
    """Verify the migration results"""
    print("\nVerifying migration...")
    print("=" * 60)
    
    quota_count = await quota_collection.count_documents({})
    print(f"Total quota records: {quota_count}")
    
    # Show sample quotas
    print("\nSample quota records:")
    sample_quotas = await quota_collection.find().limit(5).to_list(length=5)
    
    for quota in sample_quotas:
        quota.pop('_id', None)
        user_id = quota['user_id']
        total_quizzes = quota['total_quizzes']
        total_storage = quota['total_storage']
        total_storage_mb = total_storage / (1024 * 1024)
        
        print(f"\nUser: {user_id}")
        print(f"  Quizzes: {total_quizzes}")
        print(f"  Storage: {total_storage_mb:.2f} MB")
    
    print("=" * 60)


async def main():
    """Main migration function"""
    try:
        await migrate_user_quotas()
        await verify_migration()
        print("\n✅ Migration successful!")
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
