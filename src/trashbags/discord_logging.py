"""Discord Logging
"""
from discord_webhook import DiscordWebhook


class MyLittleDiscord:
    def __init__(self, config=None):
        self.config = config

    def send_channel_message(self, message) -> None:
        """Send message to Discord

        Args:
            message (string): Message to send to discord
        """
        webhook = DiscordWebhook(url=self.config.discord_webhook, content=message)
        try:
            webhook.execute()
        except Exception as error:
            print(f"Webhook failed, error: {error}")
