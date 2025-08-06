#!/usr/bin/env python3
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint
import sys

from github_similarity_service import SimilarityService

console = Console()


def format_similarity_score(score: float) -> str:
    if score >= 0.8:
        return f"[green]{score:.2%}[/green]"
    elif score >= 0.6:
        return f"[yellow]{score:.2%}[/yellow]"
    else:
        return f"[red]{score:.2%}[/red]"


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """GitHub Issues Similarity CLI - Find similar issues using semantic search"""
    pass


@cli.command()
@click.argument("repository", metavar="OWNER/REPO")
@click.option("--max-issues", "-m", default=100, help="Maximum number of issues to index")
@click.option("--include-discussions", "-d", is_flag=True, help="Also index discussions")
@click.option("--state", "-s", type=click.Choice(['open', 'closed', 'all']), default='open', help="Issue state to index (default: open)")
def index(repository, max_issues, include_discussions, state):
    """Index issues from a GitHub repository"""
    try:
        owner, repo = repository.split("/")
    except ValueError:
        console.print("[red]Error: Repository must be in format 'owner/repo'[/red]")
        sys.exit(1)
    
    try:
        service = SimilarityService()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Indexing {repository}...", total=None)
            result = service.index_repository(owner, repo, max_issues, include_discussions, issue_state=state)
            progress.update(task, completed=True)
        
        message = f"[green]✓[/green] Successfully indexed [bold]{result['indexed']}[/bold] items from {result['repository']}"
        if include_discussions and result.get('discussions', 0) > 0:
            message += f" ({result['issues']} issues, {result['discussions']} discussions)"
        
        console.print(Panel(
            message,
            title="Indexing Complete",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("issue_url", metavar="ISSUE_URL")
@click.option("--top-k", "-k", default=10, help="Number of similar issues to return")
@click.option("--min-similarity", "-s", default=0.0, help="Minimum similarity score (0-1)")
def find(issue_url, top_k, min_similarity):
    """Find similar issues to a specific GitHub issue or PR"""
    try:
        parts = issue_url.replace("https://github.com/", "").split("/")
        if len(parts) < 4 or parts[2] not in ["issues", "pull"]:
            raise ValueError("Invalid issue URL format")
        
        owner = parts[0]
        repo = parts[1]
        issue_number = int(parts[3])
    except (ValueError, IndexError):
        console.print("[red]Error: Invalid issue/PR URL. Expected format: https://github.com/owner/repo/issues/123 or https://github.com/owner/repo/pull/123[/red]")
        sys.exit(1)
    
    try:
        service = SimilarityService()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Finding similar issues...", total=None)
            results = service.find_similar_issues(owner, repo, issue_number, top_k, min_similarity)
            progress.update(task, completed=True)
        
        if not results:
            console.print("[yellow]No similar issues found.[/yellow]")
            return
        
        table = Table(title=f"Similar Issues to #{issue_number}", show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=8)
        table.add_column("Title", style="white")
        table.add_column("Similarity", justify="right", width=12)
        table.add_column("State", width=10)
        table.add_column("Type", width=12)
        
        for issue in results:
            state_style = "green" if issue["state"] == "open" else "red"
            
            if issue.get("is_discussion", False):
                type_emoji = "💬"
                type_text = "Discussion"
            elif issue["is_pull_request"]:
                type_emoji = "🔀"
                type_text = "PR"
            else:
                type_emoji = "🐛"
                type_text = "Issue"
            
            table.add_row(
                str(issue["number"]),
                issue["title"][:60] + "..." if len(issue["title"]) > 60 else issue["title"],
                format_similarity_score(issue["similarity"]),
                f"[{state_style}]{issue['state']}[/{state_style}]",
                f"{type_emoji} {type_text}"
            )
        
        console.print(table)
        console.print(f"\n[dim]View issues at: https://github.com/{owner}/{repo}/issues[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
def stats():
    """Show statistics about indexed issues"""
    try:
        service = SimilarityService()
        stats = service.get_stats()
        
        panel_content = f"[bold]Total Issues:[/bold] {stats['total_issues']}\n"
        panel_content += f"[bold]Repositories:[/bold] {len(stats['repositories'])}\n\n"
        
        if stats['repositories']:
            panel_content += "[bold]Indexed Repositories:[/bold]\n"
            for repo in stats['repositories']:
                panel_content += f"  • {repo}\n"
        
        console.print(Panel(
            panel_content.strip(),
            title="Database Statistics",
            border_style="blue"
        ))
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to clear all indexed issues?")
def clear():
    """Clear all indexed issues from the database"""
    try:
        service = SimilarityService()
        result = service.clear_all()
        console.print("[green]✓[/green] " + result["message"])
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("repository", metavar="OWNER/REPO")
@click.argument("issue_number", type=int)
@click.option("--index-first", "-i", is_flag=True, help="Index repository before finding similar issues")
@click.option("--max-issues", "-m", default=200, help="Maximum issues to index (if --index-first)")
@click.option("--top-k", "-k", default=10, help="Number of similar issues to return")
def quick(repository, issue_number, index_first, max_issues, top_k):
    """Quick command to find similar issues (optionally index first)"""
    try:
        owner, repo = repository.split("/")
    except ValueError:
        console.print("[red]Error: Repository must be in format 'owner/repo'[/red]")
        sys.exit(1)
    
    try:
        service = SimilarityService()
        
        if index_first:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:task = progress.add_task(f"Indexing {repository}...", total=None)
            result = service.index_repository(owner, repo, max_issues, False)
            progress.update(task, completed=True)
            
            console.print(f"[green]✓[/green] Indexed {result['indexed']} issues\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Finding similar issues...", total=None)
            results = service.find_similar_issues(owner, repo, issue_number, top_k)
            progress.update(task, completed=True)
        
        if not results:
            console.print("[yellow]No similar issues found.[/yellow]")
            return
        
        table = Table(title=f"Similar Issues to {repository}#{issue_number}", show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=8)
        table.add_column("Title", style="white")
        table.add_column("Similarity", justify="right", width=12)
        table.add_column("State", width=10)
        
        for issue in results[:top_k]:
            state_style = "green" if issue["state"] == "open" else "red"
            
            table.add_row(
                str(issue["number"]),
                issue["title"][:60] + "..." if len(issue["title"]) > 60 else issue["title"],
                format_similarity_score(issue["similarity"]),
                f"[{state_style}]{issue['state']}[/{state_style}]"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("repository", metavar="OWNER/REPO")
@click.option("--min-score", "-s", default=0.3, help="Minimum discussion score (0.0-1.0)")
@click.option("--max-suggestions", "-n", default=20, help="Maximum number of suggestions")
@click.option("--dry-run/--execute", default=True, help="Dry run mode (default) or execute changes")
def suggest_discussions(repository, min_score, max_suggestions, dry_run):
    """Suggest which issues should be GitHub discussions"""
    try:
        owner, repo = repository.split("/")
    except ValueError:
        console.print("[red]Error: Repository must be in format 'owner/repo'[/red]")
        sys.exit(1)
    
    try:
        service = SimilarityService()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing issues...", total=None)
            result = service.suggest_discussions(owner, repo, min_score, max_suggestions, dry_run)
            progress.update(task, completed=True)
        
        suggestions = result["suggestions"]
        
        if not suggestions:
            console.print(f"[yellow]No issues found that should be discussions (min score: {min_score})[/yellow]")
            return
        
        # Show dry run warning
        if dry_run:
            console.print(Panel(
                "[yellow]DRY RUN MODE[/yellow] - No changes will be made\nUse --execute to perform actual conversions",
                title="⚠️  Warning",
                border_style="yellow"
            ))
        
        table = Table(title=f"Discussion Suggestions for {repository}", show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=8)
        table.add_column("Title", style="white")
        table.add_column("Score", justify="right", width=8)
        table.add_column("State", width=8)
        table.add_column("Reasons", style="dim")
        
        for suggestion in suggestions:
            state_style = "green" if suggestion["state"] == "open" else "red"
            score_style = "green" if suggestion["score"] >= 0.7 else "yellow" if suggestion["score"] >= 0.5 else "red"
            
            table.add_row(
                str(suggestion["number"]),
                suggestion["title"][:50] + "..." if len(suggestion["title"]) > 50 else suggestion["title"],
                f"[{score_style}]{suggestion['score']:.2f}[/{score_style}]",
                f"[{state_style}]{suggestion['state']}[/{state_style}]",
                ", ".join(suggestion["reasons"][:2]) + ("..." if len(suggestion["reasons"]) > 2 else "")
            )
        
        console.print(table)
        
        # Summary
        console.print(f"\n[dim]Analyzed {result['total_analyzed']} issues, found {len(suggestions)} suggestions[/dim]")
        console.print(f"[dim]View issues at: https://github.com/{owner}/{repo}/issues[/dim]")
        
        if dry_run:
            console.print(f"\n[yellow]Tip:[/yellow] Use [bold]--execute[/bold] flag to convert these issues to discussions")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()