from django.db import models

from account.models import CustomUser
from upload.models import File,Video
from course.models import Course,CourseType
from command.models import BaseModel

class Theme(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    video : "Video" = models.ManyToManyField("upload.Video",related_name="themes_video")
    course : "Course" = models.ForeignKey("course.Course", on_delete=models.SET_NULL,
                                          null=True, blank=True,related_name="themes_course")
    course_type: "CourseType" = models.ManyToManyField("course.CourseType", related_name="courses_related_themes",
                                                       verbose_name="Kursning darajalari")

    materials: "File" = models.ForeignKey("upload.File", on_delete=models.SET_NULL,
                                          null=True, blank=True,related_name="themes_materials")
    link = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class ThemeAttendance(BaseModel):
    user : "CustomUser" = models.ForeignKey("account.CustomUser", on_delete=models.SET_NULL,
                                            null=True, blank=True,related_name="themes_attendance")
    theme : "Theme" = models.ForeignKey("theme.Theme", on_delete=models.SET_NULL,
                                        null=True, blank=True,related_name="themes_attendance_themes")

    is_attendance = models.BooleanField(default=True)

    is_complete_test = models.BooleanField(default=False)

    ball = models.IntegerField(default=0)

    # def __str__(self):
    #     return f"{self.user.full_name}  {self.ball}"

