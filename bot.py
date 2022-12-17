import json
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler

from utils import get_start_date_and_time, get_end_date, get_week_day, get_mapping
from postgres import db
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

scheduler = BackgroundScheduler()
scheduler.add_jobstore('sqlalchemy', url='sqlite:///jobstorage.sqlite')
scheduler.start()


def job_function(*args):
    for channel in args[1]:
        client.chat_postMessage(channel=channel, text=args[0])


def get_bot_channels():
    try:
        result = client.conversations_list(types='public_channel,private_channel')
        channels = result["channels"]
        bot_channels = []
        for chnl in channels:
            if chnl['is_member']:
                bot_channels.append(chnl['name'])
        return bot_channels
    except Exception as e:
        print(f"Error fetching conversations: {e}")


@app.route('/schedule-recurring', methods=['POST'])
def schedule_recurring():
    data = request.form
    user_id = data.get('user_id')
    print('/schedule-recurring -->', data)

    channel = data.get('channel_name')
    print('channel id -->', channel)

    bot_channels = get_bot_channels()
    options = []
    for chnl in bot_channels:
        options.append({
            "text": {
                "type": "plain_text",
                "text": f"# {chnl}",
                "emoji": True
            },
            "value": chnl
        })

    result = client.views_open(
        trigger_id=data.get("trigger_id"),
        view={
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Schedule Recurring Msg",
                "emoji": True
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit",
                "emoji": True
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel",
                "emoji": True
            },
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "multiline": True,
                        "action_id": "plain_text_input-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Message",
                        "emoji": True
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "datetimepicker",
                        "action_id": "datetimepicker-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Select Starting Date and Time",
                        "emoji": True
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select an item",
                            "emoji": True
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Every day",
                                    "emoji": True
                                },
                                "value": "every-day"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Every week",
                                    "emoji": True
                                },
                                "value": "every-week"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Every month",
                                    "emoji": True
                                },
                                "value": "every-month"
                            }
                        ],
                        "action_id": "static_select-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Select frequency",
                        "emoji": True
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "number_input",
                        "is_decimal_allowed": False,
                        "action_id": "number_input-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "No. of Times",
                        "emoji": True
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "multi_static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select options",
                            "emoji": True
                        },
                        "options": options,
                        "initial_options": [
                            {
                                "text": {
                                    "text": f'# {channel}',
                                    "type": 'plain_text',
                                },
                                "value": channel,
                            },
                        ],
                        "action_id": "multi_static_select-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Select Channel(s)",
                        "emoji": True
                    }
                },
            ]
        },
    )
    print('result -->', result)
    return Response(), 200


def get_few_words(s):
    ls_words = s.split()
    few_words = ls_words[0:10]
    msg = ' '.join(map(str, few_words))
    if len(ls_words) > 9:
        msg += '...'
    return msg


def get_scheduled_job_ids():
    jobs = scheduler.get_jobs()
    job_ids = [job.id for job in jobs]
    return job_ids


@app.route('/schedule-recurring-list', methods=['POST'])
def schedule_recurring_list():
    data = request.form
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    scheduled_job_ids = get_scheduled_job_ids()
    jobs = db.get_user_jobs(user_id, tuple(scheduled_job_ids))
    if len(jobs) == 0:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*There are NO messages scheduled currently.*"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Use `/schedule-recurring` to schedule a new recurring message."
                }
            },
        ]
        client.chat_postEphemeral(channel=channel_id, blocks=blocks, user=user_id)
        return Response(), 200

    mapping = get_mapping()
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":calendar: Your scheduled recurring messages",
                "emoji": True
            }
        },
        {
            "type": "divider"
        }
    ]
    for job in jobs:
        # print('job id -->', scheduler.get_job(job[mapping['job_id']]))
        if job[mapping['user_id']] == user_id:
            channels = ""
            for chnl in job[mapping['channels']]:
                channels += f"#{chnl} "
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Message:*\n{get_few_words(job[mapping['message']])}"
                    }
                }
            )
            blocks.append(
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Start Date:*\n{job[mapping['start_date']]}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{job[mapping['hour']]}:{job[mapping['minute']]}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Total no. of times:*\n{job[mapping['no_of_times']]}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Frequency:*\n{job[mapping['frequency']]}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Next Schedule Time:*\n{scheduler.get_job(str(job[mapping['job_id']])).next_run_time}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Channels:*\n{channels}"
                        }
                    ]
                }
            )
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Post Now"
                            },
                            "style": "primary",
                            "action_id": f"post_now_request_{job[mapping['job_id']]}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Delete"
                            },
                            "style": "danger",
                            "action_id": f"delete_request_{job[mapping['job_id']]}"
                        },
                    ]
                }
            )
            blocks.append(
                {
                    "type": "divider"
                }
            )

    blocks.pop()
    client.chat_postEphemeral(channel=channel_id, blocks=blocks, user=user_id)
    return Response(), 200


