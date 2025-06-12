# 🎵 Harmonia Subscription System

Hệ thống subscription toàn diện cho nền tảng âm nhạc Harmonia, hỗ trợ nhiều gói đăng ký, thanh toán, mã giảm giá và theo dõi sử dụng.

## 📋 Tính năng chính

### 🎯 **Subscription Plans**
- **Free Plan**: Miễn phí với tính năng cơ bản
- **Premium**: Gói cá nhân với tính năng cao cấp
- **Family**: Gói gia đình hỗ trợ 6 tài khoản
- **Student**: Giảm giá 50% cho sinh viên
- **Artist Pro**: Gói chuyên nghiệp cho nghệ sĩ

### 💳 **Payment & Billing**
- Tích hợp với các payment gateway
- Webhook xử lý thanh toán tự động
- Lịch sử thanh toán chi tiết
- Hỗ trợ monthly/yearly/lifetime billing

### 🎁 **Promo Codes**
- Mã giảm giá theo phần trăm hoặc số tiền cố định
- Giới hạn số lần sử dụng
- Áp dụng cho gói cụ thể
- Thời gian hiệu lực linh hoạt

### 📊 **Usage Tracking**
- Theo dõi hoạt động người dùng theo ngày
- Giới hạn dựa trên gói đăng ký
- Analytics chi tiết cho admin
- Revenue tracking

## 🗂️ Cấu trúc Models

### SubscriptionPlan
```python
- name: Tên gói
- plan_type: FREE/PREMIUM/FAMILY/STUDENT/ARTIST
- billing_cycle: MONTHLY/YEARLY/LIFETIME
- price: Giá gói
- Features: max_offline_tracks, audio_quality, ads_free, etc.
```

### UserSubscription
```python
- user: Người dùng
- plan: Gói đăng ký
- status: ACTIVE/CANCELLED/EXPIRED/TRIAL/PAUSED
- start_date/end_date: Thời gian hiệu lực
- Usage tracking: offline_tracks_downloaded, playlists_created, etc.
```

### PaymentHistory
```python
- subscription: Subscription liên kết
- amount: Số tiền
- status: PENDING/COMPLETED/FAILED/REFUNDED
- external_payment_id: ID từ payment gateway
```

## 🚀 API Endpoints

### Public Endpoints
- `GET /api/subscriptions/plans/` - Lấy danh sách gói
- `POST /api/subscriptions/payment-webhook/` - Webhook thanh toán

### User Endpoints
- `GET /api/subscriptions/my-subscription/` - Gói hiện tại
- `POST /api/subscriptions/upgrade/` - Nâng cấp gói
- `POST /api/subscriptions/cancel/` - Hủy gói
- `GET /api/subscriptions/payment-history/` - Lịch sử thanh toán
- `POST /api/subscriptions/validate-promo/` - Validate mã giảm giá
- `POST /api/subscriptions/check-limits/` - Kiểm tra giới hạn
- `POST /api/subscriptions/track-usage/` - Theo dõi sử dụng

### Admin Endpoints
- `GET /api/subscriptions/analytics/` - Analytics subscription

## 🛠️ Usage Examples

### 1. Lấy danh sách gói đăng ký
```python
GET /api/subscriptions/plans/

Response:
[
    {
        "id": "uuid",
        "name": "Harmonia Premium (Monthly)",
        "plan_type": "PREMIUM",
        "billing_cycle": "MONTHLY",
        "price": "9.99",
        "monthly_price": "9.99",
        "features_list": [
            "Ad-free listening",
            "High quality audio",
            "Unlimited skips"
        ]
    }
]
```

### 2. Nâng cấp subscription
```python
POST /api/subscriptions/upgrade/
{
    "plan_id": "uuid",
    "payment_method": "stripe",
    "promo_code": "STUDENT50"
}

Response:
{
    "success": true,
    "subscription": {...},
    "payment_required": true,
    "amount": "4.99",
    "promo_discount": "5.00"
}
```

### 3. Kiểm tra giới hạn subscription
```python
POST /api/subscriptions/check-limits/
{
    "action": "skip"
}

Response:
{
    "allowed": true,
    "remaining": 5,
    "limit": 6
}
```

### 4. Theo dõi sử dụng
```python
POST /api/subscriptions/track-usage/
{
    "action": "play_track",
    "value": 1
}
```

## 🔧 Services Architecture

### SubscriptionService
- `get_or_create_free_subscription()` - Tạo free subscription
- `upgrade_subscription()` - Nâng cấp gói
- `cancel_subscription()` - Hủy gói
- `check_subscription_limits()` - Kiểm tra giới hạn

### PromoCodeService
- `validate_and_apply_promo_code()` - Validate và áp dụng mã

### UsageTrackingService
- `track_usage()` - Theo dõi hoạt động

### BillingService
- `process_payment_webhook()` - Xử lý webhook thanh toán

## 📦 Setup & Installation

### 1. Thêm vào INSTALLED_APPS
```python
INSTALLED_APPS = [
    ...
    'subscription_plans',
]
```

### 2. Thêm URLs
```python
# urls.py
urlpatterns = [
    ...
    path('api/subscriptions/', include('subscription_plans.urls')),
]
```

### 3. Run migrations
```bash
python manage.py makemigrations subscription_plans
python manage.py migrate
```

### 4. Tạo default plans
```bash
python manage.py create_default_plans
```

## 🔒 Permission System

- **AllowAny**: Plans listing, webhook
- **IsAuthenticated**: User subscription management
- **IsAdminUser**: Analytics, admin functions

## 📈 Analytics & Reporting

### Subscription Overview
- Total subscribers
- Active/Trial/Cancelled users
- Revenue this month vs last month
- Plan distribution
- Churn rate

### Usage Statistics
- Daily tracking per user
- Aggregate analytics
- Revenue analytics by date

## 🔄 Workflow Examples

### New User Registration
1. User đăng ký → Tự động tạo Free subscription
2. User có thể nâng cấp bất kỳ lúc nào
3. Track usage theo realtime

### Subscription Upgrade
1. User chọn gói mới
2. Validate promo code (nếu có)
3. Tạo payment record
4. Chờ webhook confirmation
5. Active subscription

### Payment Processing
1. Payment gateway gửi webhook
2. System tìm payment record
3. Update subscription status
4. Send confirmation email

## 🚨 Error Handling

- Graceful degradation cho free users
- Retry logic cho failed payments
- Comprehensive logging
- User-friendly error messages

## 🔄 Future Enhancements

- [ ] Celery integration cho async tasks
- [ ] Multi-currency support
- [ ] Advanced analytics dashboard
- [ ] A/B testing cho pricing
- [ ] Machine learning cho churn prediction
- [ ] Integration với email marketing
- [ ] Mobile app subscriptions (iOS/Android)

## 🤝 Integration Points

### Authentication System
- Automatic free subscription creation
- User subscription status middleware

### Music Player
- Quality restrictions based on plan
- Skip limit enforcement
- Download restrictions

### Admin Dashboard
- Subscription analytics
- Revenue reporting
- User management 