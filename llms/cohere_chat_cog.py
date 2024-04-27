import discord
from discord.ext import commands
import cohere
import os

class CohereChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = cohere.Client(os.getenv('COHERE_API_KEY'))
        self.chat_history = {}

    async def process_message(self, message, api, module, prompt):
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)

        if channel_id not in self.chat_history:
            self.chat_history[channel_id] = {}

        if user_id not in self.chat_history[channel_id]:
            self.chat_history[channel_id][user_id] = {
                "messages": [],
                "last_processed_message_id": None
            }

        user_history = self.chat_history[channel_id][user_id]
        user_history["messages"].append({"role": "user", "message": message.content})
        messages_for_api = user_history["messages"][-5:]

        if message.id == user_history["last_processed_message_id"]:
            return
        user_history["last_processed_message_id"] = message.id

        async with message.channel.typing():
            response = self.client.chat(
                message=message.content,
                model=module,
                preamble=prompt,
                chat_history=messages_for_api,
                max_tokens=4000,
                temperature=0.7,
                max_input_tokens=1024,
                connectors=[{"id": "web-search"}]
            )

        bot_reply = response.text
        mention = message.author.mention
        await message.reply(f"{mention} {bot_reply}")

async def setup(bot):
    await bot.add_cog(CohereChatCog(bot))  # 將 Cog 添加到 bot 中