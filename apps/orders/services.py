from decimal import Decimal
import json
from django.db import transaction
from apps.orders.models import Order, OrderItem, Payment
from apps.products.models import ProductVariant
from django.core.exceptions import ValidationError

from apps.users.models import Address
from apps.users.v1.serializers import AddressSerializer
from django_redis import get_redis_connection
import stripe

redis_client = get_redis_connection("cart")
class CheckoutReviewService:

    def __init__(self, user, items_input: dict):
       
        self.user = user
        self.items_input = items_input
        self.warnings = []
        self.order_items = []
        self.subtotal = Decimal("0.00")
        self.total_discount = Decimal("0.00")

    def review(self):
        with transaction.atomic():
            variants = self._load_variants()
            self._process_items(variants)
            totals = self._calculate_totals()
            address = self._get_default_address()
        return {
            "items": self.order_items,
            "subtotal": totals["subtotal"],
            "total_discount": totals["total_discount"],
            "shipping_charges": totals["shipping_charges"],
            "tax_amount": totals["tax_amount"],
            "grand_total": totals["grand_total"],
            "warnings": self.warnings,
            "address" : address
        }

    def _get_default_address(self):
        try:
            address = Address.objects.get(user = self.user,is_default=True)
            if address:
                return AddressSerializer(address).data
        except:
            return None
    def _load_variants(self):
        variant_ids = list(self.items_input.keys())

        variants_qs = ProductVariant.objects.select_related("product_color__product").filter(id__in=variant_ids)

        variants_map = {v.id: v for v in variants_qs}

        for vid in variant_ids:
            if vid not in variants_map:
                raise ValidationError(f"Product variant {vid} not found.")

        return variants_map

    def _process_items(self, variants_map):
        for vid, item in self.items_input.items():

            variant = variants_map[vid]
            product = variant.product_color.product
            qty = item["qty"]

            
            if variant.stock < qty:
                raise ValidationError(
                    f"{product.name} has only {variant.stock} in stock."
                )

            current_price = product.price
            discount = product.discount_percentage or 0
            discounted = self._apply_discount(current_price, discount)

        
            if "price" in item:
                if Decimal(item["price"]) != current_price:
                    self.warnings.append(
                        f"Price updated for {product.name}. New price: {current_price}"
                    )
                if item["offer"] != discount:
                    self.warnings.append(
                        f"offer updated for{product.name} New Offer: {discount}"
                    )
        
            line_total = (discounted * qty).quantize(Decimal("0.01"))
            discount_amount = ((current_price - discounted) * qty).quantize(Decimal("0.01"))

            self.subtotal += line_total
            self.total_discount += discount_amount

            self.order_items.append({
                "variant_id": variant.id,
                "product_name": product.name,
                "sku": variant.sku,
                "quantity": qty,
                "unit_price": current_price,
                "discount_percentage": discount,
                "discounted_price": discounted,
                "line_total": line_total,
                "stock_available": variant.stock,
            })

    def _apply_discount(self, price, discount):
        price = price or Decimal("0.00")
        discount = discount or 0
        return ((price * (100 - discount)) / Decimal(100)).quantize(Decimal("0.01"))

    def _calculate_totals(self):
        shipping = Decimal("0.00")
        tax_rate = Decimal("0.00")
        tax = (self.subtotal * tax_rate / 100).quantize(Decimal("0.01"))
        grand_total = (self.subtotal + shipping + tax).quantize(Decimal("0.01"))

        return {
            "subtotal": self.subtotal.quantize(Decimal("0.01")),
            "total_discount": self.total_discount.quantize(Decimal("0.01")),
            "shipping_charges": shipping,
            "tax_amount": tax,
            "grand_total": grand_total,
        }



class CreateOrderService:
    def __init__(self, user, payment_method, address_id, source="cart", product_variant_id=None, qty=None):
        self.user = user
        self.payment_method = payment_method
        self.address_id = address_id
        self.source = source
        self.product_variant_id = product_variant_id
        self.qty = qty

        self.subtotal = Decimal("0.00")
        self.shipping = Decimal("0.00")
        self.total = Decimal("0.00")

    def create(self):
        with transaction.atomic():
            self._validate_address()

            items = self._load_items()
            variants = self._lock_variants(items)

            order = self._create_order()

            order_items = self._build_order_items(order, items, variants)
            OrderItem.objects.bulk_create(order_items)

            order.subtotal = self.subtotal
            order.total = self.subtotal + self.shipping
            order.save(update_fields=["subtotal", "total"])

            if self.payment_method == "STRIPE":
                return self._init_stripe_payment(order)

           
            self._reduce_stock(variants, items)
            self._clear_cart()
            order.payment_method ='COD'
            order.status = "CONFIRMED"
            order.save(update_fields=["status"])


            return order, None

    def _validate_address(self):
        if not Address.objects.filter(id=self.address_id, user=self.user).exists():
            raise ValidationError("Invalid address")

    def _load_items(self):
        if self.source == "cart":
            cart_key = f"cart:user:{self.user.id}"
            raw = redis_client.hgetall(cart_key)
            if not raw:
                raise ValidationError("Cart empty")

            data = {}
            for k, v in raw.items():
                k = k.decode() if isinstance(k,bytes) else k
                v = v.decode()  if isinstance(v,bytes) else v
                id = int(k.split(':')[-1])
                item = json.loads(v)
                data[id] = int(item['qty'])
            return data

        return {int(self.product_variant_id): int(self.qty)}

    def _lock_variants(self, items):
        ids = list(items.keys())
        qs = ProductVariant.objects.select_for_update().select_related(
            "product_color__product"
        ).filter(id__in=ids)

        variant_map = {v.id: v for v in qs}

        for vid in ids:
            if vid not in variant_map:
                raise ValidationError("Variant not found")

        return variant_map

    def _create_order(self):
        return Order.objects.create(
            user=self.user,
            address_id=self.address_id,
            payment_method=self.payment_method,
        )

    def _build_order_items(self, order, items, variants):
        objs = []

        for vid, qty in items.items():
            v = variants[vid]

            if v.stock < qty:
                raise ValidationError(f"{v.product_color.product.name} out of stock")

            price = v.product_color.product.price
            discount = v.product_color.product.discount_percentage or 0
            final_price = self._apply_discount(price, discount)
            line_total = final_price * qty

            objs.append(OrderItem(
                order=order,
                product=v.product_color.product,
                variant=v,
                sku=v.sku,
                quantity=qty,
                unit_price=price,
                discount=discount,
                final_price=final_price,
                line_total=line_total
            ))

            self.subtotal += line_total

        return objs

    def _apply_discount(self, price, discount):
        return ((price * (100 - discount)) / 100).quantize(Decimal("0.01"))
    
    def _clear_cart(self):
        cart_key = f"cart:user:{self.user.id}"
        redis_client.delete(cart_key)


    def _reduce_stock(self, variants, items):
        for vid, qty in items.items():
            v = variants[vid]
            v.stock -= qty
            v.save(update_fields=["stock"])

    def _init_stripe_payment(self, order):
        intent = stripe.PaymentIntent.create(
            amount=int(order.total * 100),
            currency="inr",
            metadata={"order_id": order.id}
        )
        order.payment_method ="ONLINE"
        order.save()
        Payment.objects.create(
            order=order,
            amount=order.total,
            payment_gateway="stripe",
            gateway_order_id=intent.id,
            status="CREATED"
        )

        return order, intent.client_secret


