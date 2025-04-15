from models.mongo import mongo_database

collection = mongo_database['quizzes']

async def add_quiz(quiz, user_id: str, is_public: bool=True):
  quiz_with_info = dict(quiz)
  quiz_with_info['user_id'] = user_id
  quiz_with_info['is_public'] = is_public
  return await collection.insert_one(quiz_with_info)