import base64
import io

import fitz
import json
from PIL import Image

import google.generativeai as genai
from google.genai import types
from google.api_core.exceptions import InvalidArgument

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import os
api_key = os.environ.get('GOOGLE_GENAI_KEY')

question_example = {
    "questions": [
        {
            "question": "Which of the following is the correct translation of house in Spanish?",
            "options": ["Casa", "Maison", "Haus", "Huis"],
            "answer": 0,
            "explanation": "Your explaination"
        }
    ]
}

multiple_choice_example = {
    "question": "The question",
    "options": "An array of 4 strings representing the choices",
    "answer": "The number corresponding to the index of the correct answer in the options array",
    "explanation": "Explain why you choose that answer"
}

# TODO: Remove multiple_choice_example and question_example from system prompt, and move it into the user prompt
default_prompt = f"""You are an assistant specialized in generating exam-style questions and answers. Your response must only be a JSON object with the following property:
"questions": An array of JSON objects, where each JSON object represents a question and answer pair. The JSON object representing the question must have the following properties:

{json.dumps(multiple_choice_example, indent=2)}

For example, the structure of your response should look like this:

{json.dumps(question_example, indent=2)}

STRICT RULES (REVISED):

1. NEVER use phrases that imply external documents:
- Avoid phrases like: "based on the text/diagram/passage/content", "according to the document/information", "from the provided example", "in the diagram/figure/illustration", "as mentioned earlier/previously", "from the document", "according to the text", "as mentioned", or any synonyms.

2. Questions must be self-contained with all necessary context, without referencing any other source material. This means:
- Integrate information: If the original question is based on an image, diagram, table, or text, interpret and include the essential information directly in the question.
- Describe concepts: Instead of asking the respondent to refer to a document to understand a concept, define or describe that concept within the question itself.

3. Rephrase concepts instead of copying directly from source material.

4. Include only truly essential context within the question. If the original context contains images, tables, diagrams, or similar content:
- Redraw using Markdown: If it can be interpreted concisely and effectively.
- Don't print out that question: If interpreting it makes the question too complex or unnecessary for the main objective, or you can't interpret it.
- Avoid using phrases like: "from the images/tables/diagrams/pictures...", like rule 1. If you can't interpret it, don't print out that question.

5. If the source material is in a different language, translate the context appropriately rather than referencing the origin.

6. Include only relevant excerpts when referencing examples or code.

7. For math content, use LaTeX formatting $....$.

8. For technical term, using the original language instead of translating it.

**Examples of GOOD Questions (self-contained, no external references):**

* "In the process of photosynthesis in plants, chlorophyll absorbs energy from sunlight to convert water and carbon dioxide into organic matter and oxygen. In which cellular organelle does this process primarily occur?"
* "The chemical formula for water is H₂O, indicating that each molecule consists of two hydrogen atoms and one oxygen atom. What type of chemical bond primarily holds these atoms together within a water molecule?"
* "A parliamentary system is a form of government in which the executive branch (government) is dependent on the direct or indirect support of the legislative branch (parliament), often expressed through a vote of confidence. In such a system, who typically serves as the head of government?"

**Examples of BAD Questions (violating the rules by implying external references):**

* "According to the provided diagram of the water cycle, explain the process of condensation." (Implies a "provided diagram")
* "Based on the text, what are the main differences between 'Infrastructure' and 'Superstructure'?" (Implies a "text")
* "As mentioned earlier, how is the superstructure of society structured?" (Uses "as mentioned earlier")
* "Following the illustration, describe the relationship between the base and superstructure." (Implies an "illustration")

All these rules are both applied to the generated questions and answers.

Focus on testing understanding and critical thinking while staying true to the source content."""

# TODO: Language mapping here

class GenAIClient:
  def __init__(self, api_key: str, default_prompt: str = ''):
    genai.configure(api_key=api_key)

    if len(default_prompt) > 0:
      self.model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=default_prompt)
    else:
      self.model = genai.GenerativeModel('gemini-2.0-flash')

class QuestionGenerator(GenAIClient):
  def get_user_prompt_text(self, lang: str, count: int, text: str):
    return f"""
Now generate {count} insightful question based on the following content that tests understanding of key concepts or important details:

<Begin Document>
{text}
<End Document>

The generated questions and answers must be in {lang}. However, your response must still follow the JSON format provided before. This means that while the values should be in {lang}, the keys must be the exact same as given before, in English.
"""

  def get_user_prompt_images(self, lang: str, count: int):
    return f"""
Now read carefully the contents written on these images, then generate {count} insightful question that tests understanding of key concepts or important details.
The generated questions and answers must be in {lang}. However, your response must still follow the JSON format provided before. This means that while the values should be in {lang}, the keys must be the exact same as given before, in English.
"""

  def generate_from_base64_images(self, prompt: str, images):
    contents = [prompt]
    for image in images:
      contents.append({
        "mime_type": "image/jpeg",
        "data": base64.b64decode(image)
    })
    # TODO: Replace with generate_content_async
    return self.model.generate_content(contents=contents).text

  def generate_from_text(self, content: str):
    return self.model.generate_content(contents=content).text

