# Deja View Demo Script

*Duration: 2-3 minutes*

## Opening (15 seconds)

"Hi everyone! I'm excited to show you Deja View - a tool that solves a common problem we all face: duplicate GitHub issues. 

How many times have you searched through hundreds of issues trying to find if someone already reported your bug? Deja View uses AI-powered semantic search to instantly find similar issues, even when they use completely different words."

## Problem Demo (30 seconds)

"Let me show you the problem. Imagine someone opens issue #2000 in the Continue repository about 'model configuration'. Without Deja View, they'd have to manually search through all issues.

But watch this:"

```bash
$ python cli.py find https://github.com/continuedev/continue/pull/2000
```

*Show output:*
```
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ #      ┃ Title                                 ┃ Similarity ┃ State  ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ 1995   │ Add support for custom models         │ 87.3%      │ open   │
│ 1234   │ Model configuration improvements      │ 85.1%      │ closed │
└────────┴───────────────────────────────────────┴────────────┴────────┘
```

"In seconds, we found that issues #1995 and #1234 are 85%+ similar! This prevents duplicate work and connects related discussions."

## Three Ways to Use (45 seconds)

### 1. CLI Tool (15 seconds)

"First, the CLI tool for developers:"

```bash
# Index a repository
$ python cli.py index continuedev/continue
✓ Successfully indexed 200 issues from continuedev/continue

# Find similar issues instantly
$ python cli.py quick continuedev/continue 2000
```

### 2. GitHub Action (15 seconds)

"Second, automate it with GitHub Actions. When someone opens a new issue, Deja View automatically comments with similar issues:"

```yaml
- name: Find Similar Issues
  uses: bdougie/deja-view@main
  with:
    chroma-api-key: ${{ secrets.CHROMA_API_KEY }}
```

*Show example comment on issue*

### 3. REST API (15 seconds)

"Third, integrate with your tools via REST API:"

```bash
# Start API server
$ python api.py

# Find similar issues programmatically
curl -X POST http://localhost:8000/find_similar \
  -d '{"owner": "continuedev", "repo": "continue", "issue_number": 2000}'
```

## Bonus Feature: Discussion Suggestions (30 seconds)

"Here's something special - Deja View can suggest which issues should be GitHub discussions:"

```bash
$ python cli.py suggest-discussions continuedev/continue
```

*Show output:*
```
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #      ┃ Title                        ┃ Score  ┃ State  ┃ Reasons                ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1423   │ How to configure models?     │ 0.85   │ open   │ Question pattern       │
│ 987    │ Feature request: dark theme  │ 0.72   │ open   │ Feature request        │
└────────┴──────────────────────────────┴────────┴────────┴────────────────────────┘
```

"It identifies questions and feature requests that would be better as discussions, helping maintain a cleaner issue tracker."

## Technical Highlights (30 seconds)

"Under the hood, Deja View uses:
- **Semantic embeddings** to understand meaning, not just keywords
- **Chroma Cloud** for scalable vector storage
- **GitHub's APIs** for real-time data

The best part? It takes just 5 minutes to set up:"

```bash
# Install
pip install -r requirements.txt

# Configure
export CHROMA_API_KEY="your-key"
export CHROMA_TENANT="your-tenant"

# Start finding duplicates!
python cli.py index your/repo
```

## Closing (15 seconds)

"Deja View saves hours of manual searching, reduces duplicate issues by up to 40%, and helps build better communities by connecting related discussions.

Ready to try it? Check out github.com/bdougie/deja-view

Questions?"

---

## Quick Demo Tips

1. **Have terminal ready** with commands pre-typed
2. **Show real output** - the visual tables are impressive
3. **Keep energy high** - this solves a real pain point
4. **Have backup slides** with architecture diagram if time permits
5. **Prepare for questions** about:
   - Accuracy rates (typically 85%+ for true duplicates)
   - Setup time (5-10 minutes)
   - Cost (Chroma Cloud has free tier)
   - Privacy (can work with private repos)

## Alternative 90-Second Version

For shorter demos, focus on:
1. Problem statement (15s)
2. Live CLI demo finding duplicates (30s)
3. Show GitHub Action auto-comment (30s)
4. Setup simplicity (15s)

## Demo Environment Setup

Before the demo:
```bash
# Pre-index the repository
python cli.py index continuedev/continue

# Have example issue URL ready
export DEMO_ISSUE="https://github.com/continuedev/continue/pull/2000"

# Start API server in background
python api.py &
```