import os
from dotenv import load_dotenv

# Load environment variables FIRST, before importing any modules that use them
load_dotenv()

from controllers.results_controller import router as results_router
from controllers.document_controller import router as upload_router
from controllers.quizzes_controller import router as quizzes_router
from controllers import health_controller, generator_controller, processor_controller, shared_resources
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

app = FastAPI()

# Startup event to run tests


@app.on_event("startup")
async def startup_event():
  """Run tests on server startup"""
  run_tests = os.environ.get('RUN_STARTUP_TESTS', 'true').lower() == 'true'
  test_mode = os.environ.get(
      'STARTUP_TEST_MODE', 'quick').lower()  # 'quick' or 'full'

  if run_tests:
    try:
      if test_mode == 'full':
        # Run full test suite (slow ~30-60s)
        print("\n🧪 Running FULL test suite (this may take a while)...\n")
        from test import GeminiAPITester
        tester = GeminiAPITester()
        await tester.run_all_tests()
      else:
        # Run quick tests only (fast ~5-10s)
        print("\n🧪 Running QUICK startup tests...\n")
        from test import GeminiAPITester
        tester = GeminiAPITester()

        # Run only essential tests
        print("="*60)
        print("QUICK STARTUP TESTS")
        print("="*60 + "\n")

        results = []
        results.append(await tester.test_model_info())
        results.append(await tester.test_simple_text_generation())

        # Summary
        print("="*60)
        passed = sum(results)
        total = len(results)
        if passed == total:
          print(f"✅ Quick tests passed ({passed}/{total})")
        else:
          print(f"⚠️  Some tests failed ({passed}/{total})")
        print("="*60 + "\n")

    except Exception as e:
      print(f"⚠️  Startup tests failed: {str(e)}")
      print("Server will continue to start, but some features may not work correctly.\n")
      import traceback
      traceback.print_exc()
  else:
    print("ℹ️  Startup tests disabled (set RUN_STARTUP_TESTS=true to enable)\n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_controller.router)
app.include_router(generator_controller.router)
app.include_router(processor_controller.router)
app.include_router(quizzes_router, prefix="/quiz", tags=["quiz"])
app.include_router(shared_resources.router)
app.include_router(upload_router)
app.include_router(results_router, prefix="/results", tags=["results"])


@app.get("/")
async def root():
  return {"message": "Hello World"}
