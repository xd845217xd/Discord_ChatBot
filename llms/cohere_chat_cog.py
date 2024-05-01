import discord
from discord.ext import commands
import cohere
import os

class CohereChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = cohere.Client(os.getenv('COHERE_API_KEY'))
        self.chat_history = {}

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

        user_history.append({"role": "USER", "message": message.content})
        messages_for_api = user_history[-5:]

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
        user_history.append({"role": "CHATBOT", "message": bot_reply})
        self.chat_history[channel_id][user_id]["messages"] = user_history
        return {"response": bot_reply}

async def setup(bot):
    cohere_chat_cog = CohereChatCog(bot)
    await bot.add_cog(cohere_chat_cog)