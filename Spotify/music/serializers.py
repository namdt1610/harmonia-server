from rest_framework import serializers
from .models import Artist, Album, Track, Playlist, Genre, Favorite, UserActivity

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
            return Favorite.objects.filter(user=request.user, track=obj).exists()
        return False

class PlaylistSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    tracks = serializers.PrimaryKeyRelatedField(many=True, queryset=Track.objects.all(), required=False)

    class Meta:
        model = Playlist
        fields = '__all__'

    def get_tracks_count(self, obj):
        return obj.tracks.count()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class FavoriteSerializer(serializers.ModelSerializer):
    track_details = TrackSerializer(source='track', read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'track', 'track_details', 'created_at']
        read_only_fields = ['user', 'created_at']
    
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