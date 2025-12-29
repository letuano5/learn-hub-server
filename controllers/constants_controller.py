from fastapi import APIRouter
from pydantic import BaseModel
from models.constants import get_all_constants, set_constant

router = APIRouter()


class ConstantUpdateRequest(BaseModel):
  key: str
  value: int


@router.get("/")
async def get_constants():
  """Get all system constants"""
  return await get_all_constants()


@router.post("/")
async def update_constant(request: ConstantUpdateRequest):
  """Update a system constant"""
  await set_constant(request.key, request.value)
  return {
      "message": "Constant updated successfully",
      "key": request.key,
      "value": request.value
  }
