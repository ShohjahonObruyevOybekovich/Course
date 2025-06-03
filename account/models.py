from decimal import Decimal
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from account.managers import UserManager



class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=255, unique=True, blank=True, null=True)
    chat_id = models.CharField(max_length=255, blank=True, null=True)

    # photo : 'File' = models.ForeignKey('upload.File', on_delete=models.SET_NULL, blank=True, null=True)

    language = models.CharField(choices=[
        ('en', 'English'),
        ('uz', 'Uzbek'),
        ("ru", "Russian"),
    ],max_length=10, blank=True, null=True)

    ROLE_CHOICES = (
        ("User", "User"),
        ("Admin", "Admin"),
    )

    role = models.CharField(choices=ROLE_CHOICES, max_length=30, default="User")

    has_passed = models.BooleanField(default=False, help_text="Is this user has passed the test?")

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    USERNAME_FIELD = 'phone'
    # REQUIRED_FIELDS = ['phone']

    objects = UserManager()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.full_name or self.phone


