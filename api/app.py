import json
import pytz
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from pytz import utc

from db import db
from utils.utils import util
from utils.client_helper import ClientHelper
from utils.scheduler_helper import SchedulerHelper
from ui.block_kit import blocks
from datetime import datetime, timedelta

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

# Slack client
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

# Scheduler
scheduler = BackgroundScheduler(timezone=utc)
# jobstore = SQLAlchemyJobStore(
#     url=f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
# )
# scheduler.add_jobstore(jobstore)
scheduler.add_jobstore('sqlalchemy', url='sqlite:///./data/jobstorage.sqlite')
scheduler.start()

client_helper = ClientHelper(client)
scheduler_helper = SchedulerHelper(scheduler, client)


@app.route('/schedule-help', methods=['POST'])
def schedule_help():
    data = request.form
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    client.chat_postEphemeral(
        channel=channel_id,
        blocks=blocks.schedule_help_blocks(),
        user=user_id
    )
    return Response(), 200


@app.route('/schedule', methods=['POST'])
def schedule():
    data = request.form
    user_id = data.get('user_id')
    user_info = client.users_info(user=user_id)
    user_timezone = user_info['user']['tz']
    channel = data.get('channel_name')
    bot_channels = client_helper.get_bot_channels()
    result = client.views_open(
        trigger_id=data.get("trigger_id"),
        view=blocks.schedule_msg_blocks(bot_channels, channel, user_timezone),
    )
    if not result['ok']:
        return Response(), 500
    return Response(), 200


@app.route('/schedule-list', methods=['POST'])
def schedule_list():
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
        img_url = list_data[1]['url_text_input-action'].get('value', '')
        selected_date = list_data[2]['datepicker-action']['selected_date']
        selected_time = list_data[3]['timepicker-action']['selected_time']
        dt_str = selected_date + ' ' + selected_time
        local = pytz.timezone(user_timezone)
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
        local_dt = local.localize(dt_obj, is_dst=None)
        start_date_time_timestamp_str = int(local_dt.astimezone(pytz.utc).timestamp())
        # start_date_time_timestamp_str = list_data[2]['datetimepicker-action']['selected_date_time']
        frequency = list_data[4]['static_select-action']['selected_option']['value']
        no_of_times = list_data[5]['number_input-action']['value']
        selected_options = list_data[6]['multi_static_select-action']['selected_options']
        selected_channels = []
        for val in selected_options:
            selected_channels.append(val['value'])
        resp, status = scheduler_helper.schedule_msg(
            message, start_date_time_timestamp_str, frequency, no_of_times, selected_channels, user_id, img_url
        )
        if status != 200:
            print('Error scheduling message: ', resp)
            return Response(), 500
        client.chat_postEphemeral(
            channel=selected_channels[0],
            blocks=blocks.msg_scheduled_blocks(message, util.get_channels_string(selected_channels)),
            user=user_id
        )
        return Response(), 200
    if submission_type == 'block_actions':
        user_id = form_json['user']['id']
        channel_id = form_json['channel']['id']
        action_id = form_json['actions'][0]['action_id']
        req_type, job_id = action_id.rsplit('_', 1)
        if req_type == 'post_now_request':
            try:
                record = db.get_job(job_id)
                channels = json.loads(record[2])
                message = record[3]
                image_url = record[10]
                post_now_blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
                if len(image_url):
                    post_now_blocks.append(
                        {
                            "type": "image",
                            "image_url": image_url,
                            "alt_text": ""
                        }
                    )

                for channel in channels:
                    client.chat_postMessage(channel=channel, blocks=post_now_blocks)
                return Response(), 200
            except Exception as e:
                print('Error while posting message -->', e, flush=True)
                client.chat_postEphemeral(channel=channel_id, text='Message does not exist', user=user_id)
                return Response(), 500
        if req_type == 'delete_request':
            scheduler.remove_job(job_id)
            db.delete_job(job_id)
            client.chat_postMessage(
                channel=f'@{user_id}',
                text=':eyes: *Your message has been deleted*',
            )
            return Response(), 200


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
