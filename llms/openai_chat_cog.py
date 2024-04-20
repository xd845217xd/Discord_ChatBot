import discord
from discord.ext import commands
from openai import OpenAI
import os

class OpenAIChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(api_key=os.getenv('OPENAI_TOKEN'))
        self.chat_history = {}

    async def process_message(self, message, api, module, prompt):
        user_id = str(message.author.id)
        channel_id = message.channel.id

        if channel_id not in self.chat_history:
            self.chat_history[channel_id] = {}

        if user_id not in self.chat_history[channel_id]:
            self.chat_history[channel_id][user_id] = {
                "messages": [],
                "last_processed_message_id": None
            }

        user_history = self.chat_history[channel_id][user_id]
        user_history["messages"].append({"role": "user", "content": message.content})
        messages_for_api = user_history["messages"][-5:]
        messages_for_api.append({"role": "system", "content": prompt})

        if message.id == user_history["last_processed_message_id"]:
            return
        user_history["last_processed_message_id"] = message.id

        async with message.channel.typing():
            response = self.client.chat.completions.create(
                model=module,
                messages=messages_for_api,
                max_tokens=4096,
                temperature=0.7
            )

        bot_reply = response.choices[0].message.content
        mention = message.author.mention
        await message.reply(f"{mention} {bot_reply}")

async def setup(bot):
    await bot.add_cog(OpenAIChatCog(bot))  # 將 Cog 添加到 bot 中