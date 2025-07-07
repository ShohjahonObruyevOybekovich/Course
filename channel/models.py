from django.db import models

# Create your models here.


from command.models import BaseModel

class Channel(BaseModel):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    chat_id = models.CharField(max_length=64, null=True, blank=True)
    invite_link = models.URLField()
    def __str__(self):
        return self.username