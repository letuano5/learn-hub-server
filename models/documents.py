from models.mongo import mongo_database
from datetime import datetime, timezone

collection = mongo_database['documents']


async def add_document(user_id: str, is_public: bool, filename: str, file_url: str):
  document = {
      "user_id": user_id,
      "is_public": is_public,
      "filename": filename,
      "file_url": file_url,
      "date": datetime.now(timezone.utc)
  }
  return await collection.insert_one(document)
