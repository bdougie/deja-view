import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from github import Github, PullRequest
from dotenv import load_dotenv
import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

load_dotenv()

console = Console()


class ReleaseNotesGenerator:
    """Generate release notes from GitHub PRs with tier labels."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize with GitHub token."""
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.github = Github(self.github_token)
        self.tier_labels = {
            1: ["tier 1", "tier-1", "tier1"],
            2: ["tier 2", "tier-2", "tier2"],
            3: ["tier 3", "tier-3", "tier3"]
        }
    
    def fetch_merged_prs_since(
        self,
        repo_name: str,
        since_date: datetime,
        until_date: Optional[datetime] = None
    ) -> Dict[int, List[Dict]]:
        """
        Fetch merged PRs with tier labels since a given date.
        
        Args:
            repo_name: Repository in format "owner/repo"
            since_date: Start date for filtering PRs
            until_date: Optional end date for filtering PRs
            
        Returns:
            Dictionary with tier numbers as keys and lists of PR data as values
        """
        try:
            repo = self.github.get_repo(repo_name)
        except Exception as e:
            raise ValueError(f"Could not access repository {repo_name}: {e}")
        
        # Initialize result dictionary
        tiered_prs = {1: [], 2: [], 3: []}
        other_prs = []
        
        # Ensure dates are timezone-aware
        if since_date.tzinfo is None:
            since_date = since_date.replace(tzinfo=timezone.utc)
        if until_date and until_date.tzinfo is None:
            until_date = until_date.replace(tzinfo=timezone.utc)
        
        console.print(f"[cyan]Fetching merged PRs from {repo_name} since {since_date.date()}...[/cyan]")
        
        # Fetch merged PRs
        pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')
        
        pr_count = 0
        for pr in pulls:
            # Skip if not merged
            if not pr.merged:
                continue
                
            # Check date range
            if pr.merged_at < since_date:
                break  # Since we're sorting by updated desc, we can break here
            
            if until_date and pr.merged_at > until_date:
                continue
            
            pr_count += 1
            
            # Extract PR data
            pr_data = {
                'number': pr.number,
                'title': pr.title,
                'author': pr.user.login if pr.user else 'unknown',
                'merged_at': pr.merged_at,
                'url': pr.html_url,
                'labels': [label.name for label in pr.labels]
            }
            
            # Categorize by tier
            tier_found = False
            for tier, tier_labels in self.tier_labels.items():
                if any(label.lower() in [l.lower() for l in pr_data['labels']] for label in tier_labels):
                    tiered_prs[tier].append(pr_data)
                    tier_found = True
                    break
            
            if not tier_found:
                other_prs.append(pr_data)
        
        # Add other PRs as a separate category if they exist
        if other_prs:
            tiered_prs[0] = other_prs  # Use 0 for non-tiered PRs
        
        console.print(f"[green]Found {pr_count} merged PRs total[/green]")
        for tier in [1, 2, 3]:
            if tiered_prs[tier]:
                console.print(f"  Tier {tier}: {len(tiered_prs[tier])} PRs")
        if 0 in tiered_prs and tiered_prs[0]:
            console.print(f"  Other: {len(tiered_prs[0])} PRs")
        
        return tiered_prs
    
    def format_for_changelog(
        self,
        tiered_prs: Dict[int, List[Dict]],
        version: Optional[str] = None,
        repo_name: Optional[str] = None
    ) -> str:
        """
        Format PRs for changelog.continue.dev.
        
        Args:
            tiered_prs: Dictionary of PRs organized by tier
            version: Optional version string for the release
            repo_name: Optional repository name for PR links
            
        Returns:
            Formatted markdown string for the changelog
        """
        lines = []
        
        # Add header
        if version:
            lines.append(f"# Release {version}")
        else:
            lines.append(f"# Release Notes")
        
        lines.append(f"\n_Released on {datetime.now().strftime('%B %d, %Y')}_\n")
        
        # Format Tier 1 - Major Features
        if tiered_prs.get(1):
            lines.append("## 🚀 Major Features\n")
            for pr in tiered_prs[1]:
                lines.append(f"- **{pr['title']}** ([#{pr['number']}]({pr['url']})) by @{pr['author']}")
            lines.append("")
        
        # Format Tier 2 - Improvements
        if tiered_prs.get(2):
            lines.append("## ✨ Improvements\n")
            for pr in tiered_prs[2]:
                lines.append(f"- {pr['title']} ([#{pr['number']}]({pr['url']})) by @{pr['author']}")
            lines.append("")
        
        # Format Tier 3 - Bug Fixes
        if tiered_prs.get(3):
            lines.append("## 🐛 Bug Fixes\n")
            for pr in tiered_prs[3]:
                lines.append(f"- {pr['title']} ([#{pr['number']}]({pr['url']})) by @{pr['author']}")
            lines.append("")
        
        # Format Other PRs if they exist
        if tiered_prs.get(0):
            lines.append("## 📝 Other Changes\n")
            for pr in tiered_prs[0]:
                lines.append(f"- {pr['title']} ([#{pr['number']}]({pr['url']})) by @{pr['author']}")
            lines.append("")
        
        # Add contributors section
        all_contributors = set()
        for tier_prs in tiered_prs.values():
            for pr in tier_prs:
                all_contributors.add(pr['author'])
        
        if all_contributors:
            lines.append("## 👥 Contributors\n")
            lines.append(f"Thanks to all contributors: {', '.join(f'@{c}' for c in sorted(all_contributors))}\n")
        
        return "\n".join(lines)
    
    def generate_release_notes(
        self,
        repo_name: str,
        since_date: datetime,
        until_date: Optional[datetime] = None,
        version: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate complete release notes.
        
        Args:
            repo_name: Repository in format "owner/repo"
            since_date: Start date for filtering PRs
            until_date: Optional end date for filtering PRs
            version: Optional version string for the release
            output_file: Optional file path to save the release notes
            
        Returns:
            Formatted release notes as string
        """
        # Fetch PRs
        tiered_prs = self.fetch_merged_prs_since(repo_name, since_date, until_date)
        
        # Format release notes
        release_notes = self.format_for_changelog(tiered_prs, version, repo_name)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(release_notes)
            console.print(f"[green]✓ Release notes saved to {output_file}[/green]")
        
        return release_notes


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str)
    except:
        try:
            # Try common date format
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or ISO format.")