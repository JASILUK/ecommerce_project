from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from dj_rest_auth.serializers import JWTSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model

from apps.users.models import SellerProfileTable

User = get_user_model()

class CustomPayloadSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token
    
class CustomJwtSerializer(JWTSerializer):
    access = serializers.CharField(read_only=True) 
    refresh = serializers.CharField(read_only=True)
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = RefreshToken.for_user(self.user)
        data['refresh'] = str(refresh)
        data['access'] =str(refresh.access_token)
        return data


class AuthEmailCustomSerializer(RegisterSerializer):
    username = serializers.CharField(required=False,allow_blank=True)
    email = serializers.EmailField(required=True)
    def validate_email(self, email):
        email = email.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email already exists.")
        return email

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
        }
    
class SellerApplicationSerializer(serializers.ModelSerializer):
    store_logo = serializers.ImageField(required= False, write_only = True)
    store_logo_url = serializers.SerializerMethodField()
    class Meta:
        model = SellerProfileTable
        fields = [
            'id',
            'store_name',
            'store_logo',
            'store_logo_url',
            'description',
            'business_address',
            'status',
            'creates_at'
        ]
        read_only_fields = ['status', 'creates_at']
    def get_store_logo_url(self,obj):
        if not obj.store_logo:
            return None
        try:
            return obj.store_logo.url
        except:
            return str(obj.store_logo)   

class Meserailizer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    seller_profile = serializers.SerializerMethodField()
    class Meta :
        model = User
        fields = ["email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "seller_profile"]        
    
    def get_full_name(self,obj):
        return f'{obj.first_name} {obj.last_name}'.strip()

    def get_seller_profile(self, obj):
        if hasattr(obj, "seller_profile"):
            return SellerApplicationSerializer(obj.seller_profile).data
        return None



class ManualRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only = True)

    def validate_email(self, email):
        email = email.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email already exists."})
        return email
    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"detail": "password doesnt match"})
        return attrs
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data.get('username', ''),
            email=validated_data['email'],
            is_active=False  
        )
        user.set_password(validated_data['password1'])
        user.save()
        return user




