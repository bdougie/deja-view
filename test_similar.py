#!/usr/bin/env python3
"""Test script to debug the similar issues finder."""

import os
from github import Github

# Test GitHub connection
github_token = os.environ.get('GITHUB_TOKEN')
if not github_token:
    print("No GITHUB_TOKEN found")
    exit(1)

print(f"Token length: {len(github_token)}")

try:
    g = Github(github_token)
    user = g.get_user()
    print(f"Authenticated as: {user.login}")
    
    repo = g.get_repo("continuedev/continue")
    print(f"Repository: {repo.full_name}")
    print(f"Open issues: {repo.open_issues_count}")
    
    # Try to get first issue
    issues = repo.get_issues(state='open')
    first_issue = next(iter(issues), None)
    if first_issue:
        print(f"First issue: #{first_issue.number} - {first_issue.title}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()