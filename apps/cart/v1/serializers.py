from rest_framework import serializers
from rest_framework import serializers
from apps.cart.models import Cart, CartItem
from apps.products.models import ProductVariant



class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value =1)



class CartVariantSerializer(serializers.ModelSerializer):
    size = serializers.StringRelatedField()
    product_name = serializers.CharField(source="product_color.product.name", read_only=True)
    thumbnail = serializers.SerializerMethodField()
    color_name = serializers.StringRelatedField(source = "product_color")
    slug = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ["id", "sku","color_name","slug",  "product_name","size", "thumbnail"]
    def get_slug(self,obj):
        return obj.product_color.product.slug
    def get_thumbnail(self, obj):
        img = getattr(obj.product_color,"prefetched_color_images",[])

        if img :
            try:
                return img[0].image.url
            except:
                return str(img[0].image)
        else:
            if not obj.product_color.product.thumbnail:
                return None
            try:
                return obj.product_color.product.thumbnail.url
            except:
                str(obj.product_color.product.thumbnail)
       
    
class CartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField(source = 'variant.id', read_only = True)
    variant = CartVariantSerializer(read_only=True)
    final_price = serializers.SerializerMethodField()
    item_total_price = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant_id",
            "variant",
            "quantity",
            "price_at_add",
            "discount_percentage_at_add",
            "final_price",
            "item_total_price"
        ]

    def get_final_price(self, obj):
        if obj.discount_percentage_at_add:
            return obj.price_at_add - (
                obj.price_at_add * obj.discount_percentage_at_add / 100
            )
        return obj.price_at_add
    def get_item_total_price(self,obj):
        final_price = self.get_final_price(obj) 
        return final_price * obj.quantity


class CartListSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "cart_items", "total_items", "total_price"]

    def get_total_items(self, obj):
        return obj.cart_items.count()

    def get_total_price(self, obj):
        total = 0
        for item in obj.cart_items.all():
            if item.discount_percentage_at_add:
                final_price = item.price_at_add - (
                    item.price_at_add * item.discount_percentage_at_add / 100
                )
            else:
                final_price = item.price_at_add

            total += final_price * item.quantity   
            return total


