# Documentation Structure

This document describes the organization of documentation in the Deja-View project.

## Directory Structure

```
.
├── README.md                    # Main project README (kept uppercase)
├── docs/
│   ├── README.md               # Documentation index
│   ├── api-reference.md        # REST API documentation
│   ├── api-user-comments.md    # User comments API endpoints
│   ├── architecture.md         # Technical architecture details
│   ├── architecture-overview.md # High-level system design
│   ├── cli-guide.md            # Quick CLI reference
│   ├── cli-usage.md            # Comprehensive CLI documentation
│   ├── test-final-report.md   # Test results and coverage
│   ├── user-comments.md       # User comments feature guide
│   └── setup/                  # Setup and integration guides
│       ├── authentication.md   # GitHub CLI authentication
│       ├── github-action.md    # GitHub Action setup
│       ├── github-action-guide.md # Extended Action guide
│       ├── mcp-guide.md        # MCP/Continue integration
│       ├── mcp-readme.md       # MCP quick reference
│       └── setup-guide.md      # General setup instructions
└── examples/
    ├── demo.md                 # Demo walkthrough
    └── mcp_demo.py            # MCP demo script
```

## Naming Convention

- All markdown files use **lowercase** with hyphens (e.g., `api-reference.md`)
- Exception: `README.md` files remain uppercase per convention
- Python files use underscores (e.g., `mcp_demo.py`)

## Documentation Categories

### 1. Root Documentation
- `README.md` - Main project overview and quick start

### 2. Core Documentation (`docs/`)
- API documentation (`api-*.md`)
- Architecture documentation (`architecture*.md`)
- CLI documentation (`cli-*.md`)
- Feature documentation (`user-comments.md`)
- Test reports (`test-*.md`)

### 3. Setup Documentation (`docs/setup/`)
- Installation and configuration guides
- Integration guides (MCP, GitHub Actions)
- Authentication setup

### 4. Examples (`examples/`)
- Demo scripts and walkthroughs
- Sample code and usage examples

## Link Structure

Internal links follow these patterns:

- From `docs/` to `docs/setup/`: `[Link](setup/file.md)`
- From `docs/setup/` to `docs/`: `[Link](../file.md)`
- From root to docs: `[Link](docs/file.md)`
- From root to setup: `[Link](docs/setup/file.md)`

## Migration Notes

The following files were renamed and moved:

| Old Location | New Location |
|--------------|--------------|
| `ARCHITECTURE.md` | `docs/architecture-overview.md` |
| `USER_COMMENTS.md` | `docs/user-comments.md` |
| `README_MCP.md` | `docs/setup/mcp-readme.md` |
| `AUTHENTICATION.md` | `docs/setup/authentication.md` |
| `MCP_CONTINUE_SETUP.md` | `docs/setup/mcp-guide.md` |
| `test-final-report.md` | `docs/test-final-report.md` |

All internal links have been updated to reflect the new structure.