from django.db import models

from account.models import CustomUser
from command.models import BaseModel
from upload.models import File
from course.models import Course

# Create your models here.


class Transaction(BaseModel):
    user : "CustomUser" = models.ForeignKey("account.CustomUser", on_delete=models.CASCADE,related_name="payments_user")
    amount : float = models.FloatField(default=0)
    course : "Course" = models.ForeignKey("course.Course", on_delete=models.SET_NULL,
                                          null=True,blank=True,related_name="payments_course")
    status = models.CharField(
        choices=[
            ("Pending", "Pending"),
            ("Accepted", "Accepted"),
            ("Rejected", "Rejected"),
        ], default="Pending",max_length=20,null=True,blank=True
    )
    file=models.CharField(
        max_length=200,
        null=True,
        blank=True
    )
    updater = models.ForeignKey("account.CustomUser", on_delete=models.SET_NULL,
                                null=True,blank=True,related_name="payments_updater")

    def __str__(self):
        return f"{self.user.full_name}   {self.amount}"
