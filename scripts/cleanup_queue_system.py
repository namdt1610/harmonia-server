import os
import sys
import django
from django.utils import timezone

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from stream_queue.models import Queue, QueueTrack
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db import models
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

def cleanup_queue_system():
    print("=== Cleaning up Queue System ===")
    
    total_cleaned = 0
    
    # 1. Remove orphaned queue tracks (tracks that don't exist)
    print("\n1. Cleaning orphaned queue tracks...")
    orphaned_tracks = QueueTrack.objects.filter(track__isnull=True)
    orphaned_count = orphaned_tracks.count()
    if orphaned_count > 0:
        orphaned_tracks.delete()
        print(f"   Removed {orphaned_count} orphaned queue tracks")
        total_cleaned += orphaned_count
    else:
        print("   No orphaned queue tracks found")
    
    # 2. Remove soft-deleted queue tracks older than 7 days
    print("\n2. Cleaning old soft-deleted queue tracks...")
    week_ago = timezone.now() - timezone.timedelta(days=7)
    old_deleted_tracks = QueueTrack.objects.filter(
        is_deleted=True,
        deleted_at__lt=week_ago
    )
    old_deleted_count = old_deleted_tracks.count()
    if old_deleted_count > 0:
        old_deleted_tracks.delete()
        print(f"   Removed {old_deleted_count} old soft-deleted queue tracks")
        total_cleaned += old_deleted_count
    else:
        print("   No old soft-deleted queue tracks found")
    
    # 3. Remove duplicate queues per user (keep only the latest)
    print("\n3. Cleaning duplicate queues...")
    users_with_queues = User.objects.filter(queues__isnull=False).distinct()
    duplicate_count = 0
    
    for user in users_with_queues:
        user_queues = Queue.objects.filter(user=user).order_by('-created_at')
        if user_queues.count() > 1:
            # Keep the latest queue, mark others as deleted
            latest_queue = user_queues.first()
            duplicate_queues = user_queues.exclude(id=latest_queue.id)
            
            for queue in duplicate_queues:
                # Soft delete queue tracks
                QueueTrack.objects.filter(queue=queue, is_deleted=False).update(
                    is_deleted=True,
                    deleted_at=timezone.now()
                )
                # Delete the queue
                queue.delete()
                duplicate_count += 1
                print(f"   Removed duplicate queue for user {user.username}")
    
    if duplicate_count == 0:
        print("   No duplicate queues found")
    else:
        print(f"   Removed {duplicate_count} duplicate queues")
        total_cleaned += duplicate_count
    
    # 4. Fix queue track ordering
    print("\n4. Fixing queue track ordering...")
    reordered_count = 0
    
    for queue in Queue.objects.all():
        queue_tracks = QueueTrack.objects.filter(
            queue=queue, 
            is_deleted=False
        ).order_by('order', 'added_at')
        
        # Reorder tracks sequentially
        for index, qt in enumerate(queue_tracks):
            if qt.order != index:
                qt.order = index
                qt.save()
                reordered_count += 1
        
        # Fix current_index if it's out of bounds
        max_index = queue_tracks.count() - 1
        if queue.current_index > max_index and max_index >= 0:
            queue.current_index = max_index
            queue.save()
            print(f"   Fixed current_index for queue {queue.id}")
    
    if reordered_count > 0:
        print(f"   Reordered {reordered_count} queue tracks")
    else:
        print("   All queue tracks are properly ordered")
    
    # 5. Clear queue cache
    print("\n5. Clearing queue cache...")
    cache_keys_cleared = 0
    for user in User.objects.all():
        cache_key = f"queue_{user.id}"
        if cache.get(cache_key):
            cache.delete(cache_key)
            cache_keys_cleared += 1
    
    if cache_keys_cleared > 0:
        print(f"   Cleared {cache_keys_cleared} queue cache entries")
    else:
        print("   No queue cache entries to clear")
    
    # 6. Send WebSocket updates to all users with queues
    print("\n6. Syncing WebSocket connections...")
    channel_layer = get_channel_layer()
    if channel_layer:
        sync_count = 0
        for user in users_with_queues:
            try:
                # Send queue update through WebSocket
                async_to_sync(channel_layer.group_send)(
                    f"queue_{user.id}",
                    {
                        "type": "queue_update",
                        "queue": {"tracks": [], "current_index": 0},
                        "action": "sync_required"
                    }
                )
                sync_count += 1
            except Exception as e:
                print(f"   Failed to sync WebSocket for user {user.username}: {e}")
        
        if sync_count > 0:
            print(f"   Sent sync signals to {sync_count} WebSocket connections")
        else:
            print("   No active WebSocket connections to sync")
    else:
        print("   WebSocket channel layer not available")
    
    # 7. Statistics
    print("\n=== Cleanup Statistics ===")
    print(f"Total items cleaned: {total_cleaned}")
    print(f"Active queues: {Queue.objects.count()}")
    print(f"Active queue tracks: {QueueTrack.objects.filter(is_deleted=False).count()}")
    print(f"Soft-deleted queue tracks: {QueueTrack.objects.filter(is_deleted=True).count()}")
    
    # 8. Recommendations
    print("\n=== Recommendations ===")
    empty_queues = Queue.objects.filter(queuetrack__isnull=True).count()
    if empty_queues > 0:
        print(f"- Consider removing {empty_queues} empty queues")
    
    large_queues = Queue.objects.filter(queuetrack__is_deleted=False).annotate(
        track_count=models.Count('queuetrack')
    ).filter(track_count__gt=100).count()
    if large_queues > 0:
        print(f"- {large_queues} queues have more than 100 tracks (consider pagination)")
    
    print("\n=== Queue Cleanup Complete ===")

if __name__ == '__main__':
    cleanup_queue_system() 