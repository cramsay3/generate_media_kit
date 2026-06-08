#!/usr/bin/env python3
"""
Core Spotify playlist creation logic.
Handles playlist creation, track searching, and track addition.
"""

import random
import time
from typing import List, Optional, Dict
import spotipy
from spotipy.exceptions import SpotifyException
from spotify_auth import SpotifyAuth


class SpotifyPlaylistCreator:
    """Create and manage Spotify playlists."""
    
    def __init__(self, token_file: str = 'spotify_token.json'):
        """
        Initialize playlist creator.
        
        Args:
            token_file: Path to Spotify OAuth token file
        """
        self.auth = SpotifyAuth(token_file=token_file)
        self.sp: Optional[spotipy.Spotify] = None
        self.user_id: Optional[str] = None
        self.api_calls = []  # Track API calls for rate limiting
        self.last_request_time = 0
    
    def authenticate(self) -> spotipy.Spotify:
        """
        Authenticate with Spotify and get user ID.
        
        Returns:
            Authenticated spotipy.Spotify client
        """
        self.sp = self.auth.authenticate()
        
        # Get user ID
        user = self.sp.current_user()
        self.user_id = user['id']
        
        return self.sp
    
    def _rate_limit_delay(self, min_delay: float = 0.5):
        """
        Add delay between API calls to respect rate limits.
        
        Args:
            min_delay: Minimum delay in seconds
        """
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _handle_rate_limit(self, e: SpotifyException, retry_count: int = 0) -> bool:
        """
        Handle rate limit errors with exponential backoff.
        
        Args:
            e: SpotifyException that occurred
            retry_count: Number of retries attempted
        
        Returns:
            True if should retry, False otherwise
        """
        if e.http_status == 429:
            # Get retry-after from response headers
            retry_after = int(e.headers.get('Retry-After', 30))
            wait_time = min(retry_after * (2 ** retry_count), 300)  # Max 5 minutes
            
            print(f"  ⚠ Rate limited! Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
            return True
        return False
    
    def create_playlist(self, name: str, description: str = "", public: bool = True) -> Dict:
        """
        Create a new Spotify playlist.
        
        Args:
            name: Playlist name
            description: Playlist description
            public: Whether playlist is public
        
        Returns:
            Playlist object with id, name, etc.
        """
        if not self.sp:
            self.authenticate()
        
        self._rate_limit_delay(min_delay=1.0)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                playlist = self.sp.user_playlist_create(
                    user=self.user_id,
                    name=name,
                    public=public,
                    description=description
                )
                print(f"  ✓ Created playlist: {name} (ID: {playlist['id']})")
                return playlist
            except SpotifyException as e:
                if self._handle_rate_limit(e, attempt):
                    continue
                raise Exception(f"Failed to create playlist '{name}': {e}")
        
        raise Exception(f"Failed to create playlist '{name}' after {max_retries} attempts")
    
    def search_artist_tracks(self, artist_name: str, limit: int = 20) -> List[Dict]:
        """
        Search for an artist and get their top tracks.
        
        Args:
            artist_name: Name of the artist
            limit: Maximum number of tracks to return
        
        Returns:
            List of track objects with uri, name, artists, etc.
        """
        if not self.sp:
            self.authenticate()
        
        self._rate_limit_delay(min_delay=0.5)
        
        try:
            # First, search for the artist
            results = self.sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
            
            if not results['artists']['items']:
                print(f"  ⚠ Artist not found: {artist_name}")
                return []
            
            artist = results['artists']['items'][0]
            artist_id = artist['id']
            
            # Get artist's top tracks
            self._rate_limit_delay(min_delay=0.5)
            top_tracks = self.sp.artist_top_tracks(artist_id)
            
            tracks = top_tracks.get('tracks', [])
            
            # Limit to requested number
            tracks = tracks[:limit]
            
            print(f"  ✓ Found {len(tracks)} tracks for {artist_name}")
            return tracks
            
        except SpotifyException as e:
            if e.http_status == 429:
                self._handle_rate_limit(e)
                return self.search_artist_tracks(artist_name, limit)
            print(f"  ⚠ Error searching for {artist_name}: {e}")
            return []
    
    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str], position: Optional[int] = None):
        """
        Add tracks to a playlist.
        
        Args:
            playlist_id: Spotify playlist ID
            track_uris: List of track URIs (spotify:track:xxx)
            position: Position to insert tracks (None = append)
        """
        if not self.sp:
            self.authenticate()
        
        if not track_uris:
            return
        
        # Spotify API allows max 100 tracks per request
        batch_size = 100
        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i + batch_size]
            
            self._rate_limit_delay(min_delay=0.5)
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if position is not None:
                        self.sp.playlist_add_items(
                            playlist_id=playlist_id,
                            items=batch,
                            position=position + i
                        )
                    else:
                        self.sp.playlist_add_items(
                            playlist_id=playlist_id,
                            items=batch
                        )
                    break
                except SpotifyException as e:
                    if self._handle_rate_limit(e, attempt):
                        continue
                    print(f"  ⚠ Error adding tracks to playlist: {e}")
                    raise
            
            print(f"  ✓ Added {len(batch)} tracks to playlist")
    
    def get_user_tracks(self, artist_id: str = None) -> List[Dict]:
        """
        Get tracks from user's artist profile.
        
        Args:
            artist_id: Spotify artist ID (if None, extracts from config)
        
        Returns:
            List of track objects
        """
        if not self.sp:
            self.authenticate()
        
        if not artist_id:
            # Artist ID should be passed from main script
            return []
        
        self._rate_limit_delay(min_delay=0.5)
        
        try:
            # Get artist's albums
            albums = self.sp.artist_albums(artist_id, album_type='album,single', limit=50)
            
            all_tracks = []
            for album in albums['items']:
                self._rate_limit_delay(min_delay=0.5)
                album_tracks = self.sp.album_tracks(album['id'])
                all_tracks.extend(album_tracks['items'])
            
            # Remove duplicates (same track in multiple albums)
            seen_uris = set()
            unique_tracks = []
            for track in all_tracks:
                uri = track['track']['uri'] if 'track' in track else track['uri']
                if uri not in seen_uris:
                    seen_uris.add(uri)
                    unique_tracks.append(track['track'] if 'track' in track else track)
            
            print(f"  ✓ Found {len(unique_tracks)} tracks from artist profile")
            return unique_tracks
            
        except SpotifyException as e:
            if e.http_status == 429:
                self._handle_rate_limit(e)
                return self.get_user_tracks(artist_id)
            print(f"  ⚠ Error getting user tracks: {e}")
            return []
    
    def build_playlist_tracks(
        self,
        similar_artists: List[str],
        user_song_uris: List[str],
        num_tracks: int = 30,
        user_song_position: Optional[int] = None
    ) -> List[str]:
        """
        Build a list of track URIs for a playlist.
        
        Args:
            similar_artists: List of artist names to include
            user_song_uris: List of user's track URIs to include
            num_tracks: Target number of tracks
            user_song_position: Position to insert user's songs (None = random)
        
        Returns:
            List of track URIs in order
        """
        all_tracks = []
        
        # Get tracks from similar artists
        tracks_per_artist = max(2, num_tracks // len(similar_artists)) if similar_artists else 0
        
        for artist in similar_artists:
            tracks = self.search_artist_tracks(artist, limit=tracks_per_artist)
            for track in tracks:
                all_tracks.append(track['uri'])
        
        # Shuffle to mix artists
        random.shuffle(all_tracks)
        
        # Determine user song position
        if user_song_position is None:
            # Insert user songs at random positions, but not all at the start
            user_song_position = random.randint(max(1, num_tracks // 10), num_tracks // 3)
        
        # Insert user songs
        for uri in user_song_uris:
            if uri not in all_tracks:
                all_tracks.insert(user_song_position, uri)
                user_song_position += 1
        
        # Trim to target number
        all_tracks = all_tracks[:num_tracks]
        
        return all_tracks
