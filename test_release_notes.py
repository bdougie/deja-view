#!/usr/bin/env python3
"""Test script for release notes generation."""

import os
from datetime import datetime, timedelta
from release_notes import ReleaseNotesGenerator

def test_release_notes():
    """Test the release notes generation with a sample repository."""
    
    # Check if GitHub token is available
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN not set. Please set it to test.")
        print("You can set it with: export GITHUB_TOKEN=your-github-token")
        return
    
    # Test with a sample repository (you can change this)
    repo = "continuedev/continue"  # Example repo - change to your target repo
    
    # Generate release notes for the last 30 days as an example
    since_date = datetime.now() - timedelta(days=30)
    
    print(f"📝 Testing release notes generation for {repo}")
    print(f"📅 Since: {since_date.date()}")
    
    try:
        generator = ReleaseNotesGenerator()
        
        # Generate release notes
        release_notes = generator.generate_release_notes(
            repo_name=repo,
            since_date=since_date,
            version="v0.1.0-test",
            output_file="test-release-notes.md"
        )
        
        print("\n✅ Release notes generated successfully!")
        print("\nFirst 500 characters of output:")
        print("-" * 50)
        print(release_notes[:500])
        print("-" * 50)
        print(f"\n📄 Full output saved to: test-release-notes.md")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_release_notes()