from django.db import migrations
import os
import shutil
from django.conf import settings

def update_image_paths(apps, schema_editor):
    Track = apps.get_model('tracks', 'Track')
    for track in Track.objects.all():
        if track.image:
            old_path = track.image.path
            if os.path.exists(old_path):
                # Create new directory if not exists
                new_dir = os.path.join(settings.MEDIA_ROOT, 'content', 'image', str(track.artist.id))
                os.makedirs(new_dir, exist_ok=True)
                
                # Copy file to new location
                new_path = os.path.join(new_dir, f"{track.id}_{os.path.basename(track.image.name)}")
                shutil.copy2(old_path, new_path)
                
                # Update image field
                track.image.name = os.path.join('content', 'image', str(track.artist.id), f"{track.id}_{os.path.basename(track.image.name)}")
                track.save()

def reverse_update_image_paths(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('tracks', '0004_add_image_field'),
    ]

    operations = [
        migrations.RunPython(update_image_paths, reverse_update_image_paths),
    ] 