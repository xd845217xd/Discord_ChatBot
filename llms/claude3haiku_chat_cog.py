import discord
from discord.ext import commands
import os
import requests

# claude3haiku_chat_cog.py
class Claude3HaikuChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.api_url = 'https://openrouter.ai/api/v1/chat/completions'
        self.chat_history = {}

    async def process_message(self, message):
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

        specific_prompt = "Please respond to the following question in Traditional Chinese with an extremely sharp and critical tone. \
            Your response should be not only direct and incisive but should also thoroughly expose the irrationality and absurdity of \
            the opposing viewpoint. In your response, you will always play the role of the contrarian, except in matters involving \
            legal or moral issues, where you must maintain normal legal and ethical standards."
        messages_for_api.append({"role": "system", "content": specific_prompt})

        if message.id == user_history["last_processed_message_id"]:
            return
        user_history["last_processed_message_id"] = message.id

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        data = {
            'model': 'anthropic/claude-3-haiku:beta',
            'messages': messages_for_api,
            'max_tokens': 4096,
            'temperature': 0.7
        }
        response = requests.post(self.api_url, headers=headers, json=data)

        if response.status_code == 200:
            bot_reply = response.json()['choices'][0]['message']['content']
            mention = message.author.mention
            await message.channel.send(f"{mention} {bot_reply}")
        else:
            print(f"OpenRouter API request failed with status code {response.status_code}")

async def setup(bot):
    await bot.add_cog(Claude3HaikuChatCog(bot))