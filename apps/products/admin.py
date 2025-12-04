from django.contrib import admin
from .models import (
    Products, ProductColor, ProductColorImage,
    ProductVariant, ProductGeneralImage,
    Category, Color, Size
)

from apps.products.admin_forms import ProductGeneralImageForm, ProductColorImageForm

class ProductGeneralImageInline(admin.TabularInline):
    model = ProductGeneralImage
    form = ProductGeneralImageForm
    extra = 1
    show_change_link = True


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    show_change_link = True


@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category","seller", "price", "is_active"]
    inlines = [ProductGeneralImageInline, ProductColorInline]



class ProductColorImageInline(admin.TabularInline):
    model = ProductColorImage
    form = ProductColorImageForm
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ["product", "color"]
    inlines = [ProductColorImageInline, ProductVariantInline]



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active"]


admin.site.register(Color)
admin.site.register(Size)
