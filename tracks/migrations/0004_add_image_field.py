from django.db import migrations, models
import tracks.models

class Migration(migrations.Migration):

    dependencies = [
        ('tracks', '0003_alter_track_file_alter_track_track_thumbnail_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='track',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=tracks.models.get_track_image_path),
        ),
        migrations.RemoveField(
            model_name='track',
            name='track_thumbnail',
        ),
    ] 