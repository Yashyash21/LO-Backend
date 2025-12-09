from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register_user,
    EmailLoginView,
   
    UserProfileView,send_password_reset_otp,verify_otp,reset_password
)

urlpatterns = [
    # 🧍 User Authentication
    path("register/", register_user, name="register"),
    path("login/", EmailLoginView.as_view(), name="email_login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),






    # 👤 User Profile (for logged-in users)
    path("profile/", UserProfileView.as_view(), name="user_profile"),

    
    path("password-reset-otp/", send_password_reset_otp, name="password_reset_otp"),
    path("verify-otp/", verify_otp),
    path("reset-password/", reset_password),


]

