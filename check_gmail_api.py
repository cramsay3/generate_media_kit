#!/usr/bin/env python3
"""Check if Gmail API is properly configured."""
import json
import sys

try:
    with open('credentials.json', 'r') as f:
        creds = json.load(f)
    
    project_id = creds.get('installed', {}).get('project_id', 'N/A')
    client_id = creds.get('installed', {}).get('client_id', 'N/A')
    
    print("=" * 60)
    print("Gmail API Configuration Check")
    print("=" * 60)
    print(f"\nProject ID: {project_id}")
    print(f"Client ID: {client_id[:50]}...")
    print("\nNext steps:")
    print(f"1. Enable Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com?project={project_id}")
    print(f"2. Configure OAuth: https://console.cloud.google.com/apis/credentials/consent?project={project_id}")
    print("\nSee FIX_OAUTH.md for detailed instructions.")
    print("=" * 60)
    
except FileNotFoundError:
    print("ERROR: credentials.json not found")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
