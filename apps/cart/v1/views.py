import json
from urllib import response
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.cart.models import Cart, CartItem
from apps.cart.v1.serializers import AddToCartSerializer, CartListSerializer, CartVariantSerializer
from apps.cart.services import AddToCartService, ListCartService
from apps.products.models import ProductVariant
from django_redis import get_redis_connection

cart_redis = get_redis_connection("cart")

class AddToCartApi(APIView):
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant_id = serializer.validated_data["variant_id"]
        qty = serializer.validated_data["quantity"]
        try :
            qty =int(qty)
        except ValueError:
            return Response({'error':'quantity must be an integer'},status =400)
        if variant_id is None or qty is None:
            return Response({"error": "variant_id and quantity are required"}, status=400)
        try:
            variant = ProductVariant.objects.get(id=variant_id, is_active=True)
        except ProductVariant.DoesNotExist:
            return Response({"error": "Variant not found"}, status=404)
        
        session_id = request.COOKIES.get("guest_session")
        session_id = AddToCartService.get_or_create_session_id(session_id)

        redis_key = AddToCartService.get_redis_key(request.user, session_id)
        existing = cart_redis.hget(redis_key,f"variant:{variant_id}")
        extra_qty = 0
        if existing:
            extra_qty += json.loads(existing).get("qty",0)
        ok, msg = AddToCartService.validate_stock(variant, qty,extra_qty)
        if not ok:
            return Response({"error": msg}, status=400)

        AddToCartService.save_to_redis(redis_key, variant, qty)

        response = Response({"message": "Item added to cart"}, status=201)

        if not request.user.is_authenticated:
            response.set_cookie(
                "guest_session",
                session_id,
                max_age=7*24*3600,  
                path="/"
            )
        return response

    
class UpdateCartItem(APIView):
    def patch(self,request):
        variant_id = request.data.get("variant_id")
        qty = request.data.get("quantity")
        success,result = AddToCartService.validate_data(variant_id,qty)
        if not success:
            return Response({"error":result},status=400)
        variant,qty = result
        session_id = request.COOKIES.get("guest_session")
        session_id = AddToCartService.get_or_create_session_id(session_id)

        redis_key = AddToCartService.get_redis_key(request.user, session_id)
        ok, msg = AddToCartService.update_qty(redis_key, variant, qty)
        if not ok:
            return Response({"error": msg}, status=400)

        response = Response({"message": "Quantity updated"}, status=200)
        if not request.user.is_authenticated:
            response.set_cookie("guest_session", session_id, max_age=7*24*3600, path="/")

        return response

class CartListAPIView(APIView):

    def get(self, request):
        session_id = request.COOKIES.get("guest_session")

        redis_key = ListCartService.get_redis_key(request.user, session_id)
        redis_data = ListCartService.read_from_redis(redis_key)

        if not redis_data:
            if request.user.is_authenticated:
                cart = ListCartService.load_db_cart(request.user)
                if not cart:
                    return Response({"cart_items": [], "total_items": 0, "total_price": 0})
                ListCartService.restore_redis_from_db(redis_key,cart)
                serializer = CartListSerializer(cart)
                return Response(serializer.data)
            else:
                return Response({"cart_items": [], "total_items": 0, "total_price": 0})

        response =  ListCartService.build_response_from_redis(redis_data)
        return response

class RemoveCartItemAPIView(APIView):

    def delete(self, request, variant_id):
        try:
            variant = ProductVariant.objects.get(pk=variant_id)
        except ProductVariant.DoesNotExist:
            return Response({"error": "Invalid variant"}, status=404)

        session_id = request.COOKIES.get("guest_session")
        session_id = AddToCartService.get_or_create_session_id(session_id)

        redis_key = AddToCartService.get_redis_key(request.user, session_id)

        cart_redis.hdel(redis_key, f"variant:{variant_id}")
        if request.user.is_authenticated:
            CartItem.objects.filter(
                cart__user=request.user,
                variant=variant
            ).delete()

        return Response({"message": "Item removed"}, status=200)


class ClearCartApiView(APIView):

    def delete(self, request):

        session_id = request.COOKIES.get("guest_session")
        session_id = AddToCartService.get_or_create_session_id(session_id)

        redis_key = AddToCartService.get_redis_key(request.user, session_id)

        cart_redis.delete(redis_key)

        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                CartItem.objects.filter(cart=cart).delete()

        return Response({"message": "Cart cleared"}, status=200)
