#!/usr/bin/env python3
"""
GitHub Discussions Metrics Service
Provides analytics for GitHub Discussions including:
- Week-over-week discussion creation metrics
- Unanswered Q&A discussions
- Upvote statistics
- Discussion engagement metrics
"""

import os
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import requests
from dotenv import load_dotenv
import json

load_dotenv()


@dataclass
class DiscussionMetrics:
    """Container for discussion metrics data"""
    total_discussions: int
    discussions_this_week: int
    discussions_last_week: int
    week_over_week_change: float
    week_over_week_percentage: float
    unanswered_qa: List[Dict]
    total_unanswered_qa: int
    top_upvoted: List[Dict]
    category_breakdown: Dict[str, int]
    answer_rate: float
    avg_upvotes: float
    period_start: str
    period_end: str


class DiscussionsMetricsService:
    """Service for fetching and analyzing GitHub Discussions metrics"""
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required for GraphQL API access")
    
    def _get_graphql_headers(self) -> Dict[str, str]:
        """Get headers for GitHub GraphQL API requests"""
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json"
        }
    
    def _make_graphql_request(self, query: str, variables: Dict = None) -> Dict:
        """Make a GraphQL request to GitHub API"""
        response = requests.post(
            "https://api.github.com/graphql",
            headers=self._get_graphql_headers(),
            json={"query": query, "variables": variables or {}}
        )
        response.raise_for_status()
        
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data
    
    def fetch_discussions_metrics(self, owner: str, repo: str, weeks_back: int = 4) -> DiscussionMetrics:
        """
        Fetch comprehensive discussions metrics for a repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            weeks_back: Number of weeks of historical data to analyze
        
        Returns:
            DiscussionMetrics object with all metrics
        """
        # Calculate date ranges (timezone-aware)
        from datetime import timezone
        now = datetime.now(timezone.utc)
        end_date = now
        start_date = now - timedelta(weeks=weeks_back)
        this_week_start = now - timedelta(days=7)
        last_week_start = now - timedelta(days=14)
        last_week_end = now - timedelta(days=7)
        
        # Fetch all discussions with pagination
        all_discussions = self._fetch_all_discussions(owner, repo, start_date)
        
        # Filter discussions by time periods
        discussions_this_week = [
            d for d in all_discussions 
            if datetime.fromisoformat(d['createdAt'].replace('Z', '+00:00')) >= this_week_start
        ]
        
        discussions_last_week = [
            d for d in all_discussions 
            if last_week_start <= datetime.fromisoformat(d['createdAt'].replace('Z', '+00:00')) < last_week_end
        ]
        
        # Calculate week-over-week metrics
        this_week_count = len(discussions_this_week)
        last_week_count = len(discussions_last_week)
        
        if last_week_count > 0:
            week_change = this_week_count - last_week_count
            week_percentage = (week_change / last_week_count) * 100
        else:
            week_change = this_week_count
            week_percentage = 100.0 if this_week_count > 0 else 0.0
        
        # Find unanswered Q&A discussions (including Help category)
        unanswered_qa = [
            {
                'number': d['number'],
                'title': d['title'],
                'url': d['url'],
                'createdAt': d['createdAt'],
                'upvoteCount': d['upvoteCount'],
                'category': d['category']['name'],
                'author': d['author']['login'] if d['author'] else 'deleted-user'
            }
            for d in all_discussions
            if (d['category']['name'].lower() in ['q&a', 'help'] or 'question' in d['category']['name'].lower()) 
            and not d.get('answer')
        ]
        
        # Sort by creation date (newest first)
        unanswered_qa.sort(key=lambda x: x['createdAt'], reverse=True)
        
        # Get top upvoted discussions
        top_upvoted = sorted(
            [
                {
                    'number': d['number'],
                    'title': d['title'],
                    'url': d['url'],
                    'upvoteCount': d['upvoteCount'],
                    'category': d['category']['name'],
                    'createdAt': d['createdAt'],
                    'author': d['author']['login'] if d['author'] else 'deleted-user',
                    'hasAnswer': bool(d.get('answer'))
                }
                for d in all_discussions
            ],
            key=lambda x: x['upvoteCount'],
            reverse=True
        )[:20]  # Top 20
        
        # Category breakdown
        category_breakdown = {}
        for d in all_discussions:
            category = d['category']['name']
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
        
        # Calculate answer rate for Q&A discussions (including Help category)
        qa_discussions = [
            d for d in all_discussions 
            if d['category']['name'].lower() in ['q&a', 'help'] or 'question' in d['category']['name'].lower()
        ]
        
        if qa_discussions:
            answered_qa = [d for d in qa_discussions if d.get('answer')]
            answer_rate = (len(answered_qa) / len(qa_discussions)) * 100
        else:
            answer_rate = 0.0
        
        # Calculate average upvotes
        total_upvotes = sum(d['upvoteCount'] for d in all_discussions)
        avg_upvotes = total_upvotes / len(all_discussions) if all_discussions else 0.0
        
        return DiscussionMetrics(
            total_discussions=len(all_discussions),
            discussions_this_week=this_week_count,
            discussions_last_week=last_week_count,
            week_over_week_change=week_change,
            week_over_week_percentage=week_percentage,
            unanswered_qa=unanswered_qa[:50],  # Limit to 50 for display
            total_unanswered_qa=len(unanswered_qa),
            top_upvoted=top_upvoted,
            category_breakdown=category_breakdown,
            answer_rate=answer_rate,
            avg_upvotes=avg_upvotes,
            period_start=start_date.strftime('%Y-%m-%d'),
            period_end=end_date.strftime('%Y-%m-%d')
        )
    
    def _fetch_all_discussions(self, owner: str, repo: str, since_date: datetime) -> List[Dict]:
        """Fetch all discussions since a given date with pagination"""
        all_discussions = []
        cursor = None
        has_next_page = True
        
        while has_next_page:
            query = """
            query($owner: String!, $repo: String!, $first: Int!, $after: String) {
                repository(owner: $owner, name: $repo) {
                    discussions(first: $first, after: $after, orderBy: {field: CREATED_AT, direction: DESC}) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        nodes {
                            number
                            title
                            body
                            createdAt
                            updatedAt
                            url
                            upvoteCount
                            author {
                                login
                            }
                            category {
                                name
                                slug
                            }
                            answer {
                                id
                                createdAt
                                author {
                                    login
                                }
                            }
                            comments {
                                totalCount
                            }
                            labels(first: 10) {
                                nodes {
                                    name
                                }
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                "owner": owner,
                "repo": repo,
                "first": 100,  # Max allowed
                "after": cursor
            }
            
            try:
                data = self._make_graphql_request(query, variables)
                
                repo_data = data["data"]["repository"]
                if not repo_data or not repo_data["discussions"]:
                    break
                
                discussions_data = repo_data["discussions"]
                discussions_batch = discussions_data["nodes"]
                
                # Filter discussions that are actually from our time period
                # (GitHub doesn't support filtering by createdAt in GraphQL)
                for discussion in discussions_batch:
                    created_at = datetime.fromisoformat(discussion["createdAt"].replace('Z', '+00:00'))
                    if created_at >= since_date:
                        all_discussions.append(discussion)
                    else:
                        # If we hit a discussion older than our cutoff, stop fetching
                        has_next_page = False
                        break
                
                # Check if we should continue pagination
                page_info = discussions_data["pageInfo"]
                has_next_page = has_next_page and page_info["hasNextPage"]
                cursor = page_info["endCursor"]
                
            except Exception as e:
                print(f"Error fetching discussions: {e}")
                break
        
        return all_discussions
    
    def generate_metrics_report(self, owner: str, repo: str, output_file: str = None) -> str:
        """Generate a markdown report of discussions metrics"""
        metrics = self.fetch_discussions_metrics(owner, repo)
        
        # Generate markdown report
        report = f"""# GitHub Discussions Metrics Report

