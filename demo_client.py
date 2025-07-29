#!/usr/bin/env python3
import httpx
import asyncio
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

API_BASE_URL = "http://localhost:8000"


async def demo():
    async with httpx.AsyncClient() as client:
        console.print("[bold magenta]GitHub Issues Similarity Service Demo[/bold magenta]\n")
        
        console.print("1️⃣  [bold]Checking API health...[/bold]")
        health = await client.get(f"{API_BASE_URL}/health")
        if health.status_code == 200:
            console.print("[green]✓ API is healthy![/green]\n")
        else:
            console.print("[red]✗ API is not responding[/red]")
            return
        
        console.print("2️⃣  [bold]Indexing continuedev/continue repository (100 issues)...[/bold]")
        index_response = await client.post(
            f"{API_BASE_URL}/index",
            json={"owner": "continuedev", "repo": "continue", "max_issues": 100},
            timeout=60.0
        )
        index_data = index_response.json()
        console.print(f"[green]✓ Indexed {index_data['indexed']} issues[/green]\n")
        
        console.print("3️⃣  [bold]Finding issues similar to PR #2000...[/bold]")
        similar_response = await client.post(
            f"{API_BASE_URL}/find_similar",
            json={
                "owner": "continuedev",
                "repo": "continue",
                "issue_number": 2000,
                "top_k": 5
            }
        )
        similar_data = similar_response.json()
        
        table = Table(title="Similar Issues", show_header=True, header_style="bold magenta")
        table.add_column("Issue #", style="cyan", width=10)
        table.add_column("Title", style="white")
        table.add_column("Similarity", justify="right", width=12)
        table.add_column("State", width=10)
        
        for issue in similar_data["similar_issues"]:
            state_color = "green" if issue["state"] == "open" else "red"
            similarity_pct = f"{issue['similarity']:.1%}"
            
            table.add_row(
                str(issue["number"]),
                issue["title"][:50] + "..." if len(issue["title"]) > 50 else issue["title"],
                similarity_pct,
                f"[{state_color}]{issue['state']}[/{state_color}]"
            )
        
        console.print(table)
        console.print()
        
        console.print("4️⃣  [bold]Getting database statistics...[/bold]")
        stats = await client.get(f"{API_BASE_URL}/stats")
        stats_data = stats.json()
        console.print(f"[blue]Total indexed issues: {stats_data['total_issues']}[/blue]")
        console.print(f"[blue]Repositories: {', '.join(stats_data['repositories'])}[/blue]\n")
        
        console.print("[bold green]✅ Demo completed successfully![/bold green]")
        console.print("\n[dim]Try the API yourself at http://localhost:8000/docs[/dim]")


async def custom_demo():
    console.print("[bold magenta]Custom Repository Demo[/bold magenta]\n")
    
    owner = console.input("Enter repository owner: ")
    repo = console.input("Enter repository name: ")
    max_issues = int(console.input("Number of issues to index (default 100): ") or "100")
    
    async with httpx.AsyncClient() as client:
        console.print(f"\n[bold]Indexing {owner}/{repo}...[/bold]")
        
        try:
            index_response = await client.post(
                f"{API_BASE_URL}/index",
                json={"owner": owner, "repo": repo, "max_issues": max_issues},
                timeout=120.0
            )
            index_data = index_response.json()
            console.print(f"[green]✓ Indexed {index_data['indexed']} issues[/green]\n")
            
            issue_number = int(console.input("Enter issue number to find similar issues: "))
            
            similar_response = await client.post(
                f"{API_BASE_URL}/find_similar",
                json={
                    "owner": owner,
                    "repo": repo,
                    "issue_number": issue_number,
                    "top_k": 10
                }
            )
            similar_data = similar_response.json()
            
            if similar_data["similar_issues"]:
                table = Table(title=f"Issues Similar to #{issue_number}", show_header=True)
                table.add_column("Issue #", style="cyan")
                table.add_column("Title")
                table.add_column("Similarity", justify="right")
                
                for issue in similar_data["similar_issues"][:10]:
                    table.add_row(
                        str(issue["number"]),
                        issue["title"][:60] + "..." if len(issue["title"]) > 60 else issue["title"],
                        f"{issue['similarity']:.1%}"
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No similar issues found.[/yellow]")
                
        except httpx.HTTPStatusError as e:
            console.print(f"[red]Error: {e.response.json()['detail']}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


async def main():
    console.print("[bold]Choose demo mode:[/bold]")
    console.print("1. Run default demo (continuedev/continue)")
    console.print("2. Try with custom repository")
    
    choice = console.input("\nEnter choice (1 or 2): ")
    
    if choice == "1":
        await demo()
    elif choice == "2":
        await custom_demo()
    else:
        console.print("[red]Invalid choice[/red]")


if __name__ == "__main__":
    asyncio.run(main())