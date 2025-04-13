from service.generators.generators import DocumentProcessor
from llama_index.readers.file import DocxReader

class DOCXProcessor(DocumentProcessor):

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

  async def generate_questions_from_text(self, docx_path: str, num_question: int, language: str):
    return await self.text_processor.generate_questions(self.docx_to_text(docx_path), num_question, language)