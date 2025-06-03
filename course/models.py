from django.db import models

from command.models import BaseModel
from upload.models import File


class CourseType(BaseModel):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Course(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    photo : "File" = models.ForeignKey("upload.File", on_delete=models.SET_NULL, null=True, blank=True)
    price = models.FloatField(default=0)
    course_type : "CourseType" = models.ForeignKey("course.CourseType", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
