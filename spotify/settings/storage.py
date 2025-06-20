import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Extra places for collectstatic to find static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files configuration
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_REGION")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Storage configuration based on environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
if ENVIRONMENT == "production":
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Media Storage Settings
MEDIA_STORAGE = {
    'CONTENT': {
        'AUDIO': {
            'ORIGINAL': 'content/audio/original/',
            'PROCESSED': 'content/audio/processed/',
            'THUMBNAIL': 'content/audio/thumbnail/',
        },
        'VIDEO': {
            'ORIGINAL': 'content/video/original/',
            'PROCESSED': 'content/video/processed/',
            'THUMBNAIL': 'content/video/thumbnail/',
        },
        'IMAGE': {
            'ORIGINAL': 'content/image/original/',
            'PROCESSED': 'content/image/processed/',
            'THUMBNAIL': 'content/image/thumbnail/',
        },
    },
    'ASSETS': {
        'BRANDING': 'assets/branding/',
        'ICONS': 'assets/icons/',
        'TEMPLATES': 'assets/templates/',
    },
    'BACKUPS': {
        'DAILY': 'backups/daily/',
        'WEEKLY': 'backups/weekly/',
        'MONTHLY': 'backups/monthly/',
    },
    'VERSIONS': {
        'V1': 'versions/v1/',
        'V2': 'versions/v2/',
    },
}

# Environment-specific media paths
MEDIA_ENV_PATH = os.path.join(MEDIA_ROOT, ENVIRONMENT) 