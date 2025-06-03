from django.contrib import admin

from django.contrib import admin
from django.apps import apps

try:
    models = apps.get_models()

    for model in models:
        try:
            if hasattr(model, "Admin"):
                modelAdmin = getattr(model, "Admin")

            else:
                if not hasattr(model, "CustomFilter"):
                    admin.site.register(model)
                else:

                    @admin.register(model)
                    class ModelAdmin(admin.ModelAdmin):
                        model = model

        except admin.sites.AlreadyRegistered as e:

            pass
except Exception as e:

    pass