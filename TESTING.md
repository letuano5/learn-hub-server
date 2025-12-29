# Startup Testing

## Usage

### 1. Quick Tests (Default - Fast ~5s)
```bash
uvicorn main:app --reload
```
Runs 2 basic tests:
- Model info
- Simple text generation

### 2. Full Tests (Slow ~30-60s)
Add to `.env`:
```
STARTUP_TEST_MODE=full
```
Or:
```bash
set STARTUP_TEST_MODE=full
uvicorn main:app --reload
```
Runs all 6 tests:
- Model info
- Simple text generation
- Question generation
- Vietnamese questions
- Summarization
- Different difficulties

### 3. Disable Tests (Production)
Add to `.env`:
```
RUN_STARTUP_TESTS=false
```

## Environment Variables

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `RUN_STARTUP_TESTS` | `true`/`false` | `true` | Enable/disable tests |
| `STARTUP_TEST_MODE` | `quick`/`full` | `quick` | Test mode |

## Sample Output

### Quick mode:
```
Running QUICK startup tests...

============================================================
QUICK STARTUP TESTS
============================================================

============================================================
TEST 6: Model Information
============================================================
Model: gemini-2.5-pro
System Instruction: 4567 characters

Test 6 PASSED

============================================================
TEST 1: Simple Text Generation
============================================================
Prompt: Explain what is photosynthesis in 2 sentences.

Response:
Photosynthesis is the process by which plants...

Test 1 PASSED

============================================================
Quick tests passed (2/2)
============================================================
```

## Manual Testing

```bash
# Run full test suite
python test.py

# Run health check only
python health_check.py
```

## Recommendations

| Environment | Setting | Reason |
|-------------|---------|--------|
| **Development** | `quick` | Fast, sufficient for basic error detection |
| **Testing/Staging** | `full` | Comprehensive testing before deployment |
| **Production** | `false` | Fastest startup time |

## Files

- `main.py` - Main server with startup event handler
- `test.py` - Full test suite with 6 comprehensive tests
- `health_check.py` - Quick health checks for API connectivity
- `TESTING.md` - This documentation file
