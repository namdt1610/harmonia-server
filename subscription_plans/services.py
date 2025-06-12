import logging
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from .models import (
    SubscriptionPlan, UserSubscription, PaymentHistory, 
    SubscriptionUsageStats, PromoCode, PromoCodeUsage
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service for managing user subscriptions
    """
    
    @staticmethod
    def get_or_create_free_subscription(user: User) -> UserSubscription:
        """
        Get or create a free subscription for a user
        
        Args:
            user (User): User instance
            
        Returns:
            UserSubscription: User's subscription
        """
        try:
            return user.subscription
        except UserSubscription.DoesNotExist:
            # Get free plan
            free_plan = SubscriptionPlan.objects.filter(
                plan_type='FREE', 
                is_active=True
            ).first()
            
            if not free_plan:
                # Create default free plan if doesn't exist
                free_plan = SubscriptionService.create_default_free_plan()
            
            # Create subscription
            subscription = UserSubscription.objects.create(
                user=user,
                plan=free_plan,
                status='ACTIVE',
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=365*10),  # Free plan never expires
                auto_renew=False
            )
            
            logger.info(f"Created free subscription for user {user.username}")
            return subscription
    
    @staticmethod
    def create_default_free_plan() -> SubscriptionPlan:
        """Create default free plan"""
        return SubscriptionPlan.objects.create(
            name="Harmonia Free",
            plan_type="FREE",
            billing_cycle="MONTHLY",
            price=Decimal('0.00'),
            audio_quality="STANDARD",
            ads_free=False,
            skip_limit=6,
            can_download=False,
            max_playlists=20,
            features_list=[
                "Access to millions of songs",
                "Create up to 20 playlists",
                "6 skips per hour",
                "Standard audio quality",
                "Shuffle play"
            ],
            description="Free access to Harmonia with basic features"
        )
    
    @staticmethod
    @transaction.atomic
    def upgrade_subscription(user: User, plan_id: str, payment_method: str = '', 
                           promo_code: str = '') -> dict:
        """
        Upgrade user's subscription to a new plan
        
        Args:
            user (User): User instance
            plan_id (str): New plan ID
            payment_method (str): Payment method
            promo_code (str): Optional promo code
            
        Returns:
            dict: Result with success status and details
        """
        try:
            # Get new plan
            new_plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            
            # Get or create current subscription
            current_subscription = SubscriptionService.get_or_create_free_subscription(user)
            
            # Calculate pricing with promo code
            final_price = new_plan.price
            promo_discount = Decimal('0.00')
            promo_code_obj = None
            
            if promo_code:
                promo_result = PromoCodeService.validate_and_apply_promo_code(
                    promo_code, user, new_plan
                )
                if promo_result['valid']:
                    promo_code_obj = promo_result['promo_code']
                    promo_discount = promo_result['discount']
                    final_price = max(Decimal('0.00'), final_price - promo_discount)
            
            # Calculate subscription period
            start_date = timezone.now()
            if new_plan.billing_cycle == 'MONTHLY':
                end_date = start_date + timedelta(days=30)
            elif new_plan.billing_cycle == 'YEARLY':
                end_date = start_date + timedelta(days=365)
            else:  # LIFETIME
                end_date = start_date + timedelta(days=365*50)  # 50 years
            
            # Update subscription
            current_subscription.plan = new_plan
            current_subscription.status = 'ACTIVE' if final_price == 0 else 'PENDING'
            current_subscription.start_date = start_date
            current_subscription.end_date = end_date
            current_subscription.payment_method = payment_method
            current_subscription.auto_renew = True
            current_subscription.save()
            
            # Create payment record if not free
            if final_price > 0:
                payment = PaymentHistory.objects.create(
                    subscription=current_subscription,
                    amount=final_price,
                    currency=new_plan.currency,
                    status='PENDING',
                    payment_method=payment_method,
                    billing_period_start=start_date,
                    billing_period_end=end_date
                )
            
            # Apply promo code if used
            if promo_code_obj:
                PromoCodeUsage.objects.create(
                    promo_code=promo_code_obj,
                    user=user,
                    subscription=current_subscription,
                    discount_applied=promo_discount
                )
                promo_code_obj.used_count += 1
                promo_code_obj.save()
            
            logger.info(f"Upgraded subscription for user {user.username} to {new_plan.name}")
            
            return {
                'success': True,
                'subscription': current_subscription,
                'payment_required': final_price > 0,
                'amount': final_price,
                'promo_discount': promo_discount
            }
            
        except SubscriptionPlan.DoesNotExist:
            return {'success': False, 'error': 'Invalid subscription plan'}
        except Exception as e:
            logger.error(f"Error upgrading subscription for {user.username}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def cancel_subscription(user: User, immediate: bool = False) -> dict:
        """
        Cancel user's subscription
        
        Args:
            user (User): User instance
            immediate (bool): Cancel immediately or at period end
            
        Returns:
            dict: Result with success status
        """
        try:
            subscription = user.subscription
            
            if immediate:
                subscription.status = 'CANCELLED'
                subscription.end_date = timezone.now()
                subscription.auto_renew = False
                
                # Downgrade to free plan
                free_plan = SubscriptionPlan.objects.filter(
                    plan_type='FREE', is_active=True
                ).first()
                if free_plan:
                    subscription.plan = free_plan
            else:
                subscription.auto_renew = False
                subscription.status = 'CANCELLED'
            
            subscription.save()
            
            logger.info(f"Cancelled subscription for user {user.username}")
            return {'success': True, 'immediate': immediate}
            
        except UserSubscription.DoesNotExist:
            return {'success': False, 'error': 'No active subscription found'}
        except Exception as e:
            logger.error(f"Error cancelling subscription for {user.username}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def check_subscription_limits(user: User, action: str) -> dict:
        """
        Check if user can perform action based on subscription limits
        
        Args:
            user (User): User instance
            action (str): Action to check (skip, download, create_playlist)
            
        Returns:
            dict: Result with allowed status and details
        """
        try:
            subscription = SubscriptionService.get_or_create_free_subscription(user)
            
            if action == 'skip':
                allowed = subscription.can_skip_tracks()
                remaining = max(0, subscription.plan.skip_limit - subscription.skips_used_today) if subscription.plan.skip_limit > 0 else -1
                return {
                    'allowed': allowed,
                    'remaining': remaining,
                    'limit': subscription.plan.skip_limit
                }
            
            elif action == 'download':
                allowed = subscription.can_download_tracks()
                remaining = max(0, subscription.plan.max_offline_tracks - subscription.offline_tracks_downloaded) if subscription.plan.max_offline_tracks > 0 else -1
                return {
                    'allowed': allowed,
                    'remaining': remaining,
                    'limit': subscription.plan.max_offline_tracks
                }
            
            elif action == 'create_playlist':
                allowed = subscription.can_create_playlist()
                remaining = max(0, subscription.plan.max_playlists - subscription.playlists_created) if subscription.plan.max_playlists > 0 else -1
                return {
                    'allowed': allowed,
                    'remaining': remaining,
                    'limit': subscription.plan.max_playlists
                }
            
            return {'allowed': False, 'error': 'Invalid action'}
            
        except Exception as e:
            logger.error(f"Error checking subscription limits for {user.username}: {str(e)}")
            return {'allowed': False, 'error': str(e)}


class PromoCodeService:
    """
    Service for handling promotional codes
    """
    
    @staticmethod
    def validate_and_apply_promo_code(code: str, user: User, plan: SubscriptionPlan) -> dict:
        """
        Validate and apply promo code
        
        Args:
            code (str): Promo code
            user (User): User instance  
            plan (SubscriptionPlan): Subscription plan
            
        Returns:
            dict: Validation result
        """
        try:
            promo_code = PromoCode.objects.get(code=code.upper())
            
            # Check if promo code is valid
            if not promo_code.is_valid:
                return {'valid': False, 'error': 'Promo code is expired or invalid'}
            
            # Check if user has already used this promo code
            if PromoCodeUsage.objects.filter(promo_code=promo_code, user=user).count() >= promo_code.max_uses_per_user:
                return {'valid': False, 'error': 'You have already used this promo code'}
            
            # Check if promo code applies to this plan
            if promo_code.applicable_plans.exists() and plan not in promo_code.applicable_plans.all():
                return {'valid': False, 'error': 'This promo code is not applicable to the selected plan'}
            
            # Calculate discount
            if promo_code.discount_type == 'PERCENTAGE':
                discount = plan.price * (promo_code.discount_value / 100)
            elif promo_code.discount_type == 'FIXED':
                discount = min(promo_code.discount_value, plan.price)
            else:  # FREE_TRIAL
                discount = Decimal('0.00')  # Handle trial extension separately
            
            return {
                'valid': True,
                'promo_code': promo_code,
                'discount': discount,
                'discount_type': promo_code.discount_type
            }
            
        except PromoCode.DoesNotExist:
            return {'valid': False, 'error': 'Promo code not found'}
        except Exception as e:
            logger.error(f"Error validating promo code {code}: {str(e)}")
            return {'valid': False, 'error': 'Error validating promo code'}


class UsageTrackingService:
    """
    Service for tracking subscription usage
    """
    
    @staticmethod
    def track_usage(user: User, action: str, value: int = 1):
        """
        Track user usage for analytics
        
        Args:
            user (User): User instance
            action (str): Action performed
            value (int): Value to add
        """
        try:
            subscription = user.subscription
            today = timezone.now().date()
            
            stats, created = SubscriptionUsageStats.objects.get_or_create(
                subscription=subscription,
                date=today,
                defaults={
                    'tracks_played': 0,
                    'minutes_listened': 0,
                    'tracks_downloaded': 0,
                    'tracks_skipped': 0,
                    'playlists_created': 0,
                    'searches_performed': 0,
                }
            )
            
            if action == 'play_track':
                stats.tracks_played += value
            elif action == 'listen_minutes':
                stats.minutes_listened += value
            elif action == 'download_track':
                stats.tracks_downloaded += value
                subscription.offline_tracks_downloaded += value
                subscription.save()
            elif action == 'skip_track':
                stats.tracks_skipped += value
                subscription.use_skip()
            elif action == 'create_playlist':
                stats.playlists_created += value
                subscription.playlists_created += value
                subscription.save()
            elif action == 'search':
                stats.searches_performed += value
            
            stats.save()
            
        except UserSubscription.DoesNotExist:
            # Create free subscription if doesn't exist
            SubscriptionService.get_or_create_free_subscription(user)
        except Exception as e:
            logger.error(f"Error tracking usage for {user.username}: {str(e)}")


class BillingService:
    """
    Service for handling billing and payments
    """
    
    @staticmethod
    def process_payment_webhook(payment_data: dict) -> dict:
        """
        Process payment webhook from payment provider
        
        Args:
            payment_data (dict): Payment data from webhook
            
        Returns:
            dict: Processing result
        """
        try:
            external_payment_id = payment_data.get('payment_id')
            status = payment_data.get('status')
            
            # Find payment record
            payment = PaymentHistory.objects.get(external_payment_id=external_payment_id)
            payment.status = status.upper()
            
            if status == 'completed':
                # Activate subscription
                subscription = payment.subscription
                subscription.status = 'ACTIVE'
                subscription.save()
                
                logger.info(f"Payment completed for subscription {subscription.id}")
            elif status == 'failed':
                payment.failure_reason = payment_data.get('failure_reason', '')
                logger.warning(f"Payment failed for subscription {payment.subscription.id}")
            
            payment.save()
            
            return {'success': True, 'status': status}
            
        except PaymentHistory.DoesNotExist:
            return {'success': False, 'error': 'Payment record not found'}
        except Exception as e:
            logger.error(f"Error processing payment webhook: {str(e)}")
            return {'success': False, 'error': str(e)} 