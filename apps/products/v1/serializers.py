from email.policy import default
from pyexpat import model
from rest_framework import serializers
from apps.products.models import Category, Color, ProductColor, ProductColorImage, ProductGeneralImage, ProductVariant, Products, Size 

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','slug','parent']

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['name','code']

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id','name']

class ProductGeneralImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False,write_only=True)          
    genral_image = serializers.SerializerMethodField()
    class Meta:
        model = ProductGeneralImage
        fields = ['image','genral_image']
    def get_genral_image(self,obj):
        try:
            return obj.image.url
        except:
            return str(obj.image)
    

class ProductColorImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False,write_only=True)          
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = ProductColorImage
        fields = ['image','image_url']
    def get_image_url(self,obj):
        try:
            return obj.image.url
        except:
            return str(obj.image)
    

class PublicProductVariantSerializer(serializers.ModelSerializer):
    size = serializers.CharField(source='size.name',required=False)
    class Meta :
        model = ProductVariant
        fields = ['id','stock','size','sku']


class ProductColorSerializer(serializers.ModelSerializer):
    color = ColorSerializer()
    images = ProductColorImageSerializer(source = 'color_images',many =True)
    variants = PublicProductVariantSerializer(many=True)
    class Meta:
        model = ProductColor
        fields = ['id','color','images','variants']



class PublicProductListSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    general_images = ProductGeneralImageSerializer(many =True)
    class Meta:
        model = Products
        fields = [
            "id",
            "slug",
            "name",
            "thumbnail_url",
            "price",
            "discount_percentage",
            "discount_amount",
            "final_price",
            "general_images",
        ]

    def get_thumbnail_url(self, obj):
        if not obj.thumbnail:
            return None
        try:
            return obj.thumbnail.url
        except:
            return str(obj.thumbnail)
    
    def get_discount_amount(self,obj):
        return obj.price * obj.discount_percentage /100

    def get_final_price(self, obj):
        return obj.price - (obj.price * obj.discount_percentage / 100)


class PublicProductDetailSerializer(serializers.ModelSerializer):
    discount_amount = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    general_images = ProductGeneralImageSerializer(many=True)
    colors = ProductColorSerializer(source = 'product_colors',many=True)
    class Meta:
        model = Products
        fields = [
            "id",
            "slug",
            "name",
            'description',
            "price",
            "discount_percentage",
            "discount_amount",
            "final_price",
            "general_images",
            "thumbnail_url",
            "colors"
            
        ]
    def get_thumbnail_url(self, obj):
        if not obj.thumbnail:
            return None
        try:
            return obj.thumbnail.url
        except:
            return str(obj.thumbnail)
        
    def get_discount_amount(self,obj):
        return obj.price * obj.discount_percentage /100

    def get_final_price(self, obj):
        return obj.price - (obj.price * obj.discount_percentage / 100)



class SellerProductListSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    class Meta:
        model = Products
        fields = ['name','slug','price','is_active','is_blocked','thumbnail_url']

        read_only_fields = ["is_blocked"]

    def get_thumbnail_url(self,obj):
        if not obj.thumbnail:
            return None
        try:
            return obj.thumbnail.url
        except:
            return str(obj.thumbnail)
    

class SellerProdctsDetailedSerializer(PublicProductDetailSerializer):
    class Meta(PublicProductDetailSerializer.Meta):
        fields = PublicProductDetailSerializer.Meta.fields+[
            'is_active','is_blocked','created_at','updated_at'
        ]
        read_only_fields = ["is_blocked"]
    


class SellerCreatProductSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    thumbnail = serializers.ImageField(required = False ,write_only =True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(is_active=True))
    class Meta :
        model = Products
        fields = ['name','description','price','discount_percentage','is_active','thumbnail_url','category','thumbnail']
    def get_thumbnail_url(self,obj):
        if not obj.thumbnail:
            return None
        try:
            return obj.thumbnail.url
        except:
            return str(obj.thumbnail)   
        
class CreateUpdateProductColorSL(serializers.ModelSerializer):
    class Meta :
        model = ProductColor
        fields = ['color']  

class createGeneralimagesSL(ProductGeneralImageSerializer):
    image = serializers.SerializerMethodField()
    class Meta(ProductGeneralImageSerializer.Meta):
        fields = ['id']+ProductGeneralImageSerializer.Meta.fields



class ColorImagesListSL(ProductColorImageSerializer):
    class Meta(ProductColorImageSerializer.Meta):
        fields = ['id']+ProductColorImageSerializer.Meta.fields

    
class ColorBasedVariantsListSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    class Meta:
        model = ProductVariant
        fields = ['id','stock','size','sku','images']
        read_only_fields = ['id','sku','images']
        
    def get_images(self,obj):
        return ColorImagesListSL(data = obj.product_color.color_images.all(),many=True).data


class sellerColorBasedVariantsListSerializer(ColorBasedVariantsListSerializer):
    class Meta(ColorBasedVariantsListSerializer.Meta):
        fields = ColorBasedVariantsListSerializer.Meta.fields+['is_active']



class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'is_active']


class CategorySerializer(serializers.ModelSerializer):
    subcategory = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'is_active', 'subcategory']

class CategoryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'is_active']
        read_only_fields = ['slug']

