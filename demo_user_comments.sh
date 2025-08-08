#!/bin/bash

# Demo script for the new user-comments command
# This shows how to use the CLI wrapper for fetching GitHub user comments

echo "=== Deja-View User Comments Demo ==="
echo ""
echo "This command fetches a user's recent comments from GitHub issues and PRs"
echo "It requires the GitHub CLI (gh) to be installed and authenticated"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Install it from: https://docs.astral.sh/uv/"
    echo "Quick install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Install it from: https://cli.github.com"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

echo "Available options:"
echo "  --user, -u     : GitHub username (defaults to authenticated user)"
echo "  --limit, -n    : Number of comments to fetch (default: 10)"
echo "  --repo, -r     : Filter by repository (format: owner/repo)"
echo "  --since, -s    : Show comments since date (YYYY-MM-DD)"
echo ""

echo "Example commands:"
echo ""

echo "1. Fetch your last 10 comments (authenticated user):"
echo "   uv run python cli.py user-comments"
echo ""

echo "2. Fetch last 5 comments from a specific user:"
echo "   uv run python cli.py user-comments --user octocat --limit 5"
echo ""

echo "3. Fetch comments from a specific repository:"
echo "   uv run python cli.py user-comments --repo facebook/react --limit 10"
echo ""

echo "4. Fetch comments since a specific date:"
echo "   uv run python cli.py user-comments --since 2025-01-01"
echo ""

echo "5. Combine filters - user's comments in a repo since a date:"
echo "   uv run python cli.py user-comments --user bdougie --repo open-sauced/app --since 2025-01-01 --limit 20"
echo ""

# Run a simple demo
echo "=== Running Demo ==="
echo "Fetching your last 3 comments..."
echo ""

# First ensure dependencies are installed
echo "Ensuring dependencies are installed with uv..."
uv pip install -r requirements.txt

# Run the command
uv run python cli.py user-comments --limit 3