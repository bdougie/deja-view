#!/usr/bin/env python3
"""
GitHub CLI Authentication Helper
Shared utilities for checking and managing GitHub CLI authentication
"""

import subprocess
import sys
import os


def check_gh_cli_installed():
    """Check if GitHub CLI is installed"""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_gh_auth_status():
    """Check if GitHub CLI is authenticated"""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except:
        return False


def get_authenticated_user():
    """Get the authenticated GitHub username"""
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return None


def print_auth_error_message(context="This tool"):
    """Print a friendly error message for authentication issues"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                 GitHub CLI Authentication Required           ║
╚══════════════════════════════════════════════════════════════╝

{context} requires GitHub CLI (gh) to be installed and authenticated.

Follow these steps:

1. Install GitHub CLI:
   • macOS:    brew install gh
   • Linux:    See https://github.com/cli/cli#installation
   • Windows:  winget install --id GitHub.cli

2. Authenticate with GitHub:
   gh auth login

3. Verify authentication:
   gh auth status

After authentication, try running this command again.

For more information: https://cli.github.com/manual/gh_auth_login
""")


def ensure_gh_auth(exit_on_failure=True, context="This tool"):
    """
    Ensure GitHub CLI is installed and authenticated
    
    Args:
        exit_on_failure: If True, exit the program on auth failure
        context: Context string for error messages (e.g., "The CLI", "The API server")
    
    Returns:
        tuple: (is_authenticated, username) - username is None if not authenticated
    """
    # Check if gh is installed
    if not check_gh_cli_installed():
        print(f"❌ Error: GitHub CLI (gh) is not installed")
        print_auth_error_message(context)
        if exit_on_failure:
            sys.exit(1)
        return False, None
    
    # Check if authenticated
    if not check_gh_auth_status():
        print(f"❌ Error: Not authenticated with GitHub CLI")
        print_auth_error_message(context)
        if exit_on_failure:
            sys.exit(1)
        return False, None
    
    # Get username
    username = get_authenticated_user()
    return True, username


def format_auth_check_message(is_authenticated, username=None):
    """Format a nice message about authentication status"""
    if is_authenticated and username:
        return f"✅ Authenticated as: {username}"
    elif is_authenticated:
        return "✅ GitHub CLI is authenticated"
    else:
        return "❌ GitHub CLI authentication required"


if __name__ == "__main__":
    # Test the authentication
    print("Checking GitHub CLI authentication...")
    is_auth, user = ensure_gh_auth(exit_on_failure=False)
    print(format_auth_check_message(is_auth, user))