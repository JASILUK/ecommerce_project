from django.urls import include,path

urlpatterns =[
    path('v1/',include('apps.products.v1.urls'))
]