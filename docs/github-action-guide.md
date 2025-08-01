# GitHub Action Guide

The Deja View GitHub Action automatically comments on new issues with similar existing issues, helping reduce duplicates and connecting users to relevant discussions.

## Quick Setup

### 1. Add Secrets

Go to your repository's **Settings → Secrets and variables → Actions** and add:

```
CHROMA_API_KEY    # Your Chroma Cloud API key
CHROMA_TENANT     # Your Chroma Cloud tenant ID
```

### 2. Create Workflow File

Create `.github/workflows/similar-issues.yml`:

```yaml
name: Find Similar Issues
on:
  issues:
    types: [opened]

jobs:
  find-similar:
    runs-on: ubuntu-latest
    steps:
      - uses: yourusername/deja-view@v1
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 3. Test

Open a new issue in your repository and watch for the automated comment!

## Configuration Options

### Required Inputs

| Input | Description | Example |
|-------|-------------|---------|
| `chroma-api-key` | Your Chroma Cloud API key | `${{ secrets.CHROMA_API_KEY }}` |
| `chroma-tenant` | Your Chroma Cloud tenant ID | `${{ secrets.CHROMA_TENANT }}` |
| `github-token` | GitHub token for API access | `${{ secrets.GITHUB_TOKEN }}` |

### Optional Inputs

| Input | Default | Description | Example |
|-------|---------|-------------|---------|
| `chroma-database` | `default-database` | Chroma database name | `my-repo-issues` |
| `max-issues` | `200` | Max issues to index | `500` |
| `similarity-threshold` | `0.7` | Min similarity to show (0.0-1.0) | `0.8` |
| `max-similar-issues` | `5` | Max similar issues in comment | `3` |
| `index-on-run` | `true` | Re-index repo on each run | `false` |
| `include-discussions` | `false` | Include GitHub discussions | `true` |
| `comment-template` | See below | Custom comment template | See examples |

### Outputs

| Output | Description | Example Use |
|--------|-------------|-------------|
| `similar-issues-found` | Number of similar issues found | Conditional steps |
| `commented` | Whether a comment was posted | Notifications |

## Example Configurations

### Minimal Setup

```yaml
name: Similar Issues
on:
  issues:
    types: [opened]

jobs:
  similar-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: yourusername/deja-view@v1
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
```

### High-Volume Repository

For repositories with many issues, optimize performance:

```yaml
name: Similar Issues
on:
  issues:
    types: [opened]

jobs:
  similar-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: yourusername/deja-view@v1
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          max-issues: 1000              # Index more issues
          similarity-threshold: 0.8     # Only show very similar
          max-similar-issues: 3         # Keep comments concise
          index-on-run: false          # Skip re-indexing for performance
```

### Include Discussions

For repositories using GitHub Discussions:

```yaml
name: Similar Issues and Discussions
on:
  issues:
    types: [opened]

