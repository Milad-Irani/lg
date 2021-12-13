from django.contrib import admin
from . import models

# Register your models here.


class JobAdmin(admin.ModelAdmin):
    list_display = ["job_id", "user_id", "video_id", "status", "created_at"]
    search_fields = ("job_id", "user_id", "video_id", "status", "created_at")


class PointerAdmin(admin.ModelAdmin):
    list_display = ["pointer_id", "job_id", "user_id", "video_id", "votes_count"]
    search_fields = ("pointer_id", "user_id", "video_id",)


admin.site.register(models.Job, JobAdmin)
admin.site.register(models.Pointer, PointerAdmin)
