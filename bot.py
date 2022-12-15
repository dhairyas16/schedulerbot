import json
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, redirect, url_for
from slackeventsapi import SlackEventAdapter
from apscheduler.schedulers.background import BackgroundScheduler

from utils import get_start_date_and_time, get_end_date, get_week_day

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

jobs = []


def job_function(*args):
    for chnl in args[1]:
        client.chat_postMessage(channel=chnl, text=args[0])


scheduler = BackgroundScheduler()
scheduler.start()


def list_scheduled_messages(channel):
    response = client.chat_scheduledMessages_list(channel=channel)
    messages = response.data.get('scheduled_messages')
    print('list_scheduled_messages -->', messages)

    layout = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Scheduled Messages",
                "emoji": True
            }
        },
        {
            "type": "divider"
        }
    ]

    if len(messages) == 0:
        return [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "There are no messages scheduled currently.",
                    "emoji": True
                }
            }
        ]

    cnt = 1
    for msg in messages:
        block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{cnt}*. {msg.get('text')}"
            },
            "block_id": f"text{cnt}",
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "emoji": True,
                    "text": "Delete"
                },
                "style": "danger",
                "value": msg.get('id'),
            }
        }
        layout.append(block)
        cnt += 1

    return layout


@app.route('/schedule-list', methods=['GET', 'POST'])
def scheduled_messages():
    if request.method == 'GET':
        payload = json.loads(request.args['messages'])
        layout = list_scheduled_messages(payload['channel_id'])
        client.chat_postEphemeral(channel=payload['channel_id'], blocks=layout, user=payload['user_id'])
        return Response(), 200

    if request.method == 'POST':
        data = request.form
        channel_id = data.get('channel_id')
        user_id = data.get('user_id')
        print(data)

        job = scheduler.get_job(str(job_id))
        print('next run at -->', job.next_run_time)

        layout = list_scheduled_messages(channel_id)
        client.chat_postEphemeral(channel=channel_id, blocks=layout, user=user_id)
        return Response(), 200


job_id = None


@app.route('/schedule', methods=['POST'])
def schedule():
    data = request.form
    user_id = data.get('user_id')

    print('/schedule -->', data)

    channel = data.get('channel_id')
    print('channel id -->', channel)

    result = client.views_open(
        trigger_id=data.get("trigger_id"),
        view={
            "title": {
                "type": "plain_text",
                "text": "Schedule a Message",
                "emoji": True
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit",
                "emoji": True
            },
            "type": "modal",
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
                        "action_id": "plain_text_input-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Message",
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
                        "text": "Label",
                    }
                }
            ]
        },
    )
    print('result -->', result)
    return Response(), 200


def schedule_message(channel_id, message, time_stamp, username):
    response = client.chat_scheduleMessage(channel=channel_id, text=message, post_at=time_stamp, username=username)
    print('Message scheduled -->', response.data)


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


@app.route('/schedule-recurring-list', methods=['POST'])
def schedule_recurring_list():
    data = request.form
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":calendar: Scheduled recurring messages",
                "emoji": True
            }
        },
        {
            "type": "divider"
        }
    ]
    for job in jobs:
        if job['user_id'] == user_id:
            channels = ""
            for chnl in job['channels']:
                channels += f"#{chnl} "
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Message:*\n{get_few_words(job['message'])}"
                    }
                }
            )
            blocks.append(
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Start Date:*\n{job['start_date']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{job['hour']}:{job['minute']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Total no. of times:*\n{job['count']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Frequency:*\n{job['frequency']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Next Schedule Time:*\n{scheduler.get_job(job['job_id']).next_run_time}"
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
                                "text": "Approve"
                            },
                            "style": "primary",
                            "action_id": "approve_request"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Deny"
                            },
                            "style": "danger",
                            "action_id": "deny_request"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "More info"
                            },
                            "action_id": "request_info"
                        }
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


def schedule_recurring_msg(message, start_date_time_timestamp_str, frequency, no_of_times, selected_channels):
    start_date, hour, minute = get_start_date_and_time(start_date_time_timestamp_str)
    end_date = get_end_date(start_date_time_timestamp_str, frequency, no_of_times)
    week_day = get_week_day(start_date_time_timestamp_str)
    print('start end hour min week-day -->', start_date, end_date, hour, minute, week_day)
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
    return resp


@app.route('/handle-submit', methods=['POST'])
def handle_submit():
    data = request.form
    form_json = json.loads(data.get('payload'))
    print('/handle-submit -->', data.get('payload'))

    submission_type = form_json.get('type')
    title = form_json.get('view').get('title').get('text')
    if submission_type == 'view_submission':
        # if title == 'Schedule a Message':
        #     resp = form_json.get('view').get('state').get('values')
        #     username = form_json.get('user')['username']
        #     ls = []
        #     for k, v in resp.items():
        #         ls.append(v)
        #     message = ls[0]['plain_text_input-action']['value']
        #     time_stamp = ls[1]['datetimepicker-action']['selected_date_time']
        #     schedule_message(str(channel), message, time_stamp, username)
        #     return Response(), 200
        if title == 'Schedule Recurring Msg':
            user_id = form_json['user']['id']
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
            print('selected channels -->', selected_channels)
            job_resp = schedule_recurring_msg(message, start_date_time_timestamp_str, frequency, no_of_times,
                                              selected_channels)
            global job_id
            job_id = job_resp.id
            print('Job scheduled -->', job_resp)
            start_date, hour, minute = get_start_date_and_time(start_date_time_timestamp_str)
            jobs.append(
                {
                    'user_id': user_id,
                    'job_id': job_id,
                    'channels': selected_channels,
                    'message': message,
                    'start_date': start_date,
                    'hour': hour,
                    'minute': minute,
                    'frequency': frequency,
                    'count': no_of_times
                }
            )
            return Response(), 200

    if submission_type == 'block_actions':
        msg_id = form_json.get('actions')[0]['value']
        user_id = form_json.get('user')['id']
        channel_id = form_json.get('channel')['id']
        print('channel -->', channel_id)
        client.chat_deleteScheduledMessage(channel=str(channel_id), scheduled_message_id=str(msg_id))
        messages = {
            "user_id": user_id,
            "channel_id": channel_id
        }
        return redirect(url_for('scheduled_messages', messages=json.dumps(messages)))


if __name__ == '__main__':
    app.run(debug=True, port=6000, use_reloader=False)