def schedule_recurring_msg(message, start_date_time_timestamp_str, frequency, no_of_times, selected_channels,
                           user_timezone):
    start_date, hour, minute = get_start_date_and_time(start_date_time_timestamp_str, user_timezone)
    end_date = get_end_date(start_date_time_timestamp_str, frequency, no_of_times, user_timezone)
    week_day = get_week_day(start_date_time_timestamp_str, user_timezone)
    print('start end hour min week-day -->', start_date, end_date, hour, minute, week_day)
    try:
        resp = None
        if frequency == 'every-day':
            resp = scheduler.add_job(
                job_function,
                'cron',
                start_date=start_date,
                end_date=end_date,
                hour=hour,
                minute=minute,
                # minute="*",
                args=[message, selected_channels]
            )
        elif frequency == 'every-week':
            resp = scheduler.add_job(
                job_function,
                'cron',
                start_date=start_date,
                end_date=end_date,
                day_of_week=week_day,
                hour=hour,
                minute=minute,
                args=[message, selected_channels]
            )
        elif frequency == 'every-month':
            resp = scheduler.add_job(
                job_function,
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


@app.route('/handle-submit', methods=['POST'])
def handle_submit():
    data = request.form
    form_json = json.loads(data.get('payload'))
    print('/handle-submit -->', form_json)
    submission_type = form_json.get('type')
    if submission_type == 'view_submission':
        user_id = form_json['user']['id']
        user_info = client.users_info(user=user_id)
        user_timezone = user_info['user']['tz']
        data = form_json['view']['state']['values']
        list_data = list(data.values())
        print('list data -->', list_data)
        message = list_data[0]['plain_text_input-action']['value']
        start_date_time_timestamp_str = list_data[1]['datetimepicker-action']['selected_date_time']
        frequency = list_data[2]['static_select-action']['selected_option']['value']
        no_of_times = list_data[3]['number_input-action']['value']
        selected_options = list_data[4]['multi_static_select-action']['selected_options']
        selected_channels = []
        for val in selected_options:
            selected_channels.append(val['value'])
        resp, status = schedule_recurring_msg(message, start_date_time_timestamp_str, frequency, no_of_times,
                                              selected_channels, user_timezone)
        print('Job scheduled -->', resp)
        if status != 200:
            print('Error scheduling recurring message: ', resp)
            return Response(), 500
        channels = ""
        for chnl in selected_channels:
            channels += f"#{chnl}"

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Your message was scheduled*"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Message*\n{get_few_words(message)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Channels*\n{channels}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Use `/schedule-recurring-list` to show your recurring messages."
                }
            }
        ]
        client.chat_postEphemeral(channel=selected_channels[0], blocks=blocks, user=user_id)
        start_date, hour, minute = get_start_date_and_time(start_date_time_timestamp_str, user_timezone)
        db.insert(
            (user_id, resp.id, selected_channels, message, start_date, hour, minute, frequency, no_of_times)
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
                print('Error while posting job -->', e)
        if req_type == 'delete_request':
            scheduler.remove_job(job_id)
            db.delete_job(job_id)
            return Response(), 200


if __name__ == '__main__':
    app.run(debug=True, port=6000, use_reloader=False)
