import discord
from discord.ext import commands
import json
from components.cog_select_view import CogSelectView

class ChannelSetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name='viewsetup', description='確認目前設定')
    async def view_channel_setup(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        if guild_id in self.bot.channel:
            await interaction.response.send_message(f"目前設定: {self.bot.channel[guild_id]}")
        else:
            await interaction.response.send_message("此伺服器尚未設置特定頻道。")

    @discord.app_commands.command(name='configuresetup', description='設置特定頻道和 cog')
    async def configure_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        view = CogSelectView(self.bot, "configuresetup", channel)
        await interaction.response.send_message("請選擇要配置的模組：", view=view, ephemeral=True)

    @discord.app_commands.command(name='removesetup', description='移除特定頻道設置')
    async def remove_channel(self, interaction: discord.Interaction):
        view = CogSelectView(self.bot, "removesetup")
        await interaction.response.send_message("請選擇要移除設置的模組：", view=view, ephemeral=True)

    @discord.app_commands.command(name='resetsetup', description='重置目前伺服器的所有頻道設定')
    async def reset_channel_setup(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        if guild_id in self.bot.channel:
            del self.bot.channel[guild_id]
            self.bot.save_config(self.bot.channel, self.bot.config_paths['channel'])
            await interaction.response.send_message("已重置所有頻道設定。")
        else:
            await interaction.response.send_message("此伺服器沒有設定任何特定頻道，無需重置。")

async def setup(bot):
    channel_setup_cog = ChannelSetupCog(bot)
    await bot.add_cog(channel_setup_cog)  # 將這個 cog 添加到 bot 中