class Summarizer(GenAIClient):
  def summarize_images(self, images):
    prompt = f'''
Can you provide a comprehensive summary of these given images? The summary should cover all the key points and main ideas presented in the original text, while also condensing the information into a concise and easy-to-understand format. Please ensure that the summary includes relevant details and examples that support the main ideas, while avoiding any unnecessary information or repetition. The length of the summary should be appropriate for the length and complexity of the original text, providing a clear and accurate overview without omitting any important information.
Just return the summary without any other text.
'''
    contents = [prompt]
    for image in images:
      contents.append({
        "mime_type": "image/jpeg",
        "data": base64.b64decode(image)
    })
    # TODO: Replace with generate_content_async
    return self.model.generate_content(contents=contents).text

# Generate questions with text
class TextProcessor:
  def __init__(self, generator: QuestionGenerator, chunk_size: int=10000, chunk_overlap: int=1000):
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

  def generate_questions(self, text: str, num_question: int, language: str):
    chunks = self.chunk_document(text)

    if (len(chunks) <= num_question):
      questions_json = []
      num_question_in_chunk = num_question // len(chunks)
      remain_question = num_question % len(chunks)

      for chunk in chunks:
        prompt = self.generator.get_user_prompt_text(language, num_question_in_chunk + (1 if remain_question > 0 else 0), chunk.text)
        remain_question -= 1
        questions_json.append(self.generator.generate_from_text(prompt))

      return questions_json
    else:
      # Summarized the main content
      # https://chatgpt.com/share/67f5d65f-8e78-8012-a3dd-6257744d95ff

      chunks = [node.text for node in chunks]

      vectorizer = TfidfVectorizer(stop_words='english')
      tfidf_matrix = vectorizer.fit_transform(chunks)

      sim_matrix = cosine_similarity(tfidf_matrix)

      graph = nx.from_numpy_array(sim_matrix)
      scores = nx.pagerank_numpy(graph)
      ranked_chunks = sorted(
          ((score, chunk) for chunk, score in zip(chunks, scores.values())),
          key=lambda x: x[0],
          reverse=True
      )
      selected_chunks = [chunk for score, chunk in ranked_chunks[:num_question]]

      print('Done ranking document')

      jsons = []

      for chunk in selected_chunks:
        prompt = self.generator.get_user_prompt_text(language, 1, chunk)
        jsons.append(self.generator.generate_from_text(prompt))

      return jsons

# Generate questions with images
class ImageProcessor:
  def __init__(self, generator: QuestionGenerator, summarizer: Summarizer, text_processor: TextProcessor, chunk_size: int=500, chunk_overlap: int=100):
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

  def generate_questions(self, images, num_question: int, language: str):
    image_segments = self.generate_chunks(images)

    if len(image_segments) <= num_question:
      # Just throw the image directly to the model
      questions_json = []
      num_question_in_chunk = num_question // len(image_segments)
      remain_question = num_question % len(image_segments)
      for images in image_segments:
        prompt = self.generator.get_user_prompt_images(language, num_question_in_chunk + (1 if remain_question > 0 else 0))
        remain_question -= 1
        questions_json.append(self.generator.generate_from_base64_images(prompt, images))

      return questions_json
    else:
      # Summarized the main content
      print('Summarizing the images...')
      text = ''
      for images in image_segments:
        text += self.summarizer.summarize_images(images) + '\n'

      print('Summarized text:', text)

      return text_processor.generate_questions(text, num_question, language)

class DocumentProcessor:
  def __init__(self, image_processor: ImageProcessor):
    self.image_processor = image_processor

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

  def generate_questions(self, pdf_path: str, num_question: int, language: str):
    jsons = self.image_processor.generate_questions(self.pdf_to_base64(pdf_path), num_question, language)
    questions = []
    for subquestion in jsons:
      subquestion = subquestion.replace('```json', '').replace('```', '')
      print(subquestion)
      data = json.loads(subquestion)
      # print(subquestion)

      for item in data['questions']:
        questions.append({
          "question": item["question"],
          "options": item["options"],
          "answer": item["answer"],
          "explanation": item["explanation"]
        })

    merged = {"questions": questions}
    merged_json = json.dumps(merged, ensure_ascii=False, indent=2)

    return merged_json

  def generate_questions_by_text(self, pdf_path: str, num_question: int, language: str):
    # Get text from PDF

    # Generate from text
    return


generator = QuestionGenerator(api_key=api_key, default_prompt=default_prompt)
summarizer = Summarizer(api_key=api_key)
text_processor = TextProcessor(generator)
image_processor = ImageProcessor(generator, summarizer, text_processor)
processor = PDFProcessor(image_processor)
