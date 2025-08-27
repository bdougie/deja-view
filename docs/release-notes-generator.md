# Release Notes Generator Documentation

## Overview

The Release Notes Generator is a tool that automatically creates formatted release notes from GitHub Pull Requests (PRs) with tier labels. It's designed to streamline the release documentation process for [changelog.continue.dev](https://changelog.continue.dev/) and other changelog sites.

## Key Features

- 🔍 **Automatic PR Fetching**: Retrieves merged PRs since a specified date
- 🏷️ **Tier-Based Categorization**: Organizes PRs by tier labels (tier 1, 2, 3)
- 📅 **Smart Date Detection**: Can auto-detect the last release date
- 📝 **Markdown Formatting**: Generates changelog-ready markdown
- 👥 **Contributor Attribution**: Includes PR authors and contributors section
- 🔗 **Direct PR Links**: Each entry links back to the original PR

## Installation

### Prerequisites

- Python 3.8+
- GitHub Personal Access Token with `repo` read permissions
- Dependencies from `requirements.txt`

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure GitHub Token:**
   
   Set as environment variable:
   ```bash
   export GITHUB_TOKEN=your-github-personal-access-token
   ```
   
   Or add to `.env` file:
   ```env
   GITHUB_TOKEN=your-github-personal-access-token
   ```

## Usage Methods

### Method 1: CLI Command

The most straightforward way using the integrated CLI:

```bash
# Basic usage - fetch PRs since a specific date
python cli.py release-notes owner/repo --since 2024-01-01

# With date range
python cli.py release-notes owner/repo --since 2024-01-01 --until 2024-02-01

# With version tag
python cli.py release-notes owner/repo --since 2024-01-01 --version v1.2.0

# Custom output file
python cli.py release-notes owner/repo --since 2024-01-01 --output changelog.md
```

### Method 2: Standalone Script with Auto-Detection

The advanced script that can detect the last release automatically:

```bash
# Auto-detect last release date from GitHub releases/tags
python generate_release_notes.py owner/repo

# Manually specify date
python generate_release_notes.py owner/repo 2024-01-01

# With version string
python generate_release_notes.py owner/repo 2024-01-01 v1.2.0
```

### Method 3: Python API

Use directly in Python scripts:

```python
from datetime import datetime
from release_notes import ReleaseNotesGenerator

# Initialize the generator
generator = ReleaseNotesGenerator()

# Generate release notes
release_notes = generator.generate_release_notes(
    repo_name="continuedev/continue",
    since_date=datetime(2024, 1, 1),
    until_date=datetime(2024, 2, 1),  # Optional
    version="v1.2.0",                  # Optional
    output_file="release-notes.md"     # Optional
)

print(release_notes)
```

## Tier Label System

The generator categorizes PRs based on tier labels:

| Tier | Label Patterns | Category | Icon |
|------|---------------|----------|------|
| Tier 1 | `tier 1`, `tier-1`, `tier1` | Major Features | 🚀 |
| Tier 2 | `tier 2`, `tier-2`, `tier2` | Improvements | ✨ |
| Tier 3 | `tier 3`, `tier-3`, `tier3` | Bug Fixes | 🐛 |
| None | No tier label | Other Changes | 📝 |

## Output Format

The generated markdown follows this structure:

```markdown
# Release [Version]

_Released on [Date]_

## 🚀 Major Features
- **Feature title** ([#PR](link)) by @author

## ✨ Improvements
- Improvement title ([#PR](link)) by @author

## 🐛 Bug Fixes
- Bug fix title ([#PR](link)) by @author

## 📝 Other Changes
- Other change ([#PR](link)) by @author

## 👥 Contributors
Thanks to all contributors: @author1, @author2, ...
```

## Integration with changelog.continue.dev

### Step-by-Step Process

1. **Generate Release Notes:**
   ```bash
   python cli.py release-notes continuedev/continue --since 2024-06-01
   ```

2. **Review Generated File:**
   - Open `release-notes.md`
   - Add any manual highlights or breaking changes
   - Adjust formatting if needed

3. **Copy to Changelog Repository:**
   - Copy the content to your changelog repository
   - Place in appropriate version directory

4. **Publish:**
   - Commit and push changes
   - The changelog site will automatically update

### Automation with GitHub Actions

Create `.github/workflows/release-notes.yml`:

```yaml
name: Generate Release Notes

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      since_date:
        description: 'Start date for PRs (YYYY-MM-DD)'
        required: false

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Generate Release Notes
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          if [ -n "${{ github.event.inputs.since_date }}" ]; then
            python cli.py release-notes ${{ github.repository }} \
              --since ${{ github.event.inputs.since_date }} \
              --version ${{ github.ref_name }}
          else
            python generate_release_notes.py ${{ github.repository }}
          fi
      
      - name: Upload Release Notes
        uses: actions/upload-artifact@v3
        with:
          name: release-notes
          path: release-notes*.md
```

## Customization

### Custom Tier Labels

Modify tier labels in `release_notes.py`:

