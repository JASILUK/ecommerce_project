from django.urls  import path,include
from apps.cart.v1.views import AddToCartApi, CartListAPIView, ClearCartApiView, RemoveCartItemAPIView, UpdateCartItem

urlpatterns = [
    path('add/item/',AddToCartApi.as_view(),name='add_to_cart_api'),
    path('update/item/',UpdateCartItem.as_view(),name='update-cart-item-api'),
    path('get/cart/',CartListAPIView.as_view(),name='list_cart_api'),
    path('cart/remove/<int:variant_id>/',RemoveCartItemAPIView.as_view(),name='remove_cart_api'),
    path('cart/clear/',ClearCartApiView.as_view(),name='cart_clear_api')

]   