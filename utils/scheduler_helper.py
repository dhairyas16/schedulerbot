from utils.utils import util
from job_functions import JobFunctions


class SchedulerHelper:
    def __init__(self, scheduler, client):
        self.scheduler = scheduler
        self.job_funs = JobFunctions(client)

    def get_scheduled_job_ids(self):
        jobs = self.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        return job_ids

    def schedule_recurring_msg(self, message, start_date_time_timestamp_str, frequency, no_of_times, selected_channels,
                               user_timezone):
        start_date = util.get_start_date_and_time(start_date_time_timestamp_str, user_timezone)
        hour = start_date.hour
        minute = start_date.minute
        end_date = util.get_end_date(start_date_time_timestamp_str, frequency, no_of_times, user_timezone)
        week_day = util.get_week_day(start_date_time_timestamp_str, user_timezone)
        print('start end hour min week-day -->', start_date, end_date, hour, minute, week_day)
        try:
            resp = None
            if frequency == 'every-day':
                resp = self.scheduler.add_job(
                    self.job_funs.schedule_job,
                    'cron',
                    start_date=start_date,
                    end_date=end_date,
                    hour=hour,
                    minute=minute,
                    args=[message, selected_channels]
                )
            elif frequency == 'every-week':
                resp = self.scheduler.add_job(
                    self.job_funs.schedule_job,
                    'cron',
                    start_date=start_date,
                    end_date=end_date,
                    day_of_week=week_day,
                    hour=hour,
                    minute=minute,
                    args=[message, selected_channels]
                )
            elif frequency == 'every-month':
                resp = self.scheduler.add_job(
                    self.job_funs.schedule_job,
                    'cron',
                    day=start_date.day,
                    start_date=start_date,
                    end_date=end_date,
                    hour=hour,
                    minute=minute,
                    args=[message, selected_channels]
                )
            return resp, 200
        except Exception as e:
            print(f'Error while adding job to scheduler {e}')
