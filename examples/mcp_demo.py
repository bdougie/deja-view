#!/usr/bin/env python3
"""
Demo script showing how to use the Deja-View MCP tools
This simulates what Continue does when using the MCP server
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server import (
    find_similar_issues,
    index_repository,
    get_user_comments,
    suggest_discussion_candidates,
    search_github_issues,
    get_similarity_stats
)


def demo_workflow():
    """Demonstrate a complete workflow using MCP tools"""
    
    print("=" * 60)
    print("Deja-View MCP Tools Demo")
    print("=" * 60)
    print()
    
    # Repository to work with
    repo = "continuedev/continue"
    
    # Step 1: Check current stats
    print("📊 Checking database statistics...")
    stats = get_similarity_stats()
    if "error" in stats:
        print(f"   ❌ Error: {stats['error']}")
        print("   Make sure environment variables are set correctly")
        return
    print(f"   Total indexed issues: {stats.get('total_issues', 0)}")
    print(f"   Repositories: {stats.get('repository_count', 0)}")
    print()
    
    # Step 2: Index a repository
    print(f"🔍 Indexing {repo} repository...")
    result = index_repository(repo, max_issues=50, issue_state="open")
    if "error" in result:
        print(f"   ❌ Error: {result['error']}")
    else:
        print(f"   ✅ Indexed {result.get('indexed', 0)} issues")
    print()
    
    # Step 3: Search for specific issues
    print("🔎 Searching for 'error' issues...")
    search_results = search_github_issues("error", repository=repo, limit=3)
    if "error" in search_results:
        print(f"   ❌ Error: {search_results['error']}")
    else:
        print(f"   Found {search_results.get('count', 0)} results:")
        for issue in search_results.get('results', [])[:3]:
            print(f"   - #{issue['number']}: {issue['title']}")
    print()
    
    # Step 4: Find similar issues
    if search_results.get('results'):
        first_issue = search_results['results'][0]
        issue_num = first_issue['number']
        print(f"🔗 Finding issues similar to #{issue_num}...")
        similar = find_similar_issues(repo, issue_num, limit=5, min_similarity=0.5)
        if "error" in similar:
            print(f"   ❌ Error: {similar['error']}")
        else:
            print(f"   Found {similar.get('count', 0)} similar issues:")
            for issue in similar.get('similar_issues', [])[:3]:
                similarity_pct = issue.get('similarity', 0) * 100
                print(f"   - #{issue['number']}: {issue['title']} ({similarity_pct:.1f}% similar)")
    print()
    
    # Step 5: Check user comments
    print("💬 Fetching recent comments from 'jlowin' (FastMCP creator)...")
    comments = get_user_comments("jlowin", limit=3)
    if "error" in comments:
        print(f"   ❌ Error: {comments['error']}")
    else:
        print(f"   Found {comments.get('count', 0)} recent comments:")
        for comment in comments.get('comments', []):
            print(f"   - {comment['repository']}#{comment['issue_number']}: {comment['issue_title'][:50]}...")
    print()
    
    # Step 6: Suggest discussion candidates
    print(f"💡 Checking for discussion candidates in {repo}...")
    suggestions = suggest_discussion_candidates(repo, min_score=0.5, max_suggestions=5)
    if "error" in suggestions:
        print(f"   ❌ Error: {suggestions['error']}")
    else:
        high_conf = suggestions.get('summary', {}).get('high_confidence_count', 0)
        med_conf = suggestions.get('summary', {}).get('medium_confidence_count', 0)
        print(f"   Found {high_conf} high-confidence and {med_conf} medium-confidence candidates")
        
        # Show a few examples
        for issue in suggestions.get('high_confidence', [])[:2]:
            print(f"   - #{issue['number']}: {issue['title']} (score: {issue['score']:.2f})")
    print()
    
    print("=" * 60)
    print("Demo complete! These tools are available in Continue.")
    print("=" * 60)


def interactive_demo():
    """Interactive demo where users can try different tools"""
    
    print("=" * 60)
    print("Deja-View MCP Interactive Demo")
    print("=" * 60)
    print()
    print("Available commands:")
    print("1. index <repo> - Index a repository")
    print("2. similar <repo> <issue_num> - Find similar issues")
    print("3. comments <username> - Get user's recent comments")
    print("4. search <query> - Search GitHub issues")
    print("5. stats - Show database statistics")
    print("6. quit - Exit demo")
    print()
    
    while True:
        try:
            command = input("Enter command: ").strip().lower()
            
            if command.startswith("index "):
                repo = command.replace("index ", "").strip()
                print(f"Indexing {repo}...")
                result = index_repository(repo, max_issues=50)
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"✅ Indexed {result.get('indexed', 0)} issues")
            
            elif command.startswith("similar "):
                parts = command.replace("similar ", "").split()
                if len(parts) >= 2:
                    repo = parts[0]
                    issue_num = int(parts[1])
                    print(f"Finding issues similar to {repo}#{issue_num}...")
                    result = find_similar_issues(repo, issue_num, limit=5)
                    if "error" in result:
                        print(f"Error: {result['error']}")
                    else:
                        for issue in result.get('similar_issues', []):
                            print(f"  #{issue['number']}: {issue['title']} ({issue['similarity']:.2%})")
                else:
                    print("Usage: similar <repo> <issue_number>")
            
            elif command.startswith("comments "):
                username = command.replace("comments ", "").strip()
                print(f"Getting recent comments from {username}...")
                result = get_user_comments(username, limit=5)
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    for comment in result.get('comments', []):
                        print(f"  {comment['repository']}#{comment['issue_number']}: {comment['comment_preview'][:80]}...")
            
            elif command.startswith("search "):
                query = command.replace("search ", "").strip()
                print(f"Searching for '{query}'...")
                result = search_github_issues(query, limit=5)
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    for issue in result.get('results', []):
                        print(f"  {issue['repository']}#{issue['number']}: {issue['title']}")
            
            elif command == "stats":
                result = get_similarity_stats()
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"Total issues: {result.get('total_issues', 0)}")
                    print(f"Repositories: {', '.join(result.get('repositories', []))}")
            
            elif command in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            
            else:
                print("Unknown command. Type 'quit' to exit.")
            
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        demo_workflow()