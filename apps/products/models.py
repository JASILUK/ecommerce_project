from django.db import models
from  django.utils.text import slugify
import uuid
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from apps.products.managers import CustomProductManager
from mptt.models import TreeForeignKey,MPTTModel
# Create your models here.

User = get_user_model()

class Category(MPTTModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = TreeForeignKey(
        'self', blank=True, null=True,
        on_delete=models.CASCADE,
        related_name='subcategory'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']
 
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1

            while Category.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)
    

    def __str__(self):
        return self.name
    


class Products(models.Model):
    seller = models.ForeignKey(User,on_delete=models.CASCADE,related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.IntegerField( null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    thumbnail = CloudinaryField("product/thumbnails", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    objects = CustomProductManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            while Products.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=50,unique=True)
    code = models.CharField(max_length=7) 

    def __str__(self):
        return self.name
    
class Size(models.Model):
    name = models.CharField(max_length=10,unique=True)  

    def __str__(self):
        return self.name


class ProductColor(models.Model):
    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name="product_colors"
    )
    color = models.ForeignKey(Color, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('product', 'color')

    def __str__(self):
        return f"{self.color.name}"
    

class ProductGeneralImage(models.Model):
    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name="general_images"
    )
    image = CloudinaryField("product/general_images")
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.is_default and not self.product.thumbnail:
            self.product.thumbnail = self.image
            self.product.save()



class ProductColorImage(models.Model):
    product_color = models.ForeignKey(
        ProductColor,
        on_delete=models.CASCADE,
        related_name="color_images"
    )
    image = CloudinaryField("product/colors")

    def __str__(self):
        return str(self.product_color)


class ProductVariant(models.Model):
    product_color = models.ForeignKey(
                ProductColor,
                on_delete=models.CASCADE,
                related_name='variants'
                )    
    stock = models.IntegerField(default=0)
    size = models.ForeignKey(Size,on_delete=models.CASCADE,null=True,blank=True)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('product_color', 'size')  

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"{self.product_color.product.id}-{self.product_color.color.name}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)



