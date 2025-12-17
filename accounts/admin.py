from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,UserAddress
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Remove username completely
    exclude = ("username",)

    ordering = ("email",)
    list_display = ("email", "phone", "is_staff", "is_active")
    search_fields = ("email", "phone")
    list_filter = ("is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("phone",)}),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "phone",
                "password1",
                "password2",
            ),
        }),
    )

    USERNAME_FIELD = "email"



@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "city",
        "state",
        "pincode",
        "is_default",
        "created_at",
    )
    list_filter = ("city", "state", "is_default")
    search_fields = ("user__email", "city", "state", "pincode")
