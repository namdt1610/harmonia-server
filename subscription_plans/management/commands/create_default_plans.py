from django.core.management.base import BaseCommand
from decimal import Decimal
from subscription_plans.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create default subscription plans for Harmonia'

    def handle(self, *args, **options):
        self.stdout.write('Creating default subscription plans...')
        
        plans_data = [
            {
                'name': 'Harmonia Free',
                'plan_type': 'FREE',
                'billing_cycle': 'MONTHLY',
                'price': Decimal('0.00'),
                'audio_quality': 'STANDARD',
                'ads_free': False,
                'skip_limit': 6,
                'can_download': True,  # Temporarily enabled for testing
                'max_offline_tracks': 100,  # Allow 100 downloads for free users
                'max_playlists': 20,
                'family_accounts': 1,
                'can_upload_music': False,
                'analytics_access': False,
                'priority_support': False,
                'features_list': [
                    'Access to millions of songs',
                    'Create up to 20 playlists',
                    '6 skips per hour',
                    'Standard audio quality',
                    'Download up to 100 songs',  # Updated feature
                    'Shuffle play only'
                ],
                'description': 'Free access to Harmonia with basic features',
                'sort_order': 1
            },
            {
                'name': 'Harmonia Premium (Monthly)',
                'plan_type': 'PREMIUM',
                'billing_cycle': 'MONTHLY',
                'price': Decimal('9.99'),
                'audio_quality': 'HIGH',
                'ads_free': True,
                'skip_limit': 0,  # Unlimited
                'can_download': True,
                'max_offline_tracks': 10000,
                'max_playlists': 0,  # Unlimited
                'family_accounts': 1,
                'can_upload_music': False,
                'analytics_access': False,
                'priority_support': False,
                'features_list': [
                    'Ad-free listening',
                    'High quality audio',
                    'Unlimited skips',
                    'Download up to 10,000 songs',
                    'Unlimited playlists',
                    'Play any song'
                ],
                'description': 'Premium individual plan with enhanced features',
                'sort_order': 2
            },
            {
                'name': 'Harmonia Premium (Yearly)',
                'plan_type': 'PREMIUM',
                'billing_cycle': 'YEARLY',
                'price': Decimal('99.99'),  # ~$8.33/month
                'audio_quality': 'HIGH',
                'ads_free': True,
                'skip_limit': 0,
                'can_download': True,
                'max_offline_tracks': 10000,
                'max_playlists': 0,
                'family_accounts': 1,
                'can_upload_music': False,
                'analytics_access': False,
                'priority_support': False,
                'features_list': [
                    'All Premium features',
                    '2 months free vs monthly',
                    'Ad-free listening',
                    'High quality audio',
                    'Unlimited skips',
                    'Download up to 10,000 songs'
                ],
                'description': 'Premium yearly plan with 2 months free',
                'sort_order': 3
            },
            {
                'name': 'Harmonia Family (Monthly)',
                'plan_type': 'FAMILY',
                'billing_cycle': 'MONTHLY',
                'price': Decimal('14.99'),
                'audio_quality': 'HIGH',
                'ads_free': True,
                'skip_limit': 0,
                'can_download': True,
                'max_offline_tracks': 10000,
                'max_playlists': 0,
                'family_accounts': 6,
                'can_upload_music': False,
                'analytics_access': False,
                'priority_support': True,
                'features_list': [
                    'All Premium features',
                    'Up to 6 family accounts',
                    'Individual family member profiles',
                    'Family mix playlists',
                    'Priority customer support'
                ],
                'description': 'Premium plan for up to 6 family members',
                'sort_order': 4
            },
            {
                'name': 'Harmonia Family (Yearly)',
                'plan_type': 'FAMILY',
                'billing_cycle': 'YEARLY',
                'price': Decimal('149.99'),  # ~$12.50/month
                'audio_quality': 'HIGH',
                'ads_free': True,
                'skip_limit': 0,
                'can_download': True,
                'max_offline_tracks': 10000,
                'max_playlists': 0,
                'family_accounts': 6,
                'can_upload_music': False,
                'analytics_access': False,
                'priority_support': True,
                'features_list': [
                    'All Family features',
                    '2 months free vs monthly',
                    'Up to 6 family accounts',
                    'Priority customer support'
                ],
                'description': 'Family yearly plan with savings',
                'sort_order': 5
            },
            {
                'name': 'Harmonia Student',
                'plan_type': 'STUDENT',
                'billing_cycle': 'MONTHLY',
                'price': Decimal('4.99'),
                'audio_quality': 'HIGH',
                'ads_free': True,
                'skip_limit': 0,
                'can_download': True,
                'max_offline_tracks': 10000,
                'max_playlists': 0,
                'family_accounts': 1,
                'can_upload_music': False,
                'analytics_access': False,
                'priority_support': False,
                'features_list': [
                    'All Premium features',
                    '50% student discount',
                    'Verify student status annually',
                    'Ad-free listening',
                    'High quality audio'
                ],
                'description': 'Discounted Premium plan for verified students',
                'sort_order': 6
            },
            {
                'name': 'Harmonia Artist Pro',
                'plan_type': 'ARTIST',
                'billing_cycle': 'MONTHLY',
                'price': Decimal('19.99'),
                'audio_quality': 'LOSSLESS',
                'ads_free': True,
                'skip_limit': 0,
                'can_download': True,
                'max_offline_tracks': 0,  # Unlimited
                'max_playlists': 0,
                'family_accounts': 1,
                'can_upload_music': True,
                'analytics_access': True,
                'priority_support': True,
                'features_list': [
                    'All Premium features',
                    'Lossless audio quality',
                    'Upload your own music',
                    'Advanced analytics dashboard',
                    'Priority customer support',
                    'Unlimited downloads'
                ],
                'description': 'Professional plan for artists and music creators',
                'sort_order': 7
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                plan_type=plan_data['plan_type'],
                billing_cycle=plan_data['billing_cycle'],
                defaults=plan_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created plan: {plan.name}')
                )
            else:
                # Update existing plan with new data
                for key, value in plan_data.items():
                    setattr(plan, key, value)
                plan.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated plan: {plan.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new plans, updated {updated_count} existing plans.'
            )
        ) 