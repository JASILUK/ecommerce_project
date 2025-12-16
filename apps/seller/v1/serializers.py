# apps/seller/serializers.py

from rest_framework import serializers
from apps.orders.models import OrderItem
from apps.orders.models import Order

class SellerOrderSerializer(serializers.ModelSerializer):
    buyer = serializers.CharField(source="user.username")

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "total",
            "payment_method",
            "is_paid",
            "status",
            "created_at"
        ]


class SellerOrderItemDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")

    class Meta:
        model = OrderItem
        fields = [
            "product_name",
            "sku",
            "quantity",
            "unit_price",
            "final_price",
            "line_total",
        ]


class SellerOrderDetailSerializer(serializers.ModelSerializer):
    buyer = serializers.CharField(source="user.username")
    items = SellerOrderItemDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "payment_method",
            "is_paid",
            "status",
            "address",
            "items",
            "total",
            "created_at"
        ]
