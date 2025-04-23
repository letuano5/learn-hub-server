from fastapi import APIRouter, UploadFile
from fastapi import BackgroundTasks
from service.generators.service import pdf_processor, txt_file_processor, doc_processor, image_generator, link_generator
from models.quizzes import add_quiz
from controllers.shared_resources import task_semaphore, task_results
from pydantic import BaseModel

import os
import tempfile
import uuid

router = APIRouter()


class TextRequest(BaseModel):
  text: str
  user_id: str
  is_public: bool
  count: int
  lang: str


class LinkRequest(BaseModel):
  link: str
  user_id: str
  is_public: bool
  count: int
  lang: str


@router.post("/generate")
async def gen(file: UploadFile, user_id: str, is_public: bool, count: int, lang: str, background_tasks: BackgroundTasks):
  filename = file.filename
  file_ext = os.path.splitext(filename)[1].lower()

  with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
    temp_file_path = tmp.name
    content = await file.read()
    tmp.write(content)

  task_id = str(uuid.uuid4())

  task_results[task_id] = {"status": "in_queue"}

  background_tasks.add_task(
      process_file, temp_file_path, user_id, is_public, file_ext, count, lang, task_id)

  return {"task_id": task_id, "status": "processing"}


@router.post("/generate/text")
async def gen_from_text(request: TextRequest, background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  task_results[task_id] = {"status": "in_queue"}

  background_tasks.add_task(
      process_text, request.text, request.user_id, request.is_public, request.count, request.lang, task_id)

  return {"task_id": task_id, "status": "processing"}


@router.post("/generate/link")
async def gen_from_link(request: LinkRequest, background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  task_results[task_id] = {"status": "in_queue"}

  background_tasks.add_task(
      process_link, request.link, request.user_id, request.is_public, request.count, request.lang, task_id)

  return {"task_id": task_id, "status": "processing"}


async def process_link(link: str, user_id: str, is_public: bool, count: int, lang: str, task_id: str):
  try:
    async with task_semaphore:
      task_results[task_id] = {"status": "processing", "progress": "Processing web link"}
      
      json_obj = await link_generator.generate_questions(link, count, lang, task_id)

      if len(json_obj) > 0:
        await add_quiz(json_obj, user_id, is_public)
        task_results[task_id] = {"status": "completed", "result": json_obj}
      else:
        task_results[task_id] = {"status": "error", "message": "No questions generated"}
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}


async def process_text(text: str, user_id: str, is_public: bool, count: int, lang: str, task_id: str):
  try:
    async with task_semaphore:
      task_results[task_id] = {"status": "processing", "progress": "Generating questions from text"}
      
      json_obj = await txt_file_processor.generate_questions_from_text(text, count, lang, task_id)

      if len(json_obj) > 0:
        await add_quiz(json_obj, user_id, is_public)
        task_results[task_id] = {"status": "completed", "result": json_obj}
      else:
        task_results[task_id] = {"status": "error", "message": "No questions generated"}
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}


async def process_file(temp_file_path, user_id, is_public, file_ext, count, lang, task_id):
  try:
    async with task_semaphore:
      task_results[task_id] = {"status": "processing", "progress": "Starting file processing"}
      json_obj = {}
      if file_ext == '.pdf':
        json_obj = await pdf_processor.generate_questions(temp_file_path, count, lang, task_id)
      elif file_ext == '.docx' or file_ext == '.doc':
        json_obj = await doc_processor.generate_questions_from_text(temp_file_path, count, lang, task_id)
      elif file_ext == '.md' or file_ext == '.txt':
        json_obj = await txt_file_processor.generate_questions(temp_file_path, count, lang, task_id)
      elif file_ext in ['.png', '.jpg', '.jpeg']:
        json_obj = await image_generator.generate_questions(temp_file_path, count, lang, task_id)
      else:
        raise ValueError(f"Unsupported file type: {file_ext}")

      if len(json_obj) > 0:
        await add_quiz(json_obj, user_id, is_public)
        task_results[task_id] = {"status": "completed", "result": json_obj}
      else:
        task_results[task_id] = {"status": "error", "message": "No questions generated"}
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}
  finally:
    if os.path.exists(temp_file_path):
      os.remove(temp_file_path)
