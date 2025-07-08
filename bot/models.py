from django.db import models

from command.models import BaseModel

class Leads(BaseModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    message = models.TextField(blank=True)