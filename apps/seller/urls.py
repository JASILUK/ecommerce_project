from django.urls import include,path

urlpatterns =[
    path('v1/',include('apps.seller.v1.urls'))
]