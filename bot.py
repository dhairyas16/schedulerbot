import json

import pytz
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

from postgres import db
from utils.utils import util
from utils.client_helper import ClientHelper
from utils.scheduler_helper import SchedulerHelper
from ui.block_kit import blocks

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

# Slack client
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

# Scheduler
scheduler = BackgroundScheduler(timezone=utc)
scheduler.add_jobstore('sqlalchemy', url='sqlite:///jobstorage.sqlite')
scheduler.start()

client_helper = ClientHelper(client)
scheduler_helper = SchedulerHelper(scheduler, client)


@app.route('/schedule-recurring', methods=['POST'])
def schedule_recurring():
    data = request.form
    channel = data.get('channel_name')
    bot_channels = client_helper.get_bot_channels()
    result = client.views_open(
        trigger_id=data.get("trigger_id"),
        view=blocks.schedule_msg_blocks(bot_channels, channel),
    )
    if not result['ok']:
        return Response(), 500
    return Response(), 200


@app.route('/schedule-recurring-list', methods=['POST'])
def schedule_recurring_list():
    data = request.form
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    scheduled_job_ids = scheduler_helper.get_scheduled_job_ids()
    user_info = client.users_info(user=user_id)
    user_timezone = user_info['user']['tz']
    jobs = db.get_user_jobs(user_id, tuple(scheduled_job_ids))
    client.chat_postEphemeral(
        channel=channel_id,
        blocks=blocks.schedule_list_blocks(user_id, scheduler, jobs, user_timezone),
        user=user_id
    )
    return Response(), 200


@app.route('/handle-submit', methods=['POST'])
def handle_submit():
    data = request.form
    form_json = json.loads(data.get('payload'))
    submission_type = form_json.get('type')
    if submission_type == 'view_submission':
        user_id = form_json['user']['id']
        user_info = client.users_info(user=user_id)
        user_timezone = user_info['user']['tz']
        data = form_json['view']['state']['values']
        list_data = list(data.values())
        message = list_data[0]['plain_text_input-action']['value']
        start_date_time_timestamp_str = list_data[1]['datetimepicker-action']['selected_date_time']
        frequency = list_data[2]['static_select-action']['selected_option']['value']
        no_of_times = list_data[3]['number_input-action']['value']
        selected_options = list_data[4]['multi_static_select-action']['selected_options']
        selected_channels = []
        for val in selected_options:
            selected_channels.append(val['value'])
        resp, status = scheduler_helper.schedule_recurring_msg(
            message, start_date_time_timestamp_str, frequency, no_of_times, selected_channels, user_timezone
        )
        print('job scheduled -->', resp)
        if status != 200:
            print('Error scheduling recurring message: ', resp)
            return Response(), 500

        client.chat_postEphemeral(
            channel=selected_channels[0],
            blocks=blocks.msg_scheduled_blocks(message, util.get_channels_string(selected_channels)),
            user=user_id
        )
        start_date_obj = util.get_start_date_and_time(
            start_date_time_timestamp_str, user_timezone
        ).astimezone(pytz.timezone(user_timezone))
        # start_date = start_date_obj.date()
        hour = start_date_obj.hour
        minute = start_date_obj.minute
        end_date = util.get_end_date(start_date_time_timestamp_str, frequency, no_of_times, user_timezone)
        db.insert(
            (user_id, resp.id, selected_channels, message, str(start_date_obj), hour, minute, frequency, no_of_times,
             str(end_date))
        )
        return Response(), 200
    if submission_type == 'block_actions':
        action_id = form_json['actions'][0]['action_id']
        req_type, job_id = action_id.rsplit('_', 1)
        if req_type == 'post_now_request':
            try:
                record = db.get_job(job_id)
                channels = record[2]
                message = record[3]
                for channel in channels:
                    client.chat_postMessage(channel=channel, text=message)
                scheduler.remove_job(job_id)
                db.delete_job(job_id)
                return Response(), 200
            except Exception as e:
                print('Error while posting message -->', e)
        if req_type == 'delete_request':
            scheduler.remove_job(job_id)
            db.delete_job(job_id)
            return Response(), 200


if __name__ == '__main__':
    # db.delete_all_records()
    app.run(debug=True, port=6000, use_reloader=False)
