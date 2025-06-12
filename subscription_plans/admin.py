from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    SubscriptionPlan, UserSubscription, PaymentHistory, 
    SubscriptionUsageStats, PromoCode, PromoCodeUsage
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'plan_type', 'billing_cycle', 'price', 'currency',
        'is_active', 'sort_order', 'created_at'
    ]
    list_filter = ['plan_type', 'billing_cycle', 'is_active', 'currency']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'price']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'plan_type', 'billing_cycle', 'price', 'currency', 'description')
        }),
        ('Features', {
            'fields': (
                'max_offline_tracks', 'audio_quality', 'ads_free', 'skip_limit',
                'can_download', 'can_create_playlists', 'max_playlists',
                'family_accounts', 'can_upload_music', 'analytics_access', 'priority_support'
            )
        }),
        ('Settings', {
            'fields': ('features_list', 'is_active', 'sort_order')
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return ['plan_type', 'billing_cycle']
        return []


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'plan_name', 'status', 'start_date', 'end_date',
        'is_active_status', 'auto_renew', 'created_at'
    ]
    list_filter = ['status', 'plan__plan_type', 'auto_renew', 'created_at']
    search_fields = ['user__username', 'user__email', 'plan__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Subscription Period', {
            'fields': ('start_date', 'end_date', 'trial_end_date', 'auto_renew')
        }),
        ('Payment', {
            'fields': ('payment_method', 'external_subscription_id')
        }),
        ('Usage Tracking', {
            'fields': (
                'offline_tracks_downloaded', 'playlists_created', 
                'skips_used_today', 'last_skip_reset'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def plan_name(self, obj):
        return obj.plan.name
    plan_name.short_description = 'Plan'
    
    def is_active_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        else:
            return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_status.short_description = 'Active Status'


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_user', 'amount', 'currency', 'status',
        'payment_method', 'billing_period_start', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['subscription__user__username', 'external_payment_id']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('subscription', 'amount', 'currency', 'status', 'payment_method')
        }),
        ('External References', {
            'fields': ('external_payment_id', 'invoice_url')
        }),
        ('Billing Period', {
            'fields': ('billing_period_start', 'billing_period_end')
        }),
        ('Additional Info', {
            'fields': ('failure_reason',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def subscription_user(self, obj):
        return obj.subscription.user.username
    subscription_user.short_description = 'User'


@admin.register(SubscriptionUsageStats)
class SubscriptionUsageStatsAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_user', 'date', 'tracks_played', 'minutes_listened',
        'tracks_downloaded', 'tracks_skipped', 'created_at'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['subscription__user__username']
    ordering = ['-date', '-created_at']
    readonly_fields = ['created_at']
    
    def subscription_user(self, obj):
        return obj.subscription.user.username
    subscription_user.short_description = 'User'


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'discount_type', 'discount_value',
        'used_count', 'max_uses', 'is_valid_status', 'valid_until', 'created_at'
    ]
    list_filter = ['discount_type', 'is_active', 'created_at']
    search_fields = ['code', 'name']
    ordering = ['-created_at']
    readonly_fields = ['used_count', 'created_at']
    filter_horizontal = ['applicable_plans']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'discount_type', 'discount_value')
        }),
        ('Applicable Plans', {
            'fields': ('applicable_plans',)
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'used_count', 'max_uses_per_user')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def is_valid_status(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ Invalid</span>')
    is_valid_status.short_description = 'Valid Status'


@admin.register(PromoCodeUsage)
class PromoCodeUsageAdmin(admin.ModelAdmin):
    list_display = [
        'promo_code_code', 'user_username', 'discount_applied', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['promo_code__code', 'user__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def promo_code_code(self, obj):
        return obj.promo_code.code
    promo_code_code.short_description = 'Promo Code'
    
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'User'


# Custom admin site configuration
admin.site.site_header = "Harmonia Subscription Management"
admin.site.site_title = "Harmonia Admin"
admin.site.index_title = "Subscription Management Dashboard"
