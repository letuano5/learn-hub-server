from models.mongo import mongo_database
from models.constants import get_constant
from datetime import datetime, timezone
from typing import Tuple

collection = mongo_database['quota']


async def get_or_create_quota(user_id: str) -> dict:
  """Get existing quota or create new one for user"""
  quota = await collection.find_one({'user_id': user_id})
  if not quota:
    quota = {
        'user_id': user_id,
        'total_quizzes': 0,
        'total_storage': 0,
        'created_date': datetime.now(timezone.utc),
        'last_updated': datetime.now(timezone.utc)
    }
    await collection.insert_one(quota)
  return quota


async def get_quota(user_id: str) -> dict:
  """Get quota info for user"""
  quota = await get_or_create_quota(user_id)
  # Remove _id for cleaner response
  if '_id' in quota:
    quota.pop('_id')
  return quota


async def check_quiz_quota(user_id: str) -> Tuple[bool, dict, int]:
  """
  Check if user can create a new quiz
  Returns: (can_create, quota_info, max_quizzes)
  """
  quota = await get_or_create_quota(user_id)
  max_quizzes = await get_constant("MAX_QUIZZES_PER_USER")
  
  if max_quizzes is None:
    max_quizzes = 100  # Fallback default
  
  can_create = quota['total_quizzes'] < max_quizzes
  return can_create, quota, max_quizzes


async def check_storage_quota(user_id: str, file_size: int) -> Tuple[bool, dict, int]:
  """
  Check if user can upload a file
  Returns: (can_upload, quota_info, max_storage)
  """
  quota = await get_or_create_quota(user_id)
  max_storage = await get_constant("MAX_STORAGE_PER_USER_BYTES")
  
  if max_storage is None:
    max_storage = 1073741824  # Fallback default (1GB)
  
  can_upload = (quota['total_storage'] + file_size) <= max_storage
  return can_upload, quota, max_storage


async def increment_quiz_count(user_id: str):
  """Increment quiz count by 1"""
  await collection.update_one(
      {'user_id': user_id},
      {
          '$inc': {'total_quizzes': 1},
          '$set': {'last_updated': datetime.now(timezone.utc)}
      }
  )


async def increment_storage(user_id: str, file_size: int):
  """Add file size to total storage"""
  await collection.update_one(
      {'user_id': user_id},
      {
          '$inc': {'total_storage': file_size},
          '$set': {'last_updated': datetime.now(timezone.utc)}
      }
  )


async def decrement_quiz_count(user_id: str):
  """Decrement quiz count by 1 (when quiz is deleted)"""
  await collection.update_one(
      {'user_id': user_id},
      {
          '$inc': {'total_quizzes': -1},
          '$set': {'last_updated': datetime.now(timezone.utc)}
      }
  )


async def decrement_storage(user_id: str, file_size: int):
  """Subtract file size from total storage (when document is deleted)"""
  await collection.update_one(
      {'user_id': user_id},
      {
          '$inc': {'total_storage': -file_size},
          '$set': {'last_updated': datetime.now(timezone.utc)}
      }
  )
