# apps/seller/views.py

from rest_framework.generics import ListAPIView, RetrieveAPIView
from apps.orders.models import Order
from apps.seller.v1.serializers import SellerOrderDetailSerializer, SellerOrderSerializer
from core.permissions import IsSeller
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.seller.services import SellerDashboardService


class SellerOrderListView(ListAPIView):
    permission_classes = [IsSeller]
    serializer_class = SellerOrderSerializer

    def get_queryset(self):
        user = self.request.user

        status = self.request.query_params.get("status")
        payment = self.request.query_params.get("payment")
        method = self.request.query_params.get("method")

        qs = Order.objects.filter(
            items__product__seller=user
        ).distinct()

        if status:
            qs = qs.filter(status=status)

        if payment == "paid":
            qs = qs.filter(is_paid=True)

        if payment == "unpaid":
            qs = qs.filter(is_paid=False)

        if method:
            qs = qs.filter(payment_method=method)

        return qs.order_by("-created_at")


class SellerOrderDetailView(RetrieveAPIView):
    permission_classes = [IsSeller]
    serializer_class = SellerOrderDetailSerializer

    def get_queryset(self):
        return Order.objects.filter(
            items__product__seller=self.request.user
        )







class SellerDashboardSummaryView(APIView):
    permission_classes = [IsSeller]

    def get(self, request):
        period = request.query_params.get("period", "month")

        data = SellerDashboardService.get_dashboard_data(
            user=request.user,
            range_type=period
        )

        return Response(data)
