import discord
from .operations import OPERATIONS

class ChannelSelectView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.add_item(ChannelSelect(bot))

class ChannelSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label=f"#{bot.get_channel(int(channel_id)).name}", value=channel_id)
            for guild_id, channel_dict in bot.channel.items()
            for channel_id in channel_dict.keys()
        ]
        super().__init__(placeholder="請選擇一個頻道...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        channel_id = self.values[0]
        guild_id = str(interaction.guild_id)

        if guild_id in self.bot.channel and channel_id in self.bot.channel[guild_id]:
            del self.bot.channel[guild_id][channel_id]
            self.bot.save_config(self.bot.channel, self.bot.config_paths['channel'])
            await interaction.response.send_message(f"已移除頻道 <#{channel_id}> 的設置。", ephemeral=False)
        else:
            await interaction.response.send_message(f"頻道 <#{channel_id}> 尚未設置。", ephemeral=False)
            