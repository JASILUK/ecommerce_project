from django.shortcuts import render
from django.urls import include,path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from apps.products.v1.views import (ColorBasedVariantsView, ColorImageManageView, 
                                    GenaralImageView, ListAndCreateCategory, 
                                    ListCategory, ProductColorManageView, 
                                    PublicProductsView, SellerProductViewSet, UploadFromURLAPIView)

router = DefaultRouter()

router.register('products',PublicProductsView,basename='public-products')
router.register('seller/products',SellerProductViewSet,basename='seller-products')
router.register('admin/category',ListAndCreateCategory,basename='admin-categories')

variant_router = routers.NestedDefaultRouter(router,'products',lookup='product')
product_router = routers.NestedDefaultRouter(router,'seller/products',lookup='product')

variant_router.register('color/variants',ColorBasedVariantsView,basename='color-variants')
product_router.register('color',ProductColorManageView,basename='product-color')

product_router.register('general/images',GenaralImageView,basename='general-images')

color_router  =  routers.NestedDefaultRouter(product_router,'color',lookup='color')

color_router.register('images',ColorImageManageView,basename='color-images')

urlpatterns =[
    path('',include(router.urls)),
    path('',include(product_router.urls)),
    path('',include(color_router.urls)),
    path(
        'seller/products/<slug:product_slug>/color/<int:color_pk>/add-image-url/',
        UploadFromURLAPIView.as_view(),
        name='add-color-image-url'
    ),
        
    path('categories/',ListCategory.as_view(),name='list-category'),
   
]