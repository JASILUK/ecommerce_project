from django.urls import path , include

urlpatterns = [
    path('v1/',include('apps.orders.v1.urls'))
]