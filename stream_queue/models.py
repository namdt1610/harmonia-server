from django.db import models
from tracks.models import Track
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Queue(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='queues')
    tracks = models.ManyToManyField(Track, through='QueueTrack', related_name='in_queues')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    current_index = models.PositiveIntegerField(default=0)

class QueueTrack(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ('queue', 'track') 