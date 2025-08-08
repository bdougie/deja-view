#!/bin/bash

# Deja-View MCP Server Setup Script for Continue
# This script helps set up the MCP server for use with Continue

set -e

echo "==================================="
echo "Deja-View MCP Server Setup"
echo "==================================="
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Install it from: https://docs.astral.sh/uv/"
    echo "Quick install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "✅ uv is installed"

# Check for GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) is not installed"
    echo ""
    echo "GitHub CLI is REQUIRED for deja-view to work."
    echo ""
    echo "Install GitHub CLI:"
    echo "  macOS:    brew install gh"
    echo "  Linux:    See https://github.com/cli/cli#installation"
    echo "  Windows:  winget install --id GitHub.cli"
    echo ""
    echo "After installing, run this setup script again."
    exit 1
fi
echo "✅ GitHub CLI is installed"

# Check GitHub authentication
if ! gh auth status &> /dev/null; then
    echo ""
    echo "❌ GitHub CLI is not authenticated"
    echo ""
    echo "Authentication is REQUIRED for deja-view to work."
    echo "You will now be guided through the authentication process."
    echo ""
    echo "Press Enter to continue with authentication..."
    read -r
    
    echo "Running: gh auth login"
    gh auth login
    
    # Verify authentication succeeded
    if ! gh auth status &> /dev/null; then
        echo ""
        echo "❌ Authentication failed or was cancelled"
        echo "Please run 'gh auth login' manually and then run this setup script again."
        exit 1
    fi
fi

# Get authenticated username
GITHUB_USER=$(gh api user --jq .login 2>/dev/null || echo "unknown")
echo "✅ GitHub CLI is authenticated as: $GITHUB_USER"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
uv pip install -r requirements.txt
echo "✅ Dependencies installed"

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  No .env file found. Creating template..."
    cat > .env << 'EOF'
# Chroma Cloud credentials (get from https://cloud.trychroma.com)
CHROMA_API_KEY=your-chroma-api-key
CHROMA_TENANT=your-tenant-id
CHROMA_DATABASE=default_database

# GitHub token for higher rate limits (optional)
# GITHUB_TOKEN=your-github-token
EOF
    echo "✅ Created .env template"
    echo ""
    echo "⚠️  Please edit .env and add your Chroma Cloud credentials"
    echo "   Get them from: https://cloud.trychroma.com"
    echo ""
fi

# Test MCP server
echo "Testing MCP server..."
if uv run python mcp_server.py --help > /dev/null 2>&1; then
    echo "✅ MCP server is working"
else
    echo "❌ MCP server test failed"
    echo "   Please check your .env configuration"
    exit 1
fi

# Get the current directory
CURRENT_DIR=$(pwd)

# Generate Continue configuration
echo ""
echo "==================================="
echo "Continue Configuration"
echo "==================================="
echo ""
echo "Add this to your Continue config.json file:"
echo "(Usually located at ~/.continue/config.json)"
echo ""
echo "{"
echo '  "mcpServers": ['
echo "    {"
echo '      "name": "deja-view",'
echo '      "command": "uv",'
echo "      \"args\": [\"run\", \"python\", \"$CURRENT_DIR/mcp_server.py\"]"
echo "    }"
echo "  ]"
echo "}"
echo ""
echo "==================================="
echo ""

# Create a test script
cat > test_mcp.py << 'EOF'
#!/usr/bin/env python3
"""Test script to verify MCP server functionality"""

import subprocess
import json
import sys

def test_mcp_server():
    """Test that the MCP server can be initialized and returns tools"""
    try:
        # Try to import the server
        from mcp_server import mcp
        
        # Get available tools
        tools = []
        for tool_name in dir(mcp):
            if not tool_name.startswith('_'):
                attr = getattr(mcp, tool_name)
                if callable(attr) and hasattr(attr, '__doc__'):
                    tools.append(tool_name)
        
        print("✅ MCP Server loaded successfully!")
        print(f"   Available tools: {len(tools)}")
        for tool in tools:
            if not tool.startswith('_') and not tool in ['run', 'description', 'tool']:
                print(f"   - {tool}")
        
        return True
    except Exception as e:
        print(f"❌ Error loading MCP server: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
EOF

echo "Running MCP server test..."
if uv run python test_mcp.py; then
    echo ""
    echo "✅ Setup complete!"
else
    echo ""
    echo "⚠️  Setup completed with warnings"
fi

echo ""
echo "Next steps:"
echo "1. Edit .env file with your Chroma credentials (if not done)"
echo "2. Add the configuration above to your Continue config.json"
echo "3. Restart Continue in VS Code"
echo "4. Test by asking Continue: 'What tools do you have from deja-view?'"
echo ""
echo "For detailed setup instructions, see: MCP_CONTINUE_SETUP.md"