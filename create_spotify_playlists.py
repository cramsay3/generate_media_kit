#!/usr/bin/env python3
"""
Automated Spotify playlist creator.
Reads CSV config files and creates playlists with similar artists + user's songs.
Implements rate limiting to avoid bot detection.
"""

import sys
import csv
import random
import time
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yaml
from spotify_playlist_creator import SpotifyPlaylistCreator


# Progress file to track created playlists and resume capability
PROGRESS_FILE = 'spotify_playlist_progress.json'
LOG_FILE = 'spotify_playlist.log'


def log_message(message: str, log_file: str = LOG_FILE):
    """Log a message to file and stdout."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except Exception as e:
        print(f"  ⚠ Failed to write to log: {e}")


def load_config(config_file: str = 'config.yaml') -> Dict:
    """Load configuration from YAML file."""
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        return config
    except Exception as e:
        raise Exception(f"Failed to load config.yaml: {e}")


def load_progress() -> Dict:
    """Load progress from previous run."""
    progress_path = Path(PROGRESS_FILE)
    if not progress_path.exists():
        return {
            'created_playlists': [],
            'failed_playlists': [],
            'last_created_time': None,
            'daily_count': 0,
            'hourly_count': 0,
            'hour_start': None
        }
    
    try:
        with open(progress_path, 'r', encoding='utf-8') as f:
            progress = json.load(f)
            # Reset daily/hourly counts if it's a new day/hour
            now = datetime.now()
            if progress.get('last_created_time'):
                last_created = datetime.fromisoformat(progress['last_created_time'])
                if (now - last_created).days >= 1:
                    progress['daily_count'] = 0
                if progress.get('hour_start'):
                    hour_start = datetime.fromisoformat(progress['hour_start'])
                    if (now - hour_start).total_seconds() >= 3600:  # 1 hour
                        progress['hourly_count'] = 0
                        progress['hour_start'] = now.isoformat()
            return progress
    except Exception as e:
        log_message(f"  ⚠ Failed to load progress: {e}")
        return {
            'created_playlists': [],
            'failed_playlists': [],
            'last_created_time': None,
            'daily_count': 0,
            'hourly_count': 0,
            'hour_start': None
        }


def save_progress(progress: Dict):
    """Save progress to file."""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        log_message(f"  ⚠ Failed to save progress: {e}")


def read_csv_config(csv_file: str) -> List[Dict]:
    """
    Read playlist configuration from CSV file.
    
    Expected columns:
    - playlist_name (required)
    - description (optional)
    - public (optional, default: true)
    - num_tracks (optional, default: 30)
    - user_song_uri (optional)
    - user_song_position (optional)
    """
    playlists = []
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Validate required fields
                if not row.get('playlist_name'):
                    log_message(f"  ⚠ Skipping row: missing playlist_name")
                    continue
                
                playlist_config = {
                    'playlist_name': row['playlist_name'].strip(),
                    'description': row.get('description', '').strip(),
                    'public': row.get('public', 'true').lower() == 'true',
                    'num_tracks': int(row.get('num_tracks', 30)),
                    'user_song_uri': row.get('user_song_uri', '').strip(),
                    'user_song_position': row.get('user_song_position', '').strip()
                }
                
                # Parse user_song_position
                if playlist_config['user_song_position']:
                    try:
                        playlist_config['user_song_position'] = int(playlist_config['user_song_position'])
                    except ValueError:
                        playlist_config['user_song_position'] = None
                else:
                    playlist_config['user_song_position'] = None
                
                playlists.append(playlist_config)
        
        log_message(f"  ✓ Loaded {len(playlists)} playlists from CSV")
        return playlists
        
    except Exception as e:
        raise Exception(f"Failed to read CSV file: {e}")


def check_rate_limits(progress: Dict, config: Dict) -> bool:
    """
    Check if we're within rate limits.
    
    Returns:
        True if within limits, False otherwise
    """
    spotify_config = config.get('spotify', {})
    max_per_hour = spotify_config.get('max_per_hour', 10)
    max_per_day = spotify_config.get('max_per_day', 50)
    
    now = datetime.now()
    
    # Check hourly limit
    if progress['hourly_count'] >= max_per_hour:
        if progress.get('hour_start'):
            hour_start = datetime.fromisoformat(progress['hour_start'])
            time_until_reset = 3600 - (now - hour_start).total_seconds()
            if time_until_reset > 0:
                log_message(f"  ⚠ Hourly limit reached ({max_per_hour}). Wait {int(time_until_reset/60)} minutes.")
                return False
            else:
                # Reset hourly count
                progress['hourly_count'] = 0
                progress['hour_start'] = now.isoformat()
    
    # Check daily limit
    if progress['daily_count'] >= max_per_day:
        log_message(f"  ⚠ Daily limit reached ({max_per_day}). Wait until tomorrow.")
        return False
    
    return True


def create_playlist(
    creator: SpotifyPlaylistCreator,
    playlist_config: Dict,
    similar_artists: List[str],
    default_user_songs: List[str],
    progress: Dict,
    config: Dict,
    dry_run: bool = False
) -> bool:
    """
    Create a single playlist.
    
    Returns:
        True if successful, False otherwise
    """
    name = playlist_config['playlist_name']
    description = playlist_config.get('description', '')
    public = playlist_config.get('public', True)
    num_tracks = playlist_config.get('num_tracks', 30)
    
    # Determine user songs to include (default: 2 songs)
    user_song_uri = playlist_config.get('user_song_uri')
    if user_song_uri:
        # If CSV specifies a song, use it plus one more from defaults
        user_songs = [user_song_uri]
        # Add another song from defaults if available
        for song in default_user_songs:
            if song != user_song_uri and song not in user_songs:
                user_songs.append(song)
                break
        # If we only have 1, try to get another from defaults
        if len(user_songs) == 1 and len(default_user_songs) > 1:
            for song in default_user_songs:
                if song != user_song_uri:
                    user_songs.append(song)
                    break
    else:
        # Use first 2 songs from defaults
        user_songs = default_user_songs[:2] if len(default_user_songs) >= 2 else default_user_songs
    
    user_song_position = playlist_config.get('user_song_position')
    
    if dry_run:
        log_message(f"  [DRY RUN] Would create playlist: {name}")
        log_message(f"    Description: {description}")
        log_message(f"    Public: {public}")
        log_message(f"    Tracks: {num_tracks}")
        log_message(f"    User songs: {user_songs}")
        return True
    
    # Check rate limits
    if not check_rate_limits(progress, config):
        return False
    
    try:
        # Create playlist
        playlist = creator.create_playlist(name=name, description=description, public=public)
        playlist_id = playlist['id']
        
        # Build track list
        log_message(f"  Building track list from {len(similar_artists)} artists...")
        track_uris = creator.build_playlist_tracks(
            similar_artists=similar_artists,
            user_song_uris=user_songs,
            num_tracks=num_tracks,
            user_song_position=user_song_position
        )
        
        if not track_uris:
            log_message(f"  ⚠ No tracks found for playlist {name}")
            return False
        
        # Add tracks to playlist
        log_message(f"  Adding {len(track_uris)} tracks to playlist...")
        creator.add_tracks_to_playlist(playlist_id=playlist_id, track_uris=track_uris)
        
        # Update progress
        now = datetime.now()
        progress['created_playlists'].append({
            'name': name,
            'id': playlist_id,
            'url': playlist.get('external_urls', {}).get('spotify', ''),
            'created_at': now.isoformat()
        })
        progress['last_created_time'] = now.isoformat()
        progress['daily_count'] += 1
        
        if not progress.get('hour_start'):
            progress['hour_start'] = now.isoformat()
        progress['hourly_count'] += 1
        
        save_progress(progress)
        
        log_message(f"  ✓ Successfully created playlist: {name}")
        log_message(f"    URL: {playlist.get('external_urls', {}).get('spotify', 'N/A')}")
        
        return True
        
    except Exception as e:
        log_message(f"  ✗ Failed to create playlist '{name}': {e}")
        progress['failed_playlists'].append({
            'name': name,
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        })
        save_progress(progress)
        return False


def main():
    parser = argparse.ArgumentParser(description='Create Spotify playlists from CSV config')
    parser.add_argument('--csv', required=True, help='CSV file with playlist configurations')
    parser.add_argument('--count', type=int, help='Override CSV, create N playlists')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    parser.add_argument('--dry-run', action='store_true', help='Test without creating playlists')
    parser.add_argument('--resume', action='store_true', help='Resume from progress file')
    
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        log_message(f"ERROR: {e}")
        return 1
    
    spotify_config = config.get('spotify', {})
    similar_artists = spotify_config.get('similar_artists', [])
    user_songs = spotify_config.get('user_songs', [])
    
    # Extract artist ID from config if available
    artist_spotify_link = config.get('artist', {}).get('spotify_link', '')
    artist_id = None
    if artist_spotify_link and 'artist/' in artist_spotify_link:
        # Extract ID from URL: https://open.spotify.com/artist/2s51Onhpd29JvOji1yuCKy
        artist_id = artist_spotify_link.split('artist/')[-1].split('?')[0]
    
    if not similar_artists:
        log_message("ERROR: No similar artists configured in config.yaml")
        return 1
    
    # Load CSV
    try:
        playlists = read_csv_config(args.csv)
    except Exception as e:
        log_message(f"ERROR: {e}")
        return 1
    
    # Override count if specified
    if args.count:
        playlists = playlists[:args.count]
        log_message(f"  Limited to first {args.count} playlists")
    
    # Load progress
    progress = load_progress()
    
    if args.resume:
        created_names = {p['name'] for p in progress.get('created_playlists', [])}
        playlists = [p for p in playlists if p['playlist_name'] not in created_names]
        log_message(f"  Resuming: {len(playlists)} playlists remaining")
    
    if not playlists:
        log_message("  No playlists to create")
        return 0
    
    log_message("=" * 60)
    log_message("SPOTIFY PLAYLIST CREATION")
    log_message("=" * 60)
    log_message(f"Total playlists to create: {len(playlists)}")
    log_message(f"Similar artists: {len(similar_artists)}")
    log_message(f"User songs: {len(user_songs)}")
    if args.dry_run:
        log_message("  [DRY RUN MODE - No playlists will be created]")
    log_message("")
    
    # Initialize creator
    try:
        creator = SpotifyPlaylistCreator()
        if not args.dry_run:
            creator.authenticate()
    except Exception as e:
        log_message(f"ERROR: Authentication failed: {e}")
        return 1
    
    # Rate limiting settings
    min_delay = spotify_config.get('min_delay_seconds', 5)
    max_delay = spotify_config.get('max_delay_seconds', 10)
    
    # Create playlists
    success_count = 0
    fail_count = 0
    
    for i, playlist_config in enumerate(playlists, 1):
        log_message(f"\n[{i}/{len(playlists)}] Processing: {playlist_config['playlist_name']}")
        
        # Rate limiting delay
        if i > 1:
            delay = random.uniform(min_delay, max_delay)
            log_message(f"  Waiting {delay:.1f} seconds (rate limiting)...")
            time.sleep(delay)
        
        success = create_playlist(
            creator=creator,
            playlist_config=playlist_config,
            similar_artists=similar_artists,
            default_user_songs=user_songs,
            progress=progress,
            config=config,
            dry_run=args.dry_run
        )
        
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    log_message("")
    log_message("=" * 60)
    log_message("SUMMARY")
    log_message("=" * 60)
    log_message(f"Successfully created: {success_count}")
    log_message(f"Failed: {fail_count}")
    log_message(f"Total: {len(playlists)}")
    
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
