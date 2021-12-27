from django.contrib import admin
from . import models

# Register your models here.


class JobAdmin(admin.ModelAdmin):
    list_display = ["stream_id", "user_id", "video_id", "status", "created_at"]
    search_fields = ("stream_id", "user_id", "video_id", "status")


class PointerAdmin(admin.ModelAdmin):
    list_display = ["marker_id", "stream_id", "user_id", "video_id", "votes_count"]
    search_fields = ("marker_id", "stream_id", "user_id", "video_id")


admin.site.register(models.Job, JobAdmin)
admin.site.register(models.Pointer, PointerAdmin)
