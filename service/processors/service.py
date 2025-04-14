# import os
# import tempfile
# import base64
# import io
# import json
# import fitz  # PyMuPDF
# from PIL import Image
# import google.generativeai as genai
# from llama_index.core import Document, Settings, VectorStoreIndex
# from llama_index.core.node_parser import SentenceSplitter
# from llama_index.vector_stores.pinecone import PineconeVectorStore
# from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
# from pinecone import Pinecone, ServerlessSpec
# from typing import List, Optional
# import uuid
# import asyncio

# # Initialize API keys
# GOOGLE_API_KEY = os.environ.get('GOOGLE_GENAI_KEY')
# PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
# PINECONE_ENV = os.environ.get('PINECONE_ENVIRONMENT', 'gcp-starter')
# PINECONE_INDEX = os.environ.get('PINECONE_INDEX', 'document-index')

# # Configure APIs
# genai.configure(api_key=GOOGLE_API_KEY)
# pc = Pinecone(
#     api_key=PINECONE_API_KEY
# )

# # print(pc.list_indexes())

# # # Create index if it doesn't exist
# # if PINECONE_INDEX not in pc.list_indexes():
# #   pc.create_index(
# #       name=PINECONE_INDEX,
# #       dimension=768,  # Default dimension for Google embeddings
# #       metric="cosine",
# #       spec=ServerlessSpec(
# #           cloud='aws',
# #           region='us-east-1'
# #       )
# #   )

# # Configure LlamaIndex
# Settings.embed_model = GoogleGenAIEmbedding(
#     model_name="models/text-multilingual-embedding-002",
#     api_key=GOOGLE_API_KEY
# )

# # Initialize vector store
# vector_store = PineconeVectorStore(
#     pinecone_index=pc.Index(PINECONE_INDEX),
#     namespace=os.environ.get('PINECONE_NAMESPACE', 'default')
# )

# # Initialize background tasks manager
# task_results = {}


# class DocumentProcessor:
#   def __init__(self):
#     self.model = genai.GenerativeModel('gemini-2.0-flash')
#     self.splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)

#   def process_text(self, text, doc_id=None):
#     if not doc_id:
#       doc_id = str(uuid.uuid4())

#     documents = [Document(text=text, doc_id=doc_id)]
#     nodes = self.splitter.get_nodes_from_documents(documents)

#     # Create index and store in Pinecone
#     index = VectorStoreIndex(
#         nodes=nodes,
#         storage_context=vector_store.storage_context,
#     )

#     return {"doc_id": doc_id, "nodes_count": len(nodes)}

#   def process_pdf(self, pdf_path, doc_id=None):
#     if not doc_id:
#       doc_id = str(uuid.uuid4())

#     # Extract text content
#     text_content = self.extract_text_from_pdf(pdf_path)

#     # Process text content
#     text_result = self.process_text(text_content, doc_id)

#     # Extract and process images
#     images = self.pdf_to_base64(pdf_path)
#     image_texts = self.process_images(images)

#     # Process the extracted text from images
#     if image_texts:
#       self.process_text(image_texts, f"{doc_id}_images")

#     return {
#         "doc_id": doc_id,
#         "text_nodes_count": text_result["nodes_count"],
#         "images_processed": len(images),
#         "image_text_extracted": bool(image_texts)
#     }

#   def process_images(self, images):
#     """Process base64 images and extract text using Google AI"""
#     if not images:
#       return ""

#     all_extracted_text = ""

#     # Process images in batches to avoid token limits
#     batch_size = 5
#     for i in range(0, len(images), batch_size):
#       batch = images[i:i+batch_size]
#       extracted_batch_text = self.extract_text_from_images(batch)
#       all_extracted_text += extracted_batch_text + "\n\n"

#     return all_extracted_text.strip()

#   def extract_text_from_images(self, image_batch):
#     """Extract text from a batch of base64 images using Google AI"""
#     prompt = """Please extract all the text content from these images. 
#         Format the text to preserve paragraphs, bullet points, and document structure. 
#         Include all text visible in the images, maintaining the original organization and layout as much as possible. 
#         Only output the extracted text, with no additional commentary."""

#     contents = [prompt]
#     for image in image_batch:
#       contents.append({
#           "mime_type": "image/jpeg",
#           "data": base64.b64decode(image)
#       })

#     try:
#       response = self.model.generate_content_async(contents=contents)
#       return response.text
#     except Exception as e:
#       print(f"Error extracting text from images: {str(e)}")
#       return ""

#   def extract_text_from_pdf(self, pdf_path):
#     """Extract text from PDF using PyMuPDF"""
#     text = ""
#     with fitz.open(pdf_path) as doc:
#       for page_num in range(len(doc)):
#         page = doc[page_num]
#         text += page.get_text()
#     return text

#   def pdf_to_base64(self, pdf_path):
#     """Convert PDF pages to base64 images"""
#     pdf_document = fitz.open(pdf_path)

#     pages = []
#     for page_number in range(pdf_document.page_count):
#       page = pdf_document.load_page(page_number)
#       pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)
#                             )  # Increase resolution
#       img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

#       buffer = io.BytesIO()
#       img.save(buffer, format="JPEG", quality=85)

#       pages.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

#     return pages


# class QueryEngine:
#   def __init__(self):
#     self.model = genai.GenerativeModel('gemini-2.0-flash')

#   def query_document(self, query, doc_id=None, k=5):
#     """Query the document database using RAG approach"""
#     # Create retriever from vector store
    
#     # if doc_id:
#     #   # Query specific document
#     #   retriever = vector_store.query(
#     #       filters={"doc_id": {"$eq": doc_id}},
#     #       similarity_top_k=k
#     #   )
#     # else:
#     #   # Query all documents
#     #   retriever = vector_store.query(similarity_top_k=k)

#     # Retrieve relevant nodes

#     nodes = vector_store.query()
#     # nodes = retriever.retrieve(query)

#     if not nodes:
#       return {"answer": "No relevant information found in the documents."}

#     # Prepare context from nodes
#     context = "\n\n".join([node.node.text for node in nodes])

#     # Generate response with Google AI
#     response = self.generate_response(query, context)

#     return {
#         "answer": response,
#         "sources": [
#             {"text": node.node.text, "score": node.score}
#             for node in nodes
#         ]
#     }

#   def generate_response(self, query, context):
#     """Generate response using Google AI"""
#     prompt = f"""Please answer the following query based on the provided context:

# Context:
# {context}

# Query:
# {query}

# Please provide a comprehensive and factual answer based only on the information in the context.
# If the answer cannot be determined from the context, please state so.
# """

#     try:
#       response = self.model.generate_content_async(contents=prompt)
#       return response.text
#     except Exception as e:
#       print(f"Error generating response: {str(e)}")
#       return "Sorry, I encountered an error while generating your response."


# # Initialize processors
# document_processor = DocumentProcessor()
# query_engine = QueryEngine()

# query_engine.query_document('hihi')
