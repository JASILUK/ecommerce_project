# apps/seller/urls.py

from django.urls import path
from apps.seller.v1.views import SellerDashboardSummaryView, SellerOrderListView, SellerOrderDetailView

urlpatterns = [
    path("orders/", SellerOrderListView.as_view()),
    path("orders/<int:pk>/", SellerOrderDetailView.as_view()),

    path('dashboard/',SellerDashboardSummaryView.as_view(),name='seller-dashboard')

]
