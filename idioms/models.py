from command.models import BaseModel
from django.db import models
from upload.models import File

class Idioms(BaseModel):
    text: str = models.TextField()
    time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Idioms'
        verbose_name_plural = 'Idioms'


class MaterialsCategories(BaseModel):
    category: str = models.TextField()
    type = models.CharField(choices=[
        ("Video", "Video"),
        ("Audio", "Audio"),
        ("Document", "Document"),
        ("Image", "Image"),
    ])
    def __str__(self):
        return self.category


class Materials(BaseModel):
    title: str = models.TextField(verbose_name="Title")
    choice = models.ForeignKey("idioms.MaterialsCategories",on_delete=models.SET_NULL, null=True, blank=True,related_name="materials_categories")
    type = models.CharField(choices=[
        ("File", "File"),
        ("Telegram", "Telegram"),
        ],max_length=20,default="Telegram",null=True,blank=True
    )
    telegram_id = models.CharField(max_length=120,null=True,blank=True)
    file : "File" = models.ForeignKey("upload.File",on_delete=models.SET_NULL,null=True,blank=True,related_name="materials_uploaded_file")

    def __str__(self):
        return self.choice.category

