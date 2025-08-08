# Deja-View MCP Server for Continue

This guide shows how to set up and use the Deja-View MCP server with Continue for AI-assisted GitHub issue management.

## What is MCP?

Model Context Protocol (MCP) is a standard for exposing tools and resources to AI assistants. FastMCP makes it easy to create MCP servers that Continue can connect to.

## Features

The Deja-View MCP server provides these tools to your Continue assistant:

- **`find_similar_issues`** - Find semantically similar GitHub issues
- **`index_repository`** - Index a repository's issues for similarity search
- **`get_user_comments`** - Fetch a user's recent GitHub comments
- **`suggest_discussion_candidates`** - Identify issues that should be discussions
- **`search_github_issues`** - Search GitHub issues with filters
- **`get_similarity_stats`** - Get statistics about indexed repositories

## Prerequisites

1. **Continue** installed in VS Code
2. **Python 3.8+** and **uv** package manager
3. **GitHub CLI** installed and authenticated
4. **Environment variables** for Chroma and GitHub

## Installation

### Step 1: Install Dependencies

```bash
# Clone the repository
git clone https://github.com/bdougie/deja-view.git
cd deja-view

# Install dependencies with uv
uv pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Chroma Cloud credentials (get from https://cloud.trychroma.com)
CHROMA_API_KEY=your-chroma-api-key
CHROMA_TENANT=your-tenant-id
CHROMA_DATABASE=default_database  # Optional

# GitHub token for higher rate limits (optional)
GITHUB_TOKEN=your-github-token

# GitHub CLI authentication (required)
# Run: gh auth login
```

### Step 3: Test the MCP Server

```bash
# Test that the server runs
uv run python mcp_server.py --help

# You should see available tools listed
```

## Continue Configuration

### Step 1: Add MCP Server to Continue

Open your Continue configuration file:
- Mac/Linux: `~/.continue/config.json`
- Windows: `%USERPROFILE%\.continue\config.json`

Add the Deja-View MCP server to the `mcpServers` section:

```json
{
  "models": [
    // Your existing models...
  ],
  "mcpServers": [
    {
      "name": "deja-view",
      "command": "uv",
      "args": ["run", "python", "/path/to/deja-view/mcp_server.py"],
      "env": {
        "CHROMA_API_KEY": "your-chroma-api-key",
        "CHROMA_TENANT": "your-tenant-id",
        "GITHUB_TOKEN": "your-github-token"  // Optional
      }
    }
  ]
}
```

**Important:** Replace `/path/to/deja-view` with the actual path to your deja-view directory.

### Step 2: Restart Continue

1. Open VS Code Command Palette (`Cmd+Shift+P` or `Ctrl+Shift+P`)
2. Run: `Continue: Restart Continue`
3. The MCP server should now be connected

### Step 3: Verify Connection

In Continue chat, type:
```
What tools do you have available from deja-view?
```

The assistant should list the available tools.

## Usage Examples

### Example 1: Finding Similar Issues

In Continue chat:
```
Can you find issues similar to issue #1234 in facebook/react?
```

The assistant will use the `find_similar_issues` tool automatically.

### Example 2: Index a Repository First

```
Please index the continuedev/continue repository with the last 200 issues, 
then find issues similar to #2000
```

### Example 3: Check User Activity

```
Show me the last 10 comments from user octocat in the facebook/react repository
```

### Example 4: Identify Discussion Candidates

```
Which issues in microsoft/vscode should potentially be converted to discussions?
```

### Example 5: Complex Workflow

```
1. Index the open-sauced/app repository
2. Find issues similar to #500
3. For any high similarity matches (>80%), check if the original authors have commented recently
4. Suggest which ones might be duplicates
```

## Advanced Configuration

### Using with Docker

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    environment:
      - CHROMA_API_KEY=${CHROMA_API_KEY}
      - CHROMA_TENANT=${CHROMA_TENANT}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./:/app
    command: python mcp_server.py
```

Then update Continue config to use Docker:

```json
{
  "mcpServers": [
    {
      "name": "deja-view",
      "command": "docker",
      "args": ["run", "--rm", "-i", "deja-view-mcp"]
    }
  ]
}
```

### Environment-Specific Settings

For different environments, create separate config files:

**Development** (`~/.continue/config.dev.json`):
```json
{
  "mcpServers": [
    {
      "name": "deja-view-dev",
      "command": "uv",
      "args": ["run", "python", "/path/to/deja-view/mcp_server.py"],
      "env": {
        "CHROMA_DATABASE": "dev_database"
      }
    }
  ]
}
```

**Production** (`~/.continue/config.prod.json`):
```json
{
  "mcpServers": [
    {
      "name": "deja-view-prod",
      "command": "uv",
      "args": ["run", "python", "/path/to/deja-view/mcp_server.py"],
      "env": {
        "CHROMA_DATABASE": "prod_database"
      }
    }
  ]
}
```

## Troubleshooting

### MCP Server Not Connecting

1. **Check logs**: View Continue output panel in VS Code
2. **Verify path**: Ensure the path to `mcp_server.py` is absolute
3. **Test manually**: Run `uv run python /path/to/mcp_server.py` in terminal

### Authentication Issues

```bash
# Verify GitHub CLI authentication
gh auth status