**Repository:** {owner}/{repo}  
**Analysis Period:** {metrics.period_start} to {metrics.period_end}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

## 📊 Overview

- **Total Discussions:** {metrics.total_discussions:,}
- **Discussions This Week:** {metrics.discussions_this_week:,}
- **Discussions Last Week:** {metrics.discussions_last_week:,}
- **Week-over-Week Change:** {metrics.week_over_week_change:+d} ({metrics.week_over_week_percentage:+.1f}%)
- **Average Upvotes:** {metrics.avg_upvotes:.1f}

## 📈 Weekly Trends

"""

        if metrics.week_over_week_percentage > 0:
            report += f"📈 **Growth:** Discussions increased by {metrics.week_over_week_percentage:.1f}% this week\n\n"
        elif metrics.week_over_week_percentage < 0:
            report += f"📉 **Decline:** Discussions decreased by {abs(metrics.week_over_week_percentage):.1f}% this week\n\n"
        else:
            report += f"➡️ **Stable:** No change in discussion count this week\n\n"

        # Q&A Metrics (including Help discussions)
        report += f"""## ❓ Q&A / Help Discussion Metrics

- **Total Unanswered Q&A/Help:** {metrics.total_unanswered_qa:,}
- **Answer Rate:** {metrics.answer_rate:.1f}%

