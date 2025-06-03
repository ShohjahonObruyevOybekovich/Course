from django.db import models

from upload.models import File
from course.models import Course
from command.models import BaseModel

class Theme(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    video : "File" = models.ForeignKey("upload.File", on_delete=models.SET_NULL,
                                       null=True, blank=True,related_name="themes_video")
    course : "Course" = models.ForeignKey("course.Course", on_delete=models.SET_NULL,
                                          null=True, blank=True,related_name="themes_course")
    materials: "File" = models.ForeignKey("upload.File", on_delete=models.SET_NULL,
                                          null=True, blank=True,related_name="themes_materials")
    link = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name
