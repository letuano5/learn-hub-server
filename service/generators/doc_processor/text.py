from service.generators.generators import DocumentProcessor
from llama_index.core import SimpleDirectoryReader

class TextFileProcessor(DocumentProcessor):
  def get_text(self, file_path):
    reader = SimpleDirectoryReader(input_files=[file_path])
    document = reader.load_data()[0]

    return document.get_content()

  async def generate_questions(self, file_path: str, num_question: int, language: str):
    return await self.text_processor.generate_questions(self.get_text(file_path), num_question, language)