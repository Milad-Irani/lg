from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from urllib.parse import urlparse
from os.path import basename,splitext
import string
import random
# Create your models here.

class StatusChoice(models.TextChoices):
    UNPRC = "UNPRC", _("Unprocessed")
    SCHED = "SCHED" , _("Scheduled")
    UNDPRC = "UNDPRC", _("UnderProcess")
    PRC = "PRC", _("Processed")
    FLD = "FLD", _("Failed")
    CNL = "CNL", _("Canceled")
    QUEUED = 'QUEUED' , _('Queued')


class Stream(models.Model):
    stream_id = models.CharField(max_length=25, primary_key=True)
    video_id = models.CharField(max_length=25)
    user_id = models.CharField(max_length=25)
    game_id = models.CharField(max_length=25)
    game_name = models.CharField(max_length=100)
    title = models.CharField(max_length=400)
    thumbnail_url = models.URLField(max_length=400, null = True , unique = True , blank = True)
    video_description = models.TextField(blank = True ,default = '')
    view_count = models.IntegerField(default = 0)
    created_at = models.DateTimeField(blank = True)
    published_at = models.DateTimeField(blank = True)
    video_url = models.URLField(max_length=400, null = True , unique = True , blank = True)
    status = models.CharField(
        max_length=10, choices=StatusChoice.choices, default=StatusChoice.UNPRC
    )
    failure_count = models.IntegerField(default = 0 , blank = True)
    failure_reason = models.TextField(blank = True ,default = '')

    @property
    def vid_name(self):
        def get_rnd():
            return ''.join(random.sample(string.digits + string.ascii_letters ,10))
        root , ext = splitext(basename(urlparse(self.video_url).path))
        rnd = get_rnd()
        return root + '_' + rnd + ext

class Marker(models.Model):
    marker_id = models.BigAutoField(primary_key=True)
    stream_id = models.ForeignKey(Stream, on_delete=models.CASCADE)
    # stream_id = models.CharField(max_length=25)
    position_seconds = models.PositiveIntegerField(default=0)
    votes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["stream_id"], name="marker-conflict"
            )
        ]


class Clip(models.Model):
    clip_id = models.BigAutoField(primary_key=True) # PK
    stream_id = models.ForeignKey(Stream, on_delete=models.CASCADE)
    marker_id = models.ForeignKey(Marker, on_delete=models.CASCADE)
    #marker_id = models.CharField(max_length=25) # FK
    #stream_id = models.CharField(max_length=25) # FK
    clip_url = models.URLField(max_length=400, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["stream_id", "marker_id"], name="clip-conflict"
            )
        ]
