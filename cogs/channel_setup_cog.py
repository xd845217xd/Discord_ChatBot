import discord
from discord.ext import commands
from components.channel_setup_view import ChannelSetupView, ChannelSelectView
import json

class ChannelSetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name='viewsetup', description='確認目前設定')
    async def view_channel_setup(self, interaction: discord.Interaction):
        # 獲取目前伺服器的 ID
        guild_id = str(interaction.guild_id)
        if guild_id in self.bot.channel:
            channel_setups = []
            # 遍歷該伺服器的所有頻道設定
            for channel_id, setup in self.bot.channel[guild_id].items():
                channel = self.bot.get_channel(int(channel_id))
                channel_setups.append(f"頻道: {channel.mention}, Cog: {setup['cog']}, API: {setup['api']}, 模組: {setup['module']}, 提示詞: {setup['prompt']}")
            await interaction.response.send_message("\n".join(channel_setups))
        else:
            await interaction.response.send_message("此伺服器尚未設定特定頻道。")

    @discord.app_commands.command(name='configuresetup', description='設定特定頻道、語言模型、模組和提示詞')
    async def configure_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # 創建一個 ChannelSetupView 實例,用於設定特定頻道的語言模型、模組和提示詞
        view = ChannelSetupView(self.bot, channel)
        await interaction.response.send_message("請選擇要配置的語言模型、模組和提示詞:", view=view, ephemeral=True)

    @discord.app_commands.command(name='removesetup', description='移除特定頻道設定')
    async def remove_channel(self, interaction: discord.Interaction):
        # 創建一個 ChannelSelectView 實例,用於選擇要移除設定的頻道
        await interaction.response.send_message("請選擇要移除設定的頻道:", view=ChannelSelectView(self.bot), ephemeral=True)

    @discord.app_commands.command(name='resetsetup', description='重設目前伺服器的所有頻道設定')
    async def reset_channel_setup(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        if guild_id in self.bot.channel:
            # 如果目前伺服器存在於 bot.channel 中,則刪除該伺服器的所有頻道設定
            del self.bot.channel[guild_id]
            # 將更新後的設定保存到設定檔案中
            self.bot.save_config(self.bot.channel, self.bot.config_paths['channel'])
            await interaction.response.send_message("已重設所有頻道設定。")
        else:
            await interaction.response.send_message("此伺服器沒有設定任何特定頻道,無需重設。")

async def setup(bot):
    channel_setup_cog = ChannelSetupCog(bot)
    await bot.add_cog(channel_setup_cog)  # 將這個 cog 添加到 bot 中