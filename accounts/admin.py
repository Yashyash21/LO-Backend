from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # 🛑 REMOVE default username field from UserAdmin
    exclude = ("username",)

    # 🟢 Use email instead of username
    ordering = ("email",)
    list_display = ("email", "phone", "city", "state", "pincode", "is_staff", "is_active")
    search_fields = ("email", "phone", "city", "state", "pincode")
    list_filter = ("city", "state", "is_staff", "is_active")

    # 🟢 Fields shown when editing a user
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("phone", "address", "city", "state", "pincode")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # 🟢 Fields shown when creating a new user
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "phone",
                "address",
                "city",
                "state",
                "pincode",
                "password1",
                "password2",
            ),
        }),
    )
