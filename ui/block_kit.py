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
        }

    def schedule_list_blocks(self, user_id, scheduler, jobs):
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
                        "text": "Use `/schedule-recurring` to schedule a new recurring message."
                    }
                },
            ]

        mapping = util.get_mapping()
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
                            "text": f"*Message:*\n{util.get_few_words(job[mapping['message']])}"
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
                    "text": "Use `/schedule-recurring-list` to show your recurring messages."
                }
            }
        ]


blocks = BlockKit()
