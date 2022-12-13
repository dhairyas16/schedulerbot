import json
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, redirect, url_for
from slackeventsapi import SlackEventAdapter
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']


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
        layout = list_scheduled_messages(channel_id)
        client.chat_postEphemeral(channel=channel_id, blocks=layout, user=user_id)
        return Response(), 200


channel = None


@app.route('/schedule', methods=['POST'])
def schedule():
    data = request.form
    user_id = data.get('user_id')

    print('/schedule -->', data)

    global channel
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


@app.route('/handle-submit', methods=['POST'])
def handle_submit():
    data = request.form
    form_json = json.loads(data.get('payload'))
    print('/handle-submit -->', data.get('payload'))

    global channel
    submission_type = form_json.get('type')
    title = form_json.get('view').get('title').get('text')
    if submission_type == 'view_submission':
        if title == 'Schedule a Message':
            resp = form_json.get('view').get('state').get('values')
            username = form_json.get('user')['username']
            ls = []
            for k, v in resp.items():
                ls.append(v)
            message = ls[0]['plain_text_input-action']['value']
            time_stamp = ls[1]['datetimepicker-action']['selected_date_time']
            schedule_message(str(channel), message, time_stamp, username)
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
