from models.mongo import mongo_database
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional, List

collection = mongo_database['quizzes']


async def add_quiz(quiz, user_id: str, is_public: bool = True):
  quiz_with_info = dict(quiz)
  quiz_with_info.update({
      'user_id': user_id,
      'is_public': is_public,
      'created_date': datetime.now(timezone.utc),
      'last_modified_date': datetime.now(timezone.utc),
      'num_question': len(quiz_with_info.get('questions', [])),
      'difficulty': 'N/A',
      'category': 'N/A'
  })
  return await collection.insert_one(quiz_with_info)


async def update_quiz(quiz_id: str, update_data: dict):
  update_data['last_modified_date'] = datetime.now(timezone.utc)

  if 'questions' in update_data:
    update_data['num_question'] = len(update_data['questions'])

  object_id = ObjectId(quiz_id)

  result = await collection.update_one(
      {'_id': object_id},
      {'$set': update_data}
  )
  return result


async def delete_quiz(quiz_id: str):
  object_id = ObjectId(quiz_id)

  result = await collection.delete_one({'_id': object_id})
  return result


async def search_quizzes(
    user_id: str,
    is_public: bool,
    min_created_date: Optional[datetime] = None,
    max_created_date: Optional[datetime] = None,
    min_last_modified: Optional[datetime] = None,
    max_last_modified: Optional[datetime] = None,
    difficulty: Optional[str] = None,
    categories: Optional[List[str]] = None,
    size: Optional[int] = None,
    start: Optional[int] = None
):
  query = {
      '$or': [
          {'user_id': user_id},
          {'is_public': is_public}
      ]
  }

  if min_created_date or max_created_date:
    created_date_query = {}
    if min_created_date:
      created_date_query['$gte'] = min_created_date
    if max_created_date:
      created_date_query['$lte'] = max_created_date
    query['created_date'] = created_date_query

  if min_last_modified or max_last_modified:
    last_modified_query = {}
    if min_last_modified:
      last_modified_query['$gte'] = min_last_modified
    if max_last_modified:
      last_modified_query['$lte'] = max_last_modified
    query['last_modified_date'] = last_modified_query

  if difficulty:
    query['difficulty'] = difficulty

  if categories:
    query['category'] = {'$in': categories}

  cursor = collection.find(query)
  if start is not None:
    cursor = cursor.skip(start)
  if size is not None:
    cursor = cursor.limit(size)

  results = await cursor.to_list(length=size)

  for doc in results:
    if '_id' in doc:
      doc['_id'] = str(doc['_id'])

  return results
