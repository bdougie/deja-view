# Deja View Documentation

Welcome to the Deja View documentation! Deja View is a powerful tool for finding similar GitHub issues using semantic search and AI-powered analysis.

## What is Deja View?

Deja View helps you:
- 🔍 Find similar issues across GitHub repositories
- 🤖 Automatically detect duplicate issues
- 💬 Suggest which issues should be discussions
- 🚀 Reduce duplicate issue reports

## Documentation Index

### Getting Started
- [Setup Guide](setup/setup-guide.md) - Install and configure Deja View
- [Architecture Overview](architecture.md) - Understand the system design

### Usage Guides
- [CLI Usage Guide](cli-usage.md) - Complete command-line interface guide with examples
- [GitHub Action Guide](setup/github-action.md) - Automated issue similarity detection setup
- [API Reference](api-reference.md) - REST API documentation with endpoints

### Additional Resources
- [CLI Guide](cli-guide.md) - Quick CLI reference
- [GitHub Action Guide (Extended)](setup/github-action-guide.md) - Detailed action configuration
- [Demo Walkthrough](../examples/demo.md) - 2-3 minute presentation script

## Key Features

### 1. Semantic Search
Uses vector embeddings to find conceptually similar issues, not just keyword matches.

### 2. Multiple Interfaces
- **CLI**: Interactive command-line tool
- **REST API**: Programmatic access
- **GitHub Action**: Automated workflow integration

### 3. Discussion Suggestions
AI-powered analysis to identify issues that should be GitHub discussions.

### 4. Cloud-Native
Built on Chroma Cloud for scalable vector storage without infrastructure management.

## Quick Start

### 1. Install and Configure

```bash
# Clone repository
git clone https://github.com/bdougie/deja-view.git
cd deja-view

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CHROMA_API_KEY="your-api-key"
export CHROMA_TENANT="your-tenant-id"
```

### 2. Index a Repository

```bash
python cli.py index facebook/react
```

### 3. Find Similar Issues

```bash
python cli.py find https://github.com/facebook/react/issues/1234
```

## Use Cases

### For Maintainers
- Automatically detect duplicate issues
- Suggest issues for discussion conversion
- Reduce time spent on triage

### For Contributors
- Find related issues before opening new ones
- Discover existing solutions
- Connect with similar discussions

### For Organizations
- Analyze issue patterns across repositories
- Improve documentation based on common questions
- Build knowledge bases from issues

## Architecture Overview

```
User Interfaces → Service Layer → Data Storage
      ↓                ↓              ↓
  CLI/API/Action → SimilarityService → Chroma Cloud
                         ↓
                   GitHub APIs
```

See [Architecture Guide](architecture.md) for details.

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/bdougie/deja-view/blob/main/CONTRIBUTING.md).

## Support

- **Issues**: [GitHub Issues](https://github.com/bdougie/deja-view/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bdougie/deja-view/discussions)

## License

Deja View is open source software licensed under the MIT License.