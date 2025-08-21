#!/bin/bash
# BULLETPROOF TEST RUNNER
# Motto: "NEVER AGAIN SHALL WE HANG"

set -e

echo "========================================="
echo "Running Bulletproof Test Suite"
echo "Maximum duration: 5 seconds per test"
echo "========================================="

# Activate virtual environment
source .venv/bin/activate

# Run bulletproof tests only
echo ""
echo "Running bulletproof tests..."
python -m pytest test_bulletproof.py test_github_simple.py -v --tb=short --timeout=5

# Optional: Run original tests separately
if [ "$1" == "--all" ]; then
    echo ""
    echo "Running original test suite..."
    python -m pytest test_github_similarity_service.py -v --tb=short --timeout=10
fi

echo ""
echo "========================================="
echo "All tests completed successfully!"
echo "========================================="