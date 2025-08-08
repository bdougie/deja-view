# CLI Usage Guide

## Installation

```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using traditional pip
pip install -r requirements.txt
```

## Command Overview

```bash
$ uv run python cli.py --help
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  Deja View - Find similar GitHub issues using semantic search

Commands:
  index                Index repository issues and discussions
  find                 Find similar issues to a specific issue/PR
  suggest-discussions  Suggest issues to convert to discussions
  user-comments        Fetch a user's recent comments from GitHub
  quick                Quick command to find similar issues
  stats                Show statistics about indexed issues
  clear                Clear all indexed issues

Options:
  --help  Show this message and exit.
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

Index issues from a repository with flexible filtering:

```bash
uv run python cli.py index OWNER/REPO [OPTIONS]

# Examples
uv run python cli.py index facebook/react                        # Index open issues (default)
uv run python cli.py index microsoft/vscode --state closed       # Index closed issues only
uv run python cli.py index google/material-ui --state all        # Index all issues
uv run python cli.py index continuedev/continue --include-discussions --state open
```

**Example Output:**
```
$ uv run python cli.py index continuedev/continue
✓ Successfully indexed 200 issues from continuedev/continue

# With state filter
$ uv run python cli.py index continuedev/continue --state open
✓ Successfully indexed 150 open issues from continuedev/continue

# With discussions included
$ uv run python cli.py index continuedev/continue --include-discussions --state all
✓ Successfully indexed 350 items from continuedev/continue (300 issues, 50 discussions)
```

**Options:**
- `--max-issues, -m`: Maximum number of issues to index (default: 100)
- `--state, -s`: Issue state filter - `open` (default), `closed`, or `all`
- `--include-discussions, -d`: Include GitHub discussions in indexing
- Progress bar shows indexing status
- Respects GitHub rate limits

### Find Similar Issues

Find issues similar to a specific issue or PR:

```bash
uv run python cli.py find ISSUE_URL

# Examples
uv run python cli.py find https://github.com/facebook/react/issues/1234
uv run python cli.py find https://github.com/microsoft/vscode/pull/5678
```

**Example Output:**
```
$ uv run python cli.py find https://github.com/continuedev/continue/pull/2000
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ #      ┃ Title                                 ┃ Similarity ┃ State  ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ 1995   │ Add support for custom models         │ 87.3%      │ open   │
│ 1234   │ Model configuration improvements      │ 85.1%      │ closed │
└────────┴───────────────────────────────────────┴────────────┴────────┘
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
uv run python cli.py quick OWNER/REPO ISSUE_NUMBER

# Example
uv run python cli.py quick facebook/react 1234
```

**Example Output:**
```
$ uv run python cli.py quick continuedev/continue 2000 --index-first
✓ Successfully indexed 200 issues from continuedev/continue

Searching for similar issues to #2000...

┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ #      ┃ Title                                 ┃ Similarity ┃ State  ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ 1995   │ Add support for custom models         │ 87.3%      │ open   │
│ 1234   │ Model configuration improvements      │ 85.1%      │ closed │
└────────┴───────────────────────────────────────┴────────────┴────────┘
```

**Workflow:**
1. Indexes the repository if not already done
2. Immediately searches for similar issues
3. Shows results with similarity scores

### Suggest Discussions

Find issues that should potentially be converted to discussions:

```bash
uv run python cli.py suggest-discussions OWNER/REPO

# Example
uv run python cli.py suggest-discussions facebook/react
```

**Example Output:**
```
$ uv run python cli.py suggest-discussions continuedev/continue
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #      ┃ Title                        ┃ Score  ┃ State  ┃ Reasons                ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1423   │ How to configure models?     │ 0.85   │ open   │ Question pattern       │
│ 987    │ Feature request: dark theme  │ 0.72   │ open   │ Feature request        │
└────────┴──────────────────────────────┴────────┴────────┴────────────────────────┘

Analyzed 180 issues, found 2 suggestions
Tip: Use --execute flag to convert these issues to discussions
```

**Options:**
- `--threshold`: Minimum score for suggestions (default: 0.7)
- `--limit`: Maximum suggestions (default: 10)
- `--dry-run`: Preview without making changes (default: true)
- `--execute`: Actually convert issues to discussions

**Analysis Criteria:**
- Questions and help requests
- Feature requests and proposals
- Discussions without clear bug reports
- Community feedback topics

### View Statistics

Show database statistics:

```bash
uv run python cli.py stats
```

**Example Output:**
```
$ uv run python cli.py stats
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Repository                 ┃ Issues ┃ Discussions ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━┩
│ continuedev/continue       │ 200    │ 50          │
│ microsoft/vscode           │ 500    │ 120         │
│ facebook/react             │ 350    │ 80          │
└────────────────────────────┴────────┴─────────────┘

