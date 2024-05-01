import discord
from discord.ext import commands
from openai import OpenAI
import os
import logging

logger = logging.getLogger('discord')

class MessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(api_key=os.getenv('OPENAI_TOKEN'))
        self.chat_history = {}

    @discord.app_commands.command(name="deprecated_chat", description="與ChatGPT聊天")
    async def chat(self, interaction: discord.Interaction, message: str):
        channel_id = str(interaction.channel_id)
        user_id = str(interaction.user.id)
        await interaction.response.defer(ephemeral=False)

        # 這裡的 message 參數就是用戶在 /chat 後面輸入的內容
        user_input = message

        # 初始化聊天歷史
        if channel_id not in self.chat_history:
            self.chat_history[channel_id] = {}
        if user_id not in self.chat_history[channel_id]:
            self.chat_history[channel_id][user_id] = []

        # 增加當前訊息到對話歷史中
        self.chat_history[channel_id][user_id].append({"role": "user", "content": message})

        # 準備發送給API的訊息列表
        messages_for_api = self.chat_history[channel_id][user_id][-5:]

        # 增加特定指示
        specific_prompt = """
        Respond in Traditional Chinese, use Taiwanese slang if needed.
        Prefer brief and objective replies.
        """
        messages_for_api.append({"role": "system", "content": specific_prompt})

        # 調用OpenAI的API來獲取ChatGPT的回覆
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages_for_api,
            max_tokens=4096,
            temperature=0.6
        )

        # 從回應中提取文本回覆
        bot_reply = response.choices[0].message.content

        # 將原始訊息和機器人回覆結合在一起發送
        full_reply = f"{interaction.user.display_name} 說 :\n{user_input}\n\nChatGPT :\n{bot_reply}"
        
        # 加上酷酷的框框
        formatted_reply = f"```\n{full_reply}\n```"

        # 使用 followup.send 發送最終回覆
        await interaction.followup.send(formatted_reply)  # 使用 followup.send 發送最終回覆

async def setup(bot):
    message_cog = MessageCog(bot)
    await bot.add_cog(message_cog)