# Re-authenticate if needed
gh auth login

# Test GitHub access
gh api user
```

### Environment Variables Not Found

```bash
# Verify .env file is loaded
uv run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('CHROMA_API_KEY'))"
```

### Rate Limiting

If you hit GitHub rate limits:
1. Add a `GITHUB_TOKEN` to increase limits (5000/hour vs 60/hour)
2. Use the `index_repository` tool to cache data locally
3. Implement pagination for large result sets

## Tool Documentation

### find_similar_issues

Find semantically similar issues using vector embeddings.

**Parameters:**
- `repository` (str): Repository in format "owner/repo"
- `issue_number` (int): Issue number to find similar issues for
- `limit` (int): Maximum results (default: 10)
- `min_similarity` (float): Minimum similarity score 0-1 (default: 0.0)

**Example:**
```python
find_similar_issues("facebook/react", 1234, limit=5, min_similarity=0.7)
```

### index_repository

Index repository issues for similarity search.

**Parameters:**
- `repository` (str): Repository in format "owner/repo"
- `max_issues` (int): Maximum issues to index (default: 100)
- `include_discussions` (bool): Include discussions (default: False)
- `issue_state` (str): "open", "closed", or "all" (default: "open")

**Example:**
```python
index_repository("continuedev/continue", max_issues=200, issue_state="all")
```

### get_user_comments

Fetch user's recent GitHub comments.

**Parameters:**
- `username` (str): GitHub username
- `limit` (int): Number of comments (default: 10)
- `repository` (str, optional): Filter by repository
- `since_date` (str, optional): Date filter "YYYY-MM-DD"

**Example:**
```python
get_user_comments("octocat", limit=5, repository="facebook/react")
```

### suggest_discussion_candidates

Identify issues that should be discussions.

**Parameters:**
- `repository` (str): Repository in format "owner/repo"
- `min_score` (float): Minimum score 0-1 (default: 0.5)
- `max_suggestions` (int): Maximum suggestions (default: 20)

**Example:**
```python
suggest_discussion_candidates("microsoft/vscode", min_score=0.7)
```

### search_github_issues

Search GitHub issues with filters.

**Parameters:**
- `query` (str): Search query
- `repository` (str, optional): Repository filter
- `limit` (int): Maximum results (default: 10)
- `sort` (str): "relevance", "created", "updated", "comments"

**Example:**
```python
search_github_issues("bug rendering", repository="facebook/react", limit=5)
```

### get_similarity_stats

Get statistics about indexed repositories.

**Parameters:** None

**Example:**
```python
get_similarity_stats()
```

## Best Practices

### 1. Index Before Searching

Always index a repository before searching for similar issues:

```
First, index the repository facebook/react with 500 issues.
Then find issues similar to #1234.
```

### 2. Use Appropriate Limits

- For initial indexing: 100-500 issues
- For similarity search: 5-20 results
- For user comments: 10-50 comments

### 3. Filter by State

When indexing, consider the issue state:
- `"open"` - Active issues only
- `"closed"` - Historical data
- `"all"` - Complete dataset

### 4. Combine Tools

Use multiple tools together for complex workflows:

```
1. Search for "memory leak" issues in microsoft/vscode
2. For each result, find similar issues
3. Check if any reporters have commented recently
4. Summarize the findings
```

## Integration with Continue Workflows

### Code Review Assistant

```
When I'm reviewing a PR, check if there are similar issues that might be related or duplicated by this change.
```

### Bug Triage Helper

```
For new bug reports, automatically find similar issues and suggest if it's a duplicate.
```

### Documentation Helper

```
Find all issues mentioning "documentation" and suggest which ones should be converted to discussions.
```

## Support

- **GitHub Issues**: https://github.com/bdougie/deja-view/issues
- **Continue Docs**: https://docs.continue.dev/customize/deep-dives/mcp
- **FastMCP Docs**: https://github.com/jlowin/fastmcp

## License

MIT License - See LICENSE file for details.