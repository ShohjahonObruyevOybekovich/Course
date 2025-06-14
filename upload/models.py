from django.db import models
from django.http import HttpRequest

from command.models import BaseModel


class File(BaseModel):
    file = models.FileField(upload_to="files/", null=True, blank=True)


class Video(BaseModel):
    url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.url