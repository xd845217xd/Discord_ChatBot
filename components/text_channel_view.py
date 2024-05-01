import discord
from discord.ui import Button, View

class RegenerateButton(Button):
    def __init__(self, user_id):
        super().__init__(label="重新生成", style=discord.ButtonStyle.blurple)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        print(f"Regenerate button clicked by user with ID: {interaction.user.id}")
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("只有發起對話的用戶才能使用此按鈕。", ephemeral=True)
            return
        
        if not interaction.message.embeds or not interaction.message.embeds[0].footer.text:
            print("Original message not found or footer format incorrect.")
            await interaction.followup.send("找不到原始訊息或訊息格式不正確。", ephemeral=True)
            return

        unique_id = interaction.message.embeds[0].footer.text.split("regenerate_id:")[1]
        print(f"Extracted UUID from footer: {unique_id}")

        await interaction.response.defer()

        text_channel_cog = interaction.client.get_cog("TextChannelCog")
        if not text_channel_cog:
            await interaction.followup.send("TextChannelCog 未載入。", ephemeral=True)
        elif not (original_message := await text_channel_cog.find_original_message(interaction.channel, unique_id)):
            await interaction.followup.send("找不到原始訊息。", ephemeral=True)
        else:
            success = await text_channel_cog.regenerate_response(original_message, str(interaction.channel.id), str(interaction.user.id))
            await interaction.followup.send("訊息已重新生成。" if success else "重新生成訊息時發生錯誤。", ephemeral=True)

class ResendButton(Button):
    def __init__(self, user_id):
        super().__init__(label="輸出回應", style=discord.ButtonStyle.blurple)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("只有發起對話的用戶才能使用此按鈕。", ephemeral=True)
            return

        if interaction.message.embeds and interaction.message.embeds[0].fields:
            response_text = interaction.message.embeds[0].fields[1].value
            await interaction.response.send_message(response_text, ephemeral=True)
        else:
            await interaction.response.send_message("找不到回應內容。", ephemeral=True)

class EmbedChatView(View):
    def __init__(self, user_id, timeout=14400):  # 4小時
        super().__init__(timeout=timeout)
        self.add_item(RegenerateButton(user_id))
        self.add_item(ResendButton(user_id))

    async def on_timeout(self):
        await self.message.edit(view=None)