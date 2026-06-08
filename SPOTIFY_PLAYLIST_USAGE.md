# Spotify Playlist Generator Usage Guide

## Overview

Automated script to create Spotify playlists based on CSV configuration files. Each playlist includes tracks from similar Americana/alt-country artists plus your own songs, with rate limiting to avoid bot detection.

## Prerequisites

1. **Spotify Developer Account**
   - Go to https://developer.spotify.com/dashboard
   - Create a new app
   - Note your **Client ID** and **Client Secret**
   - Add redirect URI: `http://localhost:8080`

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Credentials**
   Add to `~/.env`:
   ```bash
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```

## Configuration

### config.yaml

The script reads Spotify settings from `config.yaml`:

```yaml
spotify:
  similar_artists:
    - "Jason Isbell"
    - "Sturgill Simpson"
    # ... etc
  user_songs:
    - "spotify:track:2oSf87Lb4R5BrvN5n7IJKG"  # Your track URIs
  default_num_tracks: 30
  default_public: true
  min_delay_seconds: 5
  max_delay_seconds: 10
  max_per_hour: 10
  max_per_day: 50
```

### CSV File Format

Create a CSV file with playlist configurations:

**Required columns:**
- `playlist_name` - Name of the playlist

**Optional columns:**
- `description` - Playlist description
- `public` - `true` or `false` (default: `true`)
- `num_tracks` - Target number of tracks (default: 30)
- `user_song_uri` - Specific Spotify URI of your song to include (e.g., `spotify:track:2oSf87Lb4R5BrvN5n7IJKG`)
- `user_song_position` - Position to insert your song (default: random)

**Example CSV (`playlists.csv`):**
```csv
playlist_name,description,public,num_tracks,user_song_uri,user_song_position
"Americana Vibes","Curated Americana tracks",true,30,,
"Road Trip Mix","Perfect for long drives",true,25,spotify:track:2oSf87Lb4R5BrvN5n7IJKG,5
```

## Usage

### Basic Usage

```bash
python3 create_spotify_playlists.py --csv playlists.csv
```

### Command-Line Options

- `--csv FILE` - CSV file with playlist configurations (required)
- `--count N` - Override CSV, create only first N playlists
- `--config FILE` - Config file path (default: `config.yaml`)
- `--dry-run` - Test without creating playlists
- `--resume` - Resume from previous run (skip already created playlists)

### Examples

**Test run (no playlists created):**
```bash
python3 create_spotify_playlists.py --csv playlists.csv --dry-run
```

**Create first 5 playlists:**
```bash
python3 create_spotify_playlists.py --csv playlists.csv --count 5
```

**Resume interrupted run:**
```bash
python3 create_spotify_playlists.py --csv playlists.csv --resume
```

## First Run Authentication

On first run, the script will:
1. Open your browser for Spotify authorization
2. Ask you to log in and authorize the app
3. Save the token to `spotify_token.json` for future runs

**Important:** Make sure `http://localhost:8080` is added to your Spotify app's redirect URIs in the developer dashboard!

## Rate Limiting

The script implements conservative rate limiting to avoid bot detection:

- **Delay between playlists:** 5-10 seconds (randomized)
- **Max per hour:** 10 playlists
- **Max per day:** 50 playlists

These limits can be adjusted in `config.yaml` under `spotify` section.

## Progress Tracking

The script saves progress to `spotify_playlist_progress.json`:
- Tracks created playlists
- Tracks failed playlists
- Rate limit counters
- Allows resumption with `--resume` flag

## Logging

All activity is logged to `spotify_playlist.log` with timestamps.

## Troubleshooting

### Authentication Errors

**"Failed to get access token"**
- Check that `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are set in `~/.env`
- Verify redirect URI `http://localhost:8080` is added in Spotify dashboard
- Delete `spotify_token.json` and try again

**"Redirect URI mismatch"**
- Go to Spotify Developer Dashboard
- Edit your app settings
- Add `http://localhost:8080` to Redirect URIs

### Rate Limit Errors

**"Rate limited! Waiting X seconds..."**
- The script automatically handles rate limits
- It will wait and retry automatically
- Consider reducing `max_per_hour` in config if this happens frequently

### Artist Not Found

**"Artist not found: [name]"**
- Check artist name spelling in `config.yaml`
- Some artists may have different names on Spotify
- Search Spotify manually to verify the exact artist name

### No Tracks Found

**"No tracks found for playlist"**
- Check that similar artists in config are valid
- Verify you have internet connectivity
- Check Spotify API status

## Best Practices

1. **Start Small**: Test with `--count 1` or `--dry-run` first
2. **Gradual Scaling**: Don't create 50 playlists at once - spread them out
3. **Monitor Logs**: Check `spotify_playlist.log` for issues
4. **Resume Capability**: Use `--resume` if script is interrupted
5. **Unique Names**: Use descriptive, unique playlist names
6. **Variety**: Mix up playlist descriptions and track counts

## Files Created

- `spotify_token.json` - OAuth token (auto-generated)
- `spotify_playlist_progress.json` - Progress tracking
- `spotify_playlist.log` - Activity log

## Getting Your Track URIs

To find your track URI on Spotify:
1. Open Spotify (web or desktop)
2. Right-click on your track
3. Select "Share" → "Copy Song Link"
4. The URI format is: `spotify:track:TRACK_ID`
5. Or extract from URL: `https://open.spotify.com/track/TRACK_ID`

## Support

For issues:
1. Check `spotify_playlist.log` for error messages
2. Verify credentials in `~/.env`
3. Test authentication: `python3 -c "from spotify_auth import SpotifyAuth; SpotifyAuth().authenticate()"`
4. Check Spotify API status: https://status.spotify.com/
