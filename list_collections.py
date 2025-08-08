#!/usr/bin/env python3
"""List all Chroma collections."""

import os
import chromadb

# Get Chroma credentials
chroma_api_key = os.environ.get('CHROMA_API_KEY')
chroma_tenant = os.environ.get('CHROMA_TENANT')
chroma_database = os.environ.get('CHROMA_DATABASE', 'default-database')

if not chroma_api_key or not chroma_tenant:
    print("Missing Chroma credentials")
    exit(1)

try:
    client = chromadb.CloudClient(
        tenant=chroma_tenant,
        database=chroma_database,
        api_key=chroma_api_key
    )
    
    collections = client.list_collections()
    print(f"Found {len(collections)} collections:")
    for col in collections:
        print(f"  - {col.name} (count: {col.count()})")
        
except Exception as e:
    print(f"Error: {e}")