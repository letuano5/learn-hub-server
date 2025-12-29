from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Document
from llama_index.core.vector_stores import FilterCondition, FilterOperator, MetadataFilter, MetadataFilters
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core import Settings
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.prompts import PromptTemplate
from llama_index.readers.file import PDFReader, DocxReader, MarkdownReader
from service.generators.base import GenAIClient
from service.generators.doc_processor.pdf import PDFProcessor
from service.generators.gemini_file_upload import (
    validate_pdf_page_count,
    validate_docx_page_count,
    extract_file_pages_to_markdown,
    extract_file_to_markdown_full
)
from pinecone import Pinecone
import asyncio
import google.generativeai as genai
import os
import fitz
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

GOOGLE_GENAI_KEY = os.environ.get('GOOGLE_GENAI_KEY')
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')

genai.configure(api_key=GOOGLE_GENAI_KEY)
pc = Pinecone(
    api_key=PINECONE_API_KEY
)

Settings.llm = GoogleGenAI(
    model="gemini-2.0-flash",
    api_key=GOOGLE_GENAI_KEY,
)

Settings.embed_model = GoogleGenAIEmbedding(
    model_name="models/text-embedding-004",
    api_key=GOOGLE_GENAI_KEY
)

PINECONE_ENV = os.environ.get('PINECONE_ENVIRONMENT', 'gcp-starter')
PINECONE_INDEX = os.environ.get('PINECONE_INDEX', 'document-index')
PINECONE_NAMESPACE = os.environ.get('PINECONE_NAMESPACE', 'default')

ingestion_cache = IngestionCache()

vector_store = PineconeVectorStore(
    pinecone_index=pc.Index(PINECONE_INDEX),
    namespace=PINECONE_NAMESPACE,
)

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=1024, chunk_overlap=20),
        Settings.embed_model
    ],
    vector_store=vector_store,
    cache=ingestion_cache
)

index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
retriever = VectorIndexRetriever(index=index, similarity_top_k=5)
query_engine = RetrieverQueryEngine(retriever=retriever)

node_parser = SentenceSplitter(
    chunk_size=1024,
    chunk_overlap=20,
    paragraph_separator="\n\n",
    secondary_chunking_regex="[^,.;。]+[,.;。]?",
)


async def delete_chunks(document_id: str):
  try:
    index = vector_store._pinecone_index

    await asyncio.to_thread(
        index.delete,
        filter={"mongo_id": document_id},
        namespace=PINECONE_NAMESPACE
    )
    return True
  except Exception as e:
    raise Exception(f"Error deleting chunks from Pinecone: {str(e)}")


async def process_pdf_images(pdf_path: str, chunk_size: int = 10, chunk_overlap: int = 2) -> list[Document]:
  documents = []

  pdf_processor = PDFProcessor(None, None)
  images = pdf_processor.pdf_to_base64(pdf_path)

  chunks = []
  i = 0
  while i < len(images):
    chunk = images[i:min(len(images), i + chunk_size)]
    chunks.append(chunk)
    i += chunk_size - chunk_overlap

  genai_client = GenAIClient(
      api_key=GOOGLE_GENAI_KEY,
      default_prompt="""You are an expert at analyzing and summarizing document images.
        Your task is to:
        1. Describe the content of the image in detail
        2. If there are tables, figures, or diagrams, explain their structure and content
        3. Extract any text that appears in the image
        4. Provide a concise summary of the key concepts
        """
  )

  tasks = []
  for chunk in chunks:
    task = genai_client.model.generate_content_async(
        contents=[{"mime_type": "image/png", "data": img_str}
                  for img_str in chunk]
    )
    tasks.append(task)

  responses = await asyncio.gather(*tasks, return_exceptions=True)

  for idx, (chunk, response) in enumerate(zip(chunks, responses)):
    if isinstance(response, Exception):
      print(f"Error processing chunk {idx}: {str(response)}")
      continue

    start_page = idx * (chunk_size - chunk_overlap) + 1
    end_page = start_page + len(chunk) - 1

    doc = Document(
        text=response.text,
        metadata={
            "pages": list(range(start_page, end_page + 1)),
            "total_pages": len(images),
            "content_type": "image_summary",
            "has_image": True
        }
    )
    documents.append(doc)

  return documents


# OLD METHODS - Using direct text extraction
async def old_process_pdf(file_path: str, mode: str = "text") -> list[Document]:
  if mode == "text":
    reader = PDFReader()
    documents = reader.load_data(file_path)
  else:
    documents = await process_pdf_images(file_path)

  nodes = node_parser.get_nodes_from_documents(documents)

  chunked_documents = []
  for node in nodes:
    doc = Document(
        text=node.text,
        metadata=node.metadata
    )
    print('Current chunk: ', node.text)
    chunked_documents.append(doc)

  return chunked_documents


async def old_process_docx(file_path: str) -> list[Document]:
  reader = DocxReader()
  documents = reader.load_data(file_path)

  nodes = node_parser.get_nodes_from_documents(documents)

  chunked_documents = []
  for node in nodes:
    doc = Document(
        text=node.text,
        metadata=node.metadata
    )
    chunked_documents.append(doc)

  return chunked_documents


