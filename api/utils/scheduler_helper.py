import pytz
from uuid import uuid4
from utils.utils import util
from job_functions import JobFunctions
from db import db
from datetime import datetime, timedelta
import json


class SchedulerHelper:
    def __init__(self, scheduler, client):
        self.scheduler = scheduler
        self.client = client
        self.job_funs = JobFunctions(client)

    def get_scheduled_job_ids(self):
        jobs = self.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        return job_ids

    def schedule_msg(self, message, start_date_time_timestamp_str, frequency, no_of_times, selected_channels, user_id, img_url):
        start_date = util.get_start_date_and_time(start_date_time_timestamp_str)
        hour = start_date.hour
        minute = start_date.minute
        end_date = util.get_end_date(start_date_time_timestamp_str, frequency, no_of_times)
        job_id = uuid4().hex
        payload = {
            'message': message,
            'img_url': img_url,
            'channels': selected_channels,
        }
        try:
            resp = None
            if frequency == 'every-day':
                resp = self.scheduler.add_job(
                    id=job_id,
                    func=self.job_funs.schedule_job,
                    trigger='interval',
                    days=1,
                    start_date=start_date,
                    end_date=end_date,
                    kwargs=payload,
                )
            elif frequency == 'every-week':
                resp = self.scheduler.add_job(
                    id=job_id,
                    func=self.job_funs.schedule_job,
                    trigger='interval',
                    weeks=1,
                    start_date=start_date,
                    end_date=end_date,
                    kwargs=payload,
                )
            elif frequency == 'every-month':
                resp = self.scheduler.add_job(
                    id=job_id,
                    func=self.job_funs.schedule_job,
                    trigger='interval',
                    days=30,
                    start_date=start_date,
                    end_date=end_date,
                    kwargs=payload,
                )
            elif frequency == 'every-one-half-month':
                resp = self.scheduler.add_job(
                    id=job_id,
                    func=self.job_funs.schedule_job,
                    trigger='interval',
                    days=45,
                    start_date=start_date,
                    end_date=end_date,
                    kwargs=payload,
                )
            elif frequency == 'every-two-month':
                resp = self.scheduler.add_job(
                    id=job_id,
                    func=self.job_funs.schedule_job,
                    trigger='interval',
                    days=60,
                    start_date=start_date,
                    end_date=end_date,
                    kwargs=payload,
                )
            elif frequency == 'every-three-month':
                resp = self.scheduler.add_job(
                    id=job_id,
                    func=self.job_funs.schedule_job,
                    trigger='interval',
                    days=90,
                    start_date=start_date,
                    end_date=end_date,
                    kwargs=payload,
                )

            # Storing in DB
            db.insert(
                (
                    user_id, resp.id, json.dumps(selected_channels), message, str(start_date), hour, minute,
                    frequency, no_of_times, str(end_date)
                )
            )
            print(' inserted in db')
            return resp, 200
        except Exception as e:
            print(f'Error: schedule_msg --> {e}')
