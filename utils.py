from datetime import datetime, timedelta
import pytz


def get_start_date_and_time(start_date_time_timestamp_str):
    dt_obj = datetime.fromtimestamp(int(start_date_time_timestamp_str), pytz.timezone("Asia/Kolkata"))
    start_date = dt_obj.date()
    hour = dt_obj.time().hour
    minute = dt_obj.time().minute
    return start_date, hour, minute


def get_end_date(start_date_time_timestamp_str, frequency, no_of_times):
    dt_obj = datetime.fromtimestamp(int(start_date_time_timestamp_str), pytz.timezone("Asia/Kolkata"))
    print('dt_obj -->', dt_obj)
    ed_obj = None
    if frequency == 'every-day':
        ed_obj = dt_obj + timedelta(days=int(no_of_times) - 1)
    elif frequency == 'every-week':
        ed_obj = dt_obj + timedelta(weeks=int(no_of_times) - 1)
    elif frequency == 'every-month':
        ed_obj = dt_obj + timedelta(days=31 * (int(no_of_times) - 1))
    return ed_obj


def get_week_day(start_date_time_timestamp_str):
    dt_obj = datetime.fromtimestamp(int(start_date_time_timestamp_str), pytz.timezone("Asia/Kolkata"))
    return dt_obj.weekday()


def get_mapping():
    return {
        'user_id': 0,
        'job_id': 1,
        'channels': 2,
        'message': 3,
        'start_date': 4,
        'hour': 5,
        'minute': 6,
        'frequency': 7,
        'no_of_times': 8
    }
