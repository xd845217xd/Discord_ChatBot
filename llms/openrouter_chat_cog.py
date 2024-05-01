import discord
from discord.ext import commands
from openai import OpenAI
import os

class OpenRouterChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = 'https://openrouter.ai/api/v1'
        self.chat_history = {}
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    async def process_message(self, message, api, module, prompt, chat_history=None):
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)

        if channel_id not in self.chat_history:
            self.chat_history[channel_id] = {}

        if user_id not in self.chat_history[channel_id]:
            self.chat_history[channel_id][user_id] = {
                "messages": [],
                "last_processed_message_id": None
            }

        if chat_history is None:
            user_history = self.chat_history[channel_id][user_id]["messages"]
        else:
            user_history = chat_history

        user_history.append({"role": "user", "content": message.content})
        messages_for_api = user_history[-5:]

        messages_for_api.append({"role": "system", "content": prompt})

        async with message.channel.typing():
            response = self.client.chat.completions.create(
                model=module,
                messages=messages_for_api,
                max_tokens=4096,
                temperature=0.7
            )

        bot_reply = response.choices[0].message.content
        user_history.append({"role": "assistant", "content": bot_reply})
        self.chat_history[channel_id][user_id]["messages"] = user_history
        return {"response": bot_reply}

async def setup(bot):
    openrouter_chat_cog = OpenRouterChatCog(bot)
    await bot.add_cog(openrouter_chat_cog)