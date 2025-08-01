# GitHub Action Guide

## Overview

The Deja View GitHub Action automatically finds and comments on new issues with links to similar existing issues, helping reduce duplicates and connect related discussions.

## Quick Start

### Basic Setup

Create `.github/workflows/deja-view.yml`:

```yaml
name: Find Similar Issues
on:
  issues:
    types: [opened]

jobs:
  find-similar:
    runs-on: ubuntu-latest
    steps:
      - name: Find Similar Issues
        uses: bdougie/deja-view-action@main
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Configuration

### Required Secrets

1. **CHROMA_API_KEY**: Your Chroma Cloud API key
   - Get from: https://cloud.chroma.com
   - Add to: Settings → Secrets → Actions

2. **CHROMA_TENANT**: Your Chroma Cloud tenant ID
   - Found in Chroma Cloud dashboard
   - Add to: Settings → Secrets → Actions

### Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `chroma-api-key` | Yes | - | Chroma Cloud API key |
| `chroma-tenant` | Yes | - | Chroma Cloud tenant ID |
| `chroma-database` | No | `default_database` | Database name |
| `github-token` | No | `${{ github.token }}` | GitHub token for API access |
| `similarity-threshold` | No | `0.7` | Minimum similarity score (0.0-1.0) |
| `max-results` | No | `5` | Maximum similar issues to show |
| `index-on-not-found` | No | `true` | Auto-index if repository not found |
| `comment-template` | No | See below | Custom comment template |

### Default Comment Template

```markdown
## 🔍 Similar Issues Found

I found some issues that might be related to this one:

{similar_issues}

*This comment was automatically generated by [Deja View](https://github.com/bdougie/deja-view-action) to help you find related issues.*
```

## Advanced Usage

### Custom Comment Template

```yaml
- name: Find Similar Issues
  uses: bdougie/deja-view-action@main
  with:
    chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
    chroma-tenant: ${{ secrets.CHROMA_TENANT }}
    comment-template: |
      ## Related Issues
      
      The following issues appear similar:
      
      {similar_issues}
      
      Please check if any of these address your concern.
```

### Adjust Similarity Threshold

```yaml
- name: Find Similar Issues
  uses: bdougie/deja-view-action@main
  with:
    chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
    chroma-tenant: ${{ secrets.CHROMA_TENANT }}
    similarity-threshold: 0.5  # More lenient matching
    max-results: 10           # Show more results
```

### Disable Auto-Indexing

```yaml
- name: Find Similar Issues
  uses: bdougie/deja-view-action@main
  with:
    chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
    chroma-tenant: ${{ secrets.CHROMA_TENANT }}
    index-on-not-found: false  # Don't index automatically
```

## Workflow Examples

### Combined with Labeling

```yaml
name: Issue Management
on:
  issues:
    types: [opened]

jobs:
  manage-issue:
    runs-on: ubuntu-latest
    steps:
      - name: Find Similar Issues
        uses: bdougie/deja-view-action@main
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
      
      - name: Add Labels
        uses: actions/labeler@v4
        with:
          repo-token: ${{ secrets.GITHUB_TOKEN }}
```

### Scheduled Repository Indexing

```yaml
name: Index Repository
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:     # Manual trigger

jobs:
  index:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install Dependencies
        run: pip install -r requirements.txt
      
      - name: Index Repository
        env:
          CHROMA_API_KEY: ${{ secrets.CHROMA_API_KEY }}
          CHROMA_TENANT: ${{ secrets.CHROMA_TENANT }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python cli.py index ${{ github.repository }}
```

### Pull Request Support

```yaml
name: Find Similar PRs
on:
  pull_request:
    types: [opened]

jobs:
  find-similar:
    runs-on: ubuntu-latest
    steps:
      - name: Find Similar Issues/PRs
        uses: bdougie/deja-view-action@main
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Outputs

The action provides these outputs:

| Output | Description |
|--------|-------------|
| `similar_issues_found` | Number of similar issues found |
| `comment_posted` | Whether a comment was posted |
| `similarity_scores` | JSON array of similarity scores |

### Using Outputs

```yaml
- name: Find Similar Issues
  id: similar
  uses: bdougie/deja-view-action@main
  with:
    chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
    chroma-tenant: ${{ secrets.CHROMA_TENANT }}

- name: Check Results
  if: steps.similar.outputs.similar_issues_found > 3
  run: |
    echo "Found many similar issues!"
    echo "Consider closing as duplicate"
```

## Best Practices

1. **Initial Setup**
   - Run manual indexing before enabling action
   - Test with low similarity threshold first

2. **Performance**
   - Index large repositories during off-hours
   - Use scheduled workflows for regular updates

3. **User Experience**
   - Keep comment templates concise
   - Link to similar closed issues too
   - Consider similarity threshold based on project size

4. **Security**
   - Always use secrets for API keys
   - Limit GitHub token permissions
   - Review action permissions

## Troubleshooting

### No Similar Issues Found

1. Check if repository is indexed:
   ```bash
   python cli.py stats
   ```

2. Lower similarity threshold:
   ```yaml
   similarity-threshold: 0.5
   ```

3. Enable auto-indexing:
   ```yaml
   index-on-not-found: true
   ```

### Authentication Errors

1. Verify secrets are set correctly
2. Check Chroma Cloud API key is valid
3. Ensure GitHub token has necessary permissions

### Rate Limiting

1. Use `GITHUB_TOKEN` for higher limits
2. Implement scheduled indexing
3. Consider caching strategies

## Integration Tips

- **Combine with Templates**: Use issue templates to improve similarity matching
- **Label Management**: Auto-label potential duplicates
- **Notifications**: Alert maintainers of high-similarity issues
- **Analytics**: Track duplicate reduction over time