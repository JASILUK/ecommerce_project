from django.urls import include, path 
from apps.users.v1.views import (AdminSellerApplicationView, CustomTokenObtain, GetMeView, ManualRegisterView, UserToSellerApplicationView,
                      customTokenVerify,
                      CustomTokenBlacklist,
                      CustomTokenRefresh)
from apps.users.v1.views import ConfirmEmailApi,GoogleLoginView,ManualRegisterView
from dj_rest_auth.registration.views import (ConfirmEmailView,ResendEmailVerificationView)
from dj_rest_auth.views import (PasswordResetView,PasswordResetConfirmView)
urlpatterns = [
    path('login/',CustomTokenObtain.as_view(),name='token_obtain_api'),
    path('token/refresh/',CustomTokenRefresh.as_view(),name='token_refresh_api'),
    path('logout/',CustomTokenBlacklist.as_view(),name='token_blacklist_api'),
    path('token/varify/',customTokenVerify.as_view(),name='token_varify_api'),
    path('me/',GetMeView.as_view(),name='me_api'),
    path('auth/',include('dj_rest_auth.urls')),

    path('auth/registration/account-confirm-email/<path:key>/',ConfirmEmailApi.as_view(),name='account_confirm_email'),
    path('auth/registration/',ManualRegisterView.as_view(),name='regioster_api'),
    path('auth/registration/resend-email/', ResendEmailVerificationView.as_view(), name='rest_resend_email'),

    path('auth/password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
    path('auth/password/reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),

    path('auth/google/',GoogleLoginView.as_view(),name='google_login_api'),
   
   path('seller/application/',UserToSellerApplicationView.as_view(),name='seller-application'),
   
   path('admin/seller-application/',AdminSellerApplicationView.as_view(),name='admin-seller-application'),
   path('admin/seller-application/<int:pk>/',AdminSellerApplicationView.as_view(),name='admin-seller-application'),
   
]