# NEW METHODS - Using Gemini batch processing for better accuracy
async def process_pdf(file_path: str, mode: str = "text") -> list[Document]:
  """
  Process PDF by extracting content in 5-page batches through Gemini as markdown
  This improves accuracy for Q&A by having Gemini properly extract and format content
  """
  # Validate page count
  is_valid, total_pages = validate_pdf_page_count(file_path, max_pages=300)
  if not is_valid:
    raise ValueError(f"PDF with {total_pages} pages exceeds 300 page limit for Q&A processing")
  
  # Process in 5-page batches
  batch_size = 5
  markdown_texts = []
  
  for start_page in range(1, total_pages + 1, batch_size):
    end_page = min(start_page + batch_size - 1, total_pages)
    print(f"Extracting pages {start_page}-{end_page} as markdown...")
    
    markdown = await extract_file_pages_to_markdown(
        file_path,
        'pdf',
        start_page,
        end_page,
        GOOGLE_GENAI_KEY
    )
    
    markdown_texts.append({
        'text': markdown,
        'start_page': start_page,
        'end_page': end_page
    })
  
  # Create documents from markdown
  documents = []
  for batch in markdown_texts:
    doc = Document(
        text=batch['text'],
        metadata={
            'start_page': batch['start_page'],
            'end_page': batch['end_page'],
            'total_pages': total_pages,
            'content_type': 'markdown_extracted'
        }
    )
    documents.append(doc)
  
  # Chunk the documents
  nodes = node_parser.get_nodes_from_documents(documents)
  
  chunked_documents = []
  for node in nodes:
    doc = Document(
        text=node.text,
        metadata=node.metadata
    )
    print('Current chunk: ', node.text[:100] + '...')
    chunked_documents.append(doc)
  
  return chunked_documents


async def process_docx(file_path: str) -> list[Document]:
  """
  Process DOCX by uploading entire file to Gemini once and extracting as markdown
  This improves accuracy for Q&A and avoids multiple uploads
  """
  # Validate page count
  is_valid, estimated_pages = validate_docx_page_count(file_path, max_pages=300)
  if not is_valid:
    raise ValueError(f"DOCX with estimated {estimated_pages} pages exceeds 300 page limit for Q&A processing")
  
  print(f"Extracting entire DOCX file as markdown (estimated {estimated_pages} pages)...")
  
  # Extract entire file as markdown (upload once)
  markdown = await extract_file_to_markdown_full(
      file_path,
      'docx',
      GOOGLE_GENAI_KEY
  )
  
  # Create single document from markdown
  doc = Document(
      text=markdown,
      metadata={
          'estimated_pages': estimated_pages,
          'content_type': 'markdown_extracted_full'
      }
  )
  
  # Chunk the document
  nodes = node_parser.get_nodes_from_documents([doc])
  
  chunked_documents = []
  for node in nodes:
    doc = Document(
        text=node.text,
        metadata=node.metadata
    )
    chunked_documents.append(doc)
  
  return chunked_documents


async def process_text_file(file_path: str) -> list[Document]:
  documents = []

  if file_path.endswith('.md'):
    reader = MarkdownReader()
    documents = reader.load_data(file_path)
  else:
    reader = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()[0]

  nodes = node_parser.get_nodes_from_documents(documents)

  chunked_documents = []
  for node in nodes:
    doc = Document(
        text=node.text,
        metadata=node.metadata
    )
    chunked_documents.append(doc)

  return chunked_documents


async def add_document(doc, user_id, is_public=False, document_id=None, filename=None):
  for d in doc:
    d.metadata.update({
        "user_id": user_id,
        "is_public": is_public,
        "mongo_id": document_id,
        "real_name": filename
    })

    print(d.metadata)

  print(
      f"Adding document of {user_id}, is_public: {is_public}, document_id: {document_id}, filename: {filename}")

  return await asyncio.to_thread(pipeline.run, documents=doc)


async def query_document(query_text, user_id):
  try:
    print(f"Starting query with text: {query_text} for user: {user_id}")

    # Create filters
    filters = MetadataFilters(
        filters=[
            MetadataFilter(key="user_id", value=user_id),
            MetadataFilter(key="is_public", value="true")
        ],
        condition=FilterCondition.OR
    )
    print(f"Created filters: {filters}")

    # Create retriever
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=5,
        filters=filters
    )
    print(f"Created retriever: {retriever}")

    # Create QA template with context logging
    qa_template = PromptTemplate(
        """
      You are a helpful assistant that answers questions based ONLY on the provided context.
      Your answers must be based exclusively on the information contained in the context.
      If the context doesn't contain relevant information, refuse to answer.
      Do not use any prior knowledge or external information.
      Respond in the same language as the query.
      We have provided context information below.
      ---------------------
      "{context_str}"
      ---------------------
      Given this information, please answer the question in the same language of the query: "{query_str}"
      If you don't have information to answer the question, politely refuse in the same language as the query.
      """
    )
    print(f"Created QA template: {qa_template}")

    # Create response synthesizer
    response_synthesizer = get_response_synthesizer(
        response_mode="compact",
        text_qa_template=qa_template
    )
    print(f"Created response synthesizer: {response_synthesizer}")

    # Create query engine
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer
    )
    print(f"Created query engine: {query_engine}")

    # Execute query and get retrieved nodes
    print(f"Executing query: {query_text}")
    retrieved_nodes = await asyncio.to_thread(retriever.retrieve, query_text)
    print(f"Retrieved nodes: {[node.text for node in retrieved_nodes]}")

    # Execute query
    response = await asyncio.to_thread(query_engine.query, query_text)
    print(f"Query response: {response}")

    return response

  except Exception as e:
    print(f"Error in query_document: {str(e)}")
    import traceback
    traceback.print_exc()
    return f"Error: {str(e)}"
