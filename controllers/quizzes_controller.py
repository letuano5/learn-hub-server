from fastapi import APIRouter, BackgroundTasks, HTTPException
from models.quizzes import update_quiz, delete_quiz, search_quizzes, count_quizzes, get_quiz
from bson import ObjectId
from typing import Dict, Optional, List
from datetime import datetime, time
from pydantic import BaseModel, validator
from controllers.shared_resources import task_semaphore, task_results
import uuid

router = APIRouter()


class SearchQuery(BaseModel):
  user_id: Optional[str] = None
  is_public: Optional[bool] = None
  min_created_date: Optional[str] = None
  max_created_date: Optional[str] = None
  min_last_modified: Optional[str] = None
  max_last_modified: Optional[str] = None
  difficulty: Optional[str] = None
  categories: Optional[List[str]] = None
  size: Optional[int] = None
  start: Optional[int] = None
  title: Optional[str] = None

  @validator('min_created_date', 'max_created_date', 'min_last_modified', 'max_last_modified')
  def parse_date(cls, v):
    if v is None:
      return None
    try:
      date_obj = datetime.strptime(v, '%d/%m/%Y')
      return date_obj
    except ValueError:
      raise ValueError('Date must be in dd/mm/yyyy format')

  def model_post_init(self, __context):
    if self.max_created_date:
      self.max_created_date = self.max_created_date.replace(
          hour=23, minute=59, second=59)
    if self.max_last_modified:
      self.max_last_modified = self.max_last_modified.replace(
          hour=23, minute=59, second=59)


@router.put("/{quiz_id}")
async def update_quiz_direct(quiz_id: str, quiz_data: Dict):
  try:
    ObjectId(quiz_id)
    result = await update_quiz(quiz_id, quiz_data)
    if result.modified_count == 0:
      return {"status": "error", "message": "Quiz not found"}
    return {"status": "success", "message": "Quiz updated successfully"}
  except Exception as e:
    return {"status": "error", "message": str(e)}


@router.delete("/{quiz_id}")
async def delete_quiz_direct(quiz_id: str):
  try:
    ObjectId(quiz_id)
    result = await delete_quiz(quiz_id)
    if result.deleted_count == 0:
      return {"status": "error", "success": False, "message": "Quiz not found"}
    return {"status": "success", "success": True, "message": "Quiz deleted successfully"}
  except Exception as e:
    return {"status": "error", "success": False, "message": str(e)}


@router.get("/{quiz_id}")
async def get_quiz_direct(quiz_id: str):
  try:
    ObjectId(quiz_id)
    quiz = await get_quiz(quiz_id)
    if not quiz:
      return {"status": "error", "message": "Quiz not found"}
    return {"status": "success", "data": quiz, "message": "Quiz fetched successfully"}
  except Exception as e:
    return {"status": "error", "message": str(e)}


@router.post("/search")
async def search_quizzes_direct(query: SearchQuery):
  try:
    results = await search_quizzes(
        user_id=query.user_id,
        is_public=query.is_public,
        min_created_date=query.min_created_date,
        max_created_date=query.max_created_date,
        min_last_modified=query.min_last_modified,
        max_last_modified=query.max_last_modified,
        difficulty=query.difficulty,
        categories=query.categories,
        size=query.size,
        start=query.start,
        title=query.title
    )
    return {
        "status": "success",
        "data": results,
        "total": len(results),
        "message": "Quizzes fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "data": [],
        "total": 0,
        "message": str(e)
    }


@router.post("/count")
async def count_quizzes_direct(query: SearchQuery):
  try:
    count = await count_quizzes(
        user_id=query.user_id,
        is_public=query.is_public,
        min_created_date=query.min_created_date,
        max_created_date=query.max_created_date,
        min_last_modified=query.min_last_modified,
        max_last_modified=query.max_last_modified,
        difficulty=query.difficulty,
        categories=query.categories,
        title=query.title
    )
    return {
        "status": "success",
        "count": count,
        "message": "Count completed successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "count": 0,
        "message": str(e)
    }


# @router.put("/{quiz_id}")
# async def update_quiz_route(quiz_id: str, quiz_data: Dict, background_tasks: BackgroundTasks):
#   task_id = str(uuid.uuid4())
#   background_tasks.add_task(process_update_quiz, quiz_id, quiz_data, task_id)
#   return {"task_id": task_id, "status": "processing"}


# @router.delete("/{quiz_id}")
# async def delete_quiz_route(quiz_id: str, background_tasks: BackgroundTasks):
#   task_id = str(uuid.uuid4())
#   background_tasks.add_task(process_delete_quiz, quiz_id, task_id)
#   return {"task_id": task_id, "status": "processing"}


