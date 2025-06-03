from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import CustomUser
from account.forms import CustomUserChangeForm, CustomUserCreationForm

admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ("phone", "is_staff", "is_active",)
    list_filter = ("phone", "is_staff", "is_active",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal Info", {"fields": ("full_name","chat_id","language",
                                      "role",)}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "full_name", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    search_fields = ("phone", "full_name",)
    ordering = ("phone",)
