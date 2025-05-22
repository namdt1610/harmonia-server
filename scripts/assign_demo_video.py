import os
import sys
# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
import django
django.setup()
from tracks.models import Track

def assign_demo_video():
    demo_path = 'videos/demo_video.mp4'  # Đường dẫn tương đối trong media/
    for track in Track.objects.all():
        track.video = demo_path
        track.save(update_fields=['video'])
    print("Assigned demo video to all tracks.")

# Để chạy script này:
# python manage.py shell
# >>> from scripts.assign_demo_video import assign_demo_video
# >>> assign_demo_video()

if __name__ == "__main__":
    assign_demo_video() 