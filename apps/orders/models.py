# apps/orders/models.py
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.orders.managers import CustomeOrderManager

User = get_user_model()

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Payment"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PROCESSING = "PROCESSING", "Processing"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey("users.Address", on_delete=models.SET_NULL, null=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    payment_method = models.CharField(
        max_length=20,
        choices=[
            ("COD", "Cash On Delivery"),
            ("ONLINE", "Online Payment"),
        ]
    )

    status = models.CharField(max_length=20, choices=Status.choices, default="PENDING")
    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomeOrderManager()



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Products", on_delete=models.CASCADE)
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.CASCADE)
    sku = models.CharField(max_length=100)

    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)



class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
        REFUNDED = "REFUNDED"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")

    payment_method = models.CharField(
        max_length=30,
        choices=[
            ("COD", "Cash on Delivery"),
            ("UPI", "UPI"),
            ("CARD", "Card"),
            ("NETBANKING", "Netbanking"),
        ]
    )

    payment_gateway = models.CharField(max_length=50, default="STRIPE")
    gateway_order_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_payment_id = models.CharField(max_length=255, null=True, blank=True)

    gateway_response = models.JSONField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    created_at = models.DateTimeField(auto_now_add=True)
