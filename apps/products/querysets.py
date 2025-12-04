from django.db import models


class CustomProductsQueryset(models.QuerySet):
    def is_active (self):
        return self.filter(is_active = True)
    
    def not_blocked(self):
        return self.filter(is_blocked=False)
    
    def by_seller(self,seller):
        return self.filter(seller=seller)
    
    def by_category(self,slug):
        return self.filter(categories__slug=slug)
    


