import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from artists.models import Artist

def fix_artist_names():
    # Dictionary mapping incorrect names to correct names
    name_corrections = {
        # Add your corrections here, for example:
        # 'incorrect name': 'correct name',
        'Son Tung M-TP': 'Sơn Tùng M-TP',
        'Hoa Minzy': 'Hòa Minzy',
        'Jack - J97': 'Jack',
        'Mono': 'Mono',
        'Hoang Thuy Linh': 'Hoàng Thùy Linh',
        'Erik': 'Erik',
        'Noo Phuoc Thinh': 'Noo Phước Thịnh',
        'Ho Ngoc Ha': 'Hồ Ngọc Hà',
        'My Tam': 'Mỹ Tâm',
        'Dam Vinh Hung': 'Đàm Vĩnh Hưng',
        'Tuan Hung': 'Tuấn Hưng',
        'Ho Quynh Huong': 'Hồ Quỳnh Hương',
        'Thu Minh': 'Thu Minh',
        'Hoang Yen Chibi': 'Hoàng Yến Chibi',
        'Ho Ngoc Ha': 'Hồ Ngọc Hà',
        'My Tam': 'Mỹ Tâm',
        'Dam Vinh Hung': 'Đàm Vĩnh Hưng',
        'Tuan Hung': 'Tuấn Hưng',
        'Ho Quynh Huong': 'Hồ Quỳnh Hương',
        'Thu Minh': 'Thu Minh',
        'Hoang Yen Chibi': 'Hoàng Yến Chibi',
    }

    # Get all artists
    artists = Artist.objects.all()
    print(f"Found {artists.count()} artists in database")

    # Fix names
    for artist in artists:
        if artist.name in name_corrections:
            old_name = artist.name
            artist.name = name_corrections[artist.name]
            artist.save()
            print(f"Fixed artist name: {old_name} -> {artist.name}")

if __name__ == "__main__":
    print("Starting to fix artist names...")
    fix_artist_names()
    print("Finished fixing artist names!") 