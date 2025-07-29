# Deja View Architecture

## Overview

Deja View is a GitHub Issues Similarity Service that provides semantic search capabilities for finding similar issues and pull requests. The system is designed with a dual-interface approach: a RESTful API for programmatic access and a CLI tool for interactive use.

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   CLI Tool      │     │   REST API      │
│  (cli.py)       │     │   (api.py)      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼────────────┐
         │  Similarity Service    │
         │ (github_similarity_    │
         │    service.py)         │
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │    Chroma Cloud        │
         │  (Vector Database)     │
         └────────────────────────┘
```

## Design Decisions

### 1. Dual Interface Design

**Decision**: Provide both CLI and API interfaces
**Rationale**:
- **CLI**: Optimized for human interaction with rich formatting, progress indicators, and user-friendly commands
- **API**: Enables integration with other services, automation, and programmatic access
- Both interfaces share the same core service, ensuring consistency

### 2. Service Layer Architecture

**Decision**: Centralize business logic in `SimilarityService` class
**Rationale**:
- **Single Responsibility**: The service handles all GitHub and Chroma interactions
- **Reusability**: Both CLI and API use the same service methods
- **Testability**: Business logic is isolated from interface concerns
- **Maintainability**: Changes to core functionality only need to be made in one place

### 3. Vector Database Choice

**Decision**: Use Chroma Cloud for vector storage
**Rationale**:
- **Managed Service**: No infrastructure to maintain
- **Semantic Search**: Built-in embedding generation and similarity search
- **Scalability**: Cloud-based solution scales automatically
- **API Access**: Simple integration with Python SDK

### 4. Document Truncation Strategy

**Decision**: Truncate issue bodies to 10KB
**Rationale**:
- **Chroma Limits**: Cloud tier has 16KB document size limit
- **Relevance**: Most important information is typically in the first part of long issues
- **Performance**: Smaller documents = faster embeddings and searches
- **Cost**: Reduces token usage for embedding generation

### 5. CLI Design Choices

**Rich Terminal UI**:
- Uses `rich` library for beautiful formatting
- Progress indicators for long-running operations
- Color-coded output for better readability
- Tables for structured data display

**Command Structure**:
```
cli.py index <owner/repo>          # Index repository
cli.py find <issue_url>            # Find similar issues
cli.py quick <owner/repo> <num>    # Combined operation
cli.py stats                       # View statistics
cli.py clear                       # Clear database
```

**Design Principles**:
- **Intuitive**: Commands mirror user intent
- **Flexible**: Accept various input formats (URLs, owner/repo)
- **Informative**: Clear feedback and error messages
- **Efficient**: Batch operations where possible

### 6. API Design Choices

**RESTful Endpoints**:
```
POST /index         # Index repository
POST /find_similar  # Find similar issues
GET  /stats        # Get statistics
DELETE /clear      # Clear data
GET  /health       # Health check
```

**Design Principles**:
- **Resource-Oriented**: Each endpoint represents a clear action
- **Stateless**: No session management required
- **Self-Documenting**: FastAPI generates OpenAPI specs
- **Validated**: Pydantic models ensure data integrity

### 7. Data Models

**Issue Model**:
```python
class Issue:
    number: int
    title: str
    body: Optional[str]
    state: str
    created_at: str
    updated_at: str
    url: str
    labels: List[str]
    is_pull_request: bool
```

**Design Considerations**:
- **Unified Model**: Same structure for issues and PRs
- **Essential Fields**: Only store what's needed for similarity
- **Type Safety**: Pydantic ensures data validation

### 8. Error Handling Strategy

**CLI Error Handling**:
- User-friendly error messages
- Exit codes for scripting
- Suggestions for common issues

**API Error Handling**:
- HTTP status codes
- Detailed error responses
- Consistent error format

### 9. Configuration Management

**Environment Variables**:
```
CHROMA_API_KEY      # Required
CHROMA_TENANT       # Required
CHROMA_DATABASE     # Optional (default: "default-database")
GITHUB_TOKEN        # Optional (higher rate limits)
```

**Design Rationale**:
- **Security**: Sensitive data not in code
- **Flexibility**: Easy to change per environment
- **Standards**: Follows 12-factor app principles

### 10. Performance Optimizations

**Batch Processing**:
- Index multiple issues in single Chroma operation
- Fetch issues in pages of 100

**Caching Strategy**:
- Chroma handles embedding caching
- No additional caching layer needed initially

**Rate Limiting**:
- Respect GitHub API limits
- Optional auth token for higher limits

## Deployment Architecture

### Development
```bash
# CLI
python cli.py

# API
python api.py
```

## Conclusion

The architecture prioritizes simplicity, extensibility, and user experience. By separating concerns between the service layer and interfaces, the system remains maintainable while providing flexibility for future enhancements.