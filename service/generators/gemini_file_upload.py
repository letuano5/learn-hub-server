"""
Gemini File Upload Service
Handles file uploads to Gemini API and validation
"""

import asyncio
import tempfile
import os
from typing import Tuple, Optional

import google.generativeai as genai
import fitz  # PyMuPDF
from llama_index.readers.file import DocxReader

from service.generators.base import GenAIClient, fix_json_array
from service.generators.constants import get_user_prompt_file


class GeminiFileUploadClient(GenAIClient):
  """Client for Gemini file upload operations with validation"""
  
  def __init__(self, api_key: str):
    super().__init__(api_key=api_key)
    self.api_key = api_key
  
  async def upload_file(self, file_path: str):
    """
    Upload a file to Gemini API
    
    Args:
        file_path: Path to the file to upload
        
    Returns:
        Uploaded file reference from Gemini
    """
    uploaded_file = await asyncio.to_thread(genai.upload_file, file_path)
    return uploaded_file
  
  def validate_pdf_page_count(self, file_path: str, max_pages: int = 300) -> Tuple[bool, int]:
    """
    Validate PDF page count
    
    Args:
        file_path: Path to PDF file
        max_pages: Maximum allowed pages
        
    Returns:
        Tuple of (is_valid, page_count)
    """
    try:
      with fitz.open(file_path) as doc:
        page_count = len(doc)
        return page_count <= max_pages, page_count
    except Exception as e:
      raise Exception(f"Error reading PDF: {str(e)}")
  
  def validate_docx_page_count(self, file_path: str, max_pages: int = 300) -> Tuple[bool, int]:
    """
    Estimate DOCX page count based on word count
    Assumes ~250 words per page
    
    Args:
        file_path: Path to DOCX file
        max_pages: Maximum allowed pages
        
    Returns:
        Tuple of (is_valid, estimated_page_count)
    """
    try:
      reader = DocxReader()
      docs = reader.load_data(file_path)
      
      total_words = 0
      for doc in docs:
        total_words += len(doc.text.split())
      
      # Estimate pages: ~250 words per page
      estimated_pages = (total_words + 249) // 250  # Round up
      return estimated_pages <= max_pages, estimated_pages
    except Exception as e:
      raise Exception(f"Error reading DOCX: {str(e)}")
  
  def validate_text_word_count(self, text: str, max_words: int = 77400) -> Tuple[bool, int]:
    """
    Validate text word count
    Max words = 258 tokens/page * 300 pages = 77,400 words
    
    Args:
        text: Text content to validate
        max_words: Maximum allowed words
        
    Returns:
        Tuple of (is_valid, word_count)
    """
    word_count = len(text.split())
    return word_count <= max_words, word_count
  
  async def generate_questions_from_file(
      self,
      file_ref,
      num_questions: int,
      language: str,
      difficulty: str
  ) -> dict:
    """
    Generate questions from an uploaded file using Gemini
    
    Args:
        file_ref: Uploaded file reference from Gemini
        num_questions: Number of questions to generate
        language: Language for questions
        difficulty: Difficulty level (easy/medium/hard)
        
    Returns:
        Dictionary with questions array
    """
    # Create prompt for question generation
    prompt = get_user_prompt_file(lang=language, count=num_questions, difficulty=difficulty)
    
    # Generate questions
    response = await self.model.generate_content_async(
        contents=[prompt, file_ref]
    )
    
    # Parse response
    result = fix_json_array([response.text])
    return result
  
  async def extract_file_to_markdown_full(
      self,
      file_path: str
  ) -> str:
    """
    Extract entire file content and convert to markdown using Gemini
    Used for DOCX files where page boundaries are unclear
    
    Args:
        file_path: Path to the file
        
    Returns:
        Markdown content extracted from the entire file
    """
    try:
      # Upload to Gemini
      uploaded_file = await self.upload_file(file_path)
      
      # Create prompt to extract content as markdown
      prompt = """
Extract all content from this document and return it in Markdown format.
Include all text, preserve structure (headings, lists, tables), but do not add any commentary or extra text.
Return ONLY the markdown content, nothing else.
"""
      
      # Generate markdown
      response = await self.model.generate_content_async(
          contents=[prompt, uploaded_file]
      )
      
      return response.text
      
    except Exception as e:
      raise Exception(f"Error extracting file to markdown: {str(e)}")
  
  async def extract_pdf_pages_to_markdown(
      self,
      file_path: str,
      start_page: int,
      end_page: int
  ) -> str:
    """
    Extract pages from a PDF and convert to markdown using Gemini
    Used for Q&A document processing
    
    Args:
        file_path: Path to the PDF file
        start_page: Starting page number (1-indexed)
        end_page: Ending page number (1-indexed, inclusive)
        
    Returns:
        Markdown content extracted from the pages
    """
    temp_file_path = None
    try:
      # Extract pages from PDF
      doc = fitz.open(file_path)
      # Create new PDF with selected pages
      new_doc = fitz.open()
      for page_num in range(start_page - 1, end_page):
        if page_num < len(doc):
          new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
      
      # Close source document
      doc.close()
      
      # Save to temp file
      temp_file_path = tempfile.mktemp(suffix='.pdf')
      new_doc.save(temp_file_path)
      new_doc.close()
      
      # Upload to Gemini
      uploaded_file = await self.upload_file(temp_file_path)
      
      # Create prompt to extract content as markdown
      prompt = """
Extract all content from this PDF document and return it in Markdown format.
Include all text, preserve structure (headings, lists, tables), but do not add any commentary or extra text.
Return ONLY the markdown content, nothing else.
"""
      
      # Generate markdown
      response = await self.model.generate_content_async(
          contents=[prompt, uploaded_file]
      )
      
      return response.text
      
    finally:
      # Clean up temp file
      if temp_file_path and os.path.exists(temp_file_path):
        # try:
        os.remove(temp_file_path)
        # except PermissionError:
        #   # On Windows, sometimes file is still locked, wait a bit and retry
        #   import time
        #   time.sleep(0.1)
        #   try:
        #     os.remove(temp_file_path)
        #   except:
        #     pass  # If still fails, let OS clean it up later
