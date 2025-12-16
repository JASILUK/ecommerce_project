from django.db import models

from apps.orders.Queryset import CsutomeOrderQueryset


class CustomeOrderManager(models.Manager):
    def get_queryset(self):
        return CsutomeOrderQueryset(self.model,using=self._db)
    def my_products(self,user):
        return self.get_queryset().my_products(user=user)