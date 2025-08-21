#!/usr/bin/env python3
"""Test fetching issues from GitHub."""

import os
from github import Github
import time

github_token = os.environ.get('GITHUB_TOKEN')
if not github_token:
    print("No GITHUB_TOKEN found")
    exit(1)

start = time.time()
g = Github(github_token)
repo = g.get_repo("continuedev/continue")

print(f"Fetching open issues from {repo.full_name}...")
issues = repo.get_issues(state='open')

# Try to get first 10 issues
count = 0
for issue in issues:
    if issue.pull_request:
        continue
    count += 1
    print(f"Issue #{issue.number}: {issue.title[:50]}")
    if count >= 10:
        break

elapsed = time.time() - start
print(f"\nFetched {count} issues in {elapsed:.1f} seconds")