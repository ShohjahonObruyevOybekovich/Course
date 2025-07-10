from django.contrib import admin

from shop.models import Product, Order


# admin.site.unregister(Product)
# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description' ,'price', 'quantity')
#     list_filter = ('name', 'description', 'price', 'quantity')
#     search_fields = ('name', 'description', 'price', 'quantity')
#
#
# admin.site.unregister(Order)
# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('user__full_name', 'product__name', "product__price", 'quantity',"status")
#     list_filter = ('user__full_name', 'product__name', 'quantity',"status")
#     search_fields = ("user__full_name", "product__name", "product__price")