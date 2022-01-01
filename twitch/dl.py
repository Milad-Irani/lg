import subprocess
import os
from pathlib import Path


class TwitchDownload():
    def __init__(self , video_id , file_location):
        self.video_id = video_id
        command = "twitch-dl download -q source %s" % video_id
        self.command = command.split(' ')
        self.file_location = file_location

    def run_cmd(self):
        # change current dir
        os.chdir(self.file_location.parent)
        path = Path('.').resolve()
        has_err = False
        err = None
        run = subprocess.run(self.command , capture_output=True)
        if run.returncode != 0:
            has_err = True
            err = run.stderr
        else:
            objs = [obj for obj in path.iterdir()]
            downloaded_file = objs[0]
            os.rename(downloaded_file, self.file_location)
        return has_err , err

    def download(self):
        has_err , err = self.run_cmd()
        if has_err:
            return err
        return None
