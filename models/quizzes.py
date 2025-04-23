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
      'category': ['N/A']
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


async def get_quiz(quiz_id: str):
  object_id = ObjectId(quiz_id)
  quiz = await collection.find_one({'_id': object_id})
  
  if quiz and '_id' in quiz:
    quiz['_id'] = str(quiz['_id'])
  
  return quiz


async def search_quizzes(
    user_id: Optional[str] = None,
    is_public: Optional[bool] = None,
    min_created_date: Optional[datetime] = None,
    max_created_date: Optional[datetime] = None,
    min_last_modified: Optional[datetime] = None,
    max_last_modified: Optional[datetime] = None,
    difficulty: Optional[str] = None,
    categories: Optional[List[str]] = None,
    size: Optional[int] = None,
    start: Optional[int] = None
):
  query = {}
  
  # If user_id is not specified, only show public documents
  if user_id is None:
    query['is_public'] = True
  else:
    # If user_id is specified, show user's documents
    query['user_id'] = user_id
    # If is_public is specified, add that condition
    if is_public is not None:
      query['is_public'] = is_public

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

  projection = {'questions': 0}
  
  cursor = collection.find(query, projection)
  if start is not None:
    cursor = cursor.skip(start)
  if size is not None:
    cursor = cursor.limit(size)

  results = await cursor.to_list(length=size)

  for doc in results:
    if '_id' in doc:
      doc['_id'] = str(doc['_id'])

  return results


async def count_quizzes(
  user_id: Optional[str] = None,
  is_public: Optional[bool] = None,
  min_created_date: Optional[datetime] = None,
  max_created_date: Optional[datetime] = None,
  min_last_modified: Optional[datetime] = None,
  max_last_modified: Optional[datetime] = None,
  difficulty: Optional[str] = None,
  categories: Optional[List[str]] = None
) -> int:
  query = {}
  
  # If user_id is not specified, only show public documents
  if user_id is None:
    query['is_public'] = True
  else:
    # If user_id is specified, show user's documents
    query['user_id'] = user_id
    # If is_public is specified, add that condition
    if is_public is not None:
      query['is_public'] = is_public
  
  if min_created_date or max_created_date:
    query["created_date"] = {}
    if min_created_date:
      query["created_date"]["$gte"] = min_created_date
    if max_created_date:
      query["created_date"]["$lte"] = max_created_date
  
  if min_last_modified or max_last_modified:
    query["last_modified_date"] = {}
    if min_last_modified:
      query["last_modified_date"]["$gte"] = min_last_modified
    if max_last_modified:
      query["last_modified_date"]["$lte"] = max_last_modified
  
  if difficulty:
    query["difficulty"] = difficulty
  
  if categories:
    query["category"] = {"$in": categories}
  
  count = await collection.count_documents(query)
  return count
