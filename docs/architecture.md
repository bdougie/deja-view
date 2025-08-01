# Deja View Architecture

## Overview

Deja View is a semantic search system for GitHub issues that helps users find similar issues and suggests when issues should be converted to discussions. The system uses vector embeddings and AI-powered analysis to provide intelligent recommendations.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                           │
├─────────────────┬──────────────────┬────────────────────────────┤
│    CLI Tool     │   REST API       │    GitHub Action           │
│   (cli.py)      │   (api.py)       │    (action.py)             │
└────────┬────────┴────────┬─────────┴──────────┬─────────────────┘
         │                 │                     │
         └─────────────────┴─────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │      Similarity Service Layer       │
         │   (github_similarity_service.py)    │
         └────────────────┬────────────────────┘
                          │
         ┌────────────────┴────────────────────┐
         │                                      │
         ▼                                      ▼
┌─────────────────────┐          ┌──────────────────────────┐
│   GitHub APIs       │          │   Chroma Cloud DB        │
│ • REST (Issues/PRs) │          │ • Vector Storage         │
│ • GraphQL (Discuss) │          │ • Semantic Search        │
└─────────────────────┘          └──────────────────────────┘
```

## Core Components

### 1. Interface Layer

**CLI Tool** (`cli.py`)
- Interactive command-line interface using Click framework
- Rich terminal output with progress bars and formatted tables
- Commands: index, find, suggest-discussions, quick, stats, clear

**REST API** (`api.py`)
- FastAPI-based service with automatic OpenAPI documentation
- RESTful endpoints for all core functionality
- Suitable for integration with other services

**GitHub Action** (`action.py`)
- Automated issue similarity detection on new issues
- Comments with similar issues when threshold met
- Docker-based for easy deployment

### 2. Service Layer

**SimilarityService** (`github_similarity_service.py`)
- Core business logic implementation
- Handles GitHub API interactions (REST and GraphQL)
- Manages vector database operations
- Implements similarity algorithms and discussion suggestions

### 3. Data Storage

**Chroma Cloud**
- Managed vector database service
- Stores issue/discussion embeddings
- Enables semantic similarity search
- Scales automatically with usage

### 4. External Integrations

**GitHub APIs**
- REST API for issues and pull requests
- GraphQL API for discussions
- Rate limit handling and authentication

## Key Design Decisions

### 1. Multi-Interface Architecture
- **Rationale**: Different users have different needs
- **Benefits**: CLI for developers, API for integrations, Action for automation
- **Trade-off**: More code to maintain, but shared service layer minimizes duplication

### 2. Cloud Vector Database
- **Rationale**: Avoid managing infrastructure for embeddings
- **Benefits**: Scalability, reliability, no maintenance
- **Trade-off**: Requires API key management and internet connectivity

### 3. Service Layer Pattern
- **Rationale**: Separate business logic from interfaces
- **Benefits**: Easy to add new interfaces, consistent behavior
- **Trade-off**: Additional abstraction layer

### 4. Semantic Search Approach
- **Rationale**: Traditional keyword search misses related issues
- **Benefits**: Finds conceptually similar issues even with different wording
- **Trade-off**: Requires embedding generation and vector storage

## Data Flow

### Indexing Flow
1. User initiates indexing via any interface
2. Service fetches issues/discussions from GitHub
3. Text content is extracted and truncated if needed
4. Embeddings are generated using Chroma's default model
5. Data is stored in Chroma Cloud with metadata

### Search Flow
1. User provides an issue URL or number
2. Service fetches issue content from GitHub
3. Query embedding is generated
4. Semantic search finds similar items in Chroma
5. Results are filtered by similarity threshold
6. Formatted results returned to user

### Discussion Suggestion Flow
1. Repository issues are analyzed
2. Pattern matching identifies question-like issues
3. Scoring algorithm ranks candidates
4. Suggestions returned with reasoning

## Security Considerations

- GitHub tokens stored as environment variables
- Chroma API keys protected similarly
- No sensitive data persisted locally
- Rate limiting respected for GitHub APIs

## Scalability

- **Chroma Cloud**: Handles vector storage scaling
- **Stateless Design**: All interfaces can be scaled horizontally
- **Caching**: Not implemented but could be added at service layer
- **Rate Limits**: GitHub API limits are the primary constraint

## Future Architecture Considerations

1. **Caching Layer**: Add Redis for GitHub API response caching
2. **Webhook Support**: Real-time issue processing via webhooks
3. **Custom Embeddings**: Support for different embedding models
4. **Multi-Tenant**: Support for multiple organizations/databases
5. **Analytics**: Track usage patterns and search effectiveness