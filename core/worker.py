import os
from job import models as jmodels
import time
import logging
import concurrent.futures
import requests
from . import exceptions
import boto3
from boto3.s3.transfer import TransferConfig
from django.conf import settings
from pathlib import Path
import shutil
import ffmpeg
from urllib.parse import urlparse
import queue
from twitch.dl import TwitchDownload


AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_S3_ENDPOINT_URL = settings.AWS_S3_ENDPOINT_URL
AWS_S3_REGION_NAME = settings.AWS_S3_REGION_NAME
AWS_DEFAULT_ACL = settings.AWS_DEFAULT_ACL
MB = 1024 ** 2
S3_Config = TransferConfig(multipart_threshold=350 * MB)

logger = logging.getLogger(__name__)


class DownloadFile:
    def __init__(self, *args, **kwargs):
        """
        arg1:job
        arg2:file_location :file location
        """
        self.job = args[0]
        self.file_location = args[1]
        free = shutil.disk_usage(".").free  # get free disk/partition usage.
        self.free_disk_amount = free // (2 ** 30)

    def has_space_to_download(self):
        """first of all we should check the disk and partition we work on it has enaugh space or not. to do that we compare file size with"""
        res = requests.head(self.job.video_url)
        size = int(res.headers.get("Content-Length")) / (2 ** 30)  # convert to GB
        if size and (3 * size) >= self.free_disk_amount:
            raise exceptions.HardAbort("there is not enaugh space left on disk.")
        return

    def download_vid(self):
        self.has_space_to_download()
        res = requests.get(
            self.job.video_url, stream=True
        )  # by setting stream to True , we wont have to inect all file data to memeory. we read 2048 bytes into memory and flush it to disk.
        for cnt in res.iter_content(chunk_size=2048):
            with open(self.file_location, "ab") as f:
                f.write(cnt)

    def __call__(self):
        self.download_vid()

def twitch_dl(video_id , file_location):
    error = TwitchDownload(video_id , file_location).download()
    if error:
        raise exceptions.HardAbort(error)

class TrimFile:
    def __init__(self, *args, **kwargs):
        """
        arg1:job
        arg2:pnt
        """
        self.job = args[0]
        self.file_location = str(
            args[1]
        )  # file_location is type of Path object. so ffempeg just knows str.
        self.pointer = args[2]
        self.pnt = self.pointer.position_seconds
        self.buffer = settings.TRIM_BUFFER

    def gen_clip_file_location(self):
        # we append the pointer value to end of file name before extension to prevent overriding on main file.
        path, ext = (
            "".join(self.file_location.split(".")[:-1]),
            self.file_location.split(".")[-1],
        )
        self.clip_file_location = path + "__" + str(self.pnt) + "." + ext
        self.file_location

    def trim(self):
        self.gen_clip_file_location()
        try:
            ffmpeg.input(
                self.file_location, ss=self.pnt - self.buffer, t=2 * self.buffer
            ).output(self.clip_file_location).run()
        except ffmpeg._run.Error:
            # if any error eccured in triming video , we would enter this block.
            raise exceptions.HardAbort(
                f"failed to trim clip for job <{self.job.stream_id}> and pointer <{self.pnt}>"
            )

    def __call__(self):
        self.trim()
        return {self.pointer: self.clip_file_location}


class UploadFile:
    def __init__(self, *args, **kwargs):
        """
        arg1:clips parent directory directory path
        """
        self.clip_parent_dir = args[0]
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_S3_REGION_NAME,
            endpoint_url=AWS_S3_ENDPOINT_URL,
        )

    def upload_clip(self, clip_loc):
        file_name = self.get_file_name(clip_loc)
        with open(clip_loc, "rb") as file:
            self.s3.upload_fileobj(
                file,
                AWS_STORAGE_BUCKET_NAME,
                file_name
            )
            # about above line. some s3 object storages prevent to get files larger than ~400 mb. also uploading a large file as a whole have risks and correpted with any network issue during upload.so to prevent those sittuations we upload files as multipart. it means the boto3 client will split the video file and send every part seperated. on the other side s3 server will merge these files togheter and save this as one large file. is fun yeeeh? :))

    def get_file_name(self, clip_loc):
        # we shoudl remove directory names from clip location and just use clip name to upload.
        return os.path.basename(clip_loc)

    def __call__(self):
        # we iterate in the clips parent directory and will upload every video file exists.
        for clip_loc in self.clip_parent_dir.iterdir():
            self.upload_clip(clip_loc.resolve())


