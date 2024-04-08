import discord
from discord.ext import commands
from openai import OpenAI
import os
import json

class TextChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(api_key=os.getenv('OPENAI_TOKEN'))  # 初始化OpenAI客戶端
        self.chat_history = {}  # 用來儲存聊天歷史的字典
        self.channel_config = self.load_channel_config()  # 載入頻道配置

    def load_channel_config(self):
        # 從文件中讀取頻道配置
        with open('channel_setup_config.json', 'r') as file:
            return json.load(file)

    @commands.Cog.listener()
    async def on_message(self, message):
        # 檢查訊息是否來自機器人自己或私人對話，是的話則忽略
        if message.guild is None or message.author == self.bot.user:
            return

        guild_id = str(message.guild.id)
        channel_id = message.channel.id
        user_id = str(message.author.id)

        # 檢查是否在設定的頻道中並且機器人被提及
        if (guild_id in self.channel_config and
                channel_id == int(self.channel_config[guild_id]['text_channel_cog']) and
                self.bot.user.mentioned_in(message)):

            if channel_id not in self.chat_history:
                self.chat_history[channel_id] = {}

            if user_id not in self.chat_history[channel_id]:
                self.chat_history[channel_id][user_id] = {
                    "messages": [],
                    "last_processed_message_id": None
                }

            user_history = self.chat_history[channel_id][user_id]

            # 將新消息添加到對話歷史中，即使不立即回應
            user_history["messages"].append({"role": "user", "content": message.content})

            # 為了保持對話連貫性，使用較長的對話歷史來生成回應
            messages_for_api = user_history["messages"][-5:]  # 根據需要調整歷史長度

            # 添加系統指示以引導回應風格
            specific_prompt = "You are a lively, witty chatbot conversing in Traditional Chinese with \
            Taiwanese colloquialisms. Be casual and maintain a light-hearted tone, \
            using emojis when appropriate. Respond directly to user messages without \
            offering translations or explanations unless explicitly asked."
            messages_for_api.append({"role": "system", "content": specific_prompt})

            # 避免重複回應相同的訊息
            if message.id == user_history["last_processed_message_id"]:
                return
            user_history["last_processed_message_id"] = message.id

            # 調用OpenAI API來獲取機器人回應
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages_for_api,
                max_tokens=4096,
                temperature=0.7
            )

            bot_reply = response.choices[0].message.content

            # 發送機器人的回應
            mention = message.author.mention
            await message.channel.send(f"{mention} {bot_reply}")

async def setup(bot):
    text_channel_cog = TextChannelCog(bot)  # 創建對話管理器實例
    await bot.add_cog(text_channel_cog)  # 將實例加入機器人
    print("Text Channel Cog loaded.")
