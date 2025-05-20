import os
import pytest
import tempfile
from io import BytesIO
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from music.models import Track, Artist, Album, Playlist

# ========== Fixtures ==========

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client():
    client = APIClient()
    user = User.objects.create_user(username='testuser', password='testpass')
    client.force_authenticate(user=user)
    return client, user

@pytest.fixture
def create_artist(db):
    def _create_artist(name="Test Artist"):
        artist = Artist.objects.create(name=name)
        return artist
    return _create_artist

@pytest.fixture
def create_album(create_artist):
    def _create_album(title="Test Album", artist=None):
        if not artist:
            artist = create_artist()
        return Album.objects.create(title=title, artist=artist)
    return _create_album

@pytest.fixture
def create_track(create_artist):
    def _create_track(title="Test Track", artist=None):
        if not artist:
            artist = create_artist()
        return Track.objects.create(title=title, artist=artist)
    return _create_track

@pytest.fixture
def sample_mp3():
    file = BytesIO(b"fake mp3 content")
    file.name = "test.mp3"
    return SimpleUploadedFile("test.mp3", file.read(), content_type="audio/mp3")

# ========== Artist Tests ==========

@pytest.mark.django_db
def test_list_artists(api_client, create_artist):
    # Create test artists
    artist1 = create_artist(name="Artist 1")
    artist2 = create_artist(name="Artist 2")
    
    response = api_client.get("/api/artists/")
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    assert response.data[0]['name'] == "Artist 1"
    assert response.data[1]['name'] == "Artist 2"

