from django.db import migrations
import os
import shutil
from django.conf import settings

def update_audio_paths(apps, schema_editor):
    Track = apps.get_model('tracks', 'Track')
    for track in Track.objects.all():
        if track.file:
            old_path = track.file.path
            if os.path.exists(old_path):
                # Create new directory if not exists
                new_dir = os.path.join(settings.MEDIA_ROOT, 'content', 'audio', 'original', str(track.artist.id))
                os.makedirs(new_dir, exist_ok=True)
                
                # Copy file to new location
                new_path = os.path.join(new_dir, f"{track.id}_{os.path.basename(track.file.name)}")
                shutil.copy2(old_path, new_path)
                
                # Update file field
                track.file.name = os.path.join('content', 'audio', 'original', str(track.artist.id), f"{track.id}_{os.path.basename(track.file.name)}")
                track.save()

def reverse_update_audio_paths(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('tracks', '0005_update_image_path'),
    ]

    operations = [
        migrations.RunPython(update_audio_paths, reverse_update_audio_paths),
    ] 