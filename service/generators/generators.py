import asyncio
from service.generators.base import GenAIClient
from service.generators.base import fix_json_array
from service.generators.summarizer import Summarizer
from service.generators.constants import default_prompt, get_user_prompt_images, get_user_prompt_text, get_user_prompt_file
import base64

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# TODO: Language mapping here


class QuestionGenerator(GenAIClient):

  async def generate_from_base64_images(self, prompt: str, images):
    contents = [prompt]
    for image in images:
      contents.append({
          "mime_type": "image/jpeg",
          "data": base64.b64decode(image)
      })
    resp = await self.model.generate_content_async(contents=contents)
    return resp.text

  async def generate_from_text(self, content: str):
    resp = await self.model.generate_content_async(contents=content)
    return resp.text

  async def generate_from_genai_link(self, prompt: str, link):
    contents = [prompt, link]
    resp = await self.model.generate_content_async(contents=contents)
    return resp.text


# Generate questions with text
class TextProcessor:
  def __init__(self, generator: QuestionGenerator, chunk_size: int = 100000, chunk_overlap: int = 5000):
    if chunk_size <= chunk_overlap:
      raise ValueError('chunk_size must be greater than chunk_overlap')
    self.generator = generator
    self.chunk_size = chunk_size
    self.chunk_overlap = chunk_overlap

  def chunk_document(self, text: str):
    doc = Document(text=text)
    splitter = SentenceSplitter(
        chunk_size=self.chunk_size,
        chunk_overlap=self.chunk_overlap
    )
    chunks = splitter.get_nodes_from_documents([doc])
    return chunks

  async def generate_questions(self, text: str, num_question: int, language: str, difficulty: str = "medium"):
    chunks = self.chunk_document(text)
    all_questions = []
    attempts = 0
    max_attempts = 10
    while len(all_questions) < num_question and attempts < max_attempts:
      attempts += 1
      remaining_question = num_question - len(all_questions)
      if (len(chunks) <= remaining_question):
        questions_json = []
        num_question_in_chunk = remaining_question // len(chunks)
        remain_question = remaining_question % len(chunks)
        tasks = []
        for chunk in chunks:
          prompt = get_user_prompt_text(
              language,
              num_question_in_chunk + (1 if remain_question > 0 else 0),
              chunk.text,
              difficulty
          )
          remain_question -= 1
          tasks.append(self.generator.generate_from_text(prompt))
        questions_json = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = []
        for result in questions_json:
          if isinstance(result, Exception):
            print(f"Error in task: {result}")
            valid_results.append('{"questions": []}')
          else:
            valid_results.append(result)
        merged = fix_json_array(valid_results)
        all_questions.extend(merged["questions"])
      else:
        # Summarized the main content
        chunks_text = [node.text for node in chunks]
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(chunks_text)
        sim_matrix = cosine_similarity(tfidf_matrix)
        graph = nx.from_numpy_array(sim_matrix)
        scores = nx.pagerank(graph)
        ranked_chunks = sorted(
            ((score, chunk) for chunk, score in zip(chunks_text, scores.values())),
            key=lambda x: x[0],
            reverse=True
        )
        selected_chunks = [chunk for score,
                           chunk in ranked_chunks[:remaining_question]]
        print('Done ranking document')
        tasks = []
        for chunk in selected_chunks:
          prompt = get_user_prompt_text(language, 1, chunk, difficulty)
          tasks.append(self.generator.generate_from_text(prompt))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_jsons = []
        for result in results:
          if isinstance(result, Exception):
            print(f"Error in task: {result}")
            valid_jsons.append('{"questions": []}')
          else:
            valid_jsons.append(result)
        merged = fix_json_array(valid_jsons)
        all_questions.extend(merged["questions"])
    merged = {"questions": all_questions[:num_question]}
    return merged


# Generate questions with images
class ImageProcessor:
  def __init__(self, generator: QuestionGenerator, summarizer: Summarizer, text_processor: TextProcessor, chunk_size: int = 500, chunk_overlap: int = 100):
    if chunk_size <= chunk_overlap:
      raise ValueError('chunk_size must be greater than chunk_overlap')
    self.generator = generator
    self.summarizer = summarizer
    self.chunk_size = chunk_size
    self.chunk_overlap = chunk_overlap
    self.text_processor = text_processor

  def generate_chunks(self, images):
    chunks = []

    i = 0
    while i < len(images):
      chunk = images[i:min(len(images), i+self.chunk_size)]
      chunks.append(chunk)
      i += self.chunk_size - self.chunk_overlap

    return chunks

  async def generate_questions(self, images, num_question: int, language: str, difficulty: str = "medium"):
    image_segments = self.generate_chunks(images)
    all_questions = []
    attempts = 0
    max_attempts = 10
    while len(all_questions) < num_question and attempts < max_attempts:
      attempts += 1
      remaining_question = num_question - len(all_questions)
      if len(image_segments) <= remaining_question:
        tasks = []
        num_question_in_chunk = remaining_question // len(image_segments)
        remain_question = remaining_question % len(image_segments)
        for images in image_segments:
          prompt = get_user_prompt_images(
              language,
              num_question_in_chunk + (1 if remain_question > 0 else 0),
              difficulty
          )
          remain_question -= 1
          tasks.append(
              self.generator.generate_from_base64_images(prompt, images))
        questions_json = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = []
        for result in questions_json:
          if isinstance(result, Exception):
            print(f"Error in task: {result}")
            valid_results.append('{"questions": []}')
          else:
            valid_results.append(result)
        merged = fix_json_array(valid_results)
        all_questions.extend(merged["questions"])
      else:
        print('Summarizing the images...')
        summarize_tasks = []
        for images in image_segments:
          summarize_tasks.append(self.summarizer.summarize_images(images))
        summaries = await asyncio.gather(*summarize_tasks, return_exceptions=True)
        text = ''
        for summary in summaries:
          if isinstance(summary, Exception):
            print(f"Error in summarization: {summary}")
            continue
          text += summary + '\n'
        print('Summarized text:', text)
        merged = await self.text_processor.generate_questions(text, remaining_question, language, difficulty)
        all_questions.extend(merged["questions"])
    merged = {"questions": all_questions[:num_question]}
    return merged


# Generate questions with file, just support PDF
class FileProcessor:
  def __init__(self, generator: QuestionGenerator):
    self.generator = generator

  async def generate_questions(self, genai_link, num_question: int, language: str, difficulty: str = "medium"):
    all_questions = []
    attempts = 0
    max_attempts = 10
    while len(all_questions) < num_question and attempts < max_attempts:
      attempts += 1
      remaining_question = num_question - len(all_questions)
      prompt = get_user_prompt_file(
          lang=language, count=remaining_question, difficulty=difficulty)
      result = await self.generator.generate_from_genai_link(prompt, genai_link)
      merged = fix_json_array([result])
      all_questions.extend(merged["questions"])
    merged = {"questions": all_questions[:num_question]}
    return merged


class DocumentProcessor:
  def __init__(self, text_processor: TextProcessor, image_processor: ImageProcessor, file_processor: FileProcessor):
    self.text_processor = text_processor
    self.image_processor = image_processor
    self.file_processor = file_processor