```python
self.tier_labels = {
    1: ["breaking", "major", "tier 1"],
    2: ["feature", "enhancement", "tier 2"],  
    3: ["bugfix", "fix", "tier 3"]
}
```

### Custom Categories

Add new categories by modifying the `format_for_changelog` method:

```python
# Add a new category for documentation
if tiered_prs.get('docs'):
    lines.append("## 📚 Documentation\n")
    for pr in tiered_prs['docs']:
        lines.append(f"- {pr['title']} ([#{pr['number']}]({pr['url']})) by @{pr['author']}")
```

### Output Formats

Extend the generator for different formats:

```python
# JSON output
def format_as_json(self, tiered_prs):
    return json.dumps({
        "version": self.version,
        "date": datetime.now().isoformat(),
        "tiers": tiered_prs
    }, indent=2)

# HTML output
def format_as_html(self, tiered_prs):
    # Generate HTML changelog
    pass
```

## Troubleshooting

### Common Issues

#### No PRs Found
- **Cause**: No merged PRs in date range or wrong label format
- **Solution**: 
  - Verify PRs exist: `gh pr list --state merged --limit 10`
  - Check label names: `gh label list | grep tier`
  - Adjust date range to include more PRs

#### Authentication Error
- **Cause**: Missing or invalid GitHub token
- **Solution**:
  ```bash
  # Test token
  curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
  
  # Set token
  export GITHUB_TOKEN=ghp_your_token_here
  ```

#### Rate Limiting
- **Cause**: Too many API requests
- **Solution**:
  - Use date ranges to limit results
  - Implement caching for repeated runs
  - Use GitHub App for higher rate limits

#### Missing Tier Labels
- **Cause**: PRs not labeled with tier system
- **Solution**:
  ```bash
  # Add labels to repository
  gh label create "tier 1" --description "Major features" --color "FF0000"
  gh label create "tier 2" --description "Improvements" --color "FFA500"
  gh label create "tier 3" --description "Bug fixes" --color "00FF00"
  ```

### Debug Mode

Enable verbose output for debugging:

```python
# In release_notes.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints
console.print(f"[dim]Debug: Fetching page {page}[/dim]")
console.print(f"[dim]Debug: Found {len(batch)} PRs[/dim]")
```

## Best Practices

1. **Label Consistently**: Apply tier labels during PR review
2. **Use Semantic PR Titles**: Make titles descriptive for better release notes
3. **Regular Generation**: Generate notes frequently (weekly/bi-weekly)
4. **Review Before Publishing**: Always review auto-generated notes
5. **Version Tagging**: Use semantic versioning for releases

## API Reference

### ReleaseNotesGenerator Class

```python
class ReleaseNotesGenerator:
    def __init__(self, github_token: Optional[str] = None)
    
    def fetch_merged_prs_since(
        repo_name: str,
        since_date: datetime,
        until_date: Optional[datetime] = None
    ) -> Dict[int, List[Dict]]
    
    def format_for_changelog(
        tiered_prs: Dict[int, List[Dict]],
        version: Optional[str] = None,
        repo_name: Optional[str] = None
    ) -> str
    
    def generate_release_notes(
        repo_name: str,
        since_date: datetime,
        until_date: Optional[datetime] = None,
        version: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> str
```

### Helper Functions

```python
def parse_date(date_str: str) -> datetime
    """Parse date string to datetime object"""

def get_last_release_date(repo_name: str, github_token: str) -> datetime
    """Auto-detect last release date from GitHub"""
```

## Examples

### Real-World Usage

Generate release notes for Continue.dev:

```bash
# Last 30 days
python cli.py release-notes continuedev/continue --since 2024-06-01

# Between releases
python cli.py release-notes continuedev/continue \
  --since 2024-05-15 \
  --until 2024-06-15 \
  --version v0.9.0

# Auto-detect and generate
python generate_release_notes.py continuedev/continue
```

### Sample Output

```markdown
# Release v0.9.0

_Released on June 15, 2024_

## 🚀 Major Features

- **feat: Add MCP support** ([#1234](https://github.com/continuedev/continue/pull/1234)) by @user1
- **feat: Implement code indexing** ([#1235](https://github.com/continuedev/continue/pull/1235)) by @user2

## ✨ Improvements

- feat: Improve search performance ([#1240](https://github.com/continuedev/continue/pull/1240)) by @user3
- feat: Add keyboard shortcuts ([#1241](https://github.com/continuedev/continue/pull/1241)) by @user4

## 🐛 Bug Fixes

- fix: Resolve memory leak ([#1250](https://github.com/continuedev/continue/pull/1250)) by @user5
- fix: Fix syntax highlighting ([#1251](https://github.com/continuedev/continue/pull/1251)) by @user6

## 👥 Contributors

Thanks to all contributors: @user1, @user2, @user3, @user4, @user5, @user6
```

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review existing [GitHub issues](https://github.com/your-repo/issues)
3. Create a new issue with:
   - Error message
   - Command used
   - GitHub repository
   - Date range

## License

This tool is part of the deja-view project and follows the same license terms.