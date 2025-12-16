from django.db.models import QuerySet

class CsutomeOrderQueryset(QuerySet):

    def my_products(self,user):
        return self.filter(user = user)
    def pending_products(self):
        return self.filter(status ="PENDING")
    