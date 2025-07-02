#!/usr/bin/env python3
"""
Comprehensive script to find and fix invalid track references in Harmonia
This script will identify track IDs that don't exist but are referenced elsewhere
"""

import os
import sys
import django
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from tracks.models import Track
from stream_queue.models import Queue, QueueTrack  
from playlists.models import Playlist, PlaylistTrack
from django.contrib.auth.models import User
from user_activity.models import PlayHistory
from favorites.models import Favorite
from django.db.models import Q

def get_all_track_ids():
    """Get all existing track IDs"""
    return set(Track.objects.values_list('id', flat=True))

def find_invalid_references():
    """Find all invalid track references across the system"""
    valid_track_ids = get_all_track_ids()
    print(f"✅ Found {len(valid_track_ids)} valid tracks")
    print(f"   Valid ID range: {min(valid_track_ids)} - {max(valid_track_ids)}")
    
    issues = []
    
    # Check QueueTrack for invalid references
    print("\n🔍 Checking Queue Tracks...")
    invalid_queue_tracks = QueueTrack.objects.exclude(track_id__in=valid_track_ids)
    if invalid_queue_tracks.exists():
        invalid_ids = list(invalid_queue_tracks.values_list('track_id', flat=True).distinct())
        print(f"❌ Found {invalid_queue_tracks.count()} invalid queue track references")
        print(f"   Invalid track IDs in queue: {sorted(invalid_ids)}")
        issues.append(('queue_tracks', invalid_queue_tracks, invalid_ids))
    else:
        print("✅ No invalid queue track references found")
    
    # Check PlaylistTrack for invalid references  
    print("\n🔍 Checking Playlist Tracks...")
    invalid_playlist_tracks = PlaylistTrack.objects.exclude(track_id__in=valid_track_ids)
    if invalid_playlist_tracks.exists():
        invalid_ids = list(invalid_playlist_tracks.values_list('track_id', flat=True).distinct())
        print(f"❌ Found {invalid_playlist_tracks.count()} invalid playlist track references")
        print(f"   Invalid track IDs in playlists: {sorted(invalid_ids)}")
        issues.append(('playlist_tracks', invalid_playlist_tracks, invalid_ids))
    else:
        print("✅ No invalid playlist track references found")
    
    # Check Favorite tracks (content_type='track') for invalid references
    print("\n🔍 Checking Favorite Tracks...")
    invalid_favorite_tracks = Favorite.objects.filter(content_type='track').exclude(track_id__in=valid_track_ids)
    if invalid_favorite_tracks.exists():
        invalid_ids = list(invalid_favorite_tracks.values_list('track_id', flat=True).distinct())
        print(f"❌ Found {invalid_favorite_tracks.count()} invalid favorite track references")
        print(f"   Invalid track IDs in favorites: {sorted(invalid_ids)}")
        issues.append(('favorite_tracks', invalid_favorite_tracks, invalid_ids))
    else:
        print("✅ No invalid favorite track references found")
    
    # Check PlayHistory for invalid references
    print("\n🔍 Checking Play History...")
    invalid_play_history = PlayHistory.objects.exclude(track_id__in=valid_track_ids)
    if invalid_play_history.exists():
        invalid_ids = list(invalid_play_history.values_list('track_id', flat=True).distinct())
        print(f"❌ Found {invalid_play_history.count()} invalid play history references")
        print(f"   Invalid track IDs in play history: {sorted(invalid_ids)}")
        issues.append(('play_history', invalid_play_history, invalid_ids))
    else:
        print("✅ No invalid play history references found")
    
    return issues

