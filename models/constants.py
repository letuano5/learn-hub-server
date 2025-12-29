from models.mongo import mongo_database
from typing import Optional

collection = mongo_database['constants']


async def get_constant(key: str) -> Optional[int]:
  """Get a constant value by key"""
  doc = await collection.find_one({})
  if doc and key in doc:
    return doc[key]
  return None


async def get_all_constants() -> dict:
  """Get all constants as a dictionary"""
  doc = await collection.find_one({})
  if doc:
    # Remove MongoDB _id field
    doc.pop('_id', None)
    return doc
  return {}


async def set_constant(key: str, value: int):
  """Set or update a constant value"""
  await collection.update_one(
      {},
      {'$set': {key: value}},
      upsert=True
  )


async def init_default_constants():
  """Initialize default constants if collection is empty"""
  existing = await collection.find_one({})
  if not existing:
    await collection.insert_one({
        "MAX_QUIZZES_PER_USER": 100,
        "MAX_STORAGE_PER_USER_BYTES": 1073741824  # 1GB in bytes
    })
    print("Default constants initialized")
