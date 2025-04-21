from fastapi import APIRouter, UploadFile, File
from models.documents import add_doc_with_link, get_document, search_documents, count_documents
import os
import uuid
import tempfile
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, validator

router = APIRouter()


class SearchQuery(BaseModel):
  user_id: str
  is_public: bool
  min_date: Optional[str] = None
  max_date: Optional[str] = None
  filename: Optional[str] = None
  file_extension: Optional[str] = None
  size: Optional[int] = None
  start: Optional[int] = None

  @validator('min_date', 'max_date')
  def parse_date(cls, v):
    if v is None:
      return None
    try:
      date_obj = datetime.strptime(v, '%d/%m/%Y')
      return date_obj
    except ValueError:
      raise ValueError('Date must be in dd/mm/yyyy format')

  def model_post_init(self, __context):
    if self.max_date:
      self.max_date = self.max_date.replace(hour=23, minute=59, second=59)


@router.post("/document/search")
async def search_documents_route(query: SearchQuery):
  try:
    results = await search_documents(
      user_id=query.user_id,
      is_public=query.is_public,
      min_date=query.min_date,
      max_date=query.max_date,
      filename=query.filename,
      file_extension=query.file_extension,
      size=query.size,
      start=query.start
    )
    
    return {
      "status": "success",
      "data": results,
      "total": len(results),
      "message": "Documents fetched successfully"
    }
  except Exception as e:
    return {
      "status": "error",
      "data": [],
      "total": 0,
      "message": str(e)
    }


@router.post("/document/count")
async def count_documents_route(query: SearchQuery):
  try:
    total = await count_documents(
      user_id=query.user_id,
      is_public=query.is_public,
      min_date=query.min_date,
      max_date=query.max_date,
      filename=query.filename,
      file_extension=query.file_extension
    )
    
    return {
      "status": "success",
      "count": total,
      "message": "Count fetched successfully"
    }
  except Exception as e:
    return {
      "status": "error",
      "count": 0,
      "message": str(e)
    }


@router.get("/document/{document_id}")
async def get_document_route(document_id: str):
  try:
    document = await get_document(document_id)
    if not document:
      return {
        "status": "error",
        "data": {},
        "message": "Document not found"
      }
    
    return {
      "status": "success",
      "data": document,
      "message": "Document fetched successfully"
    }
  except Exception as e:
    return {
      "status": "error",
      "data": {},
      "message": str(e)
    }


@router.post("/upload")
async def upload_document(
    user_id: str,
    is_public: bool,
    file: UploadFile = File(...)
):
  try:
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
      temp_file_path = tmp.name
      content = await file.read()
      tmp.write(content)

    result = await add_doc_with_link(
      user_id=user_id,
      is_public=is_public,
      filename=file.filename,
      file_path=temp_file_path,
    )

    os.remove(temp_file_path)

    return {
      "status": "success",
      "message": "File uploaded successfully",
      # "result": result
    }

  except Exception as e:
    if os.path.exists(temp_file_path):
      os.remove(temp_file_path)
    
    return {
      "status": "error",
      "message": str(e)
    } 