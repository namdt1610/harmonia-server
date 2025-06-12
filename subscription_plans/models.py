from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid


class SubscriptionPlan(models.Model):
    """
    Subscription plans available for users
    """
    PLAN_TYPES = [
        ('FREE', 'Free'),
        ('PREMIUM', 'Premium Individual'),
        ('FAMILY', 'Family Plan'),
        ('STUDENT', 'Student Discount'),
        ('ARTIST', 'Artist Pro'),
    ]
    
    BILLING_CYCLES = [
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
        ('LIFETIME', 'Lifetime'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Features
    max_offline_tracks = models.IntegerField(default=0)  # 0 = unlimited
    audio_quality = models.CharField(max_length=20, default='STANDARD')  # STANDARD, HIGH, LOSSLESS
    ads_free = models.BooleanField(default=False)
    skip_limit = models.IntegerField(default=6)  # per hour, 0 = unlimited
    can_download = models.BooleanField(default=False)
    can_create_playlists = models.BooleanField(default=True)
    max_playlists = models.IntegerField(default=20)  # 0 = unlimited
    family_accounts = models.IntegerField(default=1)
    can_upload_music = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    
    # Plan details
    description = models.TextField(blank=True)
    features_list = models.JSONField(default=list)  # ["Feature 1", "Feature 2"]
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'price']
        unique_together = ['plan_type', 'billing_cycle']
    
    def __str__(self):
        return f"{self.name} ({self.get_billing_cycle_display()})"
    
    @property
    def monthly_price(self):
        """Convert price to monthly equivalent for comparison"""
        if self.billing_cycle == 'YEARLY':
            return self.price / 12
        elif self.billing_cycle == 'LIFETIME':
            return self.price / 120  # Assume 10 years
        return self.price


class UserSubscription(models.Model):
    """
    User's current subscription
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('TRIAL', 'Trial'),
        ('PAUSED', 'Paused'),
        ('PENDING', 'Pending Payment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Subscription period
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Billing
    auto_renew = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=50, blank=True)  # STRIPE, PAYPAL, etc.
    external_subscription_id = models.CharField(max_length=255, blank=True)  # Stripe subscription ID
    
    # Usage tracking
    offline_tracks_downloaded = models.IntegerField(default=0)
    playlists_created = models.IntegerField(default=0)
    skips_used_today = models.IntegerField(default=0)
    last_skip_reset = models.DateField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        now = timezone.now()
        return (
            self.status == 'ACTIVE' and 
            self.end_date > now and
            (not self.trial_end_date or self.trial_end_date > now)
        )
    
    @property
    def is_trial(self):
        """Check if user is in trial period"""
        now = timezone.now()
        return (
            self.status == 'TRIAL' and
            self.trial_end_date and
            self.trial_end_date > now
        )
    
    @property
    def days_remaining(self):
        """Get days remaining in subscription"""
        if not self.is_active:
            return 0
        return (self.end_date - timezone.now()).days
    
    def can_skip_tracks(self):
        """Check if user can skip more tracks today"""
        today = timezone.now().date()
        if self.last_skip_reset != today:
            self.skips_used_today = 0
            self.last_skip_reset = today
            self.save()
        
        if self.plan.skip_limit == 0:  # Unlimited
            return True
        return self.skips_used_today < self.plan.skip_limit
    
    def use_skip(self):
        """Use one skip"""
        if self.can_skip_tracks() and self.plan.skip_limit > 0:
            self.skips_used_today += 1
            self.save()
            return True
        return False
    
    def can_download_tracks(self):
        """Check if user can download more tracks"""
        if not self.plan.can_download:
            return False
        if self.plan.max_offline_tracks == 0:  # Unlimited
            return True
        return self.offline_tracks_downloaded < self.plan.max_offline_tracks
    
    def can_create_playlist(self):
        """Check if user can create more playlists"""
        if self.plan.max_playlists == 0:  # Unlimited
            return True
        return self.playlists_created < self.plan.max_playlists


class PaymentHistory(models.Model):
    """
    Payment history for subscriptions
    """
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    payment_method = models.CharField(max_length=50)
    external_payment_id = models.CharField(max_length=255, blank=True)  # Stripe payment intent ID
    
    billing_period_start = models.DateTimeField()
    billing_period_end = models.DateTimeField()
    
    invoice_url = models.URLField(blank=True)
    failure_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.amount} {self.currency} - {self.status}"


class SubscriptionUsageStats(models.Model):
    """
    Track subscription usage statistics
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='usage_stats')
    date = models.DateField(default=timezone.now)
    
    # Daily usage stats
    tracks_played = models.IntegerField(default=0)
    minutes_listened = models.IntegerField(default=0)
    tracks_downloaded = models.IntegerField(default=0)
    tracks_skipped = models.IntegerField(default=0)
    playlists_created = models.IntegerField(default=0)
    searches_performed = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['subscription', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.subscription.user.username} - {self.date}"


class PromoCode(models.Model):
    """
    Promotional codes for discounts
    """
    DISCOUNT_TYPES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
        ('FREE_TRIAL', 'Free Trial Extension'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Applicable plans
    applicable_plans = models.ManyToManyField(SubscriptionPlan, blank=True)
    
    # Usage limits
    max_uses = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    max_uses_per_user = models.IntegerField(default=1)
    
    # Validity
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_valid(self):
        """Check if promo code is still valid"""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            self.used_count < self.max_uses
        )


class PromoCodeUsage(models.Model):
    """
    Track promo code usage by users
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['promo_code', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} used {self.promo_code.code}"
