from django.contrib import admin
from . import models

# Register your models here.


class JobAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "created"]
    search_fields = ("id", "status", "created")


class PointerAdmin(admin.ModelAdmin):
    list_display = ["id", "job", "pointer"]
    search_fields = ("id",)


class ClipAdmin(admin.ModelAdmin):
    list_display = ["id", "job", "pointer", "created"]
    search_fields = ("id", "created")


admin.site.register(models.Job, JobAdmin)
admin.site.register(models.Pointer, PointerAdmin)
admin.site.register(models.Clip, ClipAdmin)
