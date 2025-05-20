from rest_framework import serializers
from .models import Artist, Album, Track, Playlist, Genre, UserActivity
from favorites.models import Favorite

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = '__all__'

class AlbumSerializer(serializers.ModelSerializer):
    artist = serializers.PrimaryKeyRelatedField(queryset=Artist.objects.all())

    class Meta:
        model = Album
        fields = '__all__'

class TrackSerializer(serializers.ModelSerializer):
    album = serializers.PrimaryKeyRelatedField(queryset=Album.objects.all(), required=False)
    artist = serializers.PrimaryKeyRelatedField(queryset=Artist.objects.all())
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    album_title = serializers.CharField(source='album.title', read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    genres_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        source='genres',
        write_only=True,
        required=False,
    )
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Track
        fields = '__all__'
    
    def validate_duration(self, value):
        print(f"Duration value received: {value}")
        if value is None:
            raise serializers.ValidationError("Duration cannot be null.")
        try:
            return int(value) 
        except ValueError:
            raise serializers.ValidationError("Duration must be a valid number.")
        
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, 'id'):
                try:
                    return Favorite.objects.filter(
                        user=request.user, 
                        track_id=obj.id
                    ).exists()
                except Exception as e:
                    print(f"Error checking favorite status: {e}")
                    return False
        return False
    
class TrackSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = ['id', 'title', 'artist', 'album', 'duration', 'file', 'music_video']

class PlaylistSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    tracks = TrackSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = Playlist
        fields = '__all__'

    def get_track_counts(self, obj):
        return obj.tracks.count()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class UserActivitySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    track_title = serializers.CharField(source='track.title', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'username', 'track', 'track_title', 'playlist', 'action', 'timestamp']
        read_only_fields = ['user', 'timestamp']