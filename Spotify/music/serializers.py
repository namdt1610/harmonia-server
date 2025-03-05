from rest_framework import serializers
from .models import Artist, Album, Track, Playlist

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = '__all__'

class AlbumSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer()

    class Meta:
        model = Album
        fields = '__all__'

class TrackSerializer(serializers.ModelSerializer):
    album = serializers.PrimaryKeyRelatedField(queryset=Album.objects.all(), required=False)
    artist = serializers.PrimaryKeyRelatedField(queryset=Artist.objects.all())

    class Meta:
        model = Track
        fields = '__all__'
        print(Track._meta.get_field('duration').help_text)
        
    # def validate_artist(self, value):
    #     print(f"Artist value received: {value}")
    #     if value is None:
    #         raise serializers.ValidationError("Artist cannot be null.")
    #     try:
    #         return int(value)
    #     except ValueError:
    #         raise serializers.ValidationError("Artist must be a valid number.")
    
    def validate_duration(self, value):
        print(f"Duration value received: {value}")
        if value is None:
            raise serializers.ValidationError("Duration cannot be null.")
        try:
            return int(value) 
        except ValueError:
            raise serializers.ValidationError("Duration must be a valid number.")

class PlaylistSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    tracks = TrackSerializer(many=True)

    class Meta:
        model = Playlist
        fields = '__all__'
