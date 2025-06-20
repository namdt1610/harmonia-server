from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('playlists', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ] 