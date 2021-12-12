from django.contrib import admin
from . import models

# Register your models here.


class StreamAdmin(admin.ModelAdmin):
    list_display = ["stream_id", "user_id", "video_id", "status", "created_at"]
    search_fields = ("stream_id", "user_id", "video_id", "status", "created_at")


class MarkerAdmin(admin.ModelAdmin):
    list_display = ["marker_id", "stream_id", "user_id", "video_id", "votes_count"]
    search_fields = ("marker_id", "user_id", "video_id",)


class ClipAdmin(admin.ModelAdmin):
    list_display = ["clip_id", "stream_id", "marker_id", "clip_url"]
    search_fields = ("clip_id", "stream_id", "marker_id")


admin.site.register(models.Stream, StreamAdmin)
admin.site.register(models.Marker, MarkerAdmin)
admin.site.register(models.Clip, ClipAdmin)
