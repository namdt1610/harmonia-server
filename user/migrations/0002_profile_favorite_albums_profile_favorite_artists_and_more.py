# Generated by Django 5.1.7 on 2025-03-23 04:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0009_alter_album_options_alter_artist_options_and_more'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='favorite_albums',
            field=models.ManyToManyField(blank=True, related_name='favorited_by', to='music.album'),
        ),
        migrations.AddField(
            model_name='profile',
            name='favorite_artists',
            field=models.ManyToManyField(blank=True, related_name='favorited_by', to='music.artist'),
        ),
        migrations.AddField(
            model_name='profile',
            name='favorite_tracks',
            field=models.ManyToManyField(blank=True, related_name='favorited_by', to='music.track'),
        ),
    ]
