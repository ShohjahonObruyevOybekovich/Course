from django.contrib import admin

from idioms.models import Idioms


# Register your models here.
admin.site.unregister(Idioms)

@admin.register(Idioms)
class IdiomsAdmin(admin.ModelAdmin):
    list_display = ("text","time")
    list_filter = ("time",)
    search_fields = ("text",)