# Bulletproof Testing Strategy

## Motto: "NEVER AGAIN SHALL WE HANG"

This repository follows strict bulletproof testing guidelines to ensure tests never hang and complete quickly.

## Test Structure

### Bulletproof Tests (`test_bulletproof.py`, `test_github_simple.py`)
- **Maximum duration**: 5 seconds per test
- **No async operations**
- **No external dependencies**
- **Pure functions and mocked operations only**
- **Completion time**: ~0.4 seconds for entire suite

### Original Tests (`test_github_similarity_service.py`)
- Comprehensive integration tests
- Kept separate from bulletproof suite
- Run with `./run_tests.sh --all`

## Running Tests

```bash
# Quick bulletproof tests only (recommended)
./run_tests.sh

# All tests including original suite
./run_tests.sh --all

# Individual test files
pytest test_bulletproof.py -v
pytest test_github_simple.py -v
```

## Test Guidelines

### ✅ ALLOWED
- Pure function tests
- Simple data model tests
- Mocked external dependencies
- Synchronous operations only
- Tests under 100 lines

### ❌ FORBIDDEN
- No async/await
- No setTimeout/setInterval
- No real API calls
- No database operations
- No file I/O operations
- No network requests

## Configuration

The `pytest.ini` file enforces:
- 5-second timeout per test
- Strict markers
- Short tracebacks
- Fail fast on first error

## Files Renamed

- `test_chroma.py` → `chroma_check.py` (not a test file)
- `test_fetch_issues.py` → `fetch_issues_check.py` (not a test file)

These files were renamed because they were scripts that made real API calls and could hang.

## Success Metrics

✅ Tests complete in under 2 minutes
✅ No hanging tests in CI
✅ Deterministic and reliable
✅ Easy for new developers to run
✅ Current completion time: **~0.4 seconds**