import asyncio

from aiogram import Bot
from aiogram.types import Update
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from dispatcher import dp, TOKEN
from .serializers import LeadSerializer


class LandingPageView(TemplateView):
    template_name = "index.html"



bot = Bot(TOKEN)

@csrf_exempt
async def telegram_webhook(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")

    try:
        body = request.data
        update = Update.model_validate_json(body.decode())
    except Exception as e:
        return HttpResponseBadRequest(f"Invalid JSON: {e}")

    await dp.feed_update(bot, update)
    return JsonResponse({"ok": True})




class LeadCreateView(APIView):
    def post(self, request):
        serializer = LeadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
