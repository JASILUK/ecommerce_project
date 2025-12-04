from django.urls import include, path

urlpatterns = [
    path('v1/',include('apps.cart.v1.urls'))
]   