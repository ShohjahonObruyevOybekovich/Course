import random
import string
import uuid

from decouple import config
from django.contrib.auth.models import AbstractUser
from django.db import models

from account.managers import UserManager

TOKEN = config('BOT_USERNAME')


def generate_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=255, unique=True, blank=True, null=True)
    chat_id = models.CharField(max_length=255, blank=True, null=True)

    language = models.CharField(choices=[
        ('en', 'English'),
        ('uz', 'Uzbek'),
        ("ru", "Russian"),
    ], max_length=10, blank=True, null=True)

    ROLE_CHOICES = (
        ("User", "User"),
        ("Admin", "Admin"),
    )

    balance = models.IntegerField(default=0)
    role = models.CharField(choices=ROLE_CHOICES, max_length=30, default="User")
    has_passed = models.BooleanField(default=False, help_text="Is this user has passed the test?")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_blocked = models.BooleanField(default=False, help_text="Is this user is blocked?")

    referral_code = models.CharField(max_length=20, unique=True, default=generate_ref_code)
    referred_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name="referrals"
    )

    USERNAME_FIELD = 'phone'

    objects = UserManager()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.full_name or self.phone

    def referral_link(self):
        return f"https://t.me/{TOKEN}?start={self.referral_code}"