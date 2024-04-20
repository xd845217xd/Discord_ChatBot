import discord
from .operations import OPERATIONS

class CogControlView(discord.ui.View):
    def __init__(self, bot, title):
        super().__init__()
        self.bot = bot
        self.title = title
        self.message = None  # 新增一個 message 屬性
        self.add_item(CogSelect(bot, title))

class CogSelect(discord.ui.Select):
    def __init__(self, bot, title, channel=None):
        self.bot = bot
        self.title = title
        options = [
            discord.SelectOption(label=name, value=cog)
            for cog, name in bot.cogs_config['cogs_mapping'].items()
        ]
        super().__init__(placeholder="請選擇一個模組...", min_values=1, max_values=1, options=options)
        self.channel = channel

    async def callback(self, interaction: discord.Interaction):
        cog_name = self.values[0]
        operation_class = OPERATIONS.get(self.title)

        if operation_class:
            operation = operation_class(self.bot, interaction, self.channel)
            result = await operation.execute(cog_name)
            await interaction.response.defer()
            await interaction.followup.send(result, ephemeral=True)
        else:
            await interaction.response.send_message("未知的操作類型。", ephemeral=True)
        
        await interaction.delete_original_response()
        self.view.stop()