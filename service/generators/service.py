import os
from service.generators.generators import default_prompt, QuestionGenerator, TextProcessor, ImageProcessor
from service.generators.summarizer import Summarizer
from service.generators.doc_processor.docx import DOCXProcessor
from service.generators.doc_processor.pdf import PDFProcessor
from service.generators.doc_processor.text import TextFileProcessor

api_key = os.environ.get('GOOGLE_GENAI_KEY')

generator = QuestionGenerator(api_key=api_key, default_prompt=default_prompt)
summarizer = Summarizer(api_key=api_key)
text_processor = TextProcessor(generator)
image_processor = ImageProcessor(generator, summarizer, text_processor)
pdf_processor = PDFProcessor(text_processor, image_processor)
txt_file_processor = TextFileProcessor(text_processor, image_processor)
doc_processor = DOCXProcessor(text_processor, image_processor)