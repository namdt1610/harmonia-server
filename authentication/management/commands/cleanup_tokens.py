import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import TokenBlacklist

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up expired tokens from blacklist'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_tokens = TokenBlacklist.objects.filter(expires_at__lt=now)
        count = expired_tokens.count()
        expired_tokens.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} expired tokens')
        )
        logger.info(f'Successfully deleted {count} expired tokens') 