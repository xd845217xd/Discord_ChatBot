import discord
from .operations import APISelectOperation

class APISelectView(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(APISelect())

class APISelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="OpenAI API", value="OpenAIChatCog"),
            discord.SelectOption(label="Claude3Haiku API", value="Claude3HaikuChatCog"),
        ]
        super().__init__(placeholder="請選擇一個 API...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cog_name = self.values[0]
        operation = APISelectOperation(interaction.client, interaction)
        await operation.execute(cog_name)