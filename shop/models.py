from django.db import models

from account.models import CustomUser
from command.models import BaseModel
from upload.models import File

class Product(BaseModel):
    photo : "File" = models.ForeignKey("upload.File",on_delete=models.SET_NULL,null=True,blank=True, related_name="product")
    name = models.CharField(max_length=100)
    price = models.FloatField(default=0)
    quantity = models.IntegerField(default=1)
    description = models.TextField()
    def __str__(self):
        return self.name

class Order(BaseModel):
    product : "Product" = models.ForeignKey("shop.Product", on_delete=models.CASCADE, related_name="orders_product")
    user : "CustomUser" = models.ForeignKey("account.CustomUser", on_delete=models.CASCADE, related_name="orders_user")
    quantity = models.IntegerField(default=1)
    status = models.CharField(choices=[
        ("Pending", "Pending"),
        ("Cancelled", "Cancelled"),
        ("Accepted", "Accepted"),
    ],default="Pending",max_length=10,null=True,blank=True)
    def __str__(self):
        return self.product.name
