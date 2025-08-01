# Setup Guide

## Prerequisites

- Python 3.9 or higher
- Git
- GitHub account (for accessing repositories)
- Chroma Cloud account

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/bdougie/deja-view.git
cd deja-view
```

### 2. Install Dependencies

#### Using pip

```bash
pip install -r requirements.txt
```

#### Using uv (recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt
```

#### Using Poetry

```bash
poetry install
```

### 3. Get Chroma Cloud Credentials

1. Sign up for Chroma Cloud at https://cloud.chroma.com
2. Create a new project
3. Copy your API key and tenant ID from the dashboard

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required
CHROMA_API_KEY=your-chroma-api-key
CHROMA_TENANT=your-chroma-tenant-id

# Optional
CHROMA_DATABASE=default_database
GITHUB_TOKEN=your-github-token
```

Or export them directly:

```bash
export CHROMA_API_KEY="your-chroma-api-key"
export CHROMA_TENANT="your-chroma-tenant-id"
export CHROMA_DATABASE="default_database"  # Optional
export GITHUB_TOKEN="your-github-token"     # Optional, for higher rate limits
```

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CHROMA_API_KEY` | Yes | - | Your Chroma Cloud API key |
| `CHROMA_TENANT` | Yes | - | Your Chroma Cloud tenant ID |
| `CHROMA_DATABASE` | No | `default_database` | Database name in Chroma |
| `GITHUB_TOKEN` | No | - | GitHub personal access token for higher rate limits |

### GitHub Token Setup

While optional, a GitHub token is recommended for:
- Higher API rate limits (5000/hour vs 60/hour)
- Access to private repositories
- Faster indexing of large repositories

To create a GitHub token:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories only)
4. Generate and copy the token

## Verify Installation

### CLI Verification

```bash
# Check CLI is working
python cli.py --help

# Test with a small repository
python cli.py index octocat/Hello-World
```

### API Verification

```bash
# Start the API server
python api.py

# In another terminal, check health
curl http://localhost:8000/health
```

### GitHub Action Verification

```bash
# Build the Docker image
docker build -t deja-view-action .

# Test locally (requires Docker)
docker run -e CHROMA_API_KEY=$CHROMA_API_KEY \
           -e CHROMA_TENANT=$CHROMA_TENANT \
           deja-view-action
```

## Common Setup Issues

### 1. Module Import Errors

**Problem**: `ModuleNotFoundError: No module named 'chromadb'`

**Solution**: Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### 2. Chroma Authentication Failed

**Problem**: `Authentication failed: Invalid API key`

**Solution**: 
- Verify your API key is correct
- Check there are no extra spaces or quotes
- Ensure the tenant ID matches your API key

### 3. GitHub Rate Limiting

**Problem**: `GitHub API rate limit exceeded`

**Solution**:
- Add a GitHub token to increase limits
- Wait for rate limit reset (check headers)
- Use `--max-issues` flag to limit requests

### 4. Connection Errors

**Problem**: `Failed to connect to Chroma Cloud`

**Solution**:
- Check internet connection
- Verify Chroma Cloud service status
- Check firewall/proxy settings

## Development Setup

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest test_cli.py
```

### Linting and Formatting

```bash
# Install dev dependencies
pip install black flake8 mypy

# Format code
black .

# Check linting
flake8 .

# Type checking
mypy .
```

### Local Development

For development, you might want to:

1. Use a separate Chroma database:
   ```bash
   export CHROMA_DATABASE=dev_database
   ```

2. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. Use a test GitHub repository:
   ```bash
   python cli.py index octocat/Hello-World
   ```

## Docker Setup

### Building the Image

```bash
# For general use
docker build -t deja-view .

# For GitHub Action
docker build -f Dockerfile -t deja-view-action .
```

### Running with Docker

```bash
# CLI usage
docker run -it \
  -e CHROMA_API_KEY=$CHROMA_API_KEY \
  -e CHROMA_TENANT=$CHROMA_TENANT \
  deja-view python cli.py index microsoft/vscode

# API server
docker run -p 8000:8000 \
  -e CHROMA_API_KEY=$CHROMA_API_KEY \
  -e CHROMA_TENANT=$CHROMA_TENANT \
  deja-view python api.py
```

## Production Deployment

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CHROMA_API_KEY=${CHROMA_API_KEY}
      - CHROMA_TENANT=${CHROMA_TENANT}
      - CHROMA_DATABASE=${CHROMA_DATABASE}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    command: python api.py
```

Run with:
```bash
docker-compose up
```

### Using Kubernetes

See the `/k8s` directory for example Kubernetes manifests.

### Environment-Specific Settings

For different environments, use separate `.env` files:

```bash
# Development
.env.development

# Staging  
.env.staging

# Production
.env.production
```

Load the appropriate file:
```bash
export $(cat .env.production | xargs)
```

## Next Steps

After setup is complete:

1. **Index your first repository**: See [CLI Usage Guide](cli-usage.md)
2. **Set up the GitHub Action**: See [GitHub Action Guide](github-action.md)
3. **Explore the API**: See [API Reference](api-reference.md)
4. **Understand the architecture**: See [Architecture Guide](architecture.md)