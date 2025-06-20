from django.db import models

# Create your models here.


from command.models import BaseModel

class Channel(BaseModel):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.username