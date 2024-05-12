import discord
from discord.ui import Button, View
from typing import Optional

class RegenerateButton(Button):
    def __init__(self, user_id: int):
        super().__init__(label="重新生成", style=discord.ButtonStyle.blurple)
        self.user_id = user_id

    async def check_user_permission(self, interaction: discord.Interaction) -> bool:
        # 檢查用戶權限,只有發起對話的用戶才能使用此按鈕
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("只有發起對話的用戶才能使用此按鈕。", ephemeral=True)
            return False
        return True
    
    def extract_ids_from_footer(self, footer_text: str) -> tuple[str, str]:
        """從 footer 文本中提取 message_id 和 user_id"""
        parts = footer_text.split("/")
        if len(parts) != 2:
            raise ValueError("無效的 footer 格式")

        message_id = parts[0].split("MessageID:")[1]
        user_id = parts[1].split("UserID:")[1]
        return message_id, user_id


    async def callback(self, interaction: discord.Interaction):
        # 檢查用戶權限
        if not await self.check_user_permission(interaction):
            return

        # 檢查訊息格式是否正確
        if not interaction.message.embeds or not interaction.message.embeds[0].footer.text:
            await interaction.followup.send("找不到原始訊息或訊息格式不正確。", ephemeral=True)
            return

        # 從訊息的 footer 中提取 message_id 和 user_id
        footer_text = interaction.message.embeds[0].footer.text
        try:
            message_id, user_id = self.extract_ids_from_footer(footer_text)
        except ValueError:
            await interaction.followup.send("無法從訊息 footer 中提取必要的資訊。", ephemeral=True)
            return

        await interaction.response.defer()

        # 獲取 TextChannelCog
        text_channel_cog = interaction.client.get_cog("TextChannelCog")
        if not text_channel_cog:
            await interaction.followup.send("TextChannelCog 未載入。", ephemeral=True)
            return

        # 尋找原始訊息
        found_message = await text_channel_cog.find_original_message(interaction.channel, int(message_id), int(user_id))
        if not found_message:
            await interaction.followup.send("找不到原始訊息。", ephemeral=True)
        else:
            # 重新生成回應
            success = await text_channel_cog.regenerate_response(found_message, str(interaction.channel.id), user_id)
            await interaction.followup.send("訊息已重新生成。" if success else "重新生成訊息時發生錯誤。", ephemeral=True)

class ResendButton(Button):
    def __init__(self):
        super().__init__(label="輸出回應", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        # 檢查訊息是否包含回應內容
        if interaction.message.embeds and interaction.message.embeds[0].fields:
            response_text = interaction.message.embeds[0].fields[1].value
            await interaction.response.send_message(response_text, ephemeral=True)
        else:
            await interaction.response.send_message("找不到回應內容。", ephemeral=True)

class ClearHistoryConfirmView(View):
    def __init__(self, bot):
        super().__init__(timeout=30)  # 30秒後自動關閉視圖
        self.bot = bot
        self.confirmed = False

    @discord.ui.button(label="確認", style=discord.ButtonStyle.danger)
    async def confirm_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="取消", style=discord.ButtonStyle.secondary)
    async def cancel_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.stop()

    async def on_timeout(self):
        # 超時後自動取消
        self.stop()

class EmbedChatView(View):
    def __init__(self, user_id: int, timeout: float = 14400):  # 4小時
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.add_item(RegenerateButton(user_id))
        self.add_item(ResendButton())

    async def on_timeout(self):
        # 超時後移除按鈕
        await self.message.edit(view=None)

class ChannelSetupView(discord.ui.View):
    def __init__(self, bot, channel: discord.TextChannel):
        super().__init__()
        self.bot = bot
        self.channel = channel
        self.api = None
        self.module = None
        self.prompt_name = None
        self.add_item(APISelect(bot))

class APISelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label=api, value=api)
            for api in bot.api_module.keys()
        ]
        super().__init__(placeholder="請選擇一個語言模型 API...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # 用戶選擇了一個 API
        self.view.api = self.values[0]
        self.view.clear_items()
        self.view.add_item(ModuleSelect(self.bot, self.view.api))
        await interaction.response.edit_message(view=self.view)

class ModuleSelect(discord.ui.Select):
    def __init__(self, bot, api: str):
        self.bot = bot
        self.api = api
        options = [
            discord.SelectOption(label=module['name'], value=module['value'])
            for module in bot.api_module[api]['modules']
        ]
        super().__init__(placeholder="請選擇一個模組...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # 用戶選擇了一個模組
        self.view.module = self.values[0]
        self.view.clear_items()
        self.view.add_item(PromptSelect(self.bot, self.api, self.view.module))
        await interaction.response.edit_message(view=self.view)

class PromptSelect(discord.ui.Select):
    def __init__(self, bot, api: str, module: str):
        self.bot = bot
        self.api = api
        self.module = module
        options = [
            discord.SelectOption(label=prompt['name'], value=prompt['name'])
            for prompt in bot.prompt['prompts']
        ]
        super().__init__(placeholder="請選擇一個提示詞...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # 用戶選擇了一個提示詞
        self.view.prompt_name = self.values[0]
        self.view.stop()