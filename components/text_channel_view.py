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

        channel_id = str(interaction.channel_id)
        user_id = str(interaction.user.id)

        # 根據特殊標記找到要編輯的embed訊息
        async for msg in interaction.channel.history(limit=100):
            if msg.author == interaction.client.user and msg.embeds and msg.embeds[0].footer.text == f"regenerate_id:{unique_id}":
                original_message = msg
                break
        else:
            await interaction.followup.send("找不到原始訊息。", ephemeral=True)
            return

        text_channel_cog = interaction.client.get_cog("TextChannelCog")
        if text_channel_cog:
            success = await text_channel_cog.regenerate_response(original_message, channel_id, user_id)
            if success:
                # 如果重新生成成功,移除當前的按鈕
                await interaction.message.edit(view=None)
                await interaction.followup.send("訊息已重新生成。", ephemeral=True)
            else:
                await interaction.followup.send("重新生成訊息時發生錯誤。", ephemeral=True)
        else:
            await interaction.followup.send("TextChannelCog 未載入。", ephemeral=True)

class ResendButton(Button):
    def __init__(self, user_id):
        super().__init__(label="輸出回應", style=discord.ButtonStyle.blurple)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("只有發起對話的用戶才能使用此按鈕。", ephemeral=True)
            return

        response_text = interaction.message.embeds[0].fields[1].value
        await interaction.response.send_message(response_text, ephemeral=True)

class EmbedChatView(View):
    def __init__(self, user_id, timeout=14400):  # 4小時
        super().__init__(timeout=timeout)
        self.add_item(RegenerateButton(user_id))
        self.add_item(ResendButton(user_id))