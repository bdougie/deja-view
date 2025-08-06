# API Reference

The Deja View REST API provides programmatic access to GitHub issue similarity search functionality. Built with FastAPI, it offers automatic OpenAPI documentation and type validation.

## Base URL

```
http://localhost:8000
```

## Quick Start

### Start the API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CHROMA_API_KEY="your-chroma-api-key"
export CHROMA_TENANT="your-chroma-tenant-id"

# Start server
python api.py
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Basic Example

```bash
# Index a repository (open issues by default)
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "microsoft",
    "repo": "vscode",
    "max_issues": 100,
    "issue_state": "open"
  }'

# Find similar issues
curl -X POST "http://localhost:8000/find_similar" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "microsoft",
    "repo": "vscode",
    "issue_number": 12345,
    "top_k": 5
  }'
```

## Endpoints

### Health Check

Check if the API is running and healthy.

```http
GET /health
```

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "github-issues-similarity"
}
```

### Root Endpoint

Get basic API information.

```http
GET /
```

#### Response

```json
{
  "message": "GitHub Issues Similarity API",
  "docs": "/docs",
  "health": "/health"
}
```

### Index Repository

Index issues and PRs from a GitHub repository for similarity search.

```http
POST /index
```

#### Request Body

```json
{
  "owner": "string",                    // Required: Repository owner
  "repo": "string",                     // Required: Repository name
  "max_issues": 100,                    // Optional: Max issues to index (1-1000)
  "include_discussions": false,         // Optional: Include GitHub discussions
  "issue_state": "open"                 // Optional: Issue state - "open" (default), "closed", or "all"
}
```

#### Response

```json
{
  "repository": "microsoft/vscode",
  "indexed": 150,
  "issues": 120,
  "pull_requests": 30,
  "discussions": 0,
  "message": "Successfully indexed microsoft/vscode"
}
```

#### Error Responses

| Status | Description | Example |
|--------|-------------|---------|
| 404 | Repository not found | `{"detail": "Repository microsoft/nonexistent not found"}` |
| 403 | GitHub API rate limit | `{"detail": "GitHub API rate limit exceeded"}` |
| 500 | Server error | `{"detail": "Internal server error"}` |

#### Examples

```bash
# Basic indexing
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "facebook",
    "repo": "react",
    "max_issues": 200
  }'

# Include discussions
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "microsoft",
    "repo": "vscode",
    "max_issues": 500,
    "include_discussions": true
  }'
```

### Find Similar Issues

Find issues similar to a specific GitHub issue or PR.

```http
POST /find_similar
```

#### Request Body

```json
{
  "owner": "string",                    // Required: Repository owner
  "repo": "string",                     // Required: Repository name
  "issue_number": 12345,                // Required: Issue/PR number
  "top_k": 10,                          // Optional: Number of results (1-50)
  "min_similarity": 0.0                 // Optional: Min similarity score (0.0-1.0)
}
```

#### Response

```json
{
  "query_issue": {
    "number": 12345,
    "url": "https://github.com/microsoft/vscode/issues/12345"
  },
  "similar_issues": [
    {
      "number": 12340,
      "title": "Similar bug with editor",
      "similarity": 0.92,
      "state": "closed",
      "created_at": "2023-01-15T10:30:00Z",
      "updated_at": "2023-01-20T14:45:00Z",
      "url": "https://github.com/microsoft/vscode/issues/12340",
      "labels": ["bug", "editor"],
      "is_pull_request": false,
      "is_discussion": false
    }
  ],
  "count": 1
}
```

#### Error Responses

| Status | Description | Example |
|--------|-------------|---------|
| 404 | Issue not found | `{"detail": "Issue #99999 not found in microsoft/vscode"}` |
| 500 | Server error | `{"detail": "Internal server error"}` |

#### Examples

```bash
# Find similar issues
curl -X POST "http://localhost:8000/find_similar" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "microsoft",
    "repo": "vscode",
    "issue_number": 12345
  }'

# High similarity threshold
curl -X POST "http://localhost:8000/find_similar" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "microsoft",
    "repo": "vscode", 
    "issue_number": 12345,
    "top_k": 3,
    "min_similarity": 0.8
  }'
```

### Get Statistics

Get statistics about indexed repositories and issues.

```http
GET /stats
```

#### Response

```json
{
  "total_issues": 1247,
  "repositories": [
    "microsoft/vscode",
    "facebook/react",
    "nodejs/node"
  ],
  "collections": 3
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/stats"
```

### Clear All Data

Remove all indexed issues from the database.

```http
DELETE /clear
```

#### Response

```json
{
  "message": "Successfully cleared all indexed issues from the database",
  "cleared": true
}
```

#### Example

```bash
curl -X DELETE "http://localhost:8000/clear"
```

### Suggest Discussions

Analyze issues to suggest which ones should be converted to GitHub discussions.

```http
POST /suggest_discussions
```

#### Request Body

```json
{
  "owner": "string",                    // Required: Repository owner
  "repo": "string",                     // Required: Repository name
  "min_score": 0.5,                     // Optional: Min discussion score (0.0-1.0)
  "max_suggestions": 20,                // Optional: Max suggestions (1-100)
  "dry_run": true                       // Optional: Dry run mode (default: true)
}
```

#### Response

```json
{
  "repository": "microsoft/vscode",
  "suggestions": [
    {
      "number": 12341,
      "title": "How to configure X?",
      "score": 0.85,
      "state": "open",
      "reasons": ["question", "help-wanted", "discussion-like"],
      "url": "https://github.com/microsoft/vscode/issues/12341"
    }
  ],
  "total_analyzed": 150,
  "dry_run": true
}
```

#### Example

```bash
# Analyze issues (dry run)
curl -X POST "http://localhost:8000/suggest_discussions" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "microsoft",
    "repo": "vscode",
    "min_score": 0.7
  }'
