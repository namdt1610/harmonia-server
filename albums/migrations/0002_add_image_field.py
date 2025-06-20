from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('albums', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='albums/images/'),
        ),
    ] 