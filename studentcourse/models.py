from django.db import models

from account.models import CustomUser
from command.models import BaseModel
from course.models import Course

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
