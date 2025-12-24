from rest_framework import serializers
from accounts.models import CustomUser,UserAddress
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# =========================================
# 🔹 USER REGISTRATION
# =========================================
class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    # OPTIONAL address fields
    full_address = serializers.CharField(write_only=True, required=False)
    city = serializers.CharField(write_only=True, required=False)
    state = serializers.CharField(write_only=True, required=False)
    pincode = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "phone",
            "password1",
            "password2",
            "full_address",
            "city",
            "state",
            "pincode",
        ]

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match")

        address_fields = ["full_address", "city", "state", "pincode"]
        provided = [f for f in address_fields if f in data]

        # If any address field is provided, all must be provided
        if provided and len(provided) != len(address_fields):
            raise serializers.ValidationError(
                "Please provide complete address details"
            )

        return data

    def create(self, validated_data):
        password = validated_data.pop("password1")
        validated_data.pop("password2")

        # extract address (if exists)
        address_data = {}
        for field in ["full_address", "city", "state", "pincode"]:
            if field in validated_data:
                address_data[field] = validated_data.pop(field)

        user = CustomUser.objects.create(
            email=validated_data["email"],
            phone=validated_data["phone"]
        )
        user.set_password(password)
        user.save()

        # create default address ONLY if provided
        if address_data:
            UserAddress.objects.create(
                user=user,
                is_default=True,
                **address_data
            )

        return user


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            "id",
            "full_address",
            "city",
            "state",
            "pincode",
            "phone",
            "is_default",
        ]

    def create(self, validated_data):
        user = self.context["request"].user

        if validated_data.get("is_default"):
            UserAddress.objects.filter(
                user=user, is_default=True
            ).update(is_default=False)

        return UserAddress.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("is_default"):
            UserAddress.objects.filter(
                user=instance.user, is_default=True
            ).exclude(id=instance.id).update(is_default=False)

        return super().update(instance, validated_data)



class UserProfileSerializer(serializers.ModelSerializer):
    addresses = UserAddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "phone",
            "addresses"
        ]
        read_only_fields = ["email"]
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
    addresses = UserAddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "email", "phone", "addresses"]
        read_only_fields = ["email"]