"""

        if metrics.unanswered_qa:
            report += "### 🔍 Recent Unanswered Q&A/Help Discussions\n\n"
            report += "| Discussion | Author | Created | Upvotes |\n"
            report += "|------------|---------|---------|----------|\n"
            
            for qa in metrics.unanswered_qa[:20]:  # Show top 20
                created = datetime.fromisoformat(qa['createdAt'].replace('Z', '+00:00'))
                from datetime import timezone
                now_utc = datetime.now(timezone.utc)
                days_ago = (now_utc - created).days
                age_str = f"{days_ago}d ago" if days_ago > 0 else "today"
                
                report += f"| [#{qa['number']}: {qa['title'][:50]}...]({qa['url']}) | @{qa['author']} | {age_str} | {qa['upvoteCount']} |\n"
        
        # Top Upvoted
        report += f"\n## ⭐ Top Upvoted Discussions\n\n"
        report += "| Discussion | Category | Author | Upvotes | Answered |\n"
        report += "|------------|----------|---------|---------|----------|\n"
        
        for disc in metrics.top_upvoted[:15]:  # Show top 15
            answered = "✅" if disc['hasAnswer'] else "❌"
            report += f"| [#{disc['number']}: {disc['title'][:50]}...]({disc['url']}) | {disc['category']} | @{disc['author']} | {disc['upvoteCount']} | {answered} |\n"
        
        # Category Breakdown
        report += f"\n## 📂 Discussion Categories\n\n"
        
        sorted_categories = sorted(metrics.category_breakdown.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories:
            percentage = (count / metrics.total_discussions) * 100 if metrics.total_discussions > 0 else 0
            report += f"- **{category}:** {count:,} discussions ({percentage:.1f}%)\n"
        
        # Quick Actions
        if metrics.unanswered_qa:
            report += f"\n## 🚀 Quick Actions\n\n"
            report += f"### Address Unanswered Q&A/Help\n\n"
            report += f"Consider reviewing and answering these {metrics.total_unanswered_qa} unanswered Q&A/Help discussions:\n\n"
            
            for qa in metrics.unanswered_qa[:10]:
                report += f"- [#{qa['number']}: {qa['title']}]({qa['url']})\n"
            
            if len(metrics.unanswered_qa) > 10:
                # Create search URLs for both Q&A and Help categories
                help_url = f"https://github.com/{owner}/{repo}/discussions?discussions_q=category%3AHelp+is%3Aunanswered"
                qa_url = f"https://github.com/{owner}/{repo}/discussions?discussions_q=category%3AQ%26A+is%3Aunanswered"
                report += f"\n[View all unanswered Help discussions →]({help_url})  \n"
                report += f"[View all unanswered Q&A discussions →]({qa_url})\n"
        
        report += f"\n---\n_Generated by [deja-view](https://github.com/bdougie/deja-view) discussions metrics_\n"
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
        
        return report
    
    def get_json_metrics(self, owner: str, repo: str) -> Dict:
        """Get metrics as JSON data"""
        metrics = self.fetch_discussions_metrics(owner, repo)
        return asdict(metrics)


def main():
    """CLI entry point for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python discussions_metrics.py owner/repo [output_file.md]")
        sys.exit(1)
    
    try:
        repo_arg = sys.argv[1]
        owner, repo = repo_arg.split('/')
        
        output_file = sys.argv[2] if len(sys.argv) > 2 else f"{owner}-{repo}-discussions-metrics.md"
        
        service = DiscussionsMetricsService()
        report = service.generate_metrics_report(owner, repo, output_file)
        
        print(f"✅ Discussions metrics report generated: {output_file}")
        print(f"\nPreview:")
        print("=" * 50)
        print(report[:1000] + "..." if len(report) > 1000 else report)
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Make sure to set GITHUB_TOKEN environment variable")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating metrics: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()