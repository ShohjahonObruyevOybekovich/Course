from django.contrib import admin

from transaction.models import Transaction


# Register your models here.
# @admin.register(Transaction)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ('user__full_name', "amount","status","updater__full_name","created_at")
#     list_filter = ('status',)
#     search_fields = ('user__full_name',)