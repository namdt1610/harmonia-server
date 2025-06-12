from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import SubscriptionPlan, UserSubscription, PaymentHistory, PromoCode
from .serializers import (
    SubscriptionPlanSerializer, UserSubscriptionSerializer, PaymentHistorySerializer,
    UpgradeSubscriptionSerializer, CancelSubscriptionSerializer, PromoCodeValidationSerializer,
    PromoCodeSerializer, SubscriptionLimitsSerializer, UsageTrackingSerializer,
    SubscriptionOverviewSerializer
)
from .services import (
    SubscriptionService, PromoCodeService, UsageTrackingService, BillingService
)


class SubscriptionPlansView(APIView):
    """
    API endpoint to get available subscription plans
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        tags=['Subscriptions'],
        operation_description="Get all available subscription plans",
        responses={
            200: SubscriptionPlanSerializer(many=True),
        }
    )
    def get(self, request):
        """Get all available subscription plans"""
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)


class MySubscriptionView(APIView):
    """
    API endpoint to get current user's subscription
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Subscriptions'],
        operation_description="Get current user's subscription details",
        responses={
            200: UserSubscriptionSerializer(),
        }
    )
    def get(self, request):
        """Get current user's subscription"""
        subscription = SubscriptionService.get_or_create_free_subscription(request.user)
        serializer = UserSubscriptionSerializer(subscription)
        return Response(serializer.data)


class UpgradeSubscriptionView(APIView):
    """
    API endpoint to upgrade subscription
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Subscriptions'],
        operation_description="Upgrade user's subscription to a new plan",
        request_body=UpgradeSubscriptionSerializer(),
        responses={
            200: openapi.Response(
                description="Subscription upgraded successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'subscription': UserSubscriptionSerializer(),
                        'payment_required': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'amount': openapi.Schema(type=openapi.TYPE_STRING),
                        'promo_discount': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """Upgrade user's subscription"""
        serializer = UpgradeSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            result = SubscriptionService.upgrade_subscription(
                user=request.user,
                plan_id=str(serializer.validated_data['plan_id']),
                payment_method=serializer.validated_data.get('payment_method', ''),
                promo_code=serializer.validated_data.get('promo_code', '')
            )
            
            if result['success']:
                subscription_serializer = UserSubscriptionSerializer(result['subscription'])
                return Response({
                    'success': True,
                    'subscription': subscription_serializer.data,
                    'payment_required': result['payment_required'],
                    'amount': str(result['amount']),
                    'promo_discount': str(result['promo_discount'])
                })
            else:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelSubscriptionView(APIView):
    """
    API endpoint to cancel subscription
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Subscriptions'],
        operation_description="Cancel user's subscription",
        request_body=CancelSubscriptionSerializer(),
        responses={
            200: openapi.Response(
                description="Subscription cancelled successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """Cancel user's subscription"""
        serializer = CancelSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            result = SubscriptionService.cancel_subscription(
                user=request.user,
                immediate=serializer.validated_data.get('immediate', False)
            )
            
            if result['success']:
                message = "Subscription cancelled immediately" if result['immediate'] else "Subscription will be cancelled at the end of the billing period"
                return Response({
                    'success': True,
                    'message': message
                })
            else:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ValidatePromoCodeView(APIView):
    """
    API endpoint to validate promo code
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Subscriptions'],
        operation_description="Validate a promo code",
        request_body=PromoCodeValidationSerializer(),
        responses={
            200: openapi.Response(
                description="Promo code validation result",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'discount': openapi.Schema(type=openapi.TYPE_STRING),
                        'discount_type': openapi.Schema(type=openapi.TYPE_STRING),
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """Validate promo code"""
        serializer = PromoCodeValidationSerializer(data=request.data)
        if serializer.is_valid():
            plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
            result = PromoCodeService.validate_and_apply_promo_code(
                code=serializer.validated_data['code'],
                user=request.user,
                plan=plan
            )
            
            if result['valid']:
                return Response({
                    'valid': True,
                    'discount': str(result['discount']),
                    'discount_type': result['discount_type']
                })
            else:
                return Response({
                    'valid': False,
                    'error': result['error']
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckSubscriptionLimitsView(APIView):
    """
    API endpoint to check subscription limits
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Subscriptions'],
        operation_description="Check if user can perform action based on subscription limits",
        request_body=SubscriptionLimitsSerializer(),
        responses={
            200: openapi.Response(
                description="Subscription limits check result",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'allowed': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'remaining': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'limit': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """Check subscription limits"""
        serializer = SubscriptionLimitsSerializer(data=request.data)
        if serializer.is_valid():
            result = SubscriptionService.check_subscription_limits(
                user=request.user,
                action=serializer.validated_data['action']
            )
            return Response(result)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrackUsageView(APIView):
    """
    API endpoint to track user usage
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Subscriptions'],
        operation_description="Track user usage for analytics",
        request_body=UsageTrackingSerializer(),
        responses={
            200: openapi.Response(
                description="Usage tracked successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """Track user usage"""
        serializer = UsageTrackingSerializer(data=request.data)
        if serializer.is_valid():
            UsageTrackingService.track_usage(
                user=request.user,
                action=serializer.validated_data['action'],
                value=serializer.validated_data.get('value', 1)
            )
            return Response({'success': True})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentHistoryView(APIView):
    """
    API endpoint to get user's payment history
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Subscriptions'],
        operation_description="Get user's payment history",
        responses={
            200: PaymentHistorySerializer(many=True),
        }
    )
    def get(self, request):
        """Get user's payment history"""
        try:
            subscription = request.user.subscription
            payments = PaymentHistory.objects.filter(subscription=subscription).order_by('-created_at')
            serializer = PaymentHistorySerializer(payments, many=True)
            return Response(serializer.data)
        except UserSubscription.DoesNotExist:
            return Response([])


# Admin-only views
class SubscriptionAnalyticsView(APIView):
    """
    API endpoint for subscription analytics (admin only)
    """
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        tags=['Admin - Subscriptions'],
        operation_description="Get subscription analytics overview",
        responses={
            200: SubscriptionOverviewSerializer(),
        }
    )
    def get(self, request):
        """Get subscription analytics overview"""
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Basic counts
        total_subscribers = UserSubscription.objects.count()
        active_subscribers = UserSubscription.objects.filter(status='ACTIVE').count()
        trial_users = UserSubscription.objects.filter(status='TRIAL').count()
        cancelled_subscriptions = UserSubscription.objects.filter(status='CANCELLED').count()
        
        # Revenue calculations
        revenue_this_month = PaymentHistory.objects.filter(
            status='COMPLETED',
            created_at__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        revenue_last_month = PaymentHistory.objects.filter(
            status='COMPLETED',
            created_at__gte=last_month_start,
            created_at__lt=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Plan distribution
        plan_distribution = UserSubscription.objects.values('plan__name').annotate(
            count=Count('id')
        ).order_by('-count')
        plan_distribution = {item['plan__name']: item['count'] for item in plan_distribution}
        
        # Churn rate (simplified calculation)
        churn_rate = (cancelled_subscriptions / max(total_subscribers, 1)) * 100
        
        data = {
            'total_subscribers': total_subscribers,
            'active_subscribers': active_subscribers,
            'trial_users': trial_users,
            'cancelled_subscriptions': cancelled_subscriptions,
            'revenue_this_month': revenue_this_month,
            'revenue_last_month': revenue_last_month,
            'plan_distribution': plan_distribution,
            'churn_rate': round(churn_rate, 2)
        }
        
        serializer = SubscriptionOverviewSerializer(data)
        return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    tags=['Subscriptions'],
    operation_description="Process payment webhook",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'payment_id': openapi.Schema(type=openapi.TYPE_STRING),
            'status': openapi.Schema(type=openapi.TYPE_STRING),
            'failure_reason': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={
        200: openapi.Response(
            description="Webhook processed successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: "Bad Request"
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Webhooks don't have user authentication
def payment_webhook(request):
    """Process payment webhook from payment provider"""
    result = BillingService.process_payment_webhook(request.data)
    
    if result['success']:
        return Response(result)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
