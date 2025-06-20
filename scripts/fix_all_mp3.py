import os
import subprocess

MEDIA_ROOT = "content/audio/original"

for root, dirs, files in os.walk(MEDIA_ROOT):
    for file in files:
        if file.lower().endswith(".mp3"):
            full_path = os.path.join(root, file)
            temp_path = full_path + ".fixed.mp3"
            print(f"Fixing: {full_path}")
            # Re-encode file
            cmd = [
                "ffmpeg", "-y", "-i", full_path,
                "-acodec", "libmp3lame", "-ab", "192k", temp_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                os.replace(temp_path, full_path)
                print(f"  -> Success")
            else:
                print(f"  -> Failed: {result.stderr.decode()}")
                if os.path.exists(temp_path):
                    os.remove(temp_path) 