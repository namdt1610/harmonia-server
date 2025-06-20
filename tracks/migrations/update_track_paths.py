from django.db import migrations

def update_track_paths(apps, schema_editor):
    Track = apps.get_model('tracks', 'Track')
    for track in Track.objects.all():
        if track.file and track.file.name.startswith('tracks/'):
            # Lấy tên file gốc
            old_filename = track.file.name.split('/')[-1]
            # Tạo đường dẫn mới
            new_path = f"content/audio/original/{track.artist.id}/{track.id}_{old_filename}"
            # Update trong database
            track.file.name = new_path
            track.save()

def reverse_track_paths(apps, schema_editor):
    Track = apps.get_model('tracks', 'Track')
    for track in Track.objects.all():
        if track.file and track.file.name.startswith('content/audio/original/'):
            # Lấy tên file gốc (bỏ prefix)
            old_filename = track.file.name.split('/')[-1]
            # Tạo đường dẫn cũ
            new_path = f"tracks/{old_filename}"
            # Update trong database
            track.file.name = new_path
            track.save()

class Migration(migrations.Migration):
    dependencies = [
        ('tracks', '0001_initial'),  # Thay đổi này thành migration cuối cùng của bạn
    ]

    operations = [
        migrations.RunPython(update_track_paths, reverse_track_paths),
    ] 