def show_detailed_invalid_references(issues):
    """Show detailed information about invalid references"""
    print("\n" + "="*60)
    print("📋 DETAILED INVALID REFERENCE REPORT")
    print("="*60)
    
    for issue_type, queryset, invalid_ids in issues:
        print(f"\n🔍 {issue_type.upper().replace('_', ' ')}")
        print("-" * 40)
        
        if issue_type == 'queue_tracks':
            for track_id in invalid_ids[:10]:  # Show first 10
                queue_tracks = queryset.filter(track_id=track_id)
                for qt in queue_tracks:
                    print(f"   Queue ID: {qt.queue.id} (User: {qt.queue.user.username}) -> Track ID: {track_id}")
        
        elif issue_type == 'playlist_tracks':
            for track_id in invalid_ids[:10]:
                playlist_tracks = queryset.filter(track_id=track_id)
                for pt in playlist_tracks:
                    print(f"   Playlist: '{pt.playlist.name}' (ID: {pt.playlist.id}) -> Track ID: {track_id}")
        
        elif issue_type == 'favorite_tracks':
            for track_id in invalid_ids[:10]:
                favorite_tracks = queryset.filter(track_id=track_id)
                for ft in favorite_tracks:
                    print(f"   User: {ft.user.username} -> Track ID: {track_id}")
        
        elif issue_type == 'play_history':
            for track_id in invalid_ids[:10]:
                play_histories = queryset.filter(track_id=track_id)
                for ph in play_histories:
                    print(f"   User: {ph.user.username} -> Track ID: {track_id} (Played: {ph.played_at})")
        
        if len(invalid_ids) > 10:
            print(f"   ... and {len(invalid_ids) - 10} more invalid track IDs")

def fix_invalid_references(issues, dry_run=True):
    """Fix invalid track references"""
    print("\n" + "="*60)
    if dry_run:
        print("🧪 DRY RUN - No actual changes will be made")
    else:
        print("⚡ FIXING INVALID REFERENCES")
    print("="*60)
    
    if not issues:
        print("✅ No issues to fix!")
        return
    
    total_deleted = 0
    
    with transaction.atomic():
        for issue_type, queryset, invalid_ids in issues:
            count = queryset.count()
            print(f"\n🔧 Processing {issue_type.replace('_', ' ')}...")
            print(f"   Will delete {count} invalid references")
            
            if not dry_run:
                deleted_count = queryset.delete()[0]
                print(f"   ✅ Deleted {deleted_count} invalid references")
                total_deleted += deleted_count
            else:
                print(f"   📝 Would delete {count} invalid references")
                total_deleted += count
    
    if dry_run:
        print(f"\n📊 Summary: Would delete {total_deleted} invalid references")
        print("💡 Run with --fix to actually apply these changes")
    else:
        print(f"\n📊 Summary: Deleted {total_deleted} invalid references")
        print("✅ All invalid references have been cleaned up!")

def main():
    print("🎵 Harmonia Invalid Track Reference Cleaner")
    print("="*50)
    
    # Check for track ID 1156 specifically
    track_1156_exists = Track.objects.filter(id=1156).exists()
    print(f"\n🔍 Checking specific track ID 1156: {'✅ EXISTS' if track_1156_exists else '❌ NOT FOUND'}")
    
    if not track_1156_exists:
        # Check where 1156 is referenced
        print("\n🔍 Checking where track ID 1156 is referenced:")
        queue_refs = QueueTrack.objects.filter(track_id=1156).count()
        playlist_refs = PlaylistTrack.objects.filter(track_id=1156).count() 
        favorite_refs = Favorite.objects.filter(track_id=1156).count()
        history_refs = PlayHistory.objects.filter(track_id=1156).count()
        
        print(f"   Queue references: {queue_refs}")
        print(f"   Playlist references: {playlist_refs}")
        print(f"   Favorite references: {favorite_refs}")
        print(f"   History references: {history_refs}")
    
    # Find all invalid references
    issues = find_invalid_references()
    
    if issues:
        show_detailed_invalid_references(issues)
        
        # Ask user what to do
        print("\n" + "="*60)
        print("🤔 What would you like to do?")
        print("1. Show dry run (preview changes)")
        print("2. Fix all invalid references")
        print("3. Exit without changes")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            fix_invalid_references(issues, dry_run=True)
        elif choice == "2":
            print("\n⚠️  WARNING: This will permanently delete invalid references!")
            confirm = input("Type 'YES' to confirm: ").strip()
            if confirm == "YES":
                fix_invalid_references(issues, dry_run=False)
            else:
                print("❌ Operation cancelled")
        else:
            print("👋 Exiting without changes")
    else:
        print("\n✅ No invalid track references found!")
        print("🎉 Your database is clean!")

if __name__ == "__main__":
    main() 