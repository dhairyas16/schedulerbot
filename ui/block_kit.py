import pytz

from utils.utils import util


class BlockKit:
    def schedule_msg_blocks(self, bot_channels, channel):
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

        return {
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Schedule Message",
                "emoji": True
            },
            "submit": {
                "type": "plain_text",
                "text": "Schedule",
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
        }

    def schedule_list_blocks(self, user_id, scheduler, jobs, user_timezone):
        if len(jobs) == 0:
            return [
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
                        "text": "Use `/schedule` to schedule a new message."
                    }
                },
            ]

        mapping = util.get_mapping()
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":calendar: Your scheduled messages",
                    "emoji": True
                }
            },
            {
                "type": "divider"
            }
        ]

        for job in jobs:
            if job[mapping['user_id']] == user_id:
                channels = ""
                for chnl in job[mapping['channels']]:
                    channels += f"#{chnl} "

                remaining_count = util.get_remaining_count(scheduler, job[mapping['job_id']],
                                                           job[mapping['start_date']], job[mapping['end_date']],
                                                           job[mapping['frequency']], job[mapping['no_of_times']])
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Message*\n{util.get_few_words(job[mapping['message']])}"
                        }
                    }
                )
                blocks.append(
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Start Date & Time*\n{job[mapping['start_date']]}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Next Posting At*\n{scheduler.get_job(str(job[mapping['job_id']])).next_run_time.astimezone(pytz.timezone(user_timezone)) if scheduler.get_job(str(job[mapping['job_id']])).next_run_time else 'None'}"
                            },
                            # {
                            #     "type": "mrkdwn",
                            #     "text": f"*Time:*\n{job[mapping['hour']]}:{job[mapping['minute']]}"
                            # },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total no. of times*\n{job[mapping['no_of_times']]}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Remaining no. of times*\n{remaining_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Frequency*\n{job[mapping['frequency']]}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Channels*\n{channels}"
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
        return blocks

    def msg_scheduled_blocks(self, message, channels):
        return [
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
                        "text": f"*Message*\n{util.get_few_words(message)}"
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
                    "text": "Use `/schedule-list` to show your messages."
                }
            }
        ]

    def schedule_help_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hey there 👋 I'm SchedulerBot. I'm here to help you schedule and manage messages in Slack. \nQuickly schedule and manage messages using following commands:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*1️⃣ Use the `/schedule` command*. Type `/schedule` in any channel I'll ask for a details about your message. Try it out by using the `/schedule` command in any channel."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*2️⃣ Use the `/schedule-list` command.* This will list all your scheduled messages, you can post message right at the moment using `Post Now` button or delete message using `Delete` button."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "❓Get help at any time with `/schedule-help`"
                    }
                ]
            }
        ]


blocks = BlockKit()
