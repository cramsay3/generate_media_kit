#!/usr/bin/env python3
"""
Spotify API authentication handler.
Handles OAuth 2.0 Authorization Code Flow for Spotify Web API.
"""

import os
import json
from typing import Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SpotifyAuth:
    """Handle Spotify OAuth authentication and token management."""
    
    # Required scopes for playlist creation
    SCOPES = [
        'playlist-modify-public',
        'playlist-modify-private',
        'user-read-private',
        'user-read-email'
    ]
    
    def __init__(self, token_file: str = 'spotify_token.json'):
        """
        Initialize Spotify authentication.
        
        Args:
            token_file: Path to store/load OAuth token
        """
        self.token_file = token_file
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        # Use 127.0.0.1:8080/callback (matches Spotify Dashboard)
        self.redirect_uri = 'http://127.0.0.1:8080/callback'
        self.sp = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Spotify API credentials not found!\n"
                "Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in ~/.env\n"
                "Get credentials from: https://developer.spotify.com/dashboard"
            )
    
    def authenticate(self) -> spotipy.Spotify:
        """
        Authenticate with Spotify API using OAuth 2.0.
        Uses cached token if available and valid, otherwise prompts for authorization.
        
        Returns:
            Authenticated spotipy.Spotify client
        """
        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=self.token_file)
        
        auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=' '.join(self.SCOPES),
            cache_handler=cache_handler,
            show_dialog=False  # Don't force re-auth if token exists
        )
        
        # Check if we have a valid cached token
        if auth_manager.validate_token(cache_handler.get_cached_token()):
            print("  ✓ Using cached Spotify token")
        else:
            print("  ⚠ No valid token found, opening browser for authorization...")
            print(f"  → Redirect URI: {self.redirect_uri}")
            print("  → Make sure this URI is added to your Spotify app settings!")
        
        # Get access token (will prompt if needed)
        try:
            token_info = auth_manager.get_access_token()
            if not token_info:
                raise Exception("Failed to get access token")
        except Exception as e:
            raise Exception(
                f"Spotify authentication failed: {e}\n"
                "Make sure:\n"
                "1. SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are set in ~/.env\n"
                f"2. Redirect URI '{self.redirect_uri}' is added to your Spotify app settings\n"
                "3. You have internet connectivity"
            )
        
        # Create Spotify client
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Verify authentication by getting current user
        try:
            user = self.sp.current_user()
            print(f"  ✓ Authenticated as: {user['display_name']} ({user['id']})")
        except Exception as e:
            raise Exception(f"Failed to verify authentication: {e}")
        
        return self.sp
    
    def get_client(self) -> spotipy.Spotify:
        """
        Get authenticated Spotify client.
        Authenticates if not already authenticated.
        
        Returns:
            Authenticated spotipy.Spotify client
        """
        if not self.sp:
            return self.authenticate()
        return self.sp
