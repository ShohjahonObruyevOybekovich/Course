from django.db import models

from account.models import CustomUser
from command.models import BaseModel
from course.models import Course
from theme.models import Theme
# Create your models here.


class StudentCourse(BaseModel):
    user : "CustomUser" = models.ForeignKey("account.CustomUser", on_delete=models.CASCADE, related_name="student_courses")
    course : "Course" = models.ForeignKey("course.Course", on_delete=models.CASCADE, related_name="students_course")
    status = models.CharField(
        choices=[
            ("Active", "Active"),
            ("Inactive", "Inactive"),
        ],
        default="Inactive",
        max_length=10,
    )


class UserTasks(BaseModel):
    user : "CustomUser" = models.ForeignKey("account.CustomUser", on_delete=models.CASCADE, related_name="user_schribens")
    theme : "Theme" = models.ForeignKey("theme.Theme", on_delete=models.CASCADE, related_name="user_schribens")
    ball = models.IntegerField(default=0)
    choice = models.CharField(
        choices=[
            ("Sprichen", "Sprichen"),
            ("Schreiben", "Schreiben"),
        ],max_length=12,null=True,blank=True
    )
    def __str__(self):
        return self.user.full_name