from django.db import models
from django.contrib.auth.models import BaseUserManager
from allauth.account.models import EmailAddress

class CustomUserQueryset(models.QuerySet):
    def get_sellers(self):
        return self.filter(role = 'SELLER')
    
    def get_buyers(self):
        return self.filter(role = 'BUYER')
    
class CustomUserManager(BaseUserManager):
    def create_user(self,email,password=None,username=None,**extra_fields):
        if not email :
            raise ValueError('The email feild must be set')
        if not username:
            raise ValueError('Username is required')

        email = self.normalize_email(email)
        user =self.model(email=email,username=username,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self,email,username=None,password=None,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        extra_fields.setdefault('is_active',True)
        user = self.create_user(email=email,username=username,password=password,**extra_fields)
        EmailAddress.objects.create(user=user,email=user.email,verified=True)
       
        return user
    

    def get_queryset(self):
        return CustomUserQueryset(model=self.model,using=self._db)
    
    def get_active_users(self):
        return self.get_queryset().filter(is_active = True)
    
    