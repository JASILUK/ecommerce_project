from email.mime import base
from re import U
from urllib import response
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView,
                                            TokenVerifyView,
                                            TokenBlacklistView)
from apps.users.models import Address, SellerProfileTable
from apps.users.services import  GoogleLogService, SetTokenCookie
from rest_framework.views import APIView
from allauth.account.models import EmailConfirmationHMAC,EmailConfirmation
from allauth.account.models import EmailAddress
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from apps.users.v1.serializers import AddressSerializer, ManualRegisterSerializer, Meserailizer, SellerApplicationSerializer
from config import settings
from config.settings.base import GOOGLE_CLIENT_ID
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate,get_user_model
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from allauth.account.models import EmailAddress,EmailConfirmationHMAC
from django.core.mail import send_mail
from rest_framework import viewsets

from core.permissions import IsAdmin, IsBuyer, IsSeller

from apps.cart.services import CartMergeService

# Create your views here.

User = get_user_model()

class ManualRegisterView(APIView):
    serializer_class = ManualRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            email_address = EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=False
        )
            confirmation = EmailConfirmationHMAC(email_address)
            api_url = f"http://localhost:5173/e-commerce/email-confirm/{confirmation.key}/"
            send_mail(
                 subject="Confirm your email",
            message=f"Click the link to confirm your email: {api_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email,]
            )
            return Response(
                {"detail": "Registration successful. Check your email to verify your account."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CustomTokenObtain(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)
        if not user:
            raise AuthenticationFailed("Invalid email or password.")

        if not EmailAddress.objects.filter(user=user, verified=True).exists():
            raise AuthenticationFailed("E-mail is not verified.")

        response = super().post(request, *args, **kwargs)

        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')

        auth_service = SetTokenCookie(request)
        session_id =request.COOKIES.get("guest_session")
        
        success= CartMergeService.merge_guest_to_user(session_id,user)
        if success:
            response.delete_cookie(key="guest_session",path='/')
        return auth_service.get_auth_token(response, access_token, refresh_token)


class CustomTokenRefresh(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        token  = request.COOKIES.get('refresh_token',None)
        data = request.data.copy()
        if token:
            data['refresh'] = token
        
        request._full_data = data  
        response = super().post(request, *args, **kwargs)
        access_token = response.data.get('access',None)
        refresh_token = response.data.get('refresh',None)
        cookie_handler = SetTokenCookie(request)
        response = cookie_handler.get_auth_token(response,access_token,refresh_token)
        return response
    

class CustomTokenBlacklist(APIView):
    def _delete_cookies(self, response):
        response.delete_cookie(
            key="access_token",
            path="/"
        )
        response.delete_cookie(
            key="refresh_token",
            path="/"
        )
        return response

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            authheader = request.headers.get("Authorization")
            if authheader and authheader.startswith("Bearer "):
                refresh_token = authheader.split(" ")[1]

        if not refresh_token:
            response = Response({"detail": "Already logged out"}, status=200)
            return self._delete_cookies(response)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass

        response = Response({"detail": "Logout successful"}, status=200)
        return self._delete_cookies(response)

    


class customTokenVerify(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        token = request.COOKIES.get('access_token',None)
        if token:
            request.data['access'] =token
        return super().post(request, *args, **kwargs)


class ConfirmEmailApi(APIView):
   def get(self, request, key, *args, **kwargs):
        confirmation = EmailConfirmationHMAC.from_key(key)
        if confirmation is None:
            confirmation = get_object_or_404(EmailConfirmation, key=key)
        confirmation.confirm(request)
        return Response({'detail': 'Email confirmed successfully'}, status=status.HTTP_200_OK)

class GoogleLoginView(APIView):
    def post(self,request,*args,**kwargs):
        token = request.data.get('token',None)
        if not token:
            return Response({'error':'no token provided'},status=status.HTTP_400_BAD_REQUEST)
        try:
            service = GoogleLogService(token)
            if not service.varifytoken(GOOGLE_CLIENT_ID):
                return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
            user =service.creat_user_JwtToken()

            response = Response(
                {
                    "detail": "Logged in successfully",
                    "user": Meserailizer(user).data
                },
                status=status.HTTP_200_OK
            )

            cookie_handler = SetTokenCookie(request)
            response = cookie_handler.get_auth_token(response,service.access,service.refresh)
            session_id =request.COOKIES.get("guest_session")
            
            success= CartMergeService.merge_guest_to_user(session_id,user)
            if success:
                response.delete_cookie(key="guest_session",path='/')
            return response
        
        except Exception as e:
            print('Googe login error',e)
            return Response({'error':str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


            
class GetMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        user = Meserailizer(request.user)
        return Response(data=user.data , status=200)


class UserToSellerApplicationView(APIView):
    permission_classes = [IsBuyer]
    def get(self, request):
        user = request.user
        try:
            seller_profile = user.seller_profile
            return Response(SellerApplicationSerializer(seller_profile).data, status=200)
        except SellerProfileTable.DoesNotExist:
            return Response(None, status=404)


    def post(self,request):
        user = request.user
        try:
            seller_profile = user.seller_profile
            if seller_profile.status == "pending":
                return Response({"detail": "You already applied. Status: PENDING"}, status=400)
            if seller_profile.status == "approved":
                return Response({"detail": "You are already a seller."}, status=400)
                
            serializer = SellerApplicationSerializer(seller_profile, data=request.data, partial=True)
        except SellerProfileTable.DoesNotExist:
            serializer = SellerApplicationSerializer(data=request.data)

        if serializer.is_valid():
            seller_obj = serializer.save(user=user, status="pending")
            return Response(SellerApplicationSerializer(seller_obj).data, status=201)

        return Response(serializer.errors, status=400)

    def delete(self,request):
        user = request.user
        try:
            seller_profile = user.seller_profile
        except SellerProfileTable.DoesNotExist:
            return Response({"detail": "No application to delete."}, status=404)

        if seller_profile.status == "approved":
            return Response({"detail": "You cannot delete an approved application."}, status=400)

        seller_profile.delete()
        return Response({"detail": "Application deleted."}, status=200)
    

class AdminSellerApplicationView(APIView):
    permission_classes = [IsAdmin]

    def get(self,request):
        seller_profiles = SellerProfileTable.objects.all().order_by('-creates_at')
        return Response(SellerApplicationSerializer(seller_profiles,many=True).data,status=200)
    
    def patch(self,request,pk):
        user = request.user
        try:
            sellerProfile = SellerProfileTable.objects.get(user =user ,pk=pk)
        except SellerProfileTable.DoesNotExist:
            return Response({'detail':'there is no data in this credential'},status =400)
        
        status = request.data.get('status',None)
        if status not in ['rejected','approved']:
            return Response({'detail':'invalid credential'},status =400)

        sellerProfile.status = status
        sellerProfile.save()
        if sellerProfile.status == 'approved':  
            user.role = user.Role.SELLER
            user.save()
        return response({'detail':f'Application {status}'},status =200)
    

class AddressViewAPI(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    def get_queryset(self):
        return Address.objects.filter(user = self.request.user)
    def perform_create(self, serializer):
        return serializer.save(user = self.request.user)
    