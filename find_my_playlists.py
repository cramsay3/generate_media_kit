#!/usr/bin/env python3
"""
Find all playlists containing Charley Ramsay tracks.
Uses multiple methods to find playlists.
"""

from spotify_auth import SpotifyAuth
from collections import defaultdict
import time

def check_playlist_contains_track(sp, playlist_id, track_uris):
    """Check if a playlist contains any of the given track URIs."""
    try:
        # Get playlist tracks
        results = sp.playlist_tracks(playlist_id, limit=100)
        playlist_track_uris = set()
        
        for item in results['items']:
            if item['track']:
                playlist_track_uris.add(item['track']['uri'])
        
        # Check for more pages
        while results['next']:
            results = sp.next(results)
            for item in results['items']:
                if item['track']:
                    playlist_track_uris.add(item['track']['uri'])
        
        # Check if any of our tracks are in this playlist
        found_tracks = []
        for track_uri in track_uris:
            if track_uri in playlist_track_uris:
                found_tracks.append(track_uri)
        
        return found_tracks
    except Exception as e:
        return []

def main():
    print("=" * 60)
    print("FINDING PLAYLISTS WITH CHARLEY RAMSAY TRACKS")
    print("=" * 60)
    print()

    auth = SpotifyAuth()
    sp = auth.get_client()
    user = sp.current_user()
    user_id = user['id']

    # Get Charley Ramsay artist ID
    print("1. Getting Charley Ramsay artist info...")
    results = sp.search(q='artist:"Charley Ramsay"', type='artist', limit=1)
    artist = results['artists']['items'][0]
    artist_id = artist['id']
    artist_name = artist['name']
    print(f"   ✓ Found: {artist_name} (ID: {artist_id})")
    print()

    # Get all tracks
    print("2. Getting all tracks...")
    albums = sp.artist_albums(artist_id, album_type='album,single', limit=50)
    all_tracks = []
    track_uris = []
    track_uri_to_name = {}

    for album in albums['items']:
        album_tracks = sp.album_tracks(album['id'])
        for track_item in album_tracks['items']:
            track = track_item['track'] if 'track' in track_item else track_item
            uri = track['uri']
            if uri not in track_uris:
                track_uris.append(uri)
                track_uri_to_name[uri] = track['name']
                all_tracks.append({
                    'name': track['name'],
                    'uri': uri,
                    'id': track['id']
                })

    print(f"   ✓ Found {len(all_tracks)} unique tracks")
    print()

    # Method 1: Check user's own playlists
    print("3. Checking your own playlists...")
    user_playlists = []
    results = sp.current_user_playlists(limit=50)
    
    for playlist in results['items']:
        user_playlists.append(playlist)
    
    # Get more pages if needed
    while results['next']:
        results = sp.next(results)
        user_playlists.extend(results['items'])
    
    print(f"   ✓ Found {len(user_playlists)} of your playlists")
    
    playlists_with_tracks = defaultdict(list)
    
    for playlist in user_playlists:
        playlist_id = playlist['id']
        print(f"   Checking: {playlist['name']}...", end=' ')
        found_tracks = check_playlist_contains_track(sp, playlist_id, track_uris)
        if found_tracks:
            print(f"✓ Found {len(found_tracks)} tracks")
            for track_uri in found_tracks:
                playlists_with_tracks[playlist_id].append({
                    'playlist': playlist,
                    'track': track_uri_to_name[track_uri]
                })
        else:
            print("  (none)")
        time.sleep(0.2)  # Rate limiting

    # Method 2: Search for playlists by track name (for popular tracks)
    print()
    print("4. Searching public playlists for your tracks...")
    print("   (Checking top tracks only to avoid rate limits)")
    
    top_tracks = sp.artist_top_tracks(artist_id)
    top_track_uris = [t['uri'] for t in top_tracks['tracks'][:5]]
    
    for track in top_tracks['tracks'][:5]:
        track_name = track['name']
        print(f"   Searching for: {track_name}...", end=' ')
        
        try:
            search_results = sp.search(
                q=f'track:"{track_name}" artist:"{artist_name}"',
                type='playlist',
                limit=10
            )
            
            playlists = search_results.get('playlists', {}).get('items', [])
            
            if playlists:
                print(f"Found {len(playlists)} playlists")
                for playlist in playlists:
                    playlist_id = playlist['id']
                    # Skip if already found
                    if playlist_id not in playlists_with_tracks:
                        # Verify it actually contains the track
                        found = check_playlist_contains_track(sp, playlist_id, [track['uri']])
                        if found:
                            playlists_with_tracks[playlist_id].append({
                                'playlist': playlist,
                                'track': track_name
                            })
            else:
                print("  (none)")
        except Exception as e:
            print(f"  Error: {e}")
        
        time.sleep(0.5)  # Rate limiting

    # Results
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print()

    if playlists_with_tracks:
        print(f"Found {len(playlists_with_tracks)} playlists containing your tracks:\n")
        
        for i, (playlist_id, track_list) in enumerate(playlists_with_tracks.items(), 1):
            playlist = track_list[0]['playlist']
            tracks_in_playlist = [t['track'] for t in track_list]
            
            print(f"{i}. {playlist['name']}")
            print(f"   Owner: {playlist['owner'].get('display_name') or playlist['owner'].get('id', 'Unknown')}")
            print(f"   Your tracks: {', '.join(set(tracks_in_playlist))}")
            print(f"   Public: {playlist.get('public', 'Unknown')}")
            print(f"   URL: {playlist['external_urls']['spotify']}")
            print()
    else:
        print("No playlists found containing your tracks.")
        print("\nNote: This only checks:")
        print("  - Your own playlists")
        print("  - Public playlists found via search")
        print("Private playlists owned by others are not accessible via API.")

    print("=" * 60)

if __name__ == '__main__':
    main()
