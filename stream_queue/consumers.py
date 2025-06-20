import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Queue, QueueTrack
from tracks.serializers import TrackSerializer
import logging
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Initialize all attributes first to prevent AttributeError
        self.user = None
        self.room_group_name = None
        
        try:
            # Get user from scope (authenticated by middleware)
            self.user = self.scope.get("user")
            logger.debug(f"User from scope: {self.user}")
            
            # Check authentication
            if not self.user or not hasattr(self.user, 'is_authenticated') or not self.user.is_authenticated:
                logger.warning(f"WebSocket connection rejected: User not authenticated. User: {self.user}")
                await self.close(code=4001)  # Custom close code for auth failure
                return

            # Set group name only after user validation
            self.room_group_name = f"queue_{self.user.id}"
            
            # Validate group name format
            if not self.room_group_name or len(self.room_group_name) >= 100:
                logger.error(f"Invalid group name: {self.room_group_name}")
                await self.close(code=4002)  # Custom close code for invalid group
                return
            
            # Add to channel group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Accept connection
            await self.accept()
            logger.info(f"WebSocket connected for user {self.user.id} in group {self.room_group_name}")
            
        except Exception as e:
            logger.error(f"Error during WebSocket connect: {e}")
            # Ensure clean state on error
            self.room_group_name = None
            self.user = None
            await self.close(code=4003)  # Custom close code for connection error

    async def disconnect(self, close_code):
        # Only attempt to leave group if room_group_name was set and is not None
        if (hasattr(self, 'room_group_name') and 
            self.room_group_name is not None and 
            hasattr(self, 'user') and 
            self.user is not None):
            try:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                logger.info(f"WebSocket disconnected for user {self.user.id} with code {close_code}")
            except Exception as e:
                logger.error(f"Error during group_discard for user {self.user.id}: {e}")
        else:
            logger.info(f"WebSocket disconnected with code {close_code} (no user/group set)")

    async def receive(self, text_data):
        # Check if connection is properly initialized
        if not hasattr(self, 'user') or not self.user or not hasattr(self, 'room_group_name') or not self.room_group_name:
            logger.warning("Received message on improperly initialized WebSocket connection")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Connection not properly initialized'
            }))
            return
            
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'get_queue':
                queue_data = await self.get_queue_data()
                await self.send(text_data=json.dumps({
                    'type': 'queue_update',
                    'queue': queue_data
                }))
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'sync_check':
                # Client requesting sync verification
                queue_data = await self.get_queue_data()
                await self.send(text_data=json.dumps({
                    'type': 'queue_sync',
                    'queue': queue_data,
                    'message': 'Queue sync verification'
                }))
            else:
                logger.warning(f"Unknown message type received from user {self.user.id}: {message_type}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from user {self.user.id}: {text_data}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            user_id = getattr(self.user, 'id', 'unknown') if self.user else 'unknown'
            logger.error(f"Error handling WebSocket message for user {user_id}: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    @database_sync_to_async
    def get_queue_data(self):
        try:
            # Check if user is available
            if not hasattr(self, 'user') or self.user is None or not self.user.is_authenticated:
                logger.warning("get_queue_data called without authenticated user")
                return {
                    'tracks': [], 
                    'current_index': 0,
                    'timestamp': timezone.now().isoformat(),
                    'error': 'User not authenticated'
                }

            # Always try to get fresh data from database when possible
            # Check cache first but be ready to invalidate if needed
            cache_key = f"queue_{self.user.id}"
            cached_data = cache.get(cache_key)
            
            # Get fresh data from database
            queue = Queue.objects.filter(user=self.user).first()
            if not queue:
                empty_data = {
                    'tracks': [], 
                    'current_index': 0,
                    'timestamp': timezone.now().isoformat()
                }
                # Cache empty result briefly
                cache.set(cache_key, empty_data, 60)
                return empty_data

            queue_tracks = QueueTrack.objects.filter(
                queue=queue, 
                is_deleted=False
            ).select_related(
                'track',
                'track__artist',
                'track__album'
            ).order_by('order')
            
            tracks = []
            for qt in queue_tracks:
                try:
                    track_data = TrackSerializer(qt.track).data
                    tracks.append({
                        'id': qt.id,
                        'track': track_data,
                        'order': qt.order
                    })
                except Exception as e:
                    logger.error(f"Error serializing track {qt.track.id}: {e}")
                    continue

            queue_data = {
                'tracks': tracks,
                'current_index': queue.current_index,
                'timestamp': timezone.now().isoformat()
            }
            
            # Always update cache with fresh data
            cache.set(cache_key, queue_data, 300)  # 5 minutes
            
            logger.debug(f"Retrieved queue data for user {self.user.id}: {len(tracks)} tracks")
            return queue_data
        except Exception as e:
            user_id = getattr(self.user, 'id', 'unknown') if hasattr(self, 'user') and self.user else 'unknown'
            logger.error(f"Error getting queue data for user {user_id}: {e}")
            return {
                'tracks': [], 
                'current_index': 0,
                'timestamp': timezone.now().isoformat(),
                'error': 'Failed to fetch queue data'
            }

    async def queue_update(self, event):
        """Send queue update to WebSocket"""
        try:
            # Handle sync_required action
            if event.get('action') == 'sync_required':
                # Force refresh queue data from database
                queue_data = await self.get_queue_data()
                await self.send(text_data=json.dumps({
                    'type': 'queue_sync',
                    'queue': queue_data,
                    'message': 'Queue synchronized',
                    'timestamp': timezone.now().isoformat()
                }))
            else:
                # Normal queue update - add timestamp if not present
                if 'queue' in event and 'timestamp' not in event['queue']:
                    event['queue']['timestamp'] = timezone.now().isoformat()
                
                await self.send(text_data=json.dumps(event))
                
        except Exception as e:
            logger.error(f"Error sending queue update to user {self.user.id}: {e}")
            # Send error message to client
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to process queue update',
                'timestamp': timezone.now().isoformat()
            })) 

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None 