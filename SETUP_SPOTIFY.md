# Spotify API Setup Instructions

## Step 1: Get Spotify API Credentials

1. **Go to Spotify Developer Dashboard**
   - Visit: https://developer.spotify.com/dashboard
   - Log in with your Spotify account

2. **Create a New App**
   - Click "Create an App"
   - Fill in:
     - **App Name**: e.g., "Playlist Generator"
     - **App Description**: e.g., "Automated playlist creation tool"
     - Check "I understand and agree to Spotify's Developer Terms of Service"
   - Click **CREATE**

3. **Get Your Credentials**
   - After creation, you'll see your app dashboard
   - Find:
     - **Client ID** (copy this)
     - **Client Secret** (click "SHOW CLIENT SECRET" and copy)

4. **Configure Redirect URI**
   - Click **Edit Settings**
   - Under **Redirect URIs**, add:
     ```
     http://localhost:8080
     ```
   - Click **ADD**
   - Click **SAVE**

## Step 2: Add Credentials to .env

Add these lines to your `~/.env` file:

```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

**Important:** 
- Replace `your_client_id_here` and `your_client_secret_here` with your actual credentials
- Never share your Client Secret publicly
- The `.env` file is already in `.gitignore` so it won't be committed

## Step 3: Install Dependencies

```bash
cd /home/ubuntu/projects/generate_media_kit
pip install -r requirements.txt
```

This will install `spotipy` and other dependencies.

## Step 4: Test Authentication

Run a test to verify your credentials work:

```bash
python3 -c "from spotify_auth import SpotifyAuth; auth = SpotifyAuth(); auth.authenticate()"
```

On first run, this will:
1. Open your browser
2. Ask you to log in to Spotify
3. Ask for permission to access your account
4. Save the token to `spotify_token.json`

**If you see:** `✓ Authenticated as: [Your Name] ([Your ID])`
**Then you're all set!**

## Troubleshooting

### "Redirect URI mismatch"
- Make sure `http://localhost:8080` is added in Spotify Dashboard → Edit Settings → Redirect URIs
- Make sure there are no trailing slashes or extra characters

### "Invalid client credentials"
- Double-check `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `~/.env`
- Make sure there are no extra spaces or quotes
- Restart your terminal after editing `.env`

### "Failed to get access token"
- Check internet connectivity
- Verify credentials are correct
- Try deleting `spotify_token.json` and re-authenticating

## Next Steps

Once authentication works, you can:
1. Create your CSV file (see `example_playlists.csv`)
2. Run: `python3 create_spotify_playlists.py --csv your_playlists.csv --dry-run`
3. Then run without `--dry-run` to create playlists

See `SPOTIFY_PLAYLIST_USAGE.md` for full usage instructions.
