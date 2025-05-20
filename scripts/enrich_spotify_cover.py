import requests
from tracks.models import Track
from django.core.files.base import ContentFile
from .spotify_config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

def get_spotify_token():
    resp = requests.post(
        'https://accounts.spotify.com/api/token',
        data={'grant_type': 'client_credentials'},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    resp.raise_for_status()
    return resp.json()['access_token']

def get_spotify_cover(track_title, artist_name, token):
    query = f"{track_title} {artist_name}"
    url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1"
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return None
    items = resp.json().get('tracks', {}).get('items', [])
    if items:
        images = items[0]['album']['images']
        if images:
            return images[0]['url']  # ảnh lớn nhất
    return None

def download_and_save_image(url, track):
    resp = requests.get(url)
    if resp.status_code == 200:
        track.track_thumbnail.save(
            f"{track.id}_spotify.jpg",
            ContentFile(resp.content),
            save=True
        )

def enrich_tracks_with_spotify_cover():
    token = get_spotify_token()
    for track in Track.objects.filter(track_thumbnail__isnull=True):
        cover_url = get_spotify_cover(track.title, track.artist.name, token)
        if cover_url:
            download_and_save_image(cover_url, track)
            print(f"Updated cover for {track.title}")
        else:
            print(f"No cover found for {track.title}")

# Để chạy script này:
# python manage.py shell
# >>> from scripts.enrich_spotify_cover import enrich_tracks_with_spotify_cover
# >>> enrich_tracks_with_spotify_cover() 