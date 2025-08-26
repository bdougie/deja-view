#!/usr/bin/env python3
"""
Advanced release notes generator that can detect the last release date.
"""

import os
import sys
from datetime import datetime, timezone
from github import Github
from release_notes import ReleaseNotesGenerator, parse_date
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
console = Console()


def get_last_release_date(repo_name: str, github_token: str) -> datetime:
    """
    Get the date of the last release from GitHub.
    
    Args:
        repo_name: Repository in format "owner/repo"
        github_token: GitHub access token
        
    Returns:
        DateTime of the last release, or 30 days ago if no releases found
    """
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        # Try to get the latest release
        try:
            latest_release = repo.get_latest_release()
            console.print(f"[green]Found last release: {latest_release.tag_name} ({latest_release.published_at})[/green]")
            return latest_release.published_at
        except:
            # No releases found, try tags
            tags = repo.get_tags()
            if tags.totalCount > 0:
                latest_tag = next(iter(tags))
                # Get commit date for the tag
                commit = repo.get_commit(latest_tag.commit.sha)
                console.print(f"[yellow]No releases found, using latest tag: {latest_tag.name} ({commit.commit.author.date})[/yellow]")
                return commit.commit.author.date.replace(tzinfo=timezone.utc)
            else:
                # No releases or tags, default to 30 days ago
                from datetime import timedelta
                default_date = datetime.now(timezone.utc) - timedelta(days=30)
                console.print(f"[yellow]No releases or tags found, defaulting to 30 days ago[/yellow]")
                return default_date
                
    except Exception as e:
        console.print(f"[red]Error fetching last release date: {e}[/red]")
        from datetime import timedelta
        return datetime.now(timezone.utc) - timedelta(days=30)


def main():
    """Main function to generate release notes."""
    
    # Check for GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        console.print("[red]Error: GITHUB_TOKEN environment variable is required[/red]")
        console.print("Set it with: export GITHUB_TOKEN=your-github-token")
        sys.exit(1)
    
    # Get repository from command line or use default
    if len(sys.argv) > 1:
        repo_name = sys.argv[1]
    else:
        console.print("[yellow]Usage: python generate_release_notes.py owner/repo [since_date] [version][/yellow]")
        console.print("[yellow]Using default repository for demo: continuedev/continue[/yellow]")
        repo_name = "continuedev/continue"
    
    # Get or detect since date
    if len(sys.argv) > 2:
        try:
            since_date = parse_date(sys.argv[2])
            console.print(f"[cyan]Using provided date: {since_date.date()}[/cyan]")
        except ValueError as e:
            console.print(f"[red]Invalid date format: {sys.argv[2]}[/red]")
            console.print("Use YYYY-MM-DD format")
            sys.exit(1)
    else:
        console.print("[cyan]Detecting last release date...[/cyan]")
        since_date = get_last_release_date(repo_name, github_token)
    
    # Get version if provided
    version = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    output_file = f"release-notes-{timestamp}.md"
    
    console.print(f"\n[bold]Generating Release Notes[/bold]")
    console.print(f"Repository: {repo_name}")
    console.print(f"Since: {since_date.date()}")
    if version:
        console.print(f"Version: {version}")
    console.print(f"Output: {output_file}\n")
    
    try:
        # Generate release notes
        generator = ReleaseNotesGenerator(github_token)
        release_notes = generator.generate_release_notes(
            repo_name=repo_name,
            since_date=since_date,
            version=version,
            output_file=output_file
        )
        
        console.print(f"\n[bold green]✅ Success![/bold green]")
        console.print(f"Release notes have been saved to: {output_file}")
        
        # Show stats
        lines = release_notes.split('\n')
        pr_count = len([l for l in lines if l.strip().startswith('-')])
        console.print(f"\nStats:")
        console.print(f"  • Total PRs included: {pr_count}")
        console.print(f"  • Lines generated: {len(lines)}")
        
        # Show how to use with Continue.dev
        console.print("\n[bold]Next Steps for changelog.continue.dev:[/bold]")
        console.print("1. Review the generated release notes in " + output_file)
        console.print("2. Edit as needed (add highlights, breaking changes, etc.)")
        console.print("3. Copy content to your changelog repository")
        console.print("4. Commit and push to update changelog.continue.dev")
        
    except Exception as e:
        console.print(f"[red]Error generating release notes: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()