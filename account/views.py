from decouple import config
from icecream import ic
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.exceptions import ValidationError
import os

from .models import CustomUser
from .utils import BotUserJWTAuthentication

from .telegram_webapp_auth.auth import TelegramAuthenticator, generate_secret_key


BOT_TOKEN = config("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValidationError("Bot token not found")


class JWTtokenGenerator(APIView):
    """
    Generate JWT token using telegram mini app credentials.
    """

    def post(self, request):
        init_data = request.data.get("init_data")
        # bot = request.data.get("bot").strip().upper() if request.data.get("bot") else None

        if not init_data:
            raise ValidationError("init_data is required")

        secret_key = generate_secret_key(BOT_TOKEN)

        authenticator = TelegramAuthenticator(secret_key)

        auth_data = authenticator.validate(init_data)
        user_id = auth_data.user.id
        user = CustomUser.objects.filter(chat_id=user_id).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        access = AccessToken.for_user(user)
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(access),
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)


        # try:
        #     secret_key = generate_secret_key(bot_token)
        #     ic(secret_key)
        #     authenticator = TelegramAuthenticator(secret=secret_key)
        #     ic(authenticator)
        #     bot_id = get_bot_id_from_token(bot_token)
        #     ic(bot_id)
        #     if not bot_id:
        #         raise ValidationError("Invalid bot token")
        #     init_data = authenticator.validate_third_party(init_data=init_data, bot_id=bot_id)
        #     ic(init_data)

        # except Exception as e:
        #     print(e)
        #     raise e from e
        #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # user_data = init_data.user
        # if not user_data:
        #     return Response({"error": "User data is required"}, status=status.HTTP_400_BAD_REQUEST)

        # user = CustomUser.objects.filter(chat_id=user_data.id).first()
        # if not user:
        #     return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # access = AccessToken.for_user(user)
        # refresh = RefreshToken.for_user(user)

        # access["bot_token"] = bot_token
        # refresh["bot_token"] = bot_token

        # return Response({
        #     "access": str(access),
        #     "refresh": str(refresh)
        # }, status=status.HTTP_200_OK)


class JWTtokenRefresh(APIView):
    """
    Refresh JWT token using refresh token.
    """

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token
            return Response(
                {"access": str(access), "refresh": str(refresh)},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class Me(APIView):
    authentication_classes = [BotUserJWTAuthentication]
    """
    Get user information.
    """

    def get(self, request):
        user = request.user
        if not user:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        user_data = {
            "id": user.id,
            "name": user.full_name,
            "number": user.phone,
            "chat_id": user.chat_id,
            "has_passed": user.has_passed,
        }
        return Response(user_data, status=status.HTTP_200_OK)
