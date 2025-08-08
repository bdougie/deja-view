# Authentication Guide for Deja-View

## Overview

Deja-View requires GitHub CLI (`gh`) authentication to access GitHub data. This guide explains how to set up authentication for all components.

## Why Authentication is Required

- **GitHub API Access**: To fetch issues, comments, and repository data
- **Rate Limiting**: Authenticated requests have 5,000/hour limit vs 60/hour for unauthenticated
- **Private Repos**: Access to private repositories (if you have permissions)
- **User Data**: Fetch your own comments and activity

## Prerequisites

### 1. Install GitHub CLI

GitHub CLI must be installed before you can authenticate.

#### macOS
```bash
brew install gh
```

#### Ubuntu/Debian
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

#### Windows
```powershell
winget install --id GitHub.cli
# or
choco install gh
```

#### Other platforms
See: https://github.com/cli/cli#installation

### 2. Authenticate with GitHub

Run the authentication command:
```bash
gh auth login
```

You'll be prompted to:
1. Choose GitHub.com or GitHub Enterprise
2. Select authentication method (browser or token)
3. Complete the authentication flow

#### Recommended: Browser Authentication
```
? What account do you want to log into? GitHub.com
? What is your preferred protocol for Git operations? HTTPS
? Authenticate Git with your GitHub credentials? Yes
? How would you like to authenticate GitHub CLI? Login with a web browser
```

#### Alternative: Personal Access Token
1. Create a token at: https://github.com/settings/tokens
2. Required scopes: `repo`, `read:org`, `read:user`
3. Use token when prompted

### 3. Verify Authentication

Check that authentication succeeded:
```bash
gh auth status
```

Expected output:
```
✓ Logged in to github.com as YOUR_USERNAME
✓ Git operations for github.com configured to use https protocol
✓ Token: gho_****
```

## Component-Specific Setup

### CLI Authentication

The CLI automatically checks authentication when you run commands:

```bash
# Will check auth before executing
uv run python cli.py user-comments

# If not authenticated, you'll see:
❌ Error: Not authenticated with GitHub CLI

╔══════════════════════════════════════════════════════════════╗
║                 GitHub CLI Authentication Required           ║
╚══════════════════════════════════════════════════════════════╝

The deja-view CLI requires GitHub CLI (gh) to be installed and authenticated.

Follow these steps:
1. Install GitHub CLI...
2. Authenticate with GitHub: gh auth login
3. Verify authentication: gh auth status
```

### API Server Authentication

The API checks authentication on startup:

```bash
uv run python api.py

# Output:
============================================================
GitHub Issues Similarity API
============================================================

Checking GitHub CLI authentication...
✅ Authenticated as: YOUR_USERNAME
============================================================
```

If not authenticated, the API will still start but with warnings:
```
⚠️  WARNING: GitHub CLI is not authenticated!
Some endpoints will have limited functionality.
To authenticate, run: gh auth login
```

Check auth status via API:
```bash
curl http://localhost:8000/auth/status
```

Response:
```json
{
  "github_cli_authenticated": true,
  "github_username": "YOUR_USERNAME",
  "message": "✅ Authenticated as: YOUR_USERNAME",
  "auth_command": null
}
```

### MCP Server Authentication

The MCP server checks authentication when initialized:

```bash
uv run python mcp_server.py

# Output:
Checking GitHub CLI authentication...
✅ GitHub CLI authenticated as: YOUR_USERNAME
```

If not authenticated:
```
⚠️  WARNING: GitHub CLI is not authenticated!
Some tools will have limited functionality.
To authenticate, run: gh auth login
After authenticating, restart the MCP server.
```

In Continue, you can check auth status:
```
Use the check_github_auth tool to verify authentication
```

## Automated Setup

Use the setup script for guided authentication:

```bash
./setup_mcp.sh
```

This script will:
1. Check if `gh` is installed (with install instructions if not)
2. Check authentication status
3. Guide you through `gh auth login` if needed
4. Verify authentication succeeded
5. Display your authenticated username

## Troubleshooting

### "gh: command not found"
- GitHub CLI is not installed
- Solution: Install `gh` using instructions above

### "Not authenticated"
- You haven't run `gh auth login`
- Solution: Run `gh auth login` and follow prompts

### "Authentication failed"
- Token might be expired or revoked
- Solution: Run `gh auth logout` then `gh auth login`

### "Rate limit exceeded"
- You're hitting GitHub's API limits
- Solution: Ensure you're authenticated (5000/hour vs 60/hour)

### "Permission denied"
- Token lacks required scopes
- Solution: Create new token with `repo`, `read:org`, `read:user` scopes

## Environment Variables (Optional)

While `gh` authentication is preferred, you can also set:

```bash
export GITHUB_TOKEN=your-personal-access-token
```

This is used by the SimilarityService for API calls.

## Security Best Practices

1. **Use Browser Auth**: Safer than storing tokens
2. **Minimal Scopes**: Only grant necessary permissions
3. **Rotate Tokens**: Periodically refresh access tokens
4. **Don't Commit Tokens**: Never commit tokens to git
5. **Use `.env` Files**: Store tokens in `.env` (gitignored)

## Multiple GitHub Accounts

To switch between accounts:

```bash
# Logout current account
gh auth logout

# Login with different account
gh auth login

# Check current account
gh auth status
```

## GitHub Enterprise

For GitHub Enterprise Server:

```bash
gh auth login --hostname github.your-company.com
```

## CI/CD Authentication

For automated environments:

```bash
# Use environment variable
export GH_TOKEN=your-token
gh auth status

# Or login with token
echo $GITHUB_TOKEN | gh auth login --with-token
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `gh auth login` | Authenticate with GitHub |
| `gh auth status` | Check authentication status |
| `gh auth logout` | Logout from GitHub |
| `gh api user` | Test API access |
| `gh auth refresh` | Refresh authentication |

## Getting Help

- **GitHub CLI Docs**: https://cli.github.com/manual/
- **Authentication Guide**: https://cli.github.com/manual/gh_auth_login
- **Deja-View Issues**: https://github.com/bdougie/deja-view/issues

## Summary

1. **Install**: `brew install gh` (or platform equivalent)
2. **Authenticate**: `gh auth login`
3. **Verify**: `gh auth status`
4. **Use**: All deja-view tools now have GitHub access

Authentication is required once and persists across sessions. After authenticating, all CLI commands, API endpoints, and MCP tools will work seamlessly.