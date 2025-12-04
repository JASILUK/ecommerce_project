from rest_framework.exceptions import PermissionDenied,NotFound

from apps.products.models import ProductColor, Products

class ColorProductService():
    def __init__(self,request,product_slug,color_pk):
         self.request = request
         self.product_slug =product_slug
         self.color_pk =color_pk
    def get_color_product_service(self):

            try:
                product = Products.objects.get(
                    slug=self.product_slug,
                    seller=self.request.user
                )
            except Products.DoesNotExist:
                raise PermissionDenied("You do not own this product.")

            try:
                color_product = ProductColor.objects.get(
                    product=product,
                    pk=self.color_pk
                )
            except ProductColor.DoesNotExist:
                raise NotFound("Color variant not found for this product.")

            return color_product