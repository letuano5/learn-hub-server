from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.v2.service import pdf_processor, txt_file_processor, doc_processor

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
async def gen(file: UploadFile, count: int, lang: str):
  filename = file.filename
  file_ext = os.path.splitext(filename)[1].lower()

  with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
    temp_file_path = tmp.name
    content = await file.read()
    tmp.write(content)

  try:
    json_obj = {}
    if file_ext == '.pdf':
      json_obj = pdf_processor.generate_questions(temp_file_path, count, lang)
    elif file_ext == '.docx' or file_ext == '.doc':
      json_obj = doc_processor.generate_questions_from_text(temp_file_path, count, lang)
    elif file_ext == '.md' or file_ext == '.txt':
      json_obj = txt_file_processor.generate_questions(temp_file_path, count, lang)
    return json_obj
  finally:
    if os.path.exists(temp_file_path):
      os.remove(temp_file_path)