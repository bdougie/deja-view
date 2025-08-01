# Deja View - GitHub Issues Similarity Service

Find similar GitHub issues using semantic search powered by Chroma vector database.

## Features

- **Semantic Search**: Find similar issues based on content, not just keywords
- **Discussion Suggestions**: AI-powered suggestions for converting issues to discussions
- **Discussions Support**: Index and search GitHub discussions alongside issues
- **Dry-Run Mode**: Safe preview of changes before execution
- **Dual Interface**: Use as CLI tool or REST API
- **Fast Indexing**: Index hundreds of issues in seconds
- **Rich CLI**: Beautiful terminal interface with progress indicators
- **RESTful API**: Full OpenAPI documentation at `/docs`

## Quick Start

### Prerequisites

- Python 3.8+
- Chroma Cloud account ([Get API key](https://cloud.trychroma.com))
- GitHub Personal Access Token (optional, for higher rate limits)

### Installation

```bash
# Index repository with discussions
$ python cli.py index continuedev/continue --include-discussions
✓ Successfully indexed 250 items from continuedev/continue (200 issues, 50 discussions)

# Suggest discussions (dry-run mode)
$ python cli.py suggest-discussions continuedev/continue
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #      ┃ Title                        ┃ Score  ┃ State  ┃ Reasons              ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1423   │ How to configure models?     │ 0.85   │ open   │ Question pattern     │
│ 987    │ Feature request: dark theme  │ 0.72   │ open   │ Feature request      │
└────────┴─────────────────────┴────────┴────────┴────────────────────────┘

Analyzed 180 issues, found 2 suggestions
Tip: Use --execute flag to convert these issues to discussions
```
# Clone the repository
git clone https://github.com/yourusername/deja-view.git
cd deja-view

# Install dependencies
uv pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your Chroma API key
```

### Usage

#### CLI Tool

```bash
# Index a repository (issues only)
python cli.py index continuedev/continue --max-issues 200

# Index with discussions
python cli.py index continuedev/continue --max-issues 200 --include-discussions

# Find similar issues or PRs
python cli.py find https://github.com/continuedev/continue/pull/2000

# Suggest which issues should be discussions (dry-run)
python cli.py suggest-discussions continuedev/continue

# Execute discussion suggestions
python cli.py suggest-discussions continuedev/continue --execute

# Quick command (index + find)
python cli.py quick continuedev/continue 2000 --index-first

# View statistics
python cli.py stats

# Clear database
python cli.py clear
```

#### API Server

```bash
# Start the API server
python api.py

# View API docs
open http://localhost:8000/docs
```

#### Demo Client

```bash
# Run interactive demo
python demo_client.py
```

## API Endpoints

- `POST /index` - Index repository issues and discussions
- `POST /find_similar` - Find similar issues
- `POST /suggest_discussions` - Suggest issues to convert to discussions
- `GET /stats` - Get database statistics
- `DELETE /clear` - Clear all data
- `GET /health` - Health check

## CLI Commands

- `cli.py index OWNER/REPO` - Index a repository
- `cli.py find ISSUE_URL` - Find similar issues to a specific issue/PR
- `cli.py suggest-discussions OWNER/REPO` - Suggest issues to convert to discussions
- `cli.py quick OWNER/REPO ISSUE_NUMBER` - Quick command to find similar issues
- `cli.py stats` - Show statistics about indexed issues
- `cli.py clear` - Clear all indexed issues

## Example: Find Similar Issues

```python
import requests

# Index repository with discussions
requests.post("http://localhost:8000/index", json={
    "owner": "continuedev",
    "repo": "continue",
    "max_issues": 200,
    "include_discussions": True
})

# Find similar issues or PRs
response = requests.post("http://localhost:8000/find_similar", json={
    "owner": "continuedev",
    "repo": "continue",
    "issue_number": 2000,
    "top_k": 10
})

similar_issues = response.json()["similar_issues"]

# Suggest discussions (dry-run)
response = requests.post("http://localhost:8000/suggest_discussions", json={
    "owner": "continuedev",
    "repo": "continue",
    "min_score": 0.5,
    "dry_run": True
})

suggestions = response.json()["suggestions"]
```

## CLI Examples

```bash
# Index repository
$ python cli.py index continuedev/continue
✓ Successfully indexed 200 issues from continuedev/continue

# Find similar issues/PRs with URL
$ python cli.py find https://github.com/continuedev/continue/pull/2000
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ #      ┃ Title                                 ┃ Similarity ┃ State  ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ 1995   │ Add support for custom models         │ 87.3%      │ open   │
│ 1234   │ Model configuration improvements      │ 85.1%      │ closed │
└────────┴───────────────────────────────────────┴────────────┴────────┘
```

## Environment Variables

- `CHROMA_API_KEY` - Your Chroma Cloud API key (required)
- `CHROMA_TENANT` - Chroma tenant (default: "default-tenant")
- `CHROMA_DATABASE` - Chroma database (default: "default-database")
- `GITHUB_TOKEN` - GitHub personal access token (optional)

## How It Works

1. **Indexing**: Fetches issues from GitHub and creates embeddings
2. **Storage**: Stores embeddings in Chroma vector database
3. **Search**: Uses cosine similarity to find related issues
4. **Results**: Returns ranked issues with similarity scores

## Development

```bash
# Run API in development mode
python -m uvicorn api:app --reload

# Make CLI executable
chmod +x cli.py
./cli.py --help
```

## License

MIT