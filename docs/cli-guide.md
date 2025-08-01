# CLI Guide

The Deja View CLI provides an interactive command-line interface for finding similar GitHub issues using semantic search.

## Installation & Setup

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set required environment variables
export CHROMA_API_KEY="your-chroma-api-key"
export CHROMA_TENANT="your-chroma-tenant-id"

# Optional: GitHub token for higher rate limits
export GITHUB_TOKEN="your-github-token"
```

### Verify Installation

```bash
python cli.py --version
# Output: 1.0.0
```

## Commands Overview

```bash
python cli.py --help
```

| Command | Purpose | Example |
|---------|---------|---------|
| `index` | Index repository issues | `python cli.py index microsoft/vscode` |
| `find` | Find similar issues | `python cli.py find https://github.com/microsoft/vscode/issues/123` |
| `quick` | Index + find in one command | `python cli.py quick microsoft/vscode 123` |
| `stats` | Show database statistics | `python cli.py stats` |
| `clear` | Clear all indexed data | `python cli.py clear` |
| `suggest-discussions` | Find issues that should be discussions | `python cli.py suggest-discussions microsoft/vscode` |

## Command Details

### `index` - Index Repository Issues

Index all issues and PRs from a GitHub repository for similarity search.

```bash
python cli.py index OWNER/REPO [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--max-issues, -m` | 100 | Maximum number of issues to index |
| `--include-discussions, -d` | False | Also index GitHub discussions |

#### Examples

```bash
# Basic indexing
python cli.py index microsoft/vscode

# Index up to 500 issues
python cli.py index microsoft/vscode --max-issues 500

# Include discussions
python cli.py index microsoft/vscode --include-discussions

# Combine options
python cli.py index microsoft/vscode -m 200 -d
```

#### Output

```
✅ Indexing microsoft/vscode...
✓ Successfully indexed 150 items from microsoft/vscode (120 issues, 30 discussions)
```

### `find` - Find Similar Issues

Find issues similar to a specific GitHub issue or PR.

```bash
python cli.py find ISSUE_URL [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--top-k, -k` | 10 | Number of similar issues to return |
| `--min-similarity, -s` | 0.0 | Minimum similarity score (0-1) |

#### Examples

```bash
# Find similar issues
python cli.py find https://github.com/microsoft/vscode/issues/12345

# Limit to top 5 results
python cli.py find https://github.com/microsoft/vscode/issues/12345 --top-k 5

# Only show highly similar issues
python cli.py find https://github.com/microsoft/vscode/issues/12345 --min-similarity 0.7

# Combine options
python cli.py find https://github.com/microsoft/vscode/issues/12345 -k 3 -s 0.8
```

#### Supported URL Formats

```bash
# Issues
https://github.com/owner/repo/issues/123

# Pull Requests
https://github.com/owner/repo/pull/456
```

#### Output

```
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ #      ┃ Title                      ┃ Similarity ┃ State    ┃ Type         ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 12340  │ Similar bug with editor    │      92%   │ closed   │ 🐛 Issue     │
│ 12350  │ Related feature request    │      87%   │ open     │ 🐛 Issue     │
│ 12301  │ Same error message         │      83%   │ closed   │ 🔀 PR        │
└────────┴────────────────────────────┴────────────┴──────────┴──────────────┘

View issues at: https://github.com/microsoft/vscode/issues
```

### `quick` - Quick Index and Find

Combine indexing and finding in a single command. Useful for one-off searches.

```bash
python cli.py quick OWNER/REPO ISSUE_NUMBER [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--index-first, -i` | False | Index repository before searching |
| `--max-issues, -m` | 200 | Max issues to index (if --index-first) |
| `--top-k, -k` | 10 | Number of similar issues to return |

#### Examples

```bash
# Find similar issues (assumes repo already indexed)
python cli.py quick microsoft/vscode 12345

# Index first, then find
python cli.py quick microsoft/vscode 12345 --index-first

# Index up to 500 issues, then find top 5 similar
python cli.py quick microsoft/vscode 12345 -i -m 500 -k 5
```

### `stats` - Database Statistics

Show information about indexed repositories and issues.

```bash
python cli.py stats
```

#### Output

