import uuid
import json
from django.db import transaction
from apps.cart.models import Cart, CartItem
from apps.cart.v1.serializers import CartVariantSerializer
from apps.products.models import ProductColorImage, ProductVariant
from rest_framework.response import Response
from datetime import datetime
from django_redis import get_redis_connection
from django.db.models import Prefetch

cart_redis = get_redis_connection("cart")


class AddToCartService:

    @staticmethod
    def validate_stock(variant, qty,extra_qty=0):
        if extra_qty:
            total_qty = qty +extra_qty
        else:
            total_qty =qty
        if total_qty > variant.stock:
            return False, f"Only {variant.stock} items available"
        if total_qty > 10:
            return False, "Maximum quantity per item is 10"
        return True, None
    
    @staticmethod
    def get_or_create_session_id(session_id):
        return session_id or str(uuid.uuid4())


    @staticmethod
    def get_redis_key(user, session_id):
        if user and user.is_authenticated:
            return f"cart:user:{user.id}"
        return f"cart:guest:{session_id}"


    @staticmethod
    def save_to_redis(redis_key, variant, qty):
        existing = cart_redis.hget(redis_key, f"variant:{variant.id}")
        
        if existing:
            try:
                existing = existing.decode() if isinstance(existing,bytes) else existing
                data = json.loads(existing)
                data["qty"] += qty
            except json.JSONDecodeError:
                data = {    
                    "qty": qty,
                    "price": float(variant.product_color.product.price),
                    "offer": variant.product_color.product.discount_percentage,
                }
        else:
            data = {
                "qty": qty,
                "price": float(variant.product_color.product.price),
                "offer": variant.product_color.product.discount_percentage,
            }
        data["updated_at"] = datetime.utcnow().isoformat()

        cart_redis.hset(
            redis_key,
            f"variant:{variant.id}",
            json.dumps(data)
        )

    @staticmethod
    @transaction.atomic
    def save_to_db(user, variant, qty):

        cart, created = Cart.objects.get_or_create(user=user)

        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={
                "quantity": qty,
                "price_at_add": variant.product_color.product.price,
                "discount_percentage_at_add": variant.product_color.product.discount_percentage,
                "stock_at_add": variant.stock
            }
        )

        if not item_created:
            new_qty = cart_item.quantity + qty

            if new_qty > variant.stock:
                raise ValueError(f"Only {variant.stock} items available")

            cart_item.quantity = new_qty
            cart_item.save()
    @staticmethod
    def validate_data(variant_id,qty):
        if not variant_id or qty is None:
            return False,  "variant_id and quantity required"

        try:
            qty = int(qty)
        except ValueError:
            return False, "quantity must be an integer"

        if qty < 1:
            return False ,"quantity must be >= 1" 

        try:
            variant = ProductVariant.objects.get(id=variant_id, is_active=True)
        except ProductVariant.DoesNotExist:
            return False,"Variant not found" 
        return True , (variant,qty)
    
    @staticmethod
    def update_qty(redis_key, variant, new_qty):
        redis_field = f"variant:{variant.id}"
        existing = cart_redis.hget(redis_key, redis_field)

        if not existing:
            return False, "Item not in cart"

        try:
            existing = existing.decode() if isinstance(existing,bytes) else existing
            data = json.loads(existing)
        except json.JSONDecodeError:
            return False, "Corrupted cart data"

        if new_qty > variant.stock:
            return False, f"Only {variant.stock} items available"

        if new_qty > 10:
            return False, "Maximum quantity per item is 10"

        data["qty"] = new_qty
        data["updated_at"] = datetime.utcnow().isoformat()

        cart_redis.hset(redis_key, redis_field, json.dumps(data))
        return True, None



class ListCartService:

    @staticmethod
    def get_redis_key(user, session_id):
        if user.is_authenticated:
            return f"cart:user:{user.id}"
        return f"cart:guest:{session_id}"

    @staticmethod
    def read_from_redis(redis_key):
        all_cart_data = cart_redis.hgetall(redis_key)  
        data = {}

        for key, value in all_cart_data.items():
            key = key.decode() if isinstance(key, bytes) else key
            value = value.decode() if isinstance(value, bytes) else value
            value = json.loads(value)

            variant_id = int(key.split(":")[-1])
            data[variant_id] = value

        return data

    @staticmethod
    def load_db_cart(user):
        try:
            return (
                Cart.objects
                .select_related("user")
                .prefetch_related(
                    "cart_items__variant__product_color__product"
                )
                .get(user=user)     
            )
        except Cart.DoesNotExist:
            return None
        
    @staticmethod
    def restore_redis_from_db(redis_key, cart):
        pipe = cart_redis.pipeline()
        for item in cart.cart_items.all():
            data = {
                "qty": item.quantity,
                "price": float(item.price_at_add),
                "offer": item.discount_percentage_at_add,
            }
            pipe.hset(redis_key, f"variant:{item.variant.id}", json.dumps(data))
        pipe.execute()

    @staticmethod
    def build_response_from_redis(redis_data):
        variant_ids = list(redis_data.keys())

        variants = ProductVariant.objects.filter(
            id__in=variant_ids
        ).select_related("product_color__product").prefetch_related(
            Prefetch("product_color__color_images",
                     queryset=ProductColorImage.objects.order_by("id").only("image"),
                     to_attr="prefetched_color_images")
        )

        items = []
        total_price = 0

        for variant in variants:
            item = redis_data[variant.id]
            final_price = item["price"] - (item["price"] * item.get("offer", 0) / 100)
            item_total = final_price * item["qty"]   

            items.append({
                "variant": CartVariantSerializer(variant).data,
                "quantity": item["qty"],
                "price_at_add": item["price"],
                "discount_percentage_at_add": item.get("offer"),
                "final_price": final_price,
                "item_total_price" : item_total
            })

            total_price += item_total

        return Response({
            "cart_items": items,
            "total_items": len(items),
            "total_price": total_price
        },status=200)



class CartMergeService:

    @staticmethod
    def merge_guest_to_user(session_id, user):
        guest_key = f"cart:guest:{session_id}"
        user_key = f"cart:user:{user.id}"

        guest_data = cart_redis.hgetall(guest_key)
        if not guest_data:
            return True

        user_data = cart_redis.hgetall(user_key)

        def decode(raw):
            out = {}
            for field, val in raw.items():
                field = field.decode() if isinstance(field, bytes) else field
                val = val.decode() if isinstance(val, bytes) else val
                variant_id = int(field.split(":")[-1])
                out[variant_id] = json.loads(val)
            return out

        guest_items = decode(guest_data)
        user_items = decode(user_data)

        for variant_id, g_item in guest_items.items():
            if variant_id in user_items:
                user_items[variant_id]["qty"] += g_item["qty"]
            else:
                user_items[variant_id] = g_item

        variant_ids = list(user_items.keys())
        variants = ProductVariant.objects.filter(id__in=variant_ids)
        variant_map = {v.id: v for v in variants}

        for variant_id, item in user_items.items():
            variant = variant_map.get(variant_id)
            if not variant:
                continue

            if item["qty"] > variant.stock:
                item["qty"] = variant.stock

        pipeline = cart_redis.pipeline()

        for variant_id, data in user_items.items():
            pipeline.hset(
                user_key,
                f"variant:{variant_id}",
                json.dumps(data)
            )

        pipeline.delete(guest_key)
        
        pipeline.execute()  
        return True 