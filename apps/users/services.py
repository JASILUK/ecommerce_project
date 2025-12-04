from os import name, path
from google.oauth2 import id_token
from google.auth.transport import requests
from allauth.socialaccount.models import SocialAccount,SocialToken,SocialApp
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User =get_user_model()

class SetTokenCookie():
    def __init__(self,request):
        self.request = request
        self.is_web = self.get_isweb()

    def get_isweb(self):
        client_type = self.request.headers.get('X-Client-Type','').lower()
        return client_type == 'web' 
        
    def get_auth_token(self,response,access_token,refresh_token,**kwargs):

        if self.is_web :
            response.set_cookie(
                key = 'access_token',   
                value = access_token,
                httponly =True,
                secure =False,
                samesite = "Lax",
                path='/'

            )

            response.set_cookie(
                key = 'refresh_token',
                value = refresh_token,
                httponly = True,
                secure =False,
                samesite = "Lax",
                path = '/'
            )

            response.data['message']= "response returned as cookies"
        else:
            response.data['message'] = "response returned as json"

        return response
    



class GoogleLogService():
    def __init__(self,token):
        self.token = token
        self.access = None
        self.refresh = None
        self.user = None
    
    def varifytoken(self,clintId):
        try:
            self.idinfo = id_token.verify_oauth2_token(self.token,requests.Request(),clintId)
            return True
        except ValueError:
            return False
    def creat_user_JwtToken(self):
        email = self.idinfo["email"]
        username = self.idinfo.get("name","")
        uid = self.idinfo["sub"]
        
        self.user,created = User.objects.get_or_create(email = email,defaults={"username":username})

        social_account,_ = SocialAccount.objects.get_or_create(user=self.user,provider='google',uid =uid)
        social_app = SocialApp.objects.get(provider= 'google')
        social_token,t_created =SocialToken.objects.get_or_create(account = social_account,app =social_app,defaults={"token" : self.token})

        if not t_created:
            social_token.token = self.token
            social_token.save()
        self.refresh =RefreshToken.for_user(self.user)
        self.access = self.refresh.access_token
        return self.user
    
  
    


    