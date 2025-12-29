from fastapi import APIRouter, UploadFile
from fastapi import BackgroundTasks
from service.generators.service import pdf_processor, txt_file_processor, doc_processor, image_generator, link_generator, category_client
from models.quizzes import add_quiz
from models.categories import get_all_categories
from models.quota import check_quiz_quota, increment_quiz_count
from controllers.shared_resources import task_semaphore, task_results
from pydantic import BaseModel
import os
import tempfile
import uuid
import json
from controllers.document_controller import download_document_file

router = APIRouter()


class TextRequest(BaseModel):
  text: str
  user_id: str
  is_public: bool
  count: int
  lang: str
  difficulty: str = "medium"


class LinkRequest(BaseModel):
  link: str
  user_id: str
  is_public: bool
  count: int
  lang: str
  difficulty: str = "medium"


# OLD ENDPOINT - Using manual text/image extraction
@router.post("/old-generate")
async def old_gen(file: UploadFile, user_id: str, is_public: bool, count: int, lang: str, background_tasks: BackgroundTasks, difficulty: str = "medium"):
  filename = file.filename
  file_ext = os.path.splitext(filename)[1].lower()

  with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
    temp_file_path = tmp.name
    content = await file.read()
    tmp.write(content)

  task_id = str(uuid.uuid4())

  task_results[task_id] = {"status": "in_queue"}

  background_tasks.add_task(
      old_process_file, temp_file_path, user_id, is_public, file_ext, count, lang, difficulty, task_id)

  return {"task_id": task_id, "status": "processing"}


# NEW ENDPOINT - Using Gemini file upload API
@router.post("/generate")
async def gen(file: UploadFile, user_id: str, is_public: bool, count: int, lang: str, background_tasks: BackgroundTasks, difficulty: str = "medium"):
  filename = file.filename
  file_ext = os.path.splitext(filename)[1].lower()

  with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
    temp_file_path = tmp.name
    content = await file.read()
    tmp.write(content)

  task_id = str(uuid.uuid4())

  task_results[task_id] = {"status": "in_queue"}

  background_tasks.add_task(
      process_file, temp_file_path, user_id, is_public, file_ext, count, lang, difficulty, task_id)

  return {"task_id": task_id, "status": "processing"}


