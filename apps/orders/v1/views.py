from django.forms import ValidationError
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.cart import redis_client
from apps.orders.models import Order, Payment
from apps.orders.v1.serializers import CheckoutRequestSerializer, OrderDetailSerializer, OrderListSerializer
from apps.orders.services import CheckoutReviewService, CreateOrderService
from django.db import transaction
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from apps.cart.services import ListCartService
from django.db.models import Prefetch
from apps.cart.redis_client import redis_clint
from apps.products.models import ProductColorImage

class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):   
        serializer = CheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mode = data['mode']
        items_input = {}   
        if mode == 'cart':
            redis_key  = ListCartService.get_redis_key(request.user)
            redis_data = ListCartService.read_from_redis(redis_key)
            if not redis_data:
                cart = ListCartService.load_db_cart(request.user)
                if not cart:
                    return Response({"detail":"Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
                ListCartService.restore_redis_from_db(cart)
                redis_data = ListCartService.read_from_redis(redis_key)
            items_input = redis_data
        else:  
            variant_id = data['variant_id']
            qty = data.get('quantity', 1)
            items_input= {variant_id: {'qty': qty}} 

        with transaction.atomic():
            try:
                checkout_handler = CheckoutReviewService(request.user,items_input)
                result_data = checkout_handler.review()
                return Response(data=result_data,status=200)
            except ValidationError as err:
                return Response({'error':str(err)},status=400)



class CreateOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            service = CreateOrderService(
            user=request.user,
            payment_method=request.data["payment_method"],
            address_id=request.data["address"],
            source=request.data.get("source", "cart"),
            product_variant_id=request.data.get("variant_id"),
            qty=request.data.get("qty"),
            )

            order, client_key = service.create()

            if client_key:
                return Response({
                    "order_id": order.id,
                    "payment_required": True,
                    "client_secret": client_key
                })

            return Response({
                "order_id": order.id,
                "payment_required": False
            })
        
        except ValidationError as err:
            return Response({'error':str(err)},status=400)
            


class MyOrderListView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .my_products(self.request.user)
            .prefetch_related(
                Prefetch(
                    "items__variant__product_color__color_images",
                    queryset=ProductColorImage.objects.only("id", "image"),
                    to_attr="prefetched_color_images"
                )
            )
            )
    
    def get_serializer_class(self):
        if self.action =="list":
            return OrderListSerializer
        return OrderDetailSerializer    



class StripeVerifyPayment(APIView):
    def post(self, request):
        payment_intent_id = request.data.get("payment_intent_id")
        order_id = request.data.get("order_id")

        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status == "succeeded":
            payment = Payment.objects.get(order_id=order_id)
            order = payment.order

            payment.status = "SUCCESS"
            payment.gateway_response = intent
            payment.save()

            order.status = "CONFIRMED"
            order.is_paid =True
            order.save()

            return Response({"status": "payment_success"})

        return Response({"status": "payment_failed"}, status=400)







@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    event = stripe.Webhook.construct_event(
        payload,
        sig_header,
        settings.STRIPE_WEBHOOK_SECRET
    )

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        pid = intent["id"]

        try:
            payment = Payment.objects.get(gateway_order_id=pid)
            order = payment.order
            
            cart_key = f"cart:user:{order.user.id}"
            redis_clint.delete(cart_key)

            payment.status = "SUCCESS"
            payment.gateway_payment_id = pid
            payment.save()

            order.status = "CONFIRMED"
            order.is_paid = True
            order.save()
        except Payment.DoesNotExist:
            return JsonResponse({"error": "Payment not found"}, status=404)


    return JsonResponse({"status": "ok"})
