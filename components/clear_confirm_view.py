import discord
from .operations import ClearChannelOperation

class ClearConfirmView(discord.ui.View):
    def __init__(self, bot, interaction, channel):
        super().__init__(timeout=30)  # 設定超時時間為 30 秒
        self.bot = bot
        self.interaction = interaction
        self.channel = channel

    async def on_timeout(self):
        try:
            await self.interaction.edit_original_response(content="操作已超時。", view=None)  # 如果超時,編輯原始回應並移除視圖
        except discord.errors.NotFound:
            pass

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("你無法使用這個按鈕。", ephemeral=True)  # 如果與原始互動用戶不同,發送錯誤訊息
            return False
        return True

    @discord.ui.button(label="確認", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()  # 延遲回應
        operation = ClearChannelOperation(self.bot, self.interaction, self.channel)  # 創建 ClearChannelOperation 實例
        try:
            await operation.execute()  # 執行清除頻道操作
            try:
                await self.interaction.edit_original_response(content="頻道已成功清除。", view=None)  # 編輯原始回應並移除視圖
            except discord.errors.NotFound:
                pass
        except Exception as e:
            try:
                await self.interaction.edit_original_response(content=f"清除頻道時發生錯誤: {str(e)}", view=None)  # 如果發生錯誤,編輯原始回應並顯示錯誤訊息
            except discord.errors.NotFound:
                pass
        self.stop()  # 停止視圖

    @discord.ui.button(label="取消", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()  # 延遲回應
        await self.interaction.edit_original_response(content="操作已取消。", view=None)  # 編輯原始回應並顯示取消訊息
        self.stop()  # 停止視圖