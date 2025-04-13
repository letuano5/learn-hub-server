from service.generators.generators import DocumentProcessor
import fitz
from PIL import Image
import base64
import io

class PDFProcessor(DocumentProcessor):
  # https://python.langchain.com/docs/how_to/document_loader_pdf/#use-of-multimodal-models
  def pdf_to_base64(self, pdf_path: str):
    pdf_document = fitz.open(pdf_path)

    pages = []
    for page_number in range(pdf_document.page_count):

      page = pdf_document.load_page(page_number)
      pix = page.get_pixmap()
      img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

      buffer = io.BytesIO()
      img.save(buffer, format="PNG")

      pages.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

    return pages

  def pdf_to_text(self, pdf_path: str):
    text = ""
    with fitz.open(pdf_path) as doc:
      for page_num in range(len(doc)):
        page = doc[page_num]
        text += page.get_text()

    return text

  async def generate_questions(self, pdf_path: str, num_question: int, language: str):
    return await self.image_processor.generate_questions(self.pdf_to_base64(pdf_path), num_question, language)

  async def generate_questions_from_text(self, pdf_path: str, num_question: int, language: str):
    return await self.text_processor.generate_questions(self.pdf_to_text(pdf_path), num_question, language)