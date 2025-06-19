from django.db import models

from command.models import BaseModel
from upload.models import File


class CourseType(BaseModel):
    name = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.id} - {self.name}"

class Course(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    photo : "File" = models.ForeignKey("upload.File", on_delete=models.SET_NULL, null=True, blank=True)
    price = models.FloatField(default=0)
    course_type : "CourseType" = models.ManyToManyField("course.CourseType",related_name="courses_related_types",verbose_name="Kursning darajalari")

    def __str__(self):
        return self.name