# @router.get("/{quiz_id}")
# async def get_quiz_route(quiz_id: str, background_tasks: BackgroundTasks):
#   task_id = str(uuid.uuid4())
#   background_tasks.add_task(process_get_quiz, quiz_id, task_id)
#   return {"task_id": task_id, "status": "processing"}


# @router.post("/search")
# async def search_quizzes_route(query: SearchQuery, background_tasks: BackgroundTasks):
#   task_id = str(uuid.uuid4())
#   background_tasks.add_task(process_search_quizzes, query, task_id)
#   return {"task_id": task_id, "status": "processing"}


# @router.post("/count")
# async def count_quizzes_route(query: SearchQuery, background_tasks: BackgroundTasks):
#   task_id = str(uuid.uuid4())
#   background_tasks.add_task(process_count_quizzes, query, task_id)
#   return {"task_id": task_id, "status": "processing"}


# async def process_update_quiz(quiz_id: str, quiz_data: Dict, task_id: str):
#   try:
#     async with task_semaphore:
#       task_results[task_id] = {"status": "processing"}

#       ObjectId(quiz_id)

#       result = await update_quiz(quiz_id, quiz_data)
#       if result.modified_count == 0:
#         task_results[task_id] = {"status": "error", "message": "Quiz not found"}
#         return

#       task_results[task_id] = {
#         "status": "completed",
#         "message": "Quiz updated successfully"
#       }
#   except Exception as e:
#     import traceback
#     traceback.print_exc()
#     task_results[task_id] = {"status": "error", "message": str(e)}


# async def process_delete_quiz(quiz_id: str, task_id: str):
#   try:
#     async with task_semaphore:
#       task_results[task_id] = {"status": "processing"}

#       ObjectId(quiz_id)

#       result = await delete_quiz(quiz_id)
#       if result.deleted_count == 0:
#         task_results[task_id] = {"status": "error", "success": False, "message": "Quiz not found"}
#         return

#       task_results[task_id] = {
#         "status": "completed",
#         "success": True,
#         "message": "Quiz deleted successfully"
#       }
#   except Exception as e:
#     import traceback
#     traceback.print_exc()
#     task_results[task_id] = {"status": "error", "success": False, "message": str(e)}


# async def process_get_quiz(quiz_id: str, task_id: str):
#   try:
#     async with task_semaphore:
#       task_results[task_id] = {"status": "processing"}

#       ObjectId(quiz_id)

#       quiz = await get_quiz(quiz_id)
#       if not quiz:
#         task_results[task_id] = {"status": "error", "message": "Quiz not found"}
#         return

#       task_results[task_id] = {
#         "status": "completed",
#         "data": quiz,
#         "message": "Quiz fetched successfully"
#       }
#   except Exception as e:
#     import traceback
#     traceback.print_exc()
#     task_results[task_id] = {"status": "error", "message": str(e)}


# async def process_search_quizzes(query: SearchQuery, task_id: str):
#   try:
#     async with task_semaphore:
#       task_results[task_id] = {"status": "processing"}

#       results = await search_quizzes(
#         user_id=query.user_id,
#         is_public=query.is_public,
#         min_created_date=query.min_created_date,
#         max_created_date=query.max_created_date,
#         min_last_modified=query.min_last_modified,
#         max_last_modified=query.max_last_modified,
#         difficulty=query.difficulty,
#         categories=query.categories,
#         size=query.size,
#         start=query.start
#       )

#       task_results[task_id] = {
#         "status": "completed",
#         "data": results,
#         "total": len(results),
#         "message": "Quizzes fetched successfully"
#       }
#   except Exception as e:
#     import traceback
#     traceback.print_exc()
#     task_results[task_id] = {
#       "status": "error",
#       "data": [],
#       "total": 0,
#       "message": str(e)
#     }


# async def process_count_quizzes(query: SearchQuery, task_id: str):
#   try:
#     async with task_semaphore:
#       task_results[task_id] = {"status": "processing"}

#       count = await count_quizzes(
#         user_id=query.user_id,
#         is_public=query.is_public,
#         min_created_date=query.min_created_date,
#         max_created_date=query.max_created_date,
#         min_last_modified=query.min_last_modified,
#         max_last_modified=query.max_last_modified,
#         difficulty=query.difficulty,
#         categories=query.categories
#       )

#       task_results[task_id] = {
#         "status": "completed",
#         "count": count,
#         "message": "Count completed successfully"
#       }
#   except Exception as e:
#     import traceback
#     traceback.print_exc()
#     task_results[task_id] = {
#       "status": "error",
#       "count": 0,
#       "message": str(e)
#     }
