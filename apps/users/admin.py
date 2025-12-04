from django.contrib import admin
from apps.users.models import CustomeUser,UserProfileTable,SellerProfileTable
# Register your models here.
admin.site.register(CustomeUser)
admin.site.register(UserProfileTable)
admin.site.register(SellerProfileTable)