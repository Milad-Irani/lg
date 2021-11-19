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


AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_S3_ENDPOINT_URL = settings.AWS_S3_ENDPOINT_URL
AWS_S3_REGION_NAME = settings.AWS_S3_REGION_NAME
AWS_DEFAULT_ACL = settings.AWS_DEFAULT_ACL
MB = 1024 ** 2
S3_Config = TransferConfig(multipart_threshold=350 * MB)

logger = logging.getLogger(__name__)


class DlFile:
    def __init__(self, *args, **kwargs):
        """
        arg1:job
        arg2:floc :file location
        """
        self.job = args[0]
        self.floc = args[1]
        free = shutil.disk_usage(".").free #get free disk/partition usage.
        self.free_disk_amount = free // (2 ** 30)

    def has_space_to_dl(self):
        """ first of all we should check the disk and partition we work on it has enaugh space or not. to do that we compare file size with """
        res = requests.head(self.job.video_url)
        size = int(res.headers.get("Content-Length")) / (2 ** 30) #convert to GB
        if size and (3 * size) >= self.free_disk_amount:
            raise exceptions.HardAbort("there is not enaugh space left on disk.")
        return

    def dl_vid(self):
        self.has_space_to_dl()
        res = requests.get(self.job.video_url, stream=True) #by setting stream to True , we wont have to inect all file data to memeory. we read 2048 bytes into memory and flush it to disk.
        for cnt in res.iter_content(chunk_size=2048):
            with open(self.floc, "ab") as f:
                f.write(cnt)

    def __call__(self):
        self.dl_vid()


class TrimFile:
    def __init__(self, *args, **kwargs):
        """
        arg1:job
        arg2:pnt
        """
        self.job = args[0]
        self.floc = str(
            args[1]
        )  # floc is type of Path object. so ffempeg just knows str.
        self.pointer = args[2]
        self.pnt = self.pointer.pointer
        # self.buffer = settings.TRIM_BUFFER
        self.buffer = 5

    def gen_clip_floc(self):
        # we append the pointer value to end of file name before extension to prevent overriding on main file.
        path, ext = "".join(self.floc.split(".")[:-1]), self.floc.split(".")[-1]
        self.clip_floc = path + "__" + str(self.pnt) + "." + ext
        self.floc

    def trim(self):
        self.gen_clip_floc()
        try:
            ffmpeg.input(
                self.floc, ss=self.pnt - self.buffer, t=2 * self.buffer
            ).output(self.clip_floc).run()
        except ffmpeg._run.Error:
            # if any error eccured in triming video , we would enter this block.
            raise exceptions.HardAbort(
                f"failed to trim clip for job <{self.job.id}> and pointer <{self.pnt}>"
            )

    def __call__(self):
        self.trim()
        return {self.pointer: self.clip_floc}


class UpFile:
    def __init__(self, *args, **kwargs):
        """
        arg1:clip directory path
        """
        self.cloc = args[0]
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_S3_REGION_NAME,
            endpoint_url=AWS_S3_ENDPOINT_URL,
        )

    def up_clip(self):
        cdest = self.get_cdest()
        with open(self.cloc, "rb") as file:
            self.s3.upload_fileobj(
                file,
                AWS_STORAGE_BUCKET_NAME,
                cdest,
                Config=S3_Config,
                ExtraArgs={"ACL": AWS_DEFAULT_ACL},
            )
            # about above line. some s3 object storages prevent to get files larger than ~400 mb. also uploading a large file as a whole have risks and correpted with any network issue during upload.so to prevent those sittuations we upload files as multipart. it means the boto3 client will split the video file and send every part seperated. on the other side s3 server will merge these files togheter and save this as one large file. is fun yeeeh? :))

    def get_cdest(self):
        # we shoudl remove directory names from clip location and just use clip name to upload.
        return os.path.basename(self.cloc)

    def __call__(self):
        self.up_clip()


class ProcessJob:
    def __init__(self, job):
        self.job = job
        self.pnts = self.job.pointer_set.all() #short for pointers
        self.pnt_obj_curl_map = {} #pointer objects maped to clip urls.

    def set_fname(self):
        self.fname = self.job.vid_name

    def set_floc(self):
        """
        floc is short for file location. file is the  downloaded main video file (main video file is the file that specified in job object to download and operate on it) .
        at this function we will set file location and make its directory.
        """
        self.set_fname()
        fdir_loc = Path("".join(self.fname.split(".")[:-1])).resolve()
        os.mkdir(fdir_loc)
        self.floc = fdir_loc / self.fname

    def create_clips_url(self):
        def get_basename(cloc):
            """
            gets clip location and return clips name.(basename)
            # </home/vahid/salam.mp5> path basename is <salam.mp5>
            """
            return os.path.basename(cloc)
        def get_base_url():
            #because i didn't have any clue about how to gen base url in general , i put this as hardcoded , but as soom as i get a s3 object storage , this function content would change and generate baseurl as dynamic.
            return "https://ffmpeg.s3.ir-thr-at1.arvanstorage.com/"

        base_url = get_base_url()
        if not base_url.endswith("/"):
            base_url = base_url + "/"
        for pnt_obj, cloc in self.pnt_obj_curl_map.items():
            self.pnt_obj_curl_map[pnt_obj] = base_url + get_basename(cloc)

    def create_clip_objs(self):
        for pnt_obj, curl in self.pnt_obj_curl_map.items():
            # turn this to bulk create.
            jmodels.Clip.objects.create(job=self.job, pointer=pnt_obj, clip_url=curl)

    def cleanup(self):
        # cleanup the main video directory.
        if self.floc.parent.is_dir():
            shutil.rmtree(self.floc.parent)

    def process(self):
        """
        this is the first function threads wants to do. at this function job's videos gets downloaded , trimed and uploded to remote storage.
        if any error eccured(soft abort , hard abort or onhandled) jobs status chnaged to appropriate value and a cleanup would eccured.
        """
        try:
            self.set_floc()
            self.job.status = jmodels.StatusChoice.UNDPRC
            self.job.save()
            DlFile(self.job , self.floc)()  # floc is the main video file location
            for pnt in self.pnts:
                # for every pointer , we create a copy file and trim it.
                pnt_obj_cloc = TrimFile(self.job, self.floc, pnt)()
                self.pnt_obj_curl_map.update(pnt_obj_cloc)

            self.floc.unlink()  # removing main video here before uploading clips allow other threads to use disk without problem.it reduces time to deallocating disk space back to other threads.

            for clip_loc in self.floc.parent.iterdir():
                # we iterate in the floc directory and will upload every video file exists.
                UpFile(clip_loc)()
            self.create_clips_url()
            self.create_clip_objs()

        except exceptions.SoftAbort:
            # if process a job raised with soft error excpetion , we left job status untouched to handle it again with another thread at another time.
            logger.debug(f"failed to process job <{self.job.id}>")
        except exceptions.HardAbort:
            self.job.status = jmodels.StatusChoice.FLD
            logger.exception(f"failed to process job <{self.job.id}>")
        except:
            self.job.status = jmodels.StatusChoice.FLD
            logger.exception(f"failed to process job <{self.job.id}>")
        else:
            logger.info(f'job <{self.job.id}> processed successfully')
            self.job.status = jmodels.StatusChoice.PRC
        finally:
            self.job.save()
            self.cleanup()


def process_job_func(job):
    ProcessJob(job).process()


class Main:
    def __init__(self):
        self.thr_cnt = settings.THREAD_CNT
        assert self.thr_cnt > 0

    def get_job(self):
        """get all scheduled jobs queryset (it wont query the db)"""
        return jmodels.Job.objects.filter(status=jmodels.StatusChoice.SCHED)

    def handle_jobs(self, jobs):
        # at this function excecution control gives to worker threads.
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.thr_cnt
        ) as executor:
            executor.map(process_job_func, jobs)

    def main(self):
        while True:
            jobs = self.get_job()
            if not jobs.exists():
                print("NO JOBS TO DO ------")
                time.sleep(1)
            else:
                jobs_cnt_to_process = 10
                if jobs.count() < 10:
                    jobs_cnt_to_process = jobs.count()
                self.handle_jobs(jobs[:jobs_cnt_to_process])


    def __call__(self):
        self.main()
