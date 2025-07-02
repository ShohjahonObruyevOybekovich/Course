from command.models import BaseModel
from django.db import models

class Idioms(BaseModel):
    text: str = models.TextField()
    time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Idioms'
        verbose_name_plural = 'Idioms'
