# Deja View - GitHub Issues Similarity Service

Find similar GitHub issues using semantic search powered by Chroma vector database.

## Features

- **Semantic Search**: Find similar issues based on content, not just keywords
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
# Index a repository
python cli.py index continuedev/continue --max-issues 200

# Find similar issues or PRs
python cli.py find https://github.com/continuedev/continue/pull/2000

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

- `POST /index` - Index repository issues
- `POST /find_similar` - Find similar issues
- `GET /stats` - Get database statistics
- `DELETE /clear` - Clear all data
- `GET /health` - Health check

## CLI Commands

- `cli.py index OWNER/REPO` - Index a repository
- `cli.py find ISSUE_URL` - Find similar issues to a specific issue/PR
- `cli.py quick OWNER/REPO ISSUE_NUMBER` - Quick command to find similar issues
- `cli.py stats` - Show statistics about indexed issues
- `cli.py clear` - Clear all indexed issues

## Example: Find Similar Issues

```python
import requests

# Index repository
requests.post("http://localhost:8000/index", json={
    "owner": "continuedev",
    "repo": "continue",
    "max_issues": 200
})

# Find similar issues or PRs
response = requests.post("http://localhost:8000/find_similar", json={
    "owner": "continuedev",
    "repo": "continue",
    "issue_number": 2000,
    "top_k": 10
})

similar_issues = response.json()["similar_issues"]
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