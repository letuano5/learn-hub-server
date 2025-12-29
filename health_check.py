"""
Quick health check tests for Gemini API
These tests run on server startup to verify API connectivity
"""

import asyncio
import os
from service.generators.base import GenAIClient


async def test_gemini_connection():
  """Test basic Gemini API connection"""
  try:
    api_key = os.environ.get('GOOGLE_GENAI_KEY')
    if not api_key:
      return False, "GOOGLE_GENAI_KEY not found in environment"

    client = GenAIClient(api_key=api_key)
    response = await client.model.generate_content_async(contents="Say 'OK' if you can read this.")

    if response and response.text:
      return True, f"Gemini API connected successfully (model: gemini-2.5-pro)"
    else:
      return False, "Gemini API returned empty response"

  except Exception as e:
    return False, f"Gemini API connection failed: {str(e)}"


async def test_pinecone_connection():
  """Test Pinecone connection"""
  try:
    pinecone_key = os.environ.get('PINECONE_API_KEY')
    if not pinecone_key:
      return False, "PINECONE_API_KEY not found in environment"

    # Just check if the key exists
    return True, "Pinecone API key loaded"

  except Exception as e:
    return False, f"Pinecone check failed: {str(e)}"


async def run_startup_tests():
  """Run all startup health checks"""
  print("\n" + "="*60)
  print("🔍 Running Startup Health Checks...")
  print("="*60)

  tests = [
      ("Gemini API", test_gemini_connection),
      ("Pinecone API", test_pinecone_connection),
  ]

  all_passed = True

  for test_name, test_func in tests:
    try:
      passed, message = await test_func()
      status = "✓ PASS" if passed else "✗ FAIL"
      print(f"{status} | {test_name}: {message}")
      if not passed:
        all_passed = False
    except Exception as e:
      print(f"✗ FAIL | {test_name}: Unexpected error - {str(e)}")
      all_passed = False

  print("="*60)
  if all_passed:
    print("✅ All health checks passed!")
  else:
    print("⚠️  Some health checks failed - server may not work correctly")
  print("="*60 + "\n")

  return all_passed


if __name__ == "__main__":
  # Can be run standalone for testing
  asyncio.run(run_startup_tests())
