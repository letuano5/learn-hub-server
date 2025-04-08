from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.v2.service import processor

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
  with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    temp_file_path = tmp.name
    content = await file.read()
    tmp.write(content)
  json_obj = processor.generate_questions(temp_file_path, count, lang)
  os.remove(temp_file_path)
  return JSONResponse(content=json_obj)