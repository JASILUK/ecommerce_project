from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.users.managers import CustomUserManager
from cloudinary.models import CloudinaryField
# Create your models here.

class CustomeUser(AbstractUser):
    class Role (models.TextChoices):
        ADMIN = 'ADMIN','admin'
        SELLER = 'SELLER' , 'seller'
        BUYER =  'BUYER' , 'buyer'
    username = models.CharField(max_length=150,unique=False)
    role = models.CharField(choices=Role.choices,default=Role.BUYER,max_length=10,db_index=True)

    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()
    
       
     
class UserProfileTable(models.Model):
    user = models.OneToOneField(CustomeUser,on_delete=models.CASCADE,related_name='profile')
    fullname = models.CharField(max_length=50,blank=True)
    profile_image = CloudinaryField("profile_image",null=True,blank=True)
    gender = models.CharField(max_length=30,
                              choices=[("male","MALE"),("female","FEMALE"),("other","OTHER")],
                              blank=True,null=True)
    phone = models.CharField(max_length=20, blank=True)    
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
    

class SellerProfileTable(models.Model):
    user =models.OneToOneField(CustomeUser,on_delete=models.CASCADE,related_name='seller_profile')
    store_name = models.CharField(max_length=50)
    store_logo = CloudinaryField("store_logo",null=True,blank=True)
    description = models.TextField(blank=True)
    business_address = models.TextField(blank=True)
    status = models.CharField(max_length=20,
                              choices=[("pending","PENDING"),
                                       ("approved","APPROVED"),("rejected","REJECTED")],
                              default="pending")
    creates_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_name
    
class Address(models.Model):
    user = models.ForeignKey(CustomeUser,on_delete=models.CASCADE,related_name='address')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)

    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default="India")

    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.full_name}-{self.city}'
    
    