class ProcessJob:
    def __init__(self, job):
        self.job = job
        self.pnts = self.job.pointer_set.all()  # short for pointers
        self.pnt_obj_clip_url_map = {}  # pointer objects maped to clip urls.
        self.files_base_dir = settings.FILES_BASE_DIR

    def get_base_dir(self):
        return settings.FILES_BASE_DIR  # is a path obj

    def set_filename(self):
        self.filename = self.job.vid_name

    def set_file_location(self):
        """
        file is the  downloaded main video file (main video file is the file that specified in job object to download and operate on it) .
        at this function we will set file location and make its directory.
        """
        base_dir = self.get_base_dir()
        self.set_filename()
        file_dir_location = (base_dir / Path("".join(self.filename.split(".")[:-1])) ).resolve()
        os.mkdir(file_dir_location)
        self.file_location = base_dir / file_dir_location / self.filename

    def get_clip_names(self):
        clip_names = []
        for pnt_obj, clip_url in self.pnt_obj_clip_url_map.items():
            clip_name = os.path.basename(urlparse(clip_url).path)
            clip_names.append(clip_name)
        return clip_names

    def create_clips_url(self):
        def get_basename(cloc):
            """
            gets clip location and return clips name.(basename)
            # </home/vahid/salam.mp5> path basename is <salam.mp5>
            """
            return os.path.basename(cloc)

        def get_base_url():
            return settings.AWS_S3_ENDPOINT_URL + settings.AWS_STORAGE_BUCKET_NAME

        base_url = get_base_url()
        if not base_url.endswith("/"):
            base_url = base_url + "/"
        for pnt_obj, cloc in self.pnt_obj_clip_url_map.items():
            self.pnt_obj_clip_url_map[pnt_obj] = base_url + get_basename(cloc)

    def make_clips(self):
        for pnt_obj, clip_url in self.pnt_obj_clip_url_map.items():
            pnt_obj.clip_url = clip_url
            pnt_obj.save()

    def submit_job_failure(self, exc):
        self.job.failure_count = self.job.failure_count + 1
        self.job.failure_reason = self.job.failure_reason + '\n' + str(exc)

    def disk_cleanup(self):
        # cleanup the main video directory.
        try:
            if self.file_location.parent.is_dir():
                shutil.rmtree(self.file_location.parent)
        except:
            logger.exception(f"failed to disk cleanup,job: <{self.job.stream_id}>")
            pass

    def storage_cleanup(self):
        try:
            s3 = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_S3_REGION_NAME,
                endpoint_url=AWS_S3_ENDPOINT_URL,
            )
            clip_names = self.get_clip_names()
            for name in clip_names:
                s3.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=name)
        except:
            logger.exception(f"failed to storage cleanup,job: <{self.job.stream_id}>")
            pass

    def process(self):
        """
        this is the first function threads wants to do. at this function job's videos gets downloaded , trimed and uploded to remote storage.
        if any error eccured(soft abort , hard abort or onhandled) jobs status chnaged to appropriate value and a cleanup would eccured.
        """
        try:
            self.set_file_location()
            self.job.status = jmodels.StatusChoice.UNDPRC
            self.job.save()
            twitch_dl(self.job.video_id , self.file_location) # file_location is the main video file location
            for pnt in self.pnts:
                # for every pointer , we create a copy file and trim it.
                pnt_obj_cloc = TrimFile(self.job, self.file_location, pnt)()
                self.pnt_obj_clip_url_map.update(pnt_obj_cloc)

            self.file_location.unlink()  # removing main video here before uploading clips allow other threads to use disk without problem.it reduces time to deallocating disk space back to other threads.

            UploadFile(self.file_location.parent)()
            self.create_clips_url()
            self.make_clips()
        except exceptions.SoftAbort:
            # if process a job raised with soft error excpetion , we left job status untouched to handle it again with another thread at another time.
            logger.debug(f"failed to process job <{self.job.stream_id}>")
            self.storage_cleanup()
        except exceptions.HardAbort as e:
            self.job.status = jmodels.StatusChoice.SCHED
            self.submit_job_failure(e)
            self.storage_cleanup()
            logger.exception(f"failed to process job <{self.job.stream_id}>")
        except Exception as e:
            self.job.status = jmodels.StatusChoice.SCHED
            self.submit_job_failure(e)
            self.storage_cleanup()
            logger.exception(f"failed to process job <{self.job.stream_id}>")
        else:
            logger.info(f"job <{self.job.stream_id}> processed successfully")
            self.job.status = jmodels.StatusChoice.PRC
        finally:
            self.job.save()
            self.disk_cleanup()


def process_job_func(queue):
    """
    this function called by a worker thread. it runs in a infinite loop to pick jobs from queue and process them.
    """
    while True:
        job = queue.get()
        ProcessJob(job).process()


class Main:
    """
    the whole process is handled by two entities. a producer and multiple consumers. producer actually is the main thread that put jobs in a queue and spawn worker threads. on the other side consumers are workers that pick jobs from queue and process them.
    """

    def __init__(self):
        self.thread_cnt = settings.THREAD_CNT
        assert self.thread_cnt > 0
        self.queue = queue.Queue()

    def base_dir_has_perm(self):
        """
        files directory should pass these 3 stages:
            1/should exists physically
            2/should has read permission by calling threads
            3/should has write permission by calling threads.
        """
        base_dir = settings.FILES_BASE_DIR
        perms = [
            (os.access(base_dir, os.F_OK), "directory %s does not exists."),
            (
                os.access(base_dir, os.R_OK),
                "you dont have permission to read on directory %s.",
            ),
            (
                os.access(base_dir, os.W_OK),
                "you dont have permission to write on directory %s.",
            ),
        ]  # [(bool,reason)]

        for perm in perms:
            if not perm[0]:
                raise PermissionError(perm[1] % settings.FILES_BASE_DIR)
        return

    def get_job(self):
        """get all scheduled jobs queryset (it wont query the db)"""
        return jmodels.Job.objects.filter(status=jmodels.StatusChoice.SCHED)

    def start_jobs_consumer(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.thread_cnt
        )
        for i in range(self.thread_cnt):
            self.executor.submit(process_job_func, self.queue)

    def enqueue_jobs(self):
        jobs = self.get_job()
        if jobs.count():
            print("There are " + str(jobs.count()) + " new jobs to process.")
            for job in jobs:
                self.queue.put(job)
                job.status = jmodels.StatusChoice.QUEUED
                job.save()
        else:
            print("No job found")

        time.sleep(settings.SLEEP_TIME)

    def main(self):
        self.base_dir_has_perm()
        try:
            self.start_jobs_consumer()
            while True:
                self.enqueue_jobs()
        except Exception as e:
            logger.critical(f'UNEXPECTED ERROR ECCURED: {str(e)}')
            self.executor.shutdown()

    def __call__(self):
        self.main()
