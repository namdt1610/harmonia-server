from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from subscription_plans.models import SubscriptionPlan, UserSubscription
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Assign default free subscriptions to users who don\'t have one'

    def handle(self, *args, **options):
        self.stdout.write('Assigning default subscriptions to users...')
        
        # Get the free plan
        try:
            free_plan = SubscriptionPlan.objects.get(plan_type='FREE', billing_cycle='MONTHLY')
        except SubscriptionPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR('No FREE plan found. Please create default plans first.'))
            return
        
        # Find users without subscriptions
        users_without_subscription = User.objects.filter(subscription__isnull=True)
        
        if not users_without_subscription.exists():
            self.stdout.write(self.style.SUCCESS('All users already have subscriptions.'))
            return
        
        created_count = 0
        
        for user in users_without_subscription:
            # Create free subscription for user
            end_date = timezone.now() + timedelta(days=365)  # 1 year of free access
            
            subscription = UserSubscription.objects.create(
                user=user,
                plan=free_plan,
                status='ACTIVE',
                start_date=timezone.now(),
                end_date=end_date,
                auto_renew=True
            )
            
            created_count += 1
            self.stdout.write(f'Created free subscription for user: {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} default subscriptions.')
        ) 