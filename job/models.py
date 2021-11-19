from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from urllib.parse import urlparse
from os.path import basename

# Create your models here.

class StatusChoice(models.TextChoices):
    UNPRC = "UNPRC", _("Unprocessed")
    SCHED = "SCHED" , _("Scheduled")
    UNDPRC = "UNDPRC", _("UnderProcess")
    PRC = "PRC", _("Processed")
    FLD = "FLD", _("Failed")
    CNL = "CNL", _("Canceled")


class Job(models.Model):
    status = models.CharField(
        max_length=10, choices=StatusChoice.choices, default=StatusChoice.UNPRC
    )
    video_url = models.URLField(max_length=400, null = True , unique = True , blank = False)
    created = models.DateTimeField(default=timezone.now)

    @property
    def vid_name(self):
        return basename(urlparse(self.video_url).path)

class Pointer(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    pointer = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "pointer"], name="pointer-conflict"
            )
        ]


class Clip(models.Model):
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True)
    pointer = models.ForeignKey(Pointer, on_delete=models.SET_NULL, null=True)
    clip_url = models.URLField(max_length=400, default="")
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "pointer"], name="clip-conflict"
            )
        ]
