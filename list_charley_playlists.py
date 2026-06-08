#!/usr/bin/env python3
"""
List all playlists containing Charley Ramsay tracks.
"""

from spotify_auth import SpotifyAuth

def main():
    print("=" * 60)
    print("PLAYLISTS CONTAINING 'Charley Ramsay'")
    print("=" * 60)
    print()

    auth = SpotifyAuth()
    sp = auth.get_client()

    # Search for playlists
    playlist_results = sp.search(q='Charley Ramsay', type='playlist', limit=50)
    playlists_found = playlist_results.get('playlists', {}).get('items', [])

    if playlists_found:
        print(f"Found {len(playlists_found)} playlists:\n")
        for i, playlist in enumerate(playlists_found, 1):
            try:
                name = playlist.get('name', 'Unknown')
                owner_info = playlist.get('owner', {})
                owner = owner_info.get('display_name') or owner_info.get('id', 'Unknown')
                
                # Handle tracks count - some playlists don't have this info
                tracks_count = 'N/A'
                if 'tracks' in playlist and playlist['tracks']:
                    tracks_count = playlist['tracks'].get('total', 'N/A')
                
                url = playlist.get('external_urls', {}).get('spotify', 'N/A')
                public = playlist.get('public', 'Unknown')
                
                print(f"{i}. {name}")
                print(f"   Owner: {owner}")
                print(f"   Tracks: {tracks_count}")
                print(f"   Public: {public}")
                print(f"   URL: {url}")
                print()
            except Exception as e:
                print(f"{i}. Error parsing playlist: {e}")
                print()
    else:
        print("No playlists found in search results")

    print("=" * 60)
    print("\nNote: This shows public playlists found via search.")
    print("Private playlists or playlists with few followers may not appear.")

if __name__ == '__main__':
    main()
