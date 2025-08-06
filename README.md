# Deja View - GitHub Issues Similarity Service

Find similar GitHub issues using semantic search powered by Chroma vector database.

## Features

- **Semantic Search**: Find similar issues based on content, not just keywords
- **Discussion Suggestions**: AI-powered suggestions for converting issues to discussions
- **Discussions Support**: Index and search GitHub discussions alongside issues
- **GitHub Action**: Automatically comment on new issues with similar existing issues
- **Dry-Run Mode**: Safe preview of changes before execution
- **Triple Interface**: Use as CLI tool, REST API, or GitHub Action
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
$ uv run cli.py index continuedev/continue --include-discussions
✓ Successfully indexed 250 items from continuedev/continue (200 issues, 50 discussions)

# Suggest discussions (dry-run mode)
$ uv run cli.py suggest-discussions continuedev/continue
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
# Index a repository (open issues only - default)
uv run cli.py index continuedev/continue --max-issues 200

# Index closed issues
uv run cli.py index continuedev/continue --max-issues 200 --state closed

# Index all issues regardless of state
uv run cli.py index continuedev/continue --max-issues 200 --state all

# Index with discussions
uv run cli.py index continuedev/continue --max-issues 200 --include-discussions

# Find similar issues or PRs
uv run cli.py find https://github.com/continuedev/continue/pull/2000

# Suggest which issues should be discussions (dry-run)
uv run cli.py suggest-discussions continuedev/continue

# Execute discussion suggestions
uv run cli.py suggest-discussions continuedev/continue --execute

# Quick command (index + find)
uv run cli.py quick continuedev/continue 2000 --index-first

# View statistics
uv run cli.py stats

# Clear database
uv run cli.py clear
```

#### API Server

```bash
# Start the API server
uv run api.py

# View API docs
open http://localhost:8000/docs
```

#### Demo Client

```bash
# Run interactive demo
uv run demo_client.py
```

## API Endpoints

- `POST /index` - Index repository issues and discussions
- `POST /find_similar` - Find similar issues
- `POST /suggest_discussions` - Suggest issues to convert to discussions
- `GET /stats` - Get database statistics
- `DELETE /clear` - Clear all data
- `GET /health` - Health check

## CLI Commands

- `cli.py index OWNER/REPO [--state open|closed|all]` - Index repository issues (default: open)
- `cli.py find ISSUE_URL` - Find similar issues to a specific issue/PR
- `cli.py suggest-discussions OWNER/REPO` - Suggest issues to convert to discussions
- `cli.py quick OWNER/REPO ISSUE_NUMBER` - Quick command to find similar issues
- `cli.py stats` - Show statistics about indexed issues
- `cli.py clear` - Clear all indexed issues

### Index Command Options
- `--max-issues`: Maximum number of issues to index (default: 100)
- `--state`: Issue state to index - `open` (default), `closed`, or `all`
- `--include-discussions`: Also index GitHub discussions

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
$ uv run cli.py index continuedev/continue
✓ Successfully indexed 200 issues from continuedev/continue

# Find similar issues/PRs with URL
$ uv run cli.py find https://github.com/continuedev/continue/pull/2000
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

## GitHub Action Usage

Deja View can automatically comment on new issues with similar existing issues. This helps reduce duplicates and connects related discussions.

### Quick Setup

1. Add the action to your workflow (`.github/workflows/deja-view.yml`):

```yaml
name: Find Similar Issues

on:
  issues:
    types: [opened]

jobs:
  find-similar:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      contents: read
    
    steps:
      - name: Find and Comment Similar Issues
        uses: yourusername/deja-view@v1
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          chroma-database: ${{ secrets.CHROMA_DATABASE }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

2. Add your Chroma credentials as repository secrets:
   - `CHROMA_API_KEY` - Your Chroma Cloud API key
   - `CHROMA_TENANT` - Your Chroma tenant ID
   - `CHROMA_DATABASE` - Your database name (optional, defaults to "default-database")

### Configuration Options

| Input | Description | Default |
|-------|-------------|---------|
| `chroma-api-key` | Chroma Cloud API key | Required |
| `chroma-tenant` | Chroma Cloud tenant ID | Required |
| `chroma-database` | Database name | `default-database` |
| `github-token` | GitHub token for API access | `${{ github.token }}` |
| `max-issues` | Maximum issues to index | `200` |
| `similarity-threshold` | Minimum similarity score (0-1) | `0.7` |
| `max-similar-issues` | Max similar issues to show | `5` |
| `index-on-run` | Re-index repository each run | `true` |
| `include-discussions` | Include discussions in search | `false` |
| `comment-template` | Custom comment template | See below |

### Custom Comment Template

You can customize the comment format using the `comment-template` input:

```yaml
comment-template: |
  ## 👀 Related Issues
  
  Hey @${{ github.event.issue.user.login }}, I found these similar issues:
  
  {issues_table}
  
  _Please check if any of these solve your problem!_
```

The `{issues_table}` placeholder will be replaced with a formatted table of similar issues.

### Advanced Example

```yaml
name: Smart Issue Management

on:
  issues:
    types: [opened]

jobs:
  find-similar:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      contents: read
    
    steps:
      - name: Find Similar Issues
        uses: yourusername/deja-view@v1
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          max-issues: 500
          similarity-threshold: 0.8
          max-similar-issues: 3
          include-discussions: true
          comment-template: |
            ## 🔍 Similar Issues and Discussions
            
            I found these related items that might help:
            
            {issues_table}
            
            💡 **Tip**: If this is a question or feature request, consider starting a [discussion](https://github.com/${{ github.repository }}/discussions) instead!
```

### Local Development

When using this repository as a GitHub Action, it will use the `Dockerfile` to build and run the action. The action will:

1. Check if the event is a new issue (not a PR)
2. Optionally re-index your repository 
3. Find similar issues using semantic search
4. Post a helpful comment if similar issues are found

## Development

```bash
# Run API in development mode
uv run uvicorn api:app --reload

# Make CLI executable
chmod +x cli.py
./cli.py --help

# Test the GitHub Action locally
docker build -t deja-view-action .
# Set up environment variables and run
```

## License

MIT