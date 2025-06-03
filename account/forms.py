from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

from account.models import CustomUser

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            "phone", "full_name", "language", "role",
            "chat_id",
        )

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = (
            "phone", "full_name", "language", "role",
            "chat_id","is_active", "is_staff", "is_superuser",
            "groups", "user_permissions"
        )