```
┌─ Database Statistics ─────────────────────────────┐
│ Total Issues: 1,247                               │
│ Repositories: 3                                   │
│                                                   │
│ Indexed Repositories:                             │
│   • microsoft/vscode                              │
│   • facebook/react                                │
│   • nodejs/node                                   │
└───────────────────────────────────────────────────┘
```

### `clear` - Clear Database

Remove all indexed issues from the database.

```bash
python cli.py clear
```

⚠️ **Warning**: This action requires confirmation and cannot be undone.

#### Output

```
Are you sure you want to clear all indexed issues? [y/N]: y
✓ Successfully cleared all indexed issues from the database
```

### `suggest-discussions` - Find Issues That Should Be Discussions

Analyze issues to suggest which ones should be converted to GitHub discussions.

```bash
python cli.py suggest-discussions OWNER/REPO [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--min-score, -s` | 0.3 | Minimum discussion score (0.0-1.0) |
| `--max-suggestions, -n` | 20 | Maximum number of suggestions |
| `--dry-run` / `--execute` | `--dry-run` | Dry run (default) or execute changes |

#### Examples

```bash
# Analyze issues (dry run)
python cli.py suggest-discussions microsoft/vscode

# Show only high-confidence suggestions
python cli.py suggest-discussions microsoft/vscode --min-score 0.7

# Execute conversions (be careful!)
python cli.py suggest-discussions microsoft/vscode --execute
```

#### Output

```
⚠️  Warning
DRY RUN MODE - No changes will be made
Use --execute to perform actual conversions

┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #      ┃ Title                      ┃ Score  ┃ State  ┃ Reasons                      ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 12341  │ How to configure X?        │ 0.85   │ open   │ question, help wanted        │
│ 12342  │ Best practices for Y       │ 0.78   │ closed │ discussion, documentation    │
└────────┴────────────────────────────┴────────┴────────┴──────────────────────────────┘

Analyzed 150 issues, found 2 suggestions
Tip: Use --execute flag to convert these issues to discussions
```

## Color Coding & Formatting

### Similarity Scores
- 🟢 **Green** (80-100%): Very similar, likely duplicates
- 🟡 **Yellow** (60-79%): Moderately similar, related issues
- 🔴 **Red** (0-59%): Low similarity

### Issue States
- 🟢 **Green**: Open issues/PRs
- 🔴 **Red**: Closed issues/PRs

### Issue Types
- 🐛 **Issue**: Regular GitHub issue
- 🔀 **PR**: Pull request
- 💬 **Discussion**: GitHub discussion

## Tips & Best Practices

### Performance Tips

1. **Start Small**: Index with `--max-issues 100` first, then increase
2. **Use Filters**: Use `--min-similarity` to reduce noise
3. **Regular Cleanup**: Use `stats` and `clear` to manage database size

### Workflow Recommendations

1. **One-time Search**: Use `quick` command with `--index-first`
2. **Regular Use**: Index repositories once, then use `find` repeatedly
3. **Maintenance**: Check `stats` periodically and `clear` when needed

### Common Use Cases

```bash
# Daily workflow: Check for similar issues before filing
python cli.py find https://github.com/microsoft/vscode/issues/new-issue-url

# Repository maintenance: Find all duplicates
python cli.py find https://github.com/myorg/myrepo/issues/123 --min-similarity 0.8

# Issue triage: Explore related issues
python cli.py find https://github.com/myorg/myrepo/issues/123 --top-k 20 --min-similarity 0.3

# Repository analysis: Find discussion candidates
python cli.py suggest-discussions myorg/myrepo --min-score 0.6
```

## Error Handling

### Common Errors

```bash
# Invalid repository format
Error: Repository must be in format 'owner/repo'

# Invalid issue URL
Error: Invalid issue/PR URL. Expected format: https://github.com/owner/repo/issues/123

# Missing environment variables
Error: CHROMA_API_KEY environment variable is required

# Repository not found
Error: Repository microsoft/nonexistent not found

# Rate limit exceeded
Error: GitHub API rate limit exceeded. Consider setting GITHUB_TOKEN environment variable
```

### Troubleshooting

1. **Check Environment Variables**: Ensure `CHROMA_API_KEY` and `CHROMA_TENANT` are set
2. **Verify Repository**: Make sure the repository exists and is public
3. **Check GitHub Token**: Set `GITHUB_TOKEN` for higher rate limits
4. **Network Issues**: Ensure internet connectivity to GitHub and Chroma Cloud