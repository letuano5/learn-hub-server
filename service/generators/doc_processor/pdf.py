from service.generators.generators import DocumentProcessor
import fitz
from PIL import Image
import base64
import io
import asyncio
from controllers.shared_resources import task_results

class PDFProcessor(DocumentProcessor):
  # https://python.langchain.com/docs/how_to/document_loader_pdf/#use-of-multimodal-models
  def pdf_to_base64(self, pdf_path: str, task_id: str = None):
    pdf_document = fitz.open(pdf_path)
    total_pages = pdf_document.page_count
    pages = []
    
    for page_number in range(total_pages):
      if task_id:
        task_results[task_id] = {
          "status": "processing",
          "progress": f"Processing page {page_number + 1}/{total_pages}"
        }
      
      page = pdf_document.load_page(page_number)

      original_width = page.rect.width
      original_height = page.rect.height
      
      is_portrait = original_height > original_width
      
      max_width = 720 if is_portrait else 1280
      max_height = 1280 if is_portrait else 720
      
      width_scale = max_width / original_width
      height_scale = max_height / original_height
      scale = min(width_scale, height_scale)
      
      scale = min(scale, 1.0)

      print(original_width, original_height, scale)

      # Create pixmap with calculated scale
      pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
      img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
      
      buffer = io.BytesIO()
      # Save PNG with optimization
      img.save(buffer, 
              format="PNG",
              optimize=True,  # Enable PNG optimization
              compress_level=6)  # Balanced compression
      
      pages.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))
    
    return pages

  def pdf_to_text(self, pdf_path: str, task_id: str = None):
    text = ""
    with fitz.open(pdf_path) as doc:
      total_pages = len(doc)
      for page_num in range(total_pages):
        if task_id:
          task_results[task_id] = {
            "status": "processing",
            "progress": f"Processing page {page_num + 1}/{total_pages}"
          }
        page = doc[page_num]
        text += page.get_text()
    return text

  async def generate_questions(self, pdf_path: str, num_question: int, language: str, task_id: str = None):
    base64_pages = await asyncio.to_thread(self.pdf_to_base64, pdf_path, task_id)
    if task_id:
      task_results[task_id] = {"status": "processing", "progress": "Generating questions from images"}
    return await self.image_processor.generate_questions(base64_pages, num_question, language)

  async def generate_questions_from_text(self, pdf_path: str, num_question: int, language: str, task_id: str = None):
    text = await asyncio.to_thread(self.pdf_to_text, pdf_path, task_id)
    if task_id:
      task_results[task_id] = {"status": "processing", "progress": "Generating questions from text"}
    return await self.text_processor.generate_questions(text, num_question, language)