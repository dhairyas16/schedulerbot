class ClientHelper:
    def __init__(self, client):
        self.client = client

    def get_bot_channels(self):
        try:
            result = self.client.conversations_list(types='public_channel,private_channel')
            channels = result["channels"]
            bot_channels = []
            for chnl in channels:
                if chnl['is_member']:
                    bot_channels.append(chnl['name'])
            return bot_channels
        except Exception as e:
            print(f"Error fetching channels: {e}")
