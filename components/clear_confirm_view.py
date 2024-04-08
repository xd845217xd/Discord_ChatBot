import discord
from .operations import ClearChannelOperation

class ClearConfirmView(discord.ui.View):
    def __init__(self, bot, interaction, channel):
        super().__init__(timeout=30)  # 設定超時時間為 30 秒
        self.bot = bot
        self.interaction = interaction
        self.channel = channel

    async def on_timeout(self):
        await self.interaction.edit_original_response(content="操作已超時。", view=None)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("你無法使用這個按鈕。", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="確認", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        operation = ClearChannelOperation(self.bot, self.interaction, self.channel)
        await operation.execute()
        await interaction.response.defer()
        await self.interaction.edit_original_response(content="頻道已成功清除。", view=None)
        self.stop()

    @discord.ui.button(label="取消", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.interaction.edit_original_response(content="操作已取消。", view=None)
        self.stop()