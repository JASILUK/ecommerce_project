from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import json
from datetime import datetime
from apps.cart.models import Cart, CartItem
from apps.products.models import ProductVariant
from django_redis import get_redis_connection


class Command(BaseCommand):
    help = "Sync Redis carts to DB periodically with bulk operations"

    def handle(self, *args, **kwargs):
        redis = get_redis_connection("cart")

        cursor = 0
        pattern = "cart:user:*"

        self.stdout.write("Starting optimized cart sync job...")

        while True:
            cursor, keys = redis.scan(cursor=cursor, match=pattern, count=200)

            for key in keys:
                try:
                    self.sync_single_cart(redis, key)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error syncing {key}: {e}"))

            if cursor == 0:
                break

        self.stdout.write(self.style.SUCCESS("Cart sync completed successfully."))



    def sync_single_cart(self, redis, key):

        user_id = int(key.split(":")[-1])

        last_sync = redis.get(f"{key}:last_sync")

        if last_sync:
            last_sync_dt = datetime.fromisoformat(last_sync)
        else:
            last_sync_dt = datetime.min


        cart_data = redis.hgetall(key)
        if not cart_data:
            return

        variant_ids = [
            int(field.split(":")[-1]) for field in cart_data.keys()
        ]

        variant_map = {
            v.id: v for v in ProductVariant.objects.filter(id__in=variant_ids)
        }

        new_items = []      
        update_items = []    
        existing_items = {
            item.variant_id: item
            for item in CartItem.objects.filter(cart__user_id=user_id)
        }

        cart, _ = Cart.objects.get_or_create(user_id=user_id)

        for field, raw in cart_data.items():
            variant_id = int(field.split(":")[-1])

            variant = variant_map.get(variant_id)
            if not variant:
                continue

            data = json.loads(raw)

            updated_at = datetime.fromisoformat(data.get("updated_at"))
            if updated_at <= last_sync_dt:
                continue  

            qty = data["qty"]

            if variant_id in existing_items:
                item = existing_items[variant_id]
                item.quantity = qty
                update_items.append(item)

            else:
                new_items.append(
                    CartItem(
                        cart=cart,
                        variant=variant,
                        quantity=qty,
                        price_at_add=data["price"],
                        discount_percentage_at_add=data["offer"],
                    )
                )


        with transaction.atomic():
            if new_items:
                CartItem.objects.bulk_create(new_items, batch_size=100)

            if update_items:
                CartItem.objects.bulk_update(update_items, ["quantity"], batch_size=100)

        redis.set(f"{key}:last_sync", datetime.utcnow().isoformat())