@router.post("/generate/text")
async def gen_from_text(request: TextRequest, background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  task_results[task_id] = {"status": "in_queue"}

  background_tasks.add_task(
      process_text, request.text, request.user_id, request.is_public, request.count, request.lang, request.difficulty, task_id)

  return {"task_id": task_id, "status": "processing"}


@router.post("/generate/link")
async def gen_from_link(request: LinkRequest, background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  task_results[task_id] = {"status": "in_queue"}

  background_tasks.add_task(
      process_link, request.link, request.user_id, request.is_public, request.count, request.lang, request.difficulty, task_id)

  return {"task_id": task_id, "status": "processing"}


# OLD FUNCTION - Using manual extraction
async def old_process_document_download(document_id: str, user_id: str, is_public: bool, count: int, lang: str, difficulty: str, task_id: str):
  try:
    task_results[task_id] = {"status": "processing",
                             "message": f"Downloading {document_id}"}
    temp_file_path, file_ext = await download_document_file(document_id)
    print(
        f"Downloaded {document_id} to {temp_file_path} with extension {file_ext}")
    if not temp_file_path:
      task_results[task_id] = {
          "status": "error",
          "message": file_ext
      }
      return

    await old_process_file(temp_file_path, user_id, is_public, '.' + file_ext, count, lang, difficulty, task_id)
  except Exception as e:
    task_results[task_id] = {
        "status": "error",
        "message": str(e)
    }


# NEW FUNCTION - Using Gemini file upload
async def process_document_download(document_id: str, user_id: str, is_public: bool, count: int, lang: str, difficulty: str, task_id: str):
  try:
    task_results[task_id] = {"status": "processing",
                             "message": f"Downloading {document_id}"}
    temp_file_path, file_ext = await download_document_file(document_id)
    print(
        f"Downloaded {document_id} to {temp_file_path} with extension {file_ext}")
    if not temp_file_path:
      task_results[task_id] = {
          "status": "error",
          "message": file_ext
      }
      return

    await process_file(temp_file_path, user_id, is_public, '.' + file_ext, count, lang, difficulty, task_id)
  except Exception as e:
    task_results[task_id] = {
        "status": "error",
        "message": str(e)
    }


# OLD ENDPOINT
@router.post("/old-generate/document")
async def old_generate_from_document(
    document_id: str,
    user_id: str,
    is_public: bool,
    count: int,
    lang: str,
    background_tasks: BackgroundTasks,
    difficulty: str = "medium"
):
  try:
    task_id = str(uuid.uuid4())
    task_results[task_id] = {"status": "in_queue"}

    background_tasks.add_task(
        old_process_document_download,
        document_id,
        user_id,
        is_public,
        count,
        lang,
        difficulty,
        task_id
    )

    return {"task_id": task_id, "status": "processing"}
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


# NEW ENDPOINT
@router.post("/generate/document")
async def generate_from_document(
    document_id: str,
    user_id: str,
    is_public: bool,
    count: int,
    lang: str,
    background_tasks: BackgroundTasks,
    difficulty: str = "medium"
):
  try:
    task_id = str(uuid.uuid4())
    task_results[task_id] = {"status": "in_queue"}

    background_tasks.add_task(
        process_document_download,
        document_id,
        user_id,
        is_public,
        count,
        lang,
        difficulty,
        task_id
    )

    return {"task_id": task_id, "status": "processing"}
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


async def select_categories_and_title(questions: list, categories: list) -> tuple[list[str], str]:
  """
  Use AI to select relevant categories and generate a title for the quiz
  Returns a tuple of (selected_categories, title)
  """
  prompt = f"""
    Given the following quiz questions and available categories, select the most relevant categories and generate a short, descriptive title for the quiz.
    
    Questions:
    {json.dumps(questions, indent=2)}
    
    Available Categories:
    {json.dumps(categories, indent=2)}
    
    Please respond in the following JSON format:
    {{
        "categories": ["category1", "category2", ...],  # Select 1-3 most relevant categories. Just select the categories in the list, no other text.
        "title": "A short, descriptive title for the quiz"
    }}
    """

  response = await category_client.model.generate_content_async(contents=prompt)
  result = json.loads(response.text.replace('```json', '').replace('```', ''))

  return result["categories"], result["title"]


async def process_link(link: str, user_id: str, is_public: bool, count: int, lang: str, difficulty: str, task_id: str):
  try:
    # Check quota before processing
    can_create, quota_info, max_quizzes = await check_quiz_quota(user_id)
    if not can_create:
      task_results[task_id] = {
          "status": "failed",
          "message": f"Quiz limit reached. You have created {quota_info['total_quizzes']}/{max_quizzes} quizzes."
      }
      return
    
    async with task_semaphore:
      task_results[task_id] = {"status": "processing",
                               "progress": "Processing web link"}

      json_obj = await link_generator.generate_questions(link, count, lang, task_id, difficulty)

      if len(json_obj) > 0:
        categories = await get_all_categories()

        selected_categories, title = await select_categories_and_title(json_obj["questions"], categories)

        json_obj["categories"] = selected_categories
        json_obj["title"] = title
        json_obj["difficulty"] = difficulty

        await add_quiz(json_obj, user_id, is_public)
        await increment_quiz_count(user_id)  # Increment quota after successful creation
        task_results[task_id] = {"status": "completed", "result": json_obj}
      else:
        task_results[task_id] = {"status": "error",
                                 "message": "No questions generated"}
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}


async def process_text(text: str, user_id: str, is_public: bool, count: int, lang: str, difficulty: str, task_id: str):
  try:
    # Check quota before processing
    can_create, quota_info, max_quizzes = await check_quiz_quota(user_id)
    if not can_create:
      task_results[task_id] = {
          "status": "failed",
          "message": f"Quiz limit reached. You have created {quota_info['total_quizzes']}/{max_quizzes} quizzes."
      }
      return
    
    async with task_semaphore:
      task_results[task_id] = {"status": "processing",
                               "progress": "Generating questions from text"}

      json_obj = await txt_file_processor.generate_questions_from_text(text, count, lang, task_id, difficulty)

      if len(json_obj) > 0:
        categories = await get_all_categories()

        selected_categories, title = await select_categories_and_title(json_obj["questions"], categories)

        json_obj["categories"] = selected_categories
        json_obj["title"] = title
        json_obj["difficulty"] = difficulty

        await add_quiz(json_obj, user_id, is_public)
        await increment_quiz_count(user_id)  # Increment quota after successful creation
        task_results[task_id] = {"status": "completed", "result": json_obj}
      else:
        task_results[task_id] = {"status": "error",
                                 "message": "No questions generated"}
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}


