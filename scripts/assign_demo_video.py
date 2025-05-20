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