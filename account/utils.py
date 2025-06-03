from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import CustomUser
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
import requests

class BotUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Override to get BotUser instead of User
        """
        try:
            user_id = validated_token["user_id"]
        except KeyError:
            raise AuthenticationFailed("Token contained no recognizable user identification")

        try:
            bot_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise AuthenticationFailed("BotUser not found")

        return bot_user



class IsBotUserAuthenticated(BasePermission):
    """
    Custom permission to check if the user is authenticated
    through BotUserJWTAuthentication.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user or not isinstance(request.user, CustomUser):
            raise AuthenticationFailed("Authentication credentials were not provided or user is not a BotUser")
        
        return True


def get_bot_id_from_token(bot_token):
    response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
    if response.status_code == 200:
        return response.json()['result']['id']
    raise ValueError("Invalid bot token or failed to get bot ID")