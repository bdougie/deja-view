#!/usr/bin/env python3
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint
import sys
import os
from datetime import datetime

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
@click.option("--label-duplicate", is_flag=True, help="Add 'potential-duplicate' label if high similarity found")
def find(issue_url, top_k, min_similarity, label_duplicate):
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
        
        # Check for potential duplicate and label if requested
        if label_duplicate and results:
            highest_similarity = results[0]["similarity"]
            if highest_similarity >= 0.9:
                console.print(f"\n[yellow]High similarity detected ({highest_similarity:.1%})[/yellow]")
                
                # Ensure label exists
                labels_config = {"potential-duplicate": "DC2626"}  # Red
                service.ensure_labels_exist(owner, repo, labels_config)
                
                # Add label to the issue
                if service.add_issue_labels(owner, repo, issue_number, ["potential-duplicate"]):
                    console.print(f"[green]✓[/green] Added 'potential-duplicate' label to issue #{issue_number}")
                else:
                    console.print(f"[red]✗[/red] Failed to add label to issue #{issue_number}")
            else:
                console.print(f"\n[dim]Highest similarity ({highest_similarity:.1%}) below duplicate threshold (90%)[/dim]")
        
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
@click.option("--min-score", "-s", default=0.5, help="Minimum discussion score (0.0-1.0)")
@click.option("--max-suggestions", "-n", default=100, help="Maximum number of suggestions")
@click.option("--dry-run/--execute", default=True, help="Dry run mode (default) or execute changes")
@click.option("--output", "-o", help="Output markdown file path")
@click.option("--add-labels", is_flag=True, help="Add labels to suggested issues")
def suggest_discussions(repository, min_score, max_suggestions, dry_run, output, add_labels):
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
        
        # Generate markdown report if output file specified
        if output:
            markdown_content = f"# Discussion Suggestions for {repository}\n\n"
            markdown_content += f"**Analysis Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            markdown_content += f"**Total Issues Analyzed:** {result['total_analyzed']}\n"
            markdown_content += f"**Suggestions Found:** {len(suggestions)} (minimum score: {min_score})\n\n"
            
            # Group by confidence level
            high_confidence = [s for s in suggestions if s['score'] >= 0.7]
            medium_confidence = [s for s in suggestions if 0.5 <= s['score'] < 0.7]
            
            if high_confidence:
                markdown_content += "## 🟢 High Confidence (≥70%)\n\n"
                markdown_content += "These issues strongly suggest they should be discussions.\n\n"
                markdown_content += "| # | Title | Score | State | Reasons |\n"
                markdown_content += "|---|-------|-------|-------|----------|\n"
                for s in high_confidence:
                    state_icon = "🟢" if s['state'] == 'open' else "🔴"
                    reasons = "<br>".join(f"• {r}" for r in s['reasons'])
                    markdown_content += f"| [#{s['number']}]({s['url']}) | {s['title']} | {s['score']:.0%} | {state_icon} {s['state']} | {reasons} |\n"
                markdown_content += "\n"
            
            if medium_confidence:
                markdown_content += "## 🟡 Medium Confidence (50-69%)\n\n"
                markdown_content += "These issues might be better as discussions.\n\n"
                markdown_content += "| # | Title | Score | State | Reasons |\n"
                markdown_content += "|---|-------|-------|-------|----------|\n"
                for s in medium_confidence:
                    state_icon = "🟢" if s['state'] == 'open' else "🔴"
                    reasons = "<br>".join(f"• {r}" for r in s['reasons'])
                    markdown_content += f"| [#{s['number']}]({s['url']}) | {s['title']} | {s['score']:.0%} | {state_icon} {s['state']} | {reasons} |\n"
                markdown_content += "\n"
            
            # Add summary section
            markdown_content += "## Summary\n\n"
            markdown_content += f"- **High Confidence (≥70%):** {len(high_confidence)} issues\n"
            markdown_content += f"- **Medium Confidence (50-69%):** {len(medium_confidence)} issues\n"
            markdown_content += f"- **Total Suggestions:** {len(suggestions)} issues\n\n"
            
            # Add labeling commands
            markdown_content += "## Quick Actions\n\n"
            markdown_content += "### Add Labels via GitHub CLI\n\n"
            markdown_content += "To label high-confidence issues:\n```bash\n"
            for s in high_confidence[:10]:  # Limit to first 10 for readability
                markdown_content += f"gh issue edit {s['number']} --add-label 'should-be-discussion' -R {repository}\n"
            if len(high_confidence) > 10:
                markdown_content += f"# ... and {len(high_confidence) - 10} more\n"
            markdown_content += "```\n\n"
            
            markdown_content += "To label medium-confidence issues:\n```bash\n"
            for s in medium_confidence[:10]:
                markdown_content += f"gh issue edit {s['number']} --add-label 'discussion' -R {repository}\n"
            if len(medium_confidence) > 10:
                markdown_content += f"# ... and {len(medium_confidence) - 10} more\n"
            markdown_content += "```\n\n"
            
            markdown_content += "---\n"
            markdown_content += "_Generated by [deja-view](https://github.com/bdougie/deja-view)_\n"
            
            # Write to file
            with open(output, 'w') as f:
                f.write(markdown_content)
            
            console.print(f"[green]✓[/green] Markdown report written to: {output}")
        
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
        table.add_column("Confidence", justify="center", width=12)
        table.add_column("State", width=8)
        table.add_column("Reasons", style="dim")
        
        for suggestion in suggestions[:20]:  # Show first 20 in console
            state_style = "green" if suggestion["state"] == "open" else "red"
            score_style = "green" if suggestion["score"] >= 0.7 else "yellow" if suggestion["score"] >= 0.5 else "red"
            
            # Get confidence level with emoji
            confidence = suggestion.get("confidence", "low")
            confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(confidence, "")
            confidence_display = f"{confidence_emoji} {confidence.title()}"
            
            table.add_row(
                str(suggestion["number"]),
                suggestion["title"][:50] + "..." if len(suggestion["title"]) > 50 else suggestion["title"],
                f"[{score_style}]{suggestion['score']:.2f}[/{score_style}]",
                confidence_display,
                f"[{state_style}]{suggestion['state']}[/{state_style}]",
                ", ".join(suggestion["reasons"][:2]) + ("..." if len(suggestion["reasons"]) > 2 else "")
            )
        
        console.print(table)
        
        if len(suggestions) > 20:
            console.print(f"[dim]... and {len(suggestions) - 20} more suggestions[/dim]")
        
        # Summary
        console.print(f"\n[dim]Analyzed {result['total_analyzed']} issues, found {len(suggestions)} suggestions[/dim]")
        console.print(f"[dim]View issues at: https://github.com/{owner}/{repo}/issues[/dim]")
        
        # Apply labels if requested
        if add_labels and not dry_run:
            console.print("\n[yellow]Applying labels to issues...[/yellow]")
            
            # Define label configurations
            labels_config = {
                "should-be-discussion": "8B5CF6",  # Purple
                "discussion": "0E7490",  # Teal
                "potential-duplicate": "DC2626"  # Red
            }
            
            # Ensure labels exist
            service.ensure_labels_exist(owner, repo, labels_config)
            
            labeled_count = 0
            for suggestion in suggestions:
                labels_to_add = []
                
                # Determine which label to add based on confidence
                confidence = suggestion.get("confidence", "low")
                if confidence == "high":
                    labels_to_add.append("should-be-discussion")
                elif confidence == "medium":
                    labels_to_add.append("discussion")
                
                if labels_to_add:
                    if service.add_issue_labels(owner, repo, suggestion["number"], labels_to_add):
                        labeled_count += 1
                        console.print(f"  [green]✓[/green] Added label to issue #{suggestion['number']}: {', '.join(labels_to_add)}")
                    else:
                        console.print(f"  [red]✗[/red] Failed to label issue #{suggestion['number']}")
            
            console.print(f"\n[green]Successfully labeled {labeled_count} issues[/green]")
        elif add_labels and dry_run:
            console.print("\n[yellow]Note:[/yellow] Labels will be applied when using --execute flag")
        
        if dry_run:
            console.print(f"\n[yellow]Tip:[/yellow] Use [bold]--execute[/bold] flag to convert these issues to discussions")
            if not add_labels:
                console.print(f"[yellow]Tip:[/yellow] Use [bold]--add-labels[/bold] flag to label issues based on confidence")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('repository')
@click.option('-t', '--threshold', default=0.8, help='Similarity threshold for duplicates (0-1)')
@click.option('-o', '--output', default='duplicate-issues-report.md', help='Output file for markdown report')
@click.option('--state', type=click.Choice(['open', 'closed', 'all']), default='all', help='Issue state to analyze')
def find_duplicates(repository, threshold, output, state):
    """Find potential duplicate issues in a repository using indexed Chroma data"""
    try:
        console = Console()
        service = SimilarityService()
        
        # Parse repository
        parts = repository.split('/')
        if len(parts) != 2:
            console.print("[red]Error: Repository must be in format 'owner/repo'[/red]")
            sys.exit(1)
        
        owner, repo = parts
        
        with console.status(f"[bold green]Finding duplicate issues in {repository} from indexed data..."):
            # Get documents from the collection (Chroma Cloud has a limit of 100)
            # Note: To analyze all 986 issues, you'd need to implement pagination
            # For now, we'll work with the limit of 100
            all_docs = service.collection.get(
                where={"$and": [{"owner": owner}, {"repo": repo}]}
                # Default limit is 100 due to Chroma Cloud quota
            )
            
            if not all_docs["ids"]:
                console.print(f"[red]No indexed issues found for {repository}[/red]")
                console.print("[yellow]Please run: cli.py index {repository}[/yellow]")
                sys.exit(1)
            
            # Filter by state if needed
            issues_to_analyze = []
            for i, doc_id in enumerate(all_docs["ids"]):
                metadata = all_docs["metadatas"][i] if all_docs["metadatas"] else {}
                issue_state = metadata.get("state", "unknown")
                
                if state == "all" or issue_state == state:
                    # Parse issue number from doc_id (format: owner_repo_number or full URL)
                    try:
                        if '/issues/' in doc_id:
                            issue_number = int(doc_id.split('/issues/')[-1])
                        else:
                            issue_number = int(doc_id.split("_")[-1])
                    except:
                        continue
                        
                    issues_to_analyze.append({
                        'id': doc_id,
                        'number': issue_number,
                        'title': metadata.get('title', ''),
                        'body': metadata.get('body', ''),
                        'state': issue_state,
                        'url': metadata.get('url', ''),
                        'created_at': metadata.get('created_at', ''),
                        'labels': metadata.get('labels', '') if isinstance(metadata.get('labels'), str) else metadata.get('labels', []),
                        'document': all_docs["documents"][i] if all_docs["documents"] else ''
                    })
            
            console.print(f"[cyan]Analyzing {len(issues_to_analyze)} {state} issues from Chroma index...[/cyan]")
            
            # Find duplicates for each issue
            duplicates_found = []
            
            for idx, issue in enumerate(issues_to_analyze):
                if (idx + 1) % 50 == 0:
                    console.print(f"[dim]Progress: {idx + 1}/{len(issues_to_analyze)} issues analyzed...[/dim]")
                
                # Search for similar issues
                query_text = issue['document'] or f"{issue['title']} {issue['body']}"
                results = service.collection.query(
                    query_texts=[query_text],
                    n_results=10,  # Get more results to find good matches
                    where={"$and": [{"owner": owner}, {"repo": repo}]}
                )
                
                similar = []
                if results["ids"] and results["ids"][0]:
                    for i, doc_id in enumerate(results["ids"][0]):
                        # Parse issue number from doc_id
                        try:
                            if '/issues/' in doc_id:
                                doc_number = int(doc_id.split('/issues/')[-1])
                            else:
                                doc_number = int(doc_id.split("_")[-1])
                        except:
                            continue
                            
                        # Skip self-match
                        if doc_number == issue['number']:
                            continue
                        
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        distance = results["distances"][0][i] if results["distances"] else 1.0
                        similarity = 1 - (distance / 2)  # Convert distance to similarity
                        
                        if similarity >= threshold:
                            similar.append({
                                'number': doc_number,
                                'title': metadata.get('title', 'Unknown'),
                                'url': metadata.get('url', f"https://github.com/{repository}/issues/{doc_number}"),
                                'state': metadata.get('state', 'unknown'),
                                'similarity': similarity
                            })
                
                if similar:
                    duplicates_found.append({
                        'issue': {
                            'number': issue['number'],
                            'title': issue['title'],
                            'url': issue['url'],
                            'state': issue['state'],
                            'created_at': issue['created_at'],
                            'labels': issue['labels']
                        },
                        'duplicates': similar[:3],  # Keep top 3 duplicates
                        'max_similarity': max(s['similarity'] for s in similar)
                    })
        
        # Sort by max similarity
        duplicates_found.sort(key=lambda x: x['max_similarity'], reverse=True)
        
        # Generate markdown report
        markdown_content = f"# Duplicate Issues Report for {repository}\n\n"
        markdown_content += f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown_content += f"**Issues Analyzed:** {len(issues_to_analyze)} {state} issues\n"
        markdown_content += f"**Potential Duplicates Found:** {len(duplicates_found)}\n"
        markdown_content += f"**Similarity Threshold:** {threshold * 100:.0f}%\n\n"
        
        if not duplicates_found:
            markdown_content += "_No potential duplicates found with the given threshold._\n"
        else:
            # Group by similarity level
            very_high = [d for d in duplicates_found if d['max_similarity'] >= 0.9]
            high = [d for d in duplicates_found if 0.8 <= d['max_similarity'] < 0.9]
            
            if very_high:
                markdown_content += "## 🔴 Very High Similarity (≥90%)\n\n"
                markdown_content += "These issues are very likely duplicates.\n\n"
                
                for dup in very_high[:20]:  # Limit to first 20
                    issue = dup['issue']
                    markdown_content += f"### [#{issue['number']}: {issue['title']}]({issue['url']})\n"
                    markdown_content += f"**State:** {issue['state']} | "
                    if issue['labels']:
                        if isinstance(issue['labels'], str):
                            markdown_content += f"**Labels:** {issue['labels']}\n"
                        elif isinstance(issue['labels'], list):
                            markdown_content += f"**Labels:** {', '.join(issue['labels'])}\n"
                        else:
                            markdown_content += "\n"
                    else:
                        markdown_content += "\n"
                    
                    markdown_content += "**Potential duplicates:**\n"
                    for sim in dup['duplicates']:
                        state_emoji = '🟢' if sim.get('state') == 'open' else '🔴'
                        markdown_content += f"- {state_emoji} [#{sim['number']}: {sim['title']}]({sim.get('url', '#')}) "
                        markdown_content += f"({sim['similarity'] * 100:.0f}% similar)\n"
                    markdown_content += "\n---\n\n"
            
            if high:
                markdown_content += "## 🟡 High Similarity (80-89%)\n\n"
                markdown_content += "These issues might be duplicates and should be reviewed.\n\n"
                
                markdown_content += "| Issue | Potential Duplicates | Max Similarity |\n"
                markdown_content += "|-------|---------------------|----------------|\n"
                
                for dup in high[:30]:  # Limit to first 30
                    issue = dup['issue']
                    issue_link = f"[#{issue['number']}]({issue['url']})"
                    
                    dup_links = []
                    for sim in dup['duplicates'][:2]:  # Show top 2
                        state = '🟢' if sim.get('state') == 'open' else '🔴'
                        dup_links.append(f"{state} #{sim['number']}")
                    
                    max_sim = f"{dup['max_similarity'] * 100:.0f}%"
                    markdown_content += f"| {issue_link} | {', '.join(dup_links)} | {max_sim} |\n"
        
        markdown_content += "\n## Summary\n\n"
        markdown_content += f"- **Very High Similarity (≥90%):** {len([d for d in duplicates_found if d['max_similarity'] >= 0.9])} issues\n"
        markdown_content += f"- **High Similarity (80-89%):** {len([d for d in duplicates_found if 0.8 <= d['max_similarity'] < 0.9])} issues\n"
        markdown_content += f"- **Total Potential Duplicates:** {len(duplicates_found)} issues\n\n"
        
        # Add quick actions
        if duplicates_found:
            markdown_content += "## Quick Actions\n\n"
            markdown_content += "### Add 'potential-duplicate' label to high-confidence duplicates:\n"
            markdown_content += "```bash\n"
            for dup in duplicates_found[:10]:
                if dup['max_similarity'] >= 0.9:
                    markdown_content += f"gh issue edit {dup['issue']['number']} --add-label 'potential-duplicate' -R {repository}\n"
            markdown_content += "```\n\n"
        
        markdown_content += "---\n"
        markdown_content += "_Generated by [deja-view](https://github.com/bdougie/deja-view)_\n"
        
        # Write to file
        with open(output, 'w') as f:
            f.write(markdown_content)
        
        console.print(f"[green]✓[/green] Report written to: {output}")
        
        # Display summary in console
        table = Table(title=f"Duplicate Issues Summary for {repository}")
        table.add_column("Similarity", style="cyan")
        table.add_column("Count", justify="right")
        
        table.add_row("≥90% (Very High)", str(len([d for d in duplicates_found if d['max_similarity'] >= 0.9])))
        table.add_row("80-89% (High)", str(len([d for d in duplicates_found if 0.8 <= d['max_similarity'] < 0.9])))
        table.add_row("[bold]Total", f"[bold]{len(duplicates_found)}")
        
        console.print(table)
        
        if duplicates_found:
            console.print(f"\n[yellow]Tip:[/yellow] Review the report at {output} to identify and close duplicate issues")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()