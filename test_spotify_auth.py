#!/usr/bin/env python3
"""
Test Spotify API authentication.
"""

import sys
from spotify_auth import SpotifyAuth

def main():
    print("=" * 60)
    print("SPOTIFY API AUTHENTICATION TEST")
    print("=" * 60)
    print()
    
    try:
        print("1. Initializing SpotifyAuth...")
        auth = SpotifyAuth()
        print(f"   ✓ Client ID: {auth.client_id[:10]}...")
        print(f"   ✓ Redirect URI: {auth.redirect_uri}")
        print()
        
        print("2. Authenticating...")
        print("   → This will open your browser for authorization")
        print("   → Please authorize the app when prompted")
        print()
        
        sp = auth.authenticate()
        
        print()
        print("3. Testing API access...")
        user = sp.current_user()
        
        print()
        print("=" * 60)
        print("✓ AUTHENTICATION SUCCESSFUL!")
        print("=" * 60)
        print(f"Display Name: {user['display_name']}")
        print(f"User ID: {user['id']}")
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"Country: {user.get('country', 'N/A')}")
        print(f"Followers: {user.get('followers', {}).get('total', 'N/A')}")
        print()
        print("Token saved to: spotify_token.json")
        print("You can now use the Spotify API!")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠ Authentication cancelled by user")
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ AUTHENTICATION FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check that SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are in .env")
        print("2. Verify redirect URI matches Spotify app settings:")
        print("   Expected: http://localhost:8080/callback")
        print("3. Make sure you authorized the app in the browser")
        print("4. Check internet connectivity")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
