from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.quizzes import update_quiz, delete_quiz, search_quizzes
from bson import ObjectId
from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel
from controllers.shared_resources import task_semaphore, task_results
import uuid

router = APIRouter()


class SearchQuery(BaseModel):
  user_id: str
  is_public: bool
  min_created_date: Optional[datetime] = None
  max_created_date: Optional[datetime] = None
  min_last_modified: Optional[datetime] = None
  max_last_modified: Optional[datetime] = None
  difficulty: Optional[str] = None
  categories: Optional[List[str]] = None
  size: Optional[int] = None
  start: Optional[int] = None


@router.put("/{quiz_id}")
async def update_quiz_route(quiz_id: str, quiz_data: Dict, background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  background_tasks.add_task(process_update_quiz, quiz_id, quiz_data, task_id)
  return {"task_id": task_id, "status": "processing"}


@router.delete("/{quiz_id}")
async def delete_quiz_route(quiz_id: str, background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  background_tasks.add_task(process_delete_quiz, quiz_id, task_id)
  return {"task_id": task_id, "status": "processing"}


@router.post("/search")
async def search_quizzes_route(query: SearchQuery, background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  background_tasks.add_task(process_search_quizzes, query, task_id)
  return {"task_id": task_id, "status": "processing"}


async def process_update_quiz(quiz_id: str, quiz_data: Dict, task_id: str):
  try:
    async with task_semaphore:
      task_results[task_id] = {"status": "processing"}
      
      ObjectId(quiz_id)
      
      result = await update_quiz(quiz_id, quiz_data)
      if result.modified_count == 0:
        task_results[task_id] = {"status": "error", "message": "Quiz not found"}
        return
      
      task_results[task_id] = {
        "status": "completed",
        "message": "Quiz updated successfully"
      }
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}


async def process_delete_quiz(quiz_id: str, task_id: str):
  try:
    async with task_semaphore:
      task_results[task_id] = {"status": "processing"}
      
      ObjectId(quiz_id)
      
      result = await delete_quiz(quiz_id)
      if result.deleted_count == 0:
        task_results[task_id] = {"status": "error", "message": "Quiz not found"}
        return
      
      task_results[task_id] = {
        "status": "completed",
        "message": "Quiz deleted successfully"
      }
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}


async def process_search_quizzes(query: SearchQuery, task_id: str):
  try:
    async with task_semaphore:
      task_results[task_id] = {"status": "processing"}
      
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
        start=query.start
      )
      
      task_results[task_id] = {
        "status": "completed",
        "data": results,
      }
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {
      "status": "error",
      "message": str(e)
    }
