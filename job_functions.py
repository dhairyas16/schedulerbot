from datetime import timedelta


class JobFunctions:
    def __init__(self, client):
        self.client = client

    def schedule_job(self, **kwargs):
        for channel in kwargs['channels']:
            self.client.chat_postMessage(channel=channel, text=kwargs['message'])
