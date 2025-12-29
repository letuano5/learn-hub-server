import os

from service.generators.generators import DocumentProcessor, TextProcessor, ImageProcessor, FileProcessor
from llama_index.readers.file import DocxReader
from controllers.shared_resources import task_results


class DOCXProcessor(DocumentProcessor):
  def __init__(self, text_processor: TextProcessor, image_processor: ImageProcessor, file_processor: FileProcessor):
    self.text_processor = text_processor
    self.image_processor = image_processor
    self.file_processor = file_processor

  # def docx_to_base64_images(self, docx_path):
  #   # Extract all content including images
  #   extracted = docx2python(docx_path)

  #   # Get images
  #   base64_images = []
  #   print(extracted, extracted.images)
  #   for image_data in extracted.images:
  #     # Each image is stored as (folder_path, image_name, image_bytes)
  #     # print(image_data)
  #     # image_bytes = image_data[2]
  #     image_bytes = extracted.images[image_data]
  #     base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
  #     base64_images.append(base64_encoded)

  #   return base64_images
  def docx_to_text(self, docx_path: str):
    docx_reader = DocxReader()
    docx_docs = docx_reader.load_data(docx_path)
    text = ''
    for doc in docx_docs:
      text += doc.text + '\n'
    return text

  # OLD METHOD - Using manual text extraction
  async def old_generate_questions_from_text(self, file_path: str, num_question: int, language: str, task_id: str = None, difficulty: str = "medium"):
    try:
      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Reading DOCX file"
        }

      text = self.docx_to_text(file_path)

      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Generating questions from text"
        }

      return await self.text_processor.generate_questions(text, num_question, language, difficulty)

    except Exception as e:
      if task_id:
        task_results[task_id] = {
            "status": "error",
            "message": str(e)
        }
      raise e

  # NEW METHOD - DOCX doesn't support file upload, so we extract text first
  async def generate_questions(self, file_path: str, num_question: int, language: str, task_id: str = None, difficulty: str = "medium"):
    """Generate questions from DOCX by extracting text first (Gemini doesn't support DOCX upload)"""
    try:
      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Reading DOCX file"
        }

      text = self.docx_to_text(file_path)
      
      # Validate word count (max ~77,400 words = 300 pages equivalent)
      word_count = len(text.split())
      max_words = 77400
      if word_count > max_words:
        if task_id:
          task_results[task_id] = {
              "status": "failed",
              "progress": f"DOCX with {word_count} words exceeds {max_words} word limit (~300 pages)"
          }
        raise ValueError(f"DOCX with {word_count} words exceeds {max_words} word limit (~300 pages)")

      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": f"Generating questions from text ({word_count} words)..."
        }

      return await self.text_processor.generate_questions(text, num_question, language, difficulty)

    except Exception as e:
      if task_id:
        task_results[task_id] = {
            "status": "error",
            "message": str(e)
        }
      raise e

  async def extract_pages_to_markdown(self, file_path: str, start_page: int, end_page: int) -> str:
    """Extract DOCX content as text (no page concept in DOCX, returns full text)"""
    # DOCX doesn't have clear page boundaries, just return all text
    return self.docx_to_text(file_path)
