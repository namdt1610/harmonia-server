from django.urls import path
from . import views

app_name = 'subscription_plans'

urlpatterns = [
    # Public endpoints
    path('plans/', views.SubscriptionPlansView.as_view(), name='subscription-plans'),
    
    # User subscription management
    path('my-subscription/', views.MySubscriptionView.as_view(), name='my-subscription'),
    path('upgrade/', views.UpgradeSubscriptionView.as_view(), name='upgrade-subscription'),
    path('cancel/', views.CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('payment-history/', views.PaymentHistoryView.as_view(), name='payment-history'),
    
    # Promo codes
    path('validate-promo/', views.ValidatePromoCodeView.as_view(), name='validate-promo-code'),
    
    # Usage tracking and limits
    path('check-limits/', views.CheckSubscriptionLimitsView.as_view(), name='check-subscription-limits'),
    path('track-usage/', views.TrackUsageView.as_view(), name='track-usage'),
    
    # Webhooks
    path('payment-webhook/', views.payment_webhook, name='payment-webhook'),
    
    # Admin analytics
    path('analytics/', views.SubscriptionAnalyticsView.as_view(), name='subscription-analytics'),
] 