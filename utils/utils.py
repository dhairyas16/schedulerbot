from datetime import datetime, timedelta
import pytz


class Util:
    def get_start_date_and_time(self, start_date_time_timestamp_str, user_timezone):
        dt_obj = datetime.fromtimestamp(int(start_date_time_timestamp_str), pytz.timezone('utc'))
        # start_date = dt_obj.date()
        # hour = dt_obj.time().hour
        # minute = dt_obj.time().minute
        return dt_obj

    def get_end_date(self, start_date_time_timestamp_str, frequency, no_of_times, user_timezone):
        dt_obj = datetime.fromtimestamp(int(start_date_time_timestamp_str), pytz.timezone('utc'))
        print('dt_obj -->', dt_obj)
        ed_obj = None
        if frequency == 'every-day':
            ed_obj = dt_obj + timedelta(days=int(no_of_times) - 1)
        elif frequency == 'every-week':
            ed_obj = dt_obj + timedelta(weeks=int(no_of_times) - 1)
        elif frequency == 'every-month':
            ed_obj = dt_obj + timedelta(days=31 * (int(no_of_times) - 1))
        return ed_obj

    def get_week_day(self, start_date_time_timestamp_str, user_timezone):
        dt_obj = datetime.fromtimestamp(int(start_date_time_timestamp_str), pytz.timezone('utc'))
        return dt_obj.weekday()

    def get_few_words(self, s):
        ls_words = s.split()
        few_words = ls_words[0:10]
        msg = ' '.join(map(str, few_words))
        if len(ls_words) > 9:
            msg += '...'
        return msg

    def get_channels_string(self, selected_channels):
        channels = ""
        for chnl in selected_channels:
            channels += f"#{chnl}"
        return channels

    def get_remaining_count(self, scheduler, job_id, start_date_str, end_date_str, frequency, total_count):
        start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S%z')
        end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S%z')
        next_run_time_obj = scheduler.get_job(str(job_id)).next_run_time

        if next_run_time_obj == start_date_obj:
            return total_count

        delta_days = (end_date_obj - next_run_time_obj).days
        if frequency == 'every-day':
            return delta_days + 1
        elif frequency == 'every-week':
            return int((delta_days / 7)) + 1
        elif frequency == 'every-month':
            return int((delta_days / 30)) + 1

    def get_mapping(self):
        return {
            'user_id': 0,
            'job_id': 1,
            'channels': 2,
            'message': 3,
            'start_date': 4,
            'hour': 5,
            'minute': 6,
            'frequency': 7,
            'no_of_times': 8,
            'end_date': 9
        }


util = Util()