```

## Data Models

### Issue Model

```json
{
  "number": 12345,                      // Issue/PR number
  "title": "Issue title",               // Issue title
  "body": "Issue description...",       // Issue body (truncated to 10KB)
  "state": "open",                      // "open" or "closed"
  "created_at": "2023-01-15T10:30:00Z", // ISO 8601 timestamp
  "updated_at": "2023-01-20T14:45:00Z", // ISO 8601 timestamp
  "url": "https://github.com/...",      // GitHub URL
  "labels": ["bug", "enhancement"],     // Issue labels
  "is_pull_request": false,             // Whether it's a PR
  "is_discussion": false                // Whether it's a discussion
}
```

### Similarity Result Model

```json
{
  "number": 12340,
  "title": "Similar issue",
  "similarity": 0.92,                   // Cosine similarity score (0.0-1.0)
  "state": "closed",
  "created_at": "2023-01-15T10:30:00Z",
  "updated_at": "2023-01-20T14:45:00Z", 
  "url": "https://github.com/...",
  "labels": ["bug"],
  "is_pull_request": false,
  "is_discussion": false
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Status | Meaning | Common Causes |
|--------|---------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Repository or issue not found |
| 403 | Forbidden | GitHub API rate limit or permissions |
| 422 | Validation Error | Invalid request body format |
| 500 | Server Error | Internal server or Chroma API error |

### Error Examples

```json
// Repository not found
{
  "detail": "Repository microsoft/nonexistent not found"
}

// Rate limit exceeded  
{
  "detail": "GitHub API rate limit exceeded or authentication required"
}

// Validation error
{
  "detail": [
    {
      "loc": ["body", "max_issues"],
      "msg": "ensure this value is less than or equal to 1000",
      "type": "value_error.number.not_le"
    }
  ]
}
```

## Authentication

The API currently doesn't require authentication, but uses the `GITHUB_TOKEN` environment variable for GitHub API access if available.

For production use, consider adding API key authentication:

```bash
# Optional: Set GitHub token for higher rate limits
export GITHUB_TOKEN="your-github-token"
```

## Rate Limits

### GitHub API Limits

- **Without token**: 60 requests/hour per IP
- **With token**: 5,000 requests/hour

### Chroma Cloud Limits

- **Document size**: 16KB per document
- **Request limits**: Based on your Chroma plan

## Usage Examples

### Python Client

```python
import requests

base_url = "http://localhost:8000"

# Index a repository
response = requests.post(f"{base_url}/index", json={
    "owner": "microsoft",
    "repo": "vscode",
    "max_issues": 200
})
print(response.json())

# Find similar issues
response = requests.post(f"{base_url}/find_similar", json={
    "owner": "microsoft",
    "repo": "vscode", 
    "issue_number": 12345,
    "top_k": 5,
    "min_similarity": 0.7
})
similar_issues = response.json()["similar_issues"]
for issue in similar_issues:
    print(f"#{issue['number']}: {issue['title']} ({issue['similarity']:.1%})")
```

### JavaScript Client

```javascript
const baseUrl = 'http://localhost:8000';

// Index a repository
const indexResponse = await fetch(`${baseUrl}/index`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    owner: 'microsoft',
    repo: 'vscode',
    max_issues: 200
  })
});
const indexResult = await indexResponse.json();
console.log(indexResult);

// Find similar issues
const similarResponse = await fetch(`${baseUrl}/find_similar`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    owner: 'microsoft',
    repo: 'vscode',
    issue_number: 12345,
    top_k: 5
  })
});
const similarResult = await similarResponse.json();
console.log(similarResult.similar_issues);
```

### Bash/cURL Scripts

```bash
#!/bin/bash

API_URL="http://localhost:8000"
OWNER="microsoft"
REPO="vscode"

# Function to index repository
index_repo() {
    curl -X POST "${API_URL}/index" \
         -H "Content-Type: application/json" \
         -d "{\"owner\":\"${OWNER}\",\"repo\":\"${REPO}\",\"max_issues\":500}"
}

# Function to find similar issues
find_similar() {
    local issue_number=$1
    curl -X POST "${API_URL}/find_similar" \
         -H "Content-Type: application/json" \
         -d "{\"owner\":\"${OWNER}\",\"repo\":\"${REPO}\",\"issue_number\":${issue_number}}"
}

# Usage
index_repo
find_similar 12345
```

## OpenAPI Documentation

The API provides automatic OpenAPI documentation:

- **Interactive docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Deployment

### Development

```bash
python api.py
# Runs on http://localhost:8000
```

### Production

```bash
# Using uvicorn directly
uvicorn api:app --host 0.0.0.0 --port 8000

# Using gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app

# Using Docker
docker build -t deja-view .
docker run -p 8000:8000 -e CHROMA_API_KEY=... -e CHROMA_TENANT=... deja-view
```

### Environment Variables

```bash
# Required
CHROMA_API_KEY=your-api-key
CHROMA_TENANT=your-tenant-id

# Optional
CHROMA_DATABASE=default-database
GITHUB_TOKEN=your-github-token
```