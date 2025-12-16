from django.urls import path,include 
from apps.orders.v1.views import CheckoutAPIView, CreateOrderAPIView, MyOrderListView, StripeVerifyPayment, stripe_webhook
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('myorders',MyOrderListView,basename='my-orders')
urlpatterns = [
    path('checkout/', CheckoutAPIView.as_view(), name='checkout'),
    path('create/',CreateOrderAPIView.as_view(),name='create_order_api'),
    path('payment/varify/',StripeVerifyPayment.as_view(),name='strip_varify_api'),
    path('payment/webhook/stripe/',stripe_webhook,name='stripe-webhook-api'),
    path('',include(router.urls))
]