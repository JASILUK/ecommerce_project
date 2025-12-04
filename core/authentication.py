from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class HeaderOrCookieAuth(JWTAuthentication):
    def authenticate(self, request):
        cookieToken = request.COOKIES.get('access_token',None)
        if cookieToken:
            try :
                validated = self.get_validated_token(cookieToken)
                return (self.get_user(validated),validated)
            except :
                pass
        return super().authenticate(request)
    


User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
      
        email = username or kwargs.get("email")

        if email is None or password is None:
            return None

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user

        return None
