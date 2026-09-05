from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('payment/<int:member_id>/', views.payment_view, name='payment'),
    path('payment/success/<int:member_id>/', views.payment_success_view, name='payment_success'),

    # API endpoints
    path('api/payment/status/<uuid:transaction_id>/', views.check_payment_status, name='check_payment_status'),
    path('api/payment/verify/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('api/payment/webhook/', views.payment_webhook, name='payment_webhook'),
]

