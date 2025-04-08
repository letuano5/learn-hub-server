from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import pdfplumber
import asyncio
import json
from io import BytesIO
from api.v1.service import generate

origins = ["*"]

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/check")
async def check():
  return {"Message": "Live"}

async def extract_text_from_pdf(pdf_data: bytes):
  pdf_file = BytesIO(pdf_data)
  loop = asyncio.get_running_loop()
  return await asyncio.to_thread(_sync_extract_text, pdf_file)

def _sync_extract_text(pdf_file: BytesIO):
  with pdfplumber.open(pdf_file) as pdf:
      return "\n".join([page.extract_text() or "" for page in pdf.pages])

@app.post("/generate")
async def gen(file: UploadFile, count: int, lang: str):
  pdf_data = await file.read()
  text = await extract_text_from_pdf(pdf_data)
  response = generate(text, count, lang).replace('```json', '').replace('```', '')
  json_obj = json.loads(response)
  return JSONResponse(content=json_obj)