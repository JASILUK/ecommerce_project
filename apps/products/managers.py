from django.db import models
from apps.products.querysets import CustomProductsQueryset


class CustomProductManager(models.Manager):
    def get_queryset(self):
        return CustomProductsQueryset(self.model,using=self._db)
    
    def is_active(self):
        return self.get_queryset().is_active()
    
    def not_blocked(self):
        return self.get_queryset().not_blocked()
    
    def by_seller(self,seller):
        return self.get_queryset().by_seller(seller)
    
    def in_category(self,slug):
        return self.get_queryset().by_category(slug)
    