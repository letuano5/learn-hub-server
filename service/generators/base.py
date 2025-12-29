import google.generativeai as old_genai
import json
from catboxpy import AsyncCatboxClient
from google import genai
from google.genai import types
import asyncio
import pathlib
import os
import tempfile


class GenAIClient:
  def __init__(self, api_key: str, default_prompt: str = ''):
    old_genai.configure(api_key=api_key)

    if len(default_prompt) > 0:
      self.model = old_genai.GenerativeModel(
          'gemini-2.5-pro', system_instruction=default_prompt)
    else:
      self.model = old_genai.GenerativeModel('gemini-2.5-pro')


class FileUploader(GenAIClient):
  async def upload_pdf(self, pdf_path: str):
    return await asyncio.to_thread(old_genai.upload_file, pdf_path)

# TODO: Update when error occurred to another chars (" for example)


def load_json(json_string):
  return json.loads(json_string)
  # return json.loads(json_string.replace('\\', '\\\\'))


def fix_json_array(jsons):
  print('received=', jsons)
  questions = []
  for subquestion in jsons:
    subquestion = subquestion.replace('```json', '').replace('```', '')
    print(subquestion)
    data = load_json(subquestion)
    print(data)

    for item in data['questions']:
      questions.append({
          "question": item["question"],
          "options": item["options"],
          "answer": item["answer"],
          "explanation": item["explanation"]
      })

  merged = {"questions": questions}

  return merged


async def upload_file(file_path: str):
  try:
    file_ext = os.path.splitext(file_path)[1].lower()
    temp_path = None

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
      temp_path = tmp.name
      content = await asyncio.to_thread(lambda: open(file_path, 'rb').read())
      tmp.write(content)

    if file_ext == '.doc':
      new_path = temp_path.replace('.doc', '.ahihi1')
      os.rename(temp_path, new_path)
      temp_path = new_path
    elif file_ext == '.docx':
      new_path = temp_path.replace('.docx', '.ahihi2')
      os.rename(temp_path, new_path)
      temp_path = new_path

    client = AsyncCatboxClient()
    file_url = await client.upload(temp_path)

    if temp_path and os.path.exists(temp_path):
      os.remove(temp_path)

    return file_url

  except Exception as e:
    if temp_path and os.path.exists(temp_path):
      os.remove(temp_path)
    raise Exception(f"Error uploading file: {str(e)}")