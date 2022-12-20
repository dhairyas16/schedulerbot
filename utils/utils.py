from datetime import datetime, timedelta
import pytz


class Util:
    def get_start_date_and_time(self, start_date_time_timestamp_str):
        dt_obj = datetime.fromtimestamp(int(start_date_time_timestamp_str), pytz.timezone('utc'))
        return dt_obj

    def get_end_date(self, start_date_time_timestamp_str, frequency, no_of_times):
        dt_obj = datetime.fromtimestamp(int(start_date_time_timestamp_str), pytz.timezone('utc'))
        ed_obj = None
        if frequency == 'every-day':
            ed_obj = dt_obj + timedelta(days=int(no_of_times) - 1)
        elif frequency == 'every-week':
            ed_obj = dt_obj + timedelta(weeks=int(no_of_times) - 1)
        elif frequency == 'every-month':
            ed_obj = dt_obj + timedelta(days=31 * (int(no_of_times) - 1))
        elif frequency == 'every-one-half-month':
            ed_obj = dt_obj + timedelta(days=45 * (int(no_of_times) - 1))
        elif frequency == 'every-two-month':
            ed_obj = dt_obj + timedelta(days=60 * (int(no_of_times) - 1))
        elif frequency == 'every-three-month':
            ed_obj = dt_obj + timedelta(days=90 * (int(no_of_times) - 1))
        return ed_obj

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

        if next_run_time_obj == None:
            return 0

        if next_run_time_obj == start_date_obj:
            return total_count

        delta_days = (end_date_obj - next_run_time_obj).days
        if frequency == 'every-day':
            return delta_days + 1
        elif frequency == 'every-week':
            return int((delta_days / 7)) + 1
        elif frequency == 'every-month':
            return int((delta_days / 30)) + 1
        elif frequency == 'every-one-half-month':
            return int((delta_days / 45)) + 1
        elif frequency == 'every-two-month':
            return int((delta_days / 60)) + 1
        elif frequency == 'every-three-month':
            return int((delta_days / 90)) + 1

    def get_pretty_frequency(self, frequency):
        if frequency == 'every-day':
            return 'Every Day'
        elif frequency == 'every-week':
            return 'Every Week'
        elif frequency == 'every-month':
            return 'Every Month'
        elif frequency == 'every-one-half-month':
            return 'Every 1.5 Months'
        elif frequency == 'every-two-month':
            return 'Every 2 Months'
        elif frequency == 'every-three-month':
            return 'Every 3 Months'

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
