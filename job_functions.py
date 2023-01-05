class JobFunctions:
    def __init__(self, client):
        self.client = client

    def schedule_job(self, **kwargs):
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": kwargs['message']
                }
            }
        ]
        if len(kwargs['img_url']):
            blocks.append(
                {
                    "type": "image",
                    "image_url": kwargs['img_url'],
                    "alt_text": ""
                }
            )
        for channel in kwargs['channels']:
            self.client.chat_postMessage(channel=channel, blocks=blocks)