Total repositories: 3
Total documents: 1,300
```

**Shows:**
- Total indexed repositories
- Number of issues per repository
- Number of discussions per repository
- Database collection information

### Fetch User Comments

Fetch a user's recent comments from GitHub issues and PRs:

```bash
uv run python cli.py user-comments [OPTIONS]
```

**Example Usage:**
```bash
# Fetch your own recent comments (authenticated user)
uv run python cli.py user-comments

# Fetch specific user's comments
uv run python cli.py user-comments --user octocat --limit 5

# Filter comments by repository
uv run python cli.py user-comments --repo facebook/react

# Get comments since a specific date
uv run python cli.py user-comments --since 2025-01-01

# Combine filters
uv run python cli.py user-comments --user bdougie --repo open-sauced/app --limit 20
```

**Example Output:**
```
$ uv run python cli.py user-comments --limit 5
Fetching comments for authenticated user: bdougie

┏━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Date       ┃ Repo    ┃ #      ┃ Type ┃ Comment                                     ┃
┡━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2025-01-08 │ app     │ 1234   │ 🐛   │ This looks like a duplicate of #987...      │
│ 2025-01-07 │ vscode  │ 5678   │ 🔀   │ LGTM! Thanks for the contribution.          │
│ 2025-01-06 │ react   │ 2468   │ 🐛   │ I can reproduce this issue on v18.2...     │
└────────────┴─────────┴────────┴──────┴─────────────────────────────────────────────┘

Recent comment URLs:
1. https://github.com/open-sauced/app/issues/1234#issuecomment-123456
2. https://github.com/microsoft/vscode/pull/5678#issuecomment-234567
```

**Options:**
- `--user, -u`: GitHub username (defaults to authenticated user)
- `--limit, -n`: Number of comments to fetch (default: 10)
- `--repo, -r`: Filter comments by repository (format: owner/repo)
- `--since, -s`: Show comments since date (YYYY-MM-DD)

**Requirements:**
- GitHub CLI (`gh`) must be installed and authenticated
- Install from: https://cli.github.com
- Authenticate with: `gh auth login`

### Clear Database

Remove all indexed data:

```bash
uv run python cli.py clear
```

**Example Output:**
```
$ uv run python cli.py clear
⚠️  Warning: This will delete all indexed data!
Are you sure? (y/N): y

✓ Successfully cleared all collections
```

**Warning:** This permanently deletes all indexed issues and discussions.

## Advanced Usage

### Combining with Shell Scripts

```bash
# Index multiple repositories
for repo in facebook/react microsoft/vscode google/material-ui; do
    echo "Indexing $repo..."
    uv run python cli.py index $repo
done

# Find similar issues across multiple searches
uv run python cli.py find https://github.com/facebook/react/issues/1234 --limit 10

# Batch process multiple issues
for issue in 1234 5678 9012; do
    echo "Finding similar to #$issue..."
    uv run python cli.py find https://github.com/continuedev/continue/issues/$issue
done

# Export results to file
uv run python cli.py find https://github.com/continuedev/continue/issues/2000 > similar_issues.txt
```

### Using with CI/CD

```yaml
# Example GitHub Actions workflow
- name: Index Repository
  run: |
    uv run python cli.py index ${{ github.repository }}
    
- name: Find Similar Issues
  run: |
    uv run python cli.py find ${{ github.event.issue.html_url }}
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

## Real-World Examples

### Finding Duplicate Issues

```bash
# Before opening a new issue, check for duplicates
$ uv run python cli.py find https://github.com/continuedev/continue/issues/new

# Find very similar issues only (high threshold)
$ uv run python cli.py find https://github.com/continuedev/continue/issues/2000 --threshold 0.8

# Get more results for broader search
$ uv run python cli.py find https://github.com/continuedev/continue/issues/2000 --limit 20 --threshold 0.4
```

### Repository Maintenance

```bash
# Regular indexing with discussions
$ uv run python cli.py index continuedev/continue --include-discussions

# Find and convert discussion candidates
$ uv run python cli.py suggest-discussions continuedev/continue --dry-run
$ uv run python cli.py suggest-discussions continuedev/continue --execute

# Monitor repository growth
$ uv run python cli.py stats | grep continuedev/continue
```

### Automation Scripts

```bash
#!/bin/bash
# daily-index.sh - Run daily to keep index fresh

REPOS=(
    "continuedev/continue"
    "microsoft/vscode"
    "facebook/react"
)

for repo in "${REPOS[@]}"; do
    echo "Indexing $repo at $(date)"
    uv run python cli.py index "$repo" --include-discussions
    sleep 5  # Be nice to GitHub API
done

uv run python cli.py stats
```