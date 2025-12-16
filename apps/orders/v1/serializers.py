from rest_framework import serializers
from decimal import Decimal
from apps.orders.models import Order, OrderItem
from apps.products.models import ProductVariant, Products
from django.contrib.auth import get_user_model

User = get_user_model()

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = getattr(__import__('apps.users.models', fromlist=['Address']), 'Address')
        fields = ('id','full_name','phone','address_line','city','state','pincode','country','is_default')

class OrderReviewItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    sku = serializers.CharField()
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = serializers.IntegerField(allow_null=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    in_stock = serializers.BooleanField()
    stock_available = serializers.IntegerField()

class CheckoutRequestSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=['cart', 'buy_now'])
    variant_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(required=False, min_value=1)

    def validate(self, data):
        mode = data.get('mode')
        if mode == 'buy_now':
            if not data.get('variant_id'):
                raise serializers.ValidationError("variant_id required for buy_now")
            if not data.get('quantity'):
                data['quantity'] = 1
        return data

class OrderReviewResponseSerializer(serializers.Serializer):
    items = OrderReviewItemSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    shipping_charges = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    grand_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    addresses = AddressSerializer(many=True)
    default_address_id = serializers.IntegerField(allow_null=True)
    warnings = serializers.ListField(child=serializers.CharField(), allow_empty=True)





class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    variant_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "variant_image",
            "sku",
            "unit_price",
            "quantity",
            "discount",
            "final_price",
            "line_total",
            
        ]

    def get_variant_image(self, obj):
        color = getattr(obj.variant.product_color, "prefetched_color_images", None)

        if color :
            try:
                return str(color[0].image)
            except:
                return color[0].image.url
        return None


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "total",
            "status",
            "is_paid",
            "created_at",
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "is_paid",
            "subtotal",
            "shipping",
            "total",
            "payment_method",
            "created_at",
            "items",
        ]