class JobFunctions:
    def __init__(self, client):
        self.client = client

    def schedule_job(self, *args):
        for channel in args[1]:
            self.client.chat_postMessage(channel=channel, text=args[0])