# OLD FUNCTION - Using manual extraction
async def old_process_file(temp_file_path, user_id, is_public, file_ext, count, lang, difficulty, task_id):
  try:
    # Check quota before processing
    can_create, quota_info, max_quizzes = await check_quiz_quota(user_id)
    if not can_create:
      task_results[task_id] = {
          "status": "failed",
          "message": f"Quiz limit reached. You have created {quota_info['total_quizzes']}/{max_quizzes} quizzes."
      }
      if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
      return
    
    async with task_semaphore:
      task_results[task_id] = {"status": "processing",
                               "progress": "Starting file processing"}
      print("Processing file: ", temp_file_path)
      json_obj = {}
      if file_ext == '.pdf':
        json_obj = await pdf_processor.old_generate_questions(temp_file_path, count, lang, task_id, difficulty)
      elif file_ext == '.docx' or file_ext == '.doc':
        json_obj = await doc_processor.old_generate_questions_from_text(temp_file_path, count, lang, task_id, difficulty)
      elif file_ext == '.md' or file_ext == '.txt':
        json_obj = await txt_file_processor.generate_questions(temp_file_path, count, lang, task_id, difficulty)
      elif file_ext in ['.png', '.jpg', '.jpeg']:
        json_obj = await image_generator.generate_questions(temp_file_path, count, lang, task_id, difficulty)
      else:
        raise ValueError(f"Unsupported file type: {file_ext}")

      print("Done generating questions")

      if len(json_obj) > 0:
        categories = await get_all_categories()

        selected_categories, title = await select_categories_and_title(json_obj["questions"], categories)

        json_obj["categories"] = selected_categories
        json_obj["title"] = title
        json_obj["difficulty"] = difficulty

        await add_quiz(json_obj, user_id, is_public)
        await increment_quiz_count(user_id)  # Increment quota after successful creation
        task_results[task_id] = {"status": "completed", "result": json_obj}
      else:
        task_results[task_id] = {"status": "error",
                                 "message": "No questions generated"}
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}
  finally:
    if os.path.exists(temp_file_path):
      os.remove(temp_file_path)


# NEW FUNCTION - Using Gemini file upload API
async def process_file(temp_file_path, user_id, is_public, file_ext, count, lang, difficulty, task_id):
  try:
    # Check quota before processing
    can_create, quota_info, max_quizzes = await check_quiz_quota(user_id)
    if not can_create:
      task_results[task_id] = {
          "status": "failed",
          "message": f"Quiz limit reached. You have created {quota_info['total_quizzes']}/{max_quizzes} quizzes."
      }
      if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
      return
    
    async with task_semaphore:
      task_results[task_id] = {"status": "processing",
                               "progress": "Starting file processing"}
      print("Processing file: ", temp_file_path)
      json_obj = {}
      
      # Use new Gemini file upload for PDF/DOCX
      if file_ext == '.pdf':
        json_obj = await pdf_processor.generate_questions(temp_file_path, count, lang, task_id, difficulty)
      elif file_ext == '.docx' or file_ext == '.doc':
        json_obj = await doc_processor.generate_questions(temp_file_path, count, lang, task_id, difficulty)
      # Text and image files use existing methods
      elif file_ext == '.md' or file_ext == '.txt':
        json_obj = await txt_file_processor.generate_questions(temp_file_path, count, lang, task_id, difficulty)
      elif file_ext in ['.png', '.jpg', '.jpeg']:
        json_obj = await image_generator.generate_questions(temp_file_path, count, lang, task_id, difficulty)
      else:
        raise ValueError(f"Unsupported file type: {file_ext}")

      print("Done generating questions")

      if len(json_obj) > 0:
        categories = await get_all_categories()

        selected_categories, title = await select_categories_and_title(json_obj["questions"], categories)

        json_obj["categories"] = selected_categories
        json_obj["title"] = title
        json_obj["difficulty"] = difficulty

        await add_quiz(json_obj, user_id, is_public)
        await increment_quiz_count(user_id)  # Increment quota after successful creation
        task_results[task_id] = {"status": "completed", "result": json_obj}
      else:
        task_results[task_id] = {"status": "error",
                                 "message": "No questions generated"}
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}
  finally:
    if os.path.exists(temp_file_path):
      os.remove(temp_file_path)
