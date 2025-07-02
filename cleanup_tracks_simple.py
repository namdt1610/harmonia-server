#!/usr/bin/env python3
"""
Script đơn giản để xóa tracks không có file tồn tại
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from tracks.models import Track
from playlists.models import PlaylistTrack
from favorites.models import Favorite
from user_activity.models import PlayHistory
from django.db import transaction


def main():
    print("🔍 Đang kiểm tra tracks có file bị mất...")
    
    tracks_with_missing_files = []
    all_tracks = Track.objects.all()
    
    print(f"📊 Tổng cộng {all_tracks.count()} tracks")
    
    for track in all_tracks:
        if track.file:
            file_path = track.file.path
            if not os.path.exists(file_path):
                tracks_with_missing_files.append(track)
                print(f"❌ Track {track.id}: '{track.title}' - File missing: {track.file.name}")
    
    print(f"\n🚨 Tìm thấy {len(tracks_with_missing_files)} tracks có file bị mất")
    
    if not tracks_with_missing_files:
        print("✅ Tất cả tracks đều có file tồn tại!")
        return
    
    # Hiển thị thông tin chi tiết
    print("\n📋 Chi tiết các tracks sẽ bị xóa:")
    total_related = 0
    
    for track in tracks_with_missing_files:
        playlist_count = PlaylistTrack.objects.filter(track=track).count()
        favorite_count = Favorite.objects.filter(track=track).count()
        play_history_count = PlayHistory.objects.filter(track=track).count()
        
        related_count = playlist_count + favorite_count + play_history_count
        total_related += related_count
        
        print(f"  • Track {track.id}: '{track.title}' by {track.artist.name}")
        print(f"    📁 File: {track.file.name}")
        print(f"    🔗 Related: {playlist_count} playlists, {favorite_count} favorites, {play_history_count} play history")
        print()
    
    print(f"⚠️  Tổng cộng {total_related} records liên quan sẽ bị xóa")
    
    # Xác nhận
    print("\n" + "="*60)
    confirm = input("❓ Bạn có chắc muốn xóa các tracks này không? (yes/no): ").lower()
    
    if confirm != 'yes':
        print("❌ Hủy bỏ - Không có gì bị xóa")
        return
    
    # Xóa tracks và related data
    print("\n🗑️  Đang xóa tracks và data liên quan...")
    
    deleted_tracks = 0
    deleted_related = 0
    
    try:
        with transaction.atomic():
            for track in tracks_with_missing_files:
                # Xóa related objects trước
                playlist_deleted = PlaylistTrack.objects.filter(track=track).delete()[0]
                favorite_deleted = Favorite.objects.filter(track=track).delete()[0]
                history_deleted = PlayHistory.objects.filter(track=track).delete()[0]
                
                deleted_related += playlist_deleted + favorite_deleted + history_deleted
                
                # Xóa track
                track_title = track.title
                track_id = track.id
                track.delete()
                deleted_tracks += 1
                
                print(f"  ✅ Đã xóa track {track_id}: '{track_title}'")
        
        print(f"\n🎉 Hoàn thành!")
        print(f"   • Đã xóa {deleted_tracks} tracks")
        print(f"   • Đã xóa {deleted_related} records liên quan")
        
    except Exception as e:
        print(f"❌ Lỗi khi xóa: {e}")
        return


if __name__ == "__main__":
    main() 