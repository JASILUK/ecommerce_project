from apps.orders.models import OrderItem
from apps.products.models import Products
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay, TruncMonth
from django.core.cache import cache
from datetime import timedelta
from django.utils import timezone

class SellerDashboardService:
    CACHE_TTL = 60  

    @staticmethod
    def get_dashboard_data(user, range_type="month"):
        cache_key = f"seller_dashboard_{user.id}_{range_type}"
        cached = cache.get(cache_key)

        if cached:
            return cached

        start, end = SellerDashboardService.get_date_range(range_type)

        items = OrderItem.objects.filter(
            product__seller=user
        ).select_related("order", "product")

        if start:
            items = items.filter(order__created_at__range=(start, end))

        total_sales = items.aggregate(total=Sum("line_total"))["total"] or 0
        total_orders = items.values("order_id").distinct().count()

        pending_orders = items.filter(order__status="PENDING") \
            .values("order_id").distinct().count()

        products = Products.objects.filter(seller=user)
        total_products = products.count()
        active_products = products.filter(is_active=True, is_blocked=False).count()
        blocked_products = products.filter(is_blocked=True).count()

        best_sellers = list(
            items.values("product_id", "product__name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )

        low_stock = list(
            products.filter(product_colors__variants__stock__lte=5)
            .distinct().values("id", "name")[:5]
        )
        out_of_stock = list(
            products.filter(product_colors__variants__stock =0)
            .distinct().values("id", "name","product_colors__color__name")
        )

        sales_trend = (
            items.annotate(day=TruncDay("order__created_at"))
                 .values("day")
                 .annotate(total=Sum("line_total"))
                 .order_by("day")
        )

        order_trend = (
            items.annotate(day=TruncDay("order__created_at"))
                 .values("day")
                 .annotate(total_orders=Count("order_id", distinct=True))
                 .order_by("day")
        )

        monthly_sales = (
            items.annotate(month=TruncMonth("order__created_at"))
                 .values("month")
                 .annotate(total=Sum("line_total"))
                 .order_by("month")
        )

        status_counts = (
            items.values("order__status")
                 .annotate(count=Count("order_id", distinct=True))
        )

        response = {
            "summary": {
                "total_sales": float(total_sales),
                "total_orders": total_orders,
                "pending_orders": pending_orders,
            },
            "products": {
                "total": total_products,
                "active": active_products,
                "blocked": blocked_products,
            },
            "best_sellers": best_sellers,
            "low_stock": low_stock,
            "out_of_stock":out_of_stock,
            "sales_trend": [
                {"date": x["day"].strftime("%Y-%m-%d"), "sales": float(x["total"] or 0)}
                for x in sales_trend
            ],
            "order_trend": [
                {"date": x["day"].strftime("%Y-%m-%d"), "orders": x["total_orders"]}
                for x in order_trend
            ],
            "monthly_sales": [
                {"month": x["month"].strftime("%b %Y"), "total": float(x["total"] or 0)}
                for x in monthly_sales
            ],
            "order_status": {x["order__status"]: x["count"] for x in status_counts},
        }

        cache.set(cache_key, response, SellerDashboardService.CACHE_TTL)
        return response
    
    @staticmethod
    def get_date_range(period):
        now = timezone.now()

        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        elif period == "yesterday":
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            now = start + timedelta(days=1)

        elif period == "week":  
            start = now - timedelta(days=7)

        elif period == "month":  
            start = now.replace(day=1, hour=0, minute=0, second=0)

        elif period == "30days":
            start = now - timedelta(days=30)

        elif period == "year":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0)

        else:
            start = None

        return start, now