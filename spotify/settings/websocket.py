# Channels and WebSocket Configuration
ASGI_APPLICATION = 'spotify.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
            "capacity": 1500,  # Maximum number of messages that can be in a channel layer
            "expiry": 3600,   # Message expiry time in seconds
        },
    },
}

# WebSocket URL Configuration
WEBSOCKET_URL = '/ws/' 