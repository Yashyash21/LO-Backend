from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random

from accounts.models import CustomUser, PasswordResetOTP
from .serializers import (
    UserRegistrationSerializer,
    EmailTokenObtainPairSerializer,
    UserProfileSerializer,
    PasswordResetOTPRequestSerializer,
    OTPVerifySerializer,
    ResetPasswordSerializer
)
from products.views import merge_guest_cart
from django.contrib.auth import get_user_model
User = get_user_model()

# =========================================
# 🧍 USER REGISTRATION
# =========================================
@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User registered successfully!"}, status=201)
    return Response(serializer.errors, status=400)


# =========================================
# 🔑 EMAIL LOGIN (JWT)
# =========================================
# =========================================
# 🔑 EMAIL LOGIN (JWT) + CART MERGE
# =========================================
class EmailLoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # 1️⃣ Perform normal JWT login
        response = super().post(request, *args, **kwargs)

        # 2️⃣ Get email from login data
        email = request.data.get("email")
        if not email:
            return response

        # 3️⃣ Get logged-in user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return response

        # 4️⃣ Read guest cart_code from cookies
        cart_code = request.COOKIES.get("cart_code")

        # 5️⃣ Merge guest cart into user cart
        if cart_code:
            merge_guest_cart(user, cart_code)

        # 6️⃣ Return response as normal
        return response



# =========================================
# 🔐 OTP PASSWORD RESET
# =========================================
@api_view(["POST"])
@permission_classes([AllowAny])
def send_password_reset_otp(request):
    serializer = PasswordResetOTPRequestSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data["email"]

        # Rate limit: max 3 OTP per 30 min
        time_limit = timezone.now() - timedelta(minutes=30)
        recent = PasswordResetOTP.objects.filter(email=email, created_at__gte=time_limit).count()

        if recent >= 3:
            return Response({"error": "Too many OTP requests. Try after 30 minutes."}, status=429)

        # Delete previous OTP
        PasswordResetOTP.objects.filter(email=email).delete()

        otp = str(random.randint(100000, 999999))
        PasswordResetOTP.objects.create(email=email, otp=otp)

        send_mail(
            "Password Reset OTP",
            f"Your OTP is: {otp}\nIt will expire in 5 minutes.",
            "no-reply@example.com",
            [email],
            fail_silently=False,
        )

        return Response({"message": "OTP sent to your email"}, status=200)

    return Response(serializer.errors, status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = OTPVerifySerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            otp_obj = PasswordResetOTP.objects.get(email=email)
        except PasswordResetOTP.DoesNotExist:
            return Response({"error": "OTP not found"}, status=400)

        # Check expiry
        if timezone.now() > otp_obj.created_at + timedelta(minutes=5):
            otp_obj.delete()
            return Response({"error": "OTP expired"}, status=400)

        # Wrong attempts limit
        if otp_obj.attempts >= 3:
            otp_obj.delete()
            return Response({"error": "Too many wrong attempts"}, status=400)

        # Invalid OTP
        if otp_obj.otp != otp:
            otp_obj.attempts += 1
            otp_obj.save()
            return Response({"error": "Invalid OTP"}, status=400)

        return Response({"message": "OTP verified"}, status=200)

    return Response(serializer.errors, status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data["email"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        user.set_password(new_password)
        user.save()

        PasswordResetOTP.objects.filter(email=email).delete()

        return Response({"message": "Password reset successful"}, status=200)

    return Response(serializer.errors, status=400)


# =========================================
# 👤 USER PROFILE
# =========================================
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response


User = get_user_model()

@api_view(["POST"])
def create_superuser_api(request):
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not username or not email or not password:
        return Response({"error": "username, email, and password are required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists"}, status=400)

    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )

    return Response({
        "message": "Superuser created successfully!",
        "user": user.username
    }, status=201)
