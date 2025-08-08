# User Comments CLI Command

A GitHub CLI wrapper for fetching a user's recent comments from issues and pull requests.

## Prerequisites

1. **uv** - Python package manager
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **GitHub CLI (gh)** - Must be installed and authenticated
   ```bash
   # Install gh from https://cli.github.com
   
   # Authenticate with GitHub
   gh auth login
   ```

3. **Python dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Fetch your own recent comments (authenticated user):
```bash
uv run python cli.py user-comments
```

### Command Options

- `--user, -u`: GitHub username (defaults to authenticated user)
- `--limit, -n`: Number of comments to fetch (default: 10)
- `--repo, -r`: Filter comments by repository (format: owner/repo)
- `--since, -s`: Show comments since date (YYYY-MM-DD)

### Examples

#### Fetch specific user's comments
```bash
uv run python cli.py user-comments --user octocat --limit 5
```

#### Filter by repository
```bash
uv run python cli.py user-comments --repo facebook/react
```

#### Get comments since a specific date
```bash
uv run python cli.py user-comments --since 2025-01-01
```

#### Combine multiple filters
```bash
uv run python cli.py user-comments \
  --user bdougie \
  --repo open-sauced/app \
  --since 2025-01-01 \
  --limit 20
```

## Output Format

The command displays results in a formatted table showing:
- **Date**: When the comment was made
- **Repo**: Repository name
- **#**: Issue/PR number
- **Type**: 🐛 for issues, 🔀 for pull requests
- **Comment**: Preview of the comment (truncated to 60 chars)

Example output:
```
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
3. https://github.com/facebook/react/issues/2468#issuecomment-345678
```

## Demo Script

Run the included demo script to see examples:
```bash
./demo_user_comments.sh
```

## Integration with Other Commands

Combine with other Deja-View commands for enhanced workflow:

```bash
# Find user's recent comments, then check for similar issues
uv run python cli.py user-comments --limit 5
uv run python cli.py find https://github.com/owner/repo/issues/123

# Index repositories you've commented on
uv run python cli.py user-comments --limit 20 | grep "│" | awk '{print $2}' | sort -u | while read repo; do
  uv run python cli.py index "owner/$repo"
done
```

## Troubleshooting

### GitHub CLI not found
```bash
Error: GitHub CLI (gh) is not installed
```
**Solution**: Install gh from https://cli.github.com

### Not authenticated
```bash
Error: Not authenticated with GitHub CLI
```
**Solution**: Run `gh auth login`

### Rate limiting
If you encounter rate limits, the command will use authenticated requests which have higher limits (5000/hour vs 60/hour for unauthenticated).

## Implementation Details

This command wraps GitHub CLI operations:
1. Uses `gh search issues` to find issues/PRs where the user has commented
2. Uses `gh api` to fetch the actual comment content
3. Formats and displays results using Rich terminal formatting

The implementation can be found in `cli.py` at the `user_comments` function.