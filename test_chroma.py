#!/usr/bin/env python3
"""Test Chroma connection."""

import os
import chromadb

# Get Chroma credentials
chroma_api_key = os.environ.get('CHROMA_API_KEY') or os.environ.get('CHROMA_CLOUD_API_KEY')
chroma_tenant = os.environ.get('CHROMA_TENANT')
chroma_database = os.environ.get('CHROMA_DATABASE', 'default-database')
chroma_url = os.environ.get('CHROMA_CLOUD_API_URL', 'api.trychroma.com')

print(f"Chroma URL: {chroma_url}")
print(f"API Key exists: {bool(chroma_api_key)}")
print(f"Tenant: {chroma_tenant}")
print(f"Database: {chroma_database}")

if not chroma_api_key:
    print("No Chroma API key found")
    exit(1)

try:
    # Try to connect
    client = chromadb.HttpClient(
        host=chroma_url,
        port=443,
        ssl=True,
        headers={"Authorization": f"Bearer {chroma_api_key}"},
        tenant=chroma_tenant,
        database=chroma_database
    )
    
    # List collections
    collections = client.list_collections()
    print(f"\nFound {len(collections)} collections:")
    for col in collections[:5]:  # Show first 5
        print(f"  - {col.name}")
    
    # Try to get the continue collection
    collection_name = "continuedev_continue_issues"
    try:
        collection = client.get_collection(collection_name)
        print(f"\nCollection '{collection_name}' found")
        print(f"Collection count: {collection.count()}")
    except Exception as e:
        print(f"\nCollection '{collection_name}' not found: {e}")
        print("You may need to index the repository first")
        
except Exception as e:
    print(f"\nError connecting to Chroma: {e}")
    import traceback
    traceback.print_exc()