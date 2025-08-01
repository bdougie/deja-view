# CLI Usage Guide

## Installation

```bash
# Using pip
pip install -r requirements.txt

# Using uv (recommended)
uv pip install -r requirements.txt
```

## Configuration

Set required environment variables:

```bash
export CHROMA_API_KEY="your-api-key"
export CHROMA_TENANT="your-tenant-id"
export CHROMA_DATABASE="your-database"  # Optional, defaults to 'default_database'
export GITHUB_TOKEN="your-github-token"  # Optional, for higher rate limits
```

## Commands

### Index Repository

Index all issues and discussions from a repository:

```bash
python cli.py index OWNER/REPO

# Examples
python cli.py index facebook/react
python cli.py index microsoft/vscode
```

**Options:**
- Progress bar shows indexing status
- Handles both issues and discussions
- Respects GitHub rate limits

### Find Similar Issues

Find issues similar to a specific issue or PR:

```bash
python cli.py find ISSUE_URL

# Examples
python cli.py find https://github.com/facebook/react/issues/1234
python cli.py find https://github.com/microsoft/vscode/pull/5678
```

**Options:**
- `--threshold`: Similarity threshold (0.0-1.0, default: 0.5)
- `--limit`: Maximum results to return (default: 5)

**Output:**
- Color-coded similarity scores (green=high, yellow=medium, red=low)
- Issue title, state, and labels
- Direct links to issues

### Quick Search

Combines indexing and searching in one command:

```bash
python cli.py quick OWNER/REPO ISSUE_NUMBER

# Example
python cli.py quick facebook/react 1234
```

**Workflow:**
1. Indexes the repository if not already done
2. Immediately searches for similar issues
3. Shows results with similarity scores

### Suggest Discussions

Find issues that should potentially be converted to discussions:

```bash
python cli.py suggest-discussions OWNER/REPO

# Example
python cli.py suggest-discussions facebook/react
```

**Options:**
- `--threshold`: Minimum score for suggestions (default: 0.7)
- `--limit`: Maximum suggestions (default: 10)
- `--dry-run`: Preview without making changes

**Analysis Criteria:**
- Questions and help requests
- Feature requests and proposals
- Discussions without clear bug reports
- Community feedback topics

### View Statistics

Show database statistics:

```bash
python cli.py stats
```

**Shows:**
- Total indexed repositories
- Number of issues per repository
- Number of discussions per repository
- Database collection information

### Clear Database

Remove all indexed data:

```bash
python cli.py clear
```

**Warning:** This permanently deletes all indexed issues and discussions.

## Advanced Usage

### Combining with Shell Scripts

```bash
# Index multiple repositories
for repo in facebook/react microsoft/vscode google/material-ui; do
    python cli.py index $repo
done

# Find similar issues across multiple searches
python cli.py find https://github.com/facebook/react/issues/1234 --limit 10
```

### Using with CI/CD

```yaml
# Example GitHub Actions workflow
- name: Index Repository
  run: |
    python cli.py index ${{ github.repository }}
    
- name: Find Similar Issues
  run: |
    python cli.py find ${{ github.event.issue.html_url }}
```

### Output Formatting

The CLI uses Rich for enhanced terminal output:
- **Progress bars** for long operations
- **Color coding** for similarity scores
- **Tables** for structured data
- **Markdown rendering** for issue bodies

### Error Handling

Common errors and solutions:

1. **Rate Limit Exceeded**
   - Add `GITHUB_TOKEN` for higher limits
   - Wait for rate limit reset

2. **Authentication Failed**
   - Check `CHROMA_API_KEY` is valid
   - Verify `CHROMA_TENANT` is correct

3. **Repository Not Found**
   - Verify repository exists and is public
   - Check repository name format (OWNER/REPO)

## Tips and Best Practices

1. **Initial Setup**
   - Index repositories during off-peak hours
   - Start with smaller repositories for testing

2. **Similarity Thresholds**
   - 0.7+ : Very similar issues
   - 0.5-0.7 : Related issues
   - Below 0.5 : Loosely related

3. **Performance**
   - Use `--limit` to control result size
   - Index incrementally for large repositories

4. **Integration**
   - Combine with GitHub Actions for automation
   - Use REST API for programmatic access