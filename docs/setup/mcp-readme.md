# Deja-View MCP Server Integration

Use Deja-View's GitHub issue tools directly in your AI coding assistant through the Model Context Protocol (MCP).

## Quick Start

### 1. Install Dependencies

```bash
# Install with uv
uv pip install -r requirements.txt

# Authenticate GitHub CLI
gh auth login
```

### 2. Set Environment Variables

Create `.env` file:
```env
CHROMA_API_KEY=your-api-key
CHROMA_TENANT=your-tenant-id
GITHUB_TOKEN=your-token  # Optional, for higher rate limits
```

### 3. Run Setup Script

```bash
./setup_mcp.sh
```

This will:
- Verify all dependencies
- Test the MCP server
- Generate Continue configuration

### 4. Configure Continue

Add to `~/.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "deja-view",
      "command": "uv",
      "args": ["run", "python", "/path/to/deja-view/mcp_server.py"]
    }
  ]
}
```

### 5. Restart Continue

In VS Code: `Cmd+Shift+P` → `Continue: Restart Continue`

## Available Tools

| Tool | Description | Example Use |
|------|-------------|-------------|
| `find_similar_issues` | Find semantically similar GitHub issues | "Find issues similar to #1234 in facebook/react" |
| `index_repository` | Index repository issues for search | "Index the last 500 issues from continuedev/continue" |
| `get_user_comments` | Fetch user's recent GitHub comments | "Show me octocat's last 10 comments" |
| `suggest_discussion_candidates` | Identify issues that should be discussions | "Which issues in microsoft/vscode should be discussions?" |
| `search_github_issues` | Search GitHub issues with filters | "Search for 'memory leak' in nodejs/node" |
| `get_similarity_stats` | Get indexed repository statistics | "Show me stats about indexed repositories" |

## Usage in Continue

### Example 1: Find Duplicate Issues
```
Can you check if issue #2000 in continuedev/continue has any duplicates?
First index the repository, then find similar issues.
```

### Example 2: User Activity Analysis
```
Show me what bdougie has been commenting on recently in the open-sauced organization repositories.
```

### Example 3: Issue Triage
```
Search for all "bug" labeled issues in facebook/react from the last week,
then find similar issues for each one to identify potential duplicates.
```

### Example 4: Discussion Migration
```
Analyze the microsoft/vscode repository and suggest which open issues 
should be converted to discussions. Focus on questions and feature requests.
```

## Testing

### Test MCP Server Directly

```bash
# Run interactive demo
uv run python examples/mcp_demo.py --interactive

# Run automated demo
uv run python examples/mcp_demo.py
```

### Test Individual Tools

```python
from mcp_server import find_similar_issues

# Find similar issues
result = find_similar_issues(
    repository="facebook/react",
    issue_number=1234,
    limit=5,
    min_similarity=0.7
)
print(result)
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Continue  │────▶│  MCP Server  │────▶│   GitHub   │
│  (VS Code)  │◀────│ (FastMCP)    │◀────│    API     │
└─────────────┘     └──────────────┘     └────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Chroma DB   │
                    │ (Embeddings) │
                    └──────────────┘
```

## How It Works

1. **Continue** sends natural language requests to your AI model
2. The AI model identifies when to use Deja-View tools
3. **MCP Server** receives tool calls from Continue
4. Tools interact with **GitHub API** (via gh CLI) and **Chroma DB**
5. Results are returned to Continue and presented by the AI

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CHROMA_API_KEY` | Yes | Chroma Cloud API key |
| `CHROMA_TENANT` | Yes | Chroma Cloud tenant ID |
| `CHROMA_DATABASE` | No | Database name (default: "default_database") |
| `GITHUB_TOKEN` | No | GitHub personal access token for higher rate limits |

## Rate Limits

- **Without GitHub token**: 60 requests/hour
- **With GitHub token**: 5,000 requests/hour
- **Recommendation**: Always use a GitHub token for production use

## Troubleshooting

### MCP Server Not Connecting

```bash
# Check if server runs standalone
uv run python mcp_server.py --help

# Check Continue logs
# View → Output → Continue
```

### Authentication Issues

```bash
# Verify GitHub CLI auth
gh auth status

# Test GitHub API access
gh api user
```

### Environment Variables Not Loading

```bash
# Test environment
uv run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('CHROMA_API_KEY'))"
```

## Advanced Configuration

### Custom Tool Timeout

In Continue config:
```json
{
  "mcpServers": [
    {
      "name": "deja-view",
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"],
      "timeout": 30000  // 30 seconds
    }
  ]
}
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "mcp_server.py"]
```

```json
{
  "mcpServers": [
    {
      "name": "deja-view",
      "command": "docker",
      "args": ["run", "--rm", "-i", "deja-view-mcp:latest"]
    }
  ]
}
```

## Security Considerations

1. **API Keys**: Never commit `.env` files to version control
2. **GitHub Token**: Use fine-grained personal access tokens with minimal permissions
3. **Chroma Cloud**: Use separate databases for dev/prod environments
4. **Rate Limiting**: Implement caching to reduce API calls

## Contributing

Contributions are welcome! To add new tools:

1. Add tool function to `mcp_server.py`
2. Use the `@mcp.tool()` decorator
3. Include comprehensive docstrings
4. Test with `examples/mcp_demo.py`
5. Update documentation

## Resources

- [Continue MCP Documentation](https://docs.continue.dev/customize/deep-dives/mcp)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Spec](https://github.com/modelcontextprotocol/specification)
- [Deja-View GitHub](https://github.com/bdougie/deja-view)

## License

MIT - See LICENSE file