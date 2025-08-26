# Release Notes Generator

Generate release notes from GitHub PRs with tier labels for changelog.continue.dev.

## Features

- Fetches merged PRs since the last release date
- Categorizes PRs by tier labels (tier 1, tier 2, tier 3)
- Generates markdown formatted for changelog.continue.dev
- Auto-detects last release date from GitHub releases/tags
- Supports custom date ranges and version strings

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set GitHub Token:**
   ```bash
   export GITHUB_TOKEN=your-github-personal-access-token
   ```
   
   Or create a `.env` file:
   ```
   GITHUB_TOKEN=your-github-personal-access-token
   ```

## Usage

### Using the CLI Command

```bash
# Basic usage - specify repository and start date
python cli.py release-notes owner/repo --since 2024-01-01

# With end date and version
python cli.py release-notes owner/repo --since 2024-01-01 --until 2024-02-01 --version v1.2.0

# Custom output file
python cli.py release-notes owner/repo --since 2024-01-01 --output changelog.md
```

### Using the Standalone Script

The standalone script can auto-detect the last release date:

```bash
# Auto-detect last release date
python generate_release_notes.py owner/repo

# Specify date manually
python generate_release_notes.py owner/repo 2024-01-01

# With version
python generate_release_notes.py owner/repo 2024-01-01 v1.2.0
```

### Using as a Python Module

```python
from datetime import datetime
from release_notes import ReleaseNotesGenerator

# Initialize generator
generator = ReleaseNotesGenerator()

# Generate release notes
release_notes = generator.generate_release_notes(
    repo_name="owner/repo",
    since_date=datetime(2024, 1, 1),
    version="v1.2.0",
    output_file="release-notes.md"
)
```

## Tier Labels

The generator looks for these label patterns:

- **Tier 1** (Major Features): `tier 1`, `tier-1`, `tier1`
- **Tier 2** (Improvements): `tier 2`, `tier-2`, `tier2`  
- **Tier 3** (Bug Fixes): `tier 3`, `tier-3`, `tier3`

PRs without tier labels are listed under "Other Changes".

## Output Format

The generated markdown includes:

```markdown
# Release v1.2.0

_Released on January 15, 2024_

## 🚀 Major Features

- **Feature title** ([#123](link)) by @author

## ✨ Improvements

- Improvement title ([#456](link)) by @author

## 🐛 Bug Fixes

- Bug fix title ([#789](link)) by @author

## 📝 Other Changes

- Other change title ([#012](link)) by @author

## 👥 Contributors

Thanks to all contributors: @author1, @author2, @author3
```

## Integration with changelog.continue.dev

1. **Generate release notes:**
   ```bash
   python generate_release_notes.py continuedev/continue
   ```

2. **Review and edit** the generated markdown file

3. **Copy to your changelog repository**

4. **Commit and push** to update the live changelog site

## Testing

Run the test script to verify everything works:

```bash
python test_release_notes.py
```

This will generate a test release notes file for the last 30 days.

## Troubleshooting

### No PRs Found
- Check that the repository has merged PRs in the specified date range
- Verify tier labels are properly applied to PRs
- Ensure GitHub token has repository read access

### Authentication Error
- Verify GITHUB_TOKEN is set correctly
- Check token has necessary permissions (repo:read)

### Rate Limiting
- The script uses GitHub API which has rate limits
- For large repositories, consider using a date range to limit results

## Advanced Usage

### Custom Tier Labels

Modify the tier labels in `release_notes.py`:

```python
self.tier_labels = {
    1: ["breaking", "major", "tier 1"],
    2: ["feature", "enhancement", "tier 2"],
    3: ["bugfix", "fix", "tier 3"]
}
```

### Output Formats

The generator can be extended to support different formats:
- Markdown (default)
- JSON (for automation)
- HTML (for web display)

### CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Generate Release Notes
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    python generate_release_notes.py ${{ github.repository }} \
      --since ${{ github.event.before }} \
      --version ${{ github.ref_name }}
```