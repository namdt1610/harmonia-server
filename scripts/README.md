# Data Population Scripts

This directory contains scripts to populate your database with sample data.

## Spotify Data Importer

The `populate_spotify_data.py` script fetches data from the Spotify Web API and populates your database with artists, albums, tracks, and playlists.

### Prerequisites

1. You need a Spotify Developer account (free)
2. You need to create an app in the Spotify Developer Dashboard
3. You need to get your Client ID and Client Secret from the Spotify Developer Dashboard

### Setup

1. Copy `spotify_config.py.example` to `spotify_config.py`
2. Edit `spotify_config.py` and add your Spotify API credentials:
   ```python
   SPOTIFY_CLIENT_ID = 'your_client_id_here'
   SPOTIFY_CLIENT_SECRET = 'your_client_secret_here'
   ```

### Usage

Run the script from the project root directory:

```bash
python scripts/populate_spotify_data.py
```

Or make it executable first:

```bash
chmod +x scripts/populate_spotify_data.py
./scripts/populate_spotify_data.py
```

### What it does

The script will:

1. Fetch information for popular artists from Spotify
2. Create artist records in your database
3. Fetch albums for each artist
4. Create album records in your database
5. Fetch tracks for each album
6. Create track records in your database (with dummy audio files)
7. Create sample playlists with random tracks

### Limitations

- The script creates dummy audio files since the Spotify API doesn't provide actual audio files
- The image URLs from Spotify might expire eventually
- The API has rate limits, so the script uses delays to avoid hitting them

### Troubleshooting

If you encounter errors:

1. Verify your Spotify API credentials are correct
2. Check your internet connection
3. Make sure you have all required Python packages installed:
   ```bash
   pip install spotipy requests
   ```
4. If you hit rate limits, increase the sleep durations in the script 