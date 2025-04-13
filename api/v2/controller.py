from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from api.v2.service import pdf_processor, txt_file_processor, doc_processor

import asyncio
import os
import tempfile
import shutil

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/check")
async def check():
  return {"Message": "Live"}

@app.post("/generate")
async def gen(file: UploadFile, count: int, lang: str, background_tasks: BackgroundTasks):
  filename = file.filename
  file_ext = os.path.splitext(filename)[1].lower()

  with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
    temp_file_path = tmp.name
    content = await file.read()
    tmp.write(content)
  
  # Sử dụng task ID để theo dõi tiến trình
  task_id = f"{filename}_{count}_{lang}"
  
  # Khởi tạo task trong background
  background_tasks.add_task(process_file, temp_file_path, file_ext, count, lang, task_id)
  
  # Trả về ngay lập tức task_id
  return {"task_id": task_id, "status": "processing"}
  
# Thêm route mới để kiểm tra kết quả
@app.get("/status/{task_id}")
async def get_status(task_id: str):
  if task_id in task_results:
    return task_results[task_id]
    # if task_results[task_id]["status"] == "completed":
    #   return task_results[task_id]["result"]
    # return {"status": task_results[task_id]["status"]}
  return {"status": "not_found"}

# Thêm biến lưu trữ kết quả các task
task_results = {}

# Hàm xử lý file trong background
async def process_file(temp_file_path, file_ext, count, lang, task_id):
  try:
    task_results[task_id] = {"status": "processing"}
    json_obj = {}
    if file_ext == '.pdf':
      json_obj = await pdf_processor.generate_questions(temp_file_path, count, lang)
    elif file_ext == '.docx' or file_ext == '.doc':
      json_obj = await doc_processor.generate_questions_from_text(temp_file_path, count, lang)
    elif file_ext == '.md' or file_ext == '.txt':
      json_obj = await txt_file_processor.generate_questions(temp_file_path, count, lang)
    
    task_results[task_id] = {"status": "completed", "result": json_obj}
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}
  finally:
    if os.path.exists(temp_file_path):
      os.remove(temp_file_path)