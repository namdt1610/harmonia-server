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

def reset_and_populate_artists():
    # Danh sách nghệ sĩ Việt Nam chuẩn
    artists_data = [
        {
            'name': 'Sơn Tùng M-TP',
            'bio': 'Sơn Tùng M-TP là ca sĩ, nhạc sĩ nổi tiếng Việt Nam.'
        },
        {
            'name': 'Hòa Minzy',
            'bio': 'Hòa Minzy là ca sĩ nổi tiếng với giọng hát nội lực.'
        },
        {
            'name': 'Jack',
            'bio': 'Jack là ca sĩ, nhạc sĩ trẻ nổi bật với nhiều bản hit.'
        },
        {
            'name': 'Mono',
            'bio': 'Mono là rapper, producer trẻ của Việt Nam.'
        },
        {
            'name': 'Hoàng Thùy Linh',
            'bio': 'Hoàng Thùy Linh là ca sĩ, diễn viên nổi tiếng.'
        },
        {
            'name': 'Erik',
            'bio': 'Erik là ca sĩ trẻ với nhiều bản hit ballad.'
        },
        {
            'name': 'Noo Phước Thịnh',
            'bio': 'Noo Phước Thịnh là ca sĩ nhạc trẻ nổi tiếng.'
        },
        {
            'name': 'Hồ Ngọc Hà',
            'bio': 'Hồ Ngọc Hà là ca sĩ, người mẫu, diễn viên nổi tiếng.'
        },
        {
            'name': 'Mỹ Tâm',
            'bio': 'Mỹ Tâm là ca sĩ nổi tiếng với nhiều giải thưởng lớn.'
        },
        {
            'name': 'Đàm Vĩnh Hưng',
            'bio': 'Đàm Vĩnh Hưng là ca sĩ nhạc nhẹ nổi tiếng.'
        },
        {
            'name': 'Tuấn Hưng',
            'bio': 'Tuấn Hưng là ca sĩ nhạc trẻ nổi tiếng.'
        },
        {
            'name': 'Hồ Quỳnh Hương',
            'bio': 'Hồ Quỳnh Hương là ca sĩ nổi tiếng với giọng hát nội lực.'
        },
        {
            'name': 'Thu Minh',
            'bio': 'Thu Minh là ca sĩ nổi tiếng với chất giọng cao.'
        },
        {
            'name': 'Hoàng Yến Chibi',
            'bio': 'Hoàng Yến Chibi là ca sĩ, diễn viên trẻ nổi bật.'
        },
    ]

    # Xóa toàn bộ nghệ sĩ
    print(f"Deleting all artists...")
    Artist.objects.all().delete()
    print(f"All artists deleted.")

    # Thêm lại nghệ sĩ
    for data in artists_data:
        artist = Artist.objects.create(name=data['name'], bio=data['bio'])
        print(f"Added artist: {artist.name}")

if __name__ == "__main__":
    print("Resetting and repopulating artists...")
    reset_and_populate_artists()
    print("Done!") 