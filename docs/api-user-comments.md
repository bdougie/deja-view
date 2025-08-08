# User Comments API Endpoints

## Overview

The API provides endpoints to fetch GitHub user information and their recent comments on issues and pull requests.

## Base URL

```
http://localhost:8000
```

## Authentication

The server must be authenticated with GitHub CLI (`gh auth login`) to access GitHub data.

## Endpoints

### 1. Get User Comments

Fetch a user's recent comments from GitHub issues and PRs with detailed information.

**Endpoint:** `GET /user/{username}/comments`

**Parameters:**
- `username` (path, required): GitHub username
- `limit` (query, optional): Number of comments to fetch (1-100, default: 10)
- `repo` (query, optional): Filter by repository (format: owner/repo)
- `since` (query, optional): Show comments since date (YYYY-MM-DD)

**Example Request:**
```bash
# Using curl
curl "http://localhost:8000/user/octocat/comments?limit=5&repo=facebook/react"

# Using httpie
http GET localhost:8000/user/octocat/comments limit==5 repo==facebook/react

# Using uv and Python
uv run python -c "import requests; print(requests.get('http://localhost:8000/user/octocat/comments?limit=5').json())"
```

**Response:**
```json
{
  "username": "octocat",
  "repository_filter": "facebook/react",
  "since_date": null,
  "count": 5,
  "comments": [
    {
      "issue": {
        "number": 1234,
        "title": "Bug: Component not rendering correctly",
        "repository": "facebook/react",
        "state": "open",
        "is_pull_request": false,
        "url": "https://github.com/facebook/react/issues/1234",
        "labels": ["bug", "needs-triage"]
      },
      "comment": {
        "id": 123456789,
        "body": "I can reproduce this issue with the following code...",
        "body_preview": "I can reproduce this issue with the following code...",
        "created_at": "2025-01-08T10:30:00Z",
        "url": "https://github.com/facebook/react/issues/1234#issuecomment-123456789"
      }
    }
  ]
}
```

### 2. Get Current User Comments

Fetch the authenticated user's recent comments (server must be authenticated with `gh`).

**Endpoint:** `GET /user/current/comments`

**Parameters:**
- `limit` (query, optional): Number of comments to fetch (1-100, default: 10)
- `repo` (query, optional): Filter by repository (format: owner/repo)
- `since` (query, optional): Show comments since date (YYYY-MM-DD)

**Example Request:**
```bash
curl "http://localhost:8000/user/current/comments?limit=3"
```

**Response:** Same format as `/user/{username}/comments`

### 3. Get User Commented Issues (Legacy)

Fetch issues a user has commented on (simplified version).

**Endpoint:** `GET /user/{username}/commented-issues`

**Parameters:**
- `username` (path, required): GitHub username
- `repo` (query, optional): Filter by repository
- `limit` (query, optional): Number of issues to fetch (default: 5)

**Example Request:**
```bash
curl "http://localhost:8000/user/octocat/commented-issues?limit=10"
```

**Response:**
```json
{
  "username": "octocat",
  "repository_filter": null,
  "count": 10,
  "issues": [
    {
      "number": 1234,
      "title": "Bug: Component not rendering",
      "repository": "facebook/react",
      "state": "open",
      "url": "https://github.com/facebook/react/issues/1234",
      "labels": ["bug"],
      "updated_at": "2025-01-08T10:30:00Z",
      "last_comment": {
        "body": "I can reproduce this...",
        "created_at": "2025-01-08T10:30:00Z"
      }
    }
  ]
}
```

### 4. Get User Information

Fetch basic GitHub user information.

**Endpoint:** `GET /user/{username}`

**Parameters:**
- `username` (path, required): GitHub username

**Example Request:**
```bash
curl "http://localhost:8000/user/octocat"
```

**Response:**
```json
{
  "login": "octocat",
  "name": "The Octocat",
  "bio": "GitHub mascot",
  "company": "@github",
  "location": "San Francisco",
  "public_repos": 8,
  "followers": 3938,
  "following": 9,
  "created_at": "2011-01-25T18:44:36Z",
  "avatar_url": "https://avatars.githubusercontent.com/u/583231?v=4",
  "html_url": "https://github.com/octocat"
}
```

## Error Responses

All endpoints return appropriate HTTP status codes and error messages:

### 404 Not Found
```json
{
  "detail": "User octocat not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "GitHub CLI (gh) is not installed on the server"
}
```

### 401 Unauthorized
```json
{
  "detail": "Server is not authenticated with GitHub CLI"
}
```

## Rate Limiting

The API uses GitHub's rate limits:
- Authenticated requests: 5,000 requests per hour
- Unauthenticated requests: 60 requests per hour

## Running the API Server

### Using uv (recommended)

```bash
# Install dependencies
uv pip install -r requirements.txt

# Start the server
uv run python api.py

# Or with uvicorn directly
uv run uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Using Docker

```bash
# Build the image
docker build -t deja-view-api .

# Run the container
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e CHROMA_API_KEY=$CHROMA_API_KEY \
  deja-view-api
```

## Testing the API

### Using the built-in docs

Navigate to `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Example test script

```python
import requests

# Test user comments endpoint
response = requests.get(
    "http://localhost:8000/user/bdougie/comments",
    params={
        "limit": 5,
        "repo": "open-sauced/app",
        "since": "2025-01-01"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Found {data['count']} comments")
    for comment_data in data['comments']:
        issue = comment_data['issue']
        comment = comment_data['comment']
        print(f"- {issue['repository']}#{issue['number']}: {comment['body_preview']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Integration Examples

### JavaScript/TypeScript

```typescript
async function getUserComments(username: string, limit: number = 10) {
  const response = await fetch(
    `http://localhost:8000/user/${username}/comments?limit=${limit}`
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

// Usage
getUserComments('octocat', 5)
  .then(data => console.log(`Found ${data.count} comments`))
  .catch(error => console.error('Error:', error));
```

### Python with uv

```python
# save as test_api.py
import requests
import sys

def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "octocat"
    
    response = requests.get(
        f"http://localhost:8000/user/{username}/comments",
        params={"limit": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Recent comments by {username}:")
        for comment_data in data['comments']:
            issue = comment_data['issue']
            print(f"- {issue['repository']}#{issue['number']}: {issue['title']}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    main()
```

Run with:
```bash
uv run python test_api.py bdougie
```

## Notes

- The server must have GitHub CLI installed and authenticated
- Comment bodies are returned in full and with a preview (first 200 characters)
- The API respects GitHub's rate limiting
- All dates are in ISO 8601 format
- Pull requests are included in the results (marked with `is_pull_request: true`)