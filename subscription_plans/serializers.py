from rest_framework import serializers
from .models import (
    SubscriptionPlan, UserSubscription, PaymentHistory, 
    SubscriptionUsageStats, PromoCode
)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    
    monthly_price = serializers.ReadOnlyField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'plan_type', 'billing_cycle', 'price', 'monthly_price',
            'currency', 'max_offline_tracks', 'audio_quality', 'ads_free',
            'skip_limit', 'can_download', 'can_create_playlists', 'max_playlists',
            'family_accounts', 'can_upload_music', 'analytics_access', 
            'priority_support', 'description', 'features_list', 'sort_order'
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions"""
    
    plan = SubscriptionPlanSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    is_trial = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user_username', 'plan', 'status', 'start_date', 'end_date',
            'trial_end_date', 'auto_renew', 'payment_method', 'is_active',
            'is_trial', 'days_remaining', 'offline_tracks_downloaded',
            'playlists_created', 'skips_used_today', 'created_at'
        ]


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history"""
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'amount', 'currency', 'status', 'payment_method',
            'billing_period_start', 'billing_period_end', 'invoice_url',
            'failure_reason', 'created_at'
        ]


class SubscriptionUsageStatsSerializer(serializers.ModelSerializer):
    """Serializer for usage statistics"""
    
    class Meta:
        model = SubscriptionUsageStats
        fields = [
            'id', 'date', 'tracks_played', 'minutes_listened',
            'tracks_downloaded', 'tracks_skipped', 'playlists_created',
            'searches_performed'
        ]


class UpgradeSubscriptionSerializer(serializers.Serializer):
    """Serializer for subscription upgrade requests"""
    
    plan_id = serializers.UUIDField()
    payment_method = serializers.CharField(max_length=50, required=False, allow_blank=True)
    promo_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    def validate_plan_id(self, value):
        """Validate that the plan exists and is active"""
        if not SubscriptionPlan.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive subscription plan")
        return value


class CancelSubscriptionSerializer(serializers.Serializer):
    """Serializer for subscription cancellation"""
    
    immediate = serializers.BooleanField(default=False)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class PromoCodeValidationSerializer(serializers.Serializer):
    """Serializer for promo code validation"""
    
    code = serializers.CharField(max_length=50)
    plan_id = serializers.UUIDField()
    
    def validate_plan_id(self, value):
        """Validate that the plan exists and is active"""
        if not SubscriptionPlan.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive subscription plan")
        return value


class PromoCodeSerializer(serializers.ModelSerializer):
    """Serializer for promo codes (admin only)"""
    
    is_valid = serializers.ReadOnlyField()
    
    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'name', 'discount_type', 'discount_value',
            'max_uses', 'used_count', 'max_uses_per_user', 'valid_from',
            'valid_until', 'is_active', 'is_valid', 'created_at'
        ]


class SubscriptionLimitsSerializer(serializers.Serializer):
    """Serializer for subscription limits check"""
    
    action = serializers.ChoiceField(choices=['skip', 'download', 'create_playlist'])


class UsageTrackingSerializer(serializers.Serializer):
    """Serializer for usage tracking"""
    
    action = serializers.ChoiceField(choices=[
        'play_track', 'listen_minutes', 'download_track', 
        'skip_track', 'create_playlist', 'search'
    ])
    value = serializers.IntegerField(default=1, min_value=1)


class SubscriptionOverviewSerializer(serializers.Serializer):
    """Serializer for subscription overview (analytics)"""
    
    total_subscribers = serializers.IntegerField()
    active_subscribers = serializers.IntegerField()
    trial_users = serializers.IntegerField()
    cancelled_subscriptions = serializers.IntegerField()
    revenue_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_last_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    plan_distribution = serializers.DictField()
    churn_rate = serializers.FloatField()


class RevenueAnalyticsSerializer(serializers.Serializer):
    """Serializer for revenue analytics"""
    
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    subscribers = serializers.IntegerField()
    new_subscribers = serializers.IntegerField()
    cancelled_subscribers = serializers.IntegerField() 