#!/usr/bin/env python3
from crontab import CronTab
import os
import sys
import inspect
import time

from . import config, root_logger

logger = root_logger.getChild("scheduling")

cmd = os.path.join(os.path.split(os.path.abspath(sys.argv[0]))[0], "schedule.py")
crontab = CronTab(user=True)

callbacks = []


def check_setup():
    if config["scheduling"]["type"] == "cron":
        if len(list(crontab.find_command(cmd))) == 0:
            logger.warning("Cron job not found. Creating now.")
            job = crontab.new(command=cmd)
            if config["scheduling"]["frequency"] == "daily":
                job.day.every(1)
            elif config["scheduling"]["frequency"] == "hourly":
                job.hour.every(1)
            else:
                raise ValueError(
                    "Scheduling frequency is not valid."
                    "Must be one of 'daily', 'hourly'."
                )
            job.enable()
            crontab.write()

    else:
        raise ValueError(
            "Scheduling type is not valid."
            "Must be one of 'cron'."
        )

def add(callback):
    callbacks.append(callback)

def main():
    for func in callbacks:
        func(time.time())

check_setup()
if __name__ == "__main__":
    main()