@pytest.mark.django_db
def test_create_artist(api_client):
    artist_data = {"name": "New Artist"}
    response = api_client.post("/api/artists/", artist_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert Artist.objects.count() == 1
    assert Artist.objects.first().name == "New Artist"

@pytest.mark.django_db
def test_retrieve_artist(api_client, create_artist):
    artist = create_artist(name="Test Artist")
    
    response = api_client.get(f"/api/artists/{artist.id}/")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == "Test Artist"
    assert response.data['id'] == artist.id

@pytest.mark.django_db
def test_update_artist(api_client, create_artist):
    artist = create_artist(name="Old Name")
    
    response = api_client.put(
        f"/api/artists/{artist.id}/", 
        {"name": "Updated Name"}, 
        format='json'
    )
    
    assert response.status_code == status.HTTP_200_OK
    artist.refresh_from_db()
    assert artist.name == "Updated Name"

@pytest.mark.django_db
def test_delete_artist(api_client, create_artist):
    artist = create_artist()
    
    response = api_client.delete(f"/api/artists/{artist.id}/")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Artist.objects.count() == 0

# ========== Album Tests ==========

@pytest.mark.django_db
def test_list_albums(api_client, create_album):
    album1 = create_album(title="Album 1")
    album2 = create_album(title="Album 2")
    
    response = api_client.get("/api/albums/")
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    assert response.data[0]['title'] == "Album 1"
    assert response.data[1]['title'] == "Album 2"

@pytest.mark.django_db
def test_create_album(api_client, create_artist):
    artist = create_artist()
    album_data = {
        "title": "New Album",
        "artist": artist.id,
    }
    
    response = api_client.post("/api/albums/", album_data, format='json')
    print(response.status_code, response)

    assert response.status_code == status.HTTP_201_CREATED
    assert Album.objects.count() == 1
    assert Album.objects.first().title == "New Album"

@pytest.mark.django_db
def test_retrieve_album(api_client, create_album):
    album = create_album(title="Test Album")
    
    response = api_client.get(f"/api/albums/{album.id}/")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == "Test Album"

# ========== Track Tests ==========

@pytest.mark.django_db
def test_get_tracks(api_client, create_artist, create_track):
    artist = create_artist(name="Artist 1")
    track1 = create_track(title="Track 1", artist=artist)
    track2 = create_track(title="Track 2", artist=artist)

    response = api_client.get("/api/tracks/")
    print(response.status_code, response.data)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    assert response.data[0]['title'] == "Track 2"
    assert response.data[1]['title'] == "Track 1"

@pytest.mark.django_db
def test_create_track(api_client, create_artist):
    artist = create_artist()
    
    test_mp3 = SimpleUploadedFile(
            name="test.mp3",
            content=b"fake mp3 content",
            content_type="audio/mpeg"
      )
    
    track_data = {
        "title": "New Track",
        "artist": artist.id,
        "file": test_mp3,
    }
    
    response = api_client.post("/api/tracks/", track_data, format='multipart')
    print(response.status_code, response.data)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert Track.objects.count() == 1
    assert Track.objects.first().title == "New Track"

@pytest.mark.django_db
def test_search_tracks_by_title(api_client, create_artist, create_track):
    artist = create_artist()
    create_track(title="Rock Song", artist=artist)
    create_track(title="Pop Song", artist=artist)
    create_track(title="Rock Anthem", artist=artist)
    
    response = api_client.get("/api/tracks/", {"search": "Rock"})
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    titles = [track['title'] for track in response.data]
    assert "Rock Song" in titles
    assert "Rock Anthem" in titles
    assert "Pop Song" not in titles

@pytest.mark.django_db
def test_search_tracks_by_artist_name(api_client, create_artist, create_track):
    artist1 = create_artist(name="Queen")
    artist2 = create_artist(name="Michael Jackson")
    
    create_track(title="Bohemian Rhapsody", artist=artist1)
    create_track(title="Radio Gaga", artist=artist1)
    create_track(title="Thriller", artist=artist2)
    
    response = api_client.get("/api/tracks/", {"search": "Queen"})
    print(response.status_code, response.data)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    
    artists = [track['artist_name'] for track in response.data]
    assert all(name == "Queen" for name in artists)

# ========== Playlist Tests ==========

@pytest.mark.django_db
def test_create_playlist(authenticated_client, create_track):
    client, user = authenticated_client
    track1 = create_track(title="Track 1")
    track2 = create_track(title="Track 2")
    
    playlist_data = {
        "name": "My Playlist",
        "tracks": [track1.id, track2.id]
    }
    
    response = client.post("/api/playlists/", playlist_data, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert Playlist.objects.count() == 1
    playlist = Playlist.objects.first()
    assert playlist.name == "My Playlist"
    assert playlist.user == user
    assert playlist.tracks.count() == 2

@pytest.mark.django_db
def test_playlist_requires_authentication(api_client):
    playlist_data = {"name": "Unauthorized Playlist"}
    
    response = api_client.post("/api/playlists/", playlist_data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Playlist.objects.count() == 0

@pytest.mark.django_db
def test_user_can_only_see_own_playlists(authenticated_client, create_track):
    client1, user1 = authenticated_client
    
    # Create a second user with a playlist
    client2 = APIClient()
    user2 = User.objects.create_user(username='otheruser', password='pass')
    client2.force_authenticate(user=user2)
    
    track = create_track()
    
    # Create playlist for first user
    playlist1_data = {"name": "User1 Playlist", "tracks": [track.id]}
    client1.post("/api/playlists/", playlist1_data, format='json')
    
    # Create playlist for second user
    playlist2_data = {"name": "User2 Playlist", "tracks": [track.id]}
    client2.post("/api/playlists/", playlist2_data, format='json')
    
    # First user should only see their playlist
    response1 = client1.get("/api/playlists/")
    print(response1.status_code, response1.data)
    assert response1.status_code == status.HTTP_200_OK
    assert len(response1.data) == 1
    assert response1.data[0]['name'] == "User1 Playlist"
    
    # Second user should only see their playlist
    response2 = client2.get("/api/playlists/")
    print(response2.status_code, response2.data)
    assert response2.status_code == status.HTTP_200_OK
    assert len(response2.data) == 1
    assert response2.data[0]['name'] == "User2 Playlist"

# ========== Upload Tests ==========

@pytest.mark.django_db
def test_upload_track(api_client, create_artist, sample_mp3):
    artist = create_artist()
    
    sample_mp3 = SimpleUploadedFile(
            name="test.mp3",
            content=b"fake mp3 content",
            content_type="audio/mpeg"
      )
    
    data = {
        'title': "Track Title",
        'file': sample_mp3,
        'artist': artist.id,
        'duration': 180  # 3 minutes in seconds
    }
    
    response = api_client.post("/api/upload-tracks/", data, format='multipart')
    print(response.status_code, response.data)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.data
    assert "file" in response.data
    
    # Check that track was created
    track_id = response.data["id"]
    track = Track.objects.get(id=track_id)
    assert track.title == "Track Title"
    assert track.artist == artist
    assert track.duration == 180

@pytest.mark.django_db
def test_upload_requires_file(api_client, create_artist):
    artist = create_artist()
    
    data = {
        'title': "Track Title",
        'artist': artist.id,
        'duration': 180,
        
        
    }
    
    response = api_client.post("/api/upload-tracks/", data, format='multipart')
    print(response.status_code, response)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["file"][0].code == 'required'

@pytest.mark.django_db
def test_upload_requires_artist(api_client, sample_mp3):
      
    sample_mp3 = SimpleUploadedFile(
            name="test.mp3",
            content=b"fake mp3 content",
            content_type="audio/mpeg"
      )  
      
    data = {
        'title': "Track Title",
        'file': sample_mp3,
        'duration': 180
    }
    
    response = api_client.post("/api/upload-tracks/", data, format='multipart')
    print(response.status_code, response.data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['artist'][0].code == 'required'

@pytest.mark.django_db
def test_upload_with_nonexistent_artist(api_client, sample_mp3):
    data = {
        'file': sample_mp3,
        'artist': 999,  # Non-existent artist ID
        'duration': 180
    }
    
    response = api_client.post("/api/upload-tracks/", data, format='multipart')
    print(response.status_code, response.data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Artist not found" in response.data["error"]

# ========== Pagination Tests ==========

@pytest.mark.django_db
def test_tracks_pagination(api_client, create_artist, create_track):
    artist = create_artist()
    
    # Create 15 tracks
    for i in range(15):
        create_track(title=f"Track {i+1}", artist=artist)
    
    # Get first page (default 10 items)
    response = api_client.get("/api/tracks/")
    print(response.status_code, response.data)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 10
    
    # Get second page
    response = api_client.get("/api/tracks/?page=2")
    print(response.status_code, response.data)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 5
    
    # Test custom page size
    response = api_client.get("/api/tracks/?size=5")
    print(response.status_code, response.data)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 5