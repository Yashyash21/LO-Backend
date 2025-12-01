from rest_framework import serializers
from accounts.models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# =========================================
# 🔹 USER REGISTRATION
# =========================================
class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = [
            "email", "phone", "address", "city", "state", "pincode",
            "password1", "password2"
        ]

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = CustomUser(
            email=validated_data["email"],
            phone=validated_data["phone"],
            address=validated_data["address"],
            city=validated_data["city"],
            state=validated_data["state"],
            pincode=validated_data["pincode"],
        )
        user.set_password(validated_data["password1"])
        user.save()
        return user


# =========================================
# 🔹 EMAIL-BASED JWT LOGIN
# =========================================
class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        fields = ("email", "password")

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid password."})

        attrs["username"] = user.email
        attrs["password"] = password

        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["phone"] = user.phone
        token["city"] = user.city
        token["state"] = user.state
        return token


# =========================================
# 🔹 OTP PASSWORD RESET
# =========================================
class PasswordResetOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email not found.")
        return value


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField(min_length=6)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data


# =========================================
# 🔹 USER PROFILE
# =========================================
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "email", "phone", "address", "city", "state", "pincode"]
        read_only_fields = ["email"]