jobs:
  similar-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: yourusername/deja-view@v1
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          include-discussions: true
          comment-template: |
            ## 🔍 Similar Issues and Discussions
            
            I found these similar items that might help:
            
            {issues_table}
            
            💡 **Tip**: Consider searching [Discussions](https://github.com/${{ github.repository }}/discussions) for community solutions.
            
            <sub>Powered by [Deja View](https://github.com/yourusername/deja-view)</sub>
```

### Custom Comment Template

```yaml
name: Similar Issues
on:
  issues:
    types: [opened]

jobs:
  similar-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: yourusername/deja-view@v1
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          comment-template: |
            ## 👋 Welcome!
            
            Thanks for opening this issue! I found some similar issues that might be helpful:
            
            {issues_table}
            
            **Before proceeding**, please check if any of these resolve your issue. If not, feel free to provide more details!
            
            ---
            <sub>This is an automated message. [Learn more](https://github.com/yourusername/deja-view)</sub>
```

## Advanced Workflows

### Conditional Actions

Only run similarity search for certain labels or conditions:

```yaml
name: Conditional Similar Issues
on:
  issues:
    types: [opened, labeled]

jobs:
  similar-issues:
    runs-on: ubuntu-latest
    if: contains(github.event.issue.labels.*.name, 'bug') || contains(github.event.issue.labels.*.name, 'question')
    steps:
      - uses: yourusername/deja-view@v1
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Multiple Repository Support

Use different configurations for different repositories:

```yaml
name: Similar Issues
on:
  issues:
    types: [opened]

jobs:
  similar-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: yourusername/deja-view@v1
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          chroma-database: ${{ github.repository_owner }}-${{ github.event.repository.name }}
          max-issues: ${{ github.repository_owner == 'microsoft' && 2000 || 500 }}
```

### Notification Integration

Send notifications when similar issues are found:

```yaml
name: Similar Issues with Notifications
on:
  issues:
    types: [opened]

jobs:
  similar-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: yourusername/deja-view@v1
        id: similarity
        with:
          chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
          chroma-tenant: ${{ secrets.CHROMA_TENANT }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Notify maintainers
        if: steps.similarity.outputs.similar-issues-found > 3
        uses: 8398a7/action-slack@v3
        with:
          status: custom
          custom_payload: |
            {
              text: `Issue #${{ github.event.issue.number }} has ${{ steps.similarity.outputs.similar-issues-found }} similar issues - might be a duplicate!`,
              channel: '#issue-triage'
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Comment Examples

### Default Comment

```markdown
## 🔍 Similar Issues Found

I found these similar issues that might be related:

| # | Title | Similarity | State | Type |
|---|-------|------------|-------|------|
| #12340 | Similar bug with editor | 92% | closed | 🐛 Issue |
| #12350 | Related feature request | 87% | open | 🐛 Issue |
| #12301 | Same error message | 83% | closed | 🔀 PR |

> This comment was automatically generated by [Deja View](https://github.com/yourusername/deja-view) using semantic similarity search.
```

### Custom Comment with Branding

```markdown
## 👋 Welcome to MyProject!

Thanks for reporting this issue! Our bot found some similar issues:

| # | Title | Similarity | State | Type |
|---|-------|------------|-------|------|
| #123 | Similar issue | 85% | open | 🐛 Issue |

**Next Steps:**
1. Check if the similar issues solve your problem
2. If not, add more details to help us understand
3. Join our [Discord](https://discord.gg/myproject) for real-time help

---
<sub>Powered by [Deja View](https://github.com/yourusername/deja-view) | [Report Issues](https://github.com/myproject/issues/new)</sub>
```

## Troubleshooting

### Common Issues

#### No Comments Appearing

1. **Check Secrets**: Ensure `CHROMA_API_KEY` and `CHROMA_TENANT` are set correctly
2. **Verify Workflow**: Check the workflow file is in `.github/workflows/`
3. **Test Trigger**: Make sure you're opening new issues (not editing existing ones)
4. **Check Logs**: Look at the Action logs in the GitHub Actions tab

#### Rate Limits

```yaml
# Solution: Add GitHub token
github-token: ${{ secrets.GITHUB_TOKEN }}

# Or use a personal access token for higher limits
github-token: ${{ secrets.PAT_TOKEN }}
```

#### Too Many/Few Similar Issues

```yaml
# Adjust similarity threshold
similarity-threshold: 0.8    # Higher = fewer, more similar results
similarity-threshold: 0.5    # Lower = more, less similar results

# Adjust max results
max-similar-issues: 3        # Fewer results
max-similar-issues: 10       # More results
```

#### Performance Issues

```yaml
# Optimize for large repositories
max-issues: 500              # Index fewer issues
index-on-run: false         # Skip re-indexing
similarity-threshold: 0.75   # Higher threshold = faster
```

### Action Logs

Check the GitHub Actions logs for detailed information:

```
Repository: microsoft/vscode
Issue: #12345
Indexing: Skipped (index-on-run: false)
Similar issues found: 3
Comment posted: ✅
```

### Testing

Test your configuration with a test repository:

1. Create a test repository
2. Add some sample issues
3. Configure the action
4. Open a new issue and verify the comment appears

## Best Practices

### Repository Size Considerations

| Repository Size | Recommended Settings |
|----------------|---------------------|
| Small (<100 issues) | `max-issues: 100`, `index-on-run: true` |
| Medium (100-1000) | `max-issues: 500`, `index-on-run: false` |
| Large (1000+) | `max-issues: 1000`, `index-on-run: false`, `similarity-threshold: 0.8` |

### Comment Guidelines

1. **Keep it concise**: Use `max-similar-issues: 3-5`
2. **Be helpful**: Include links to relevant documentation
3. **Brand consistently**: Use custom templates for organization repos
4. **Provide context**: Explain what the bot does

### Maintenance

1. **Monitor performance**: Check action execution times
2. **Update thresholds**: Adjust based on user feedback
3. **Clean database**: Periodically clear old issues if needed
4. **Version updates**: Keep the action version updated

### Security

1. **Use repository secrets**: Never commit API keys
2. **Limit permissions**: Use minimal required GitHub token permissions
3. **Review access**: Regularly audit who has access to secrets