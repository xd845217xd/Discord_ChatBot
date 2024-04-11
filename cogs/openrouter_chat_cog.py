import discord
from discord.ext import commands
import os
import json
import requests

class OpenRouterChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.api_url = 'https://openrouter.ai/api/v1/chat/completions'
        self.chat_history = {}
        self.channel_config = self.load_channel_config()

    def load_channel_config(self):
        with open('channel_setup_config.json', 'r') as file:
            return json.load(file)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None or message.author == self.bot.user:
            return

        guild_id = str(message.guild.id)
        channel_id = message.channel.id
        user_id = str(message.author.id)

        if (guild_id in self.channel_config and
                channel_id == int(self.channel_config[guild_id].get('openrouter_chat_cog', 0)) and
                self.bot.user.mentioned_in(message)):

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

            specific_prompt = "You are a lively, witty chatbot conversing in Traditional Chinese with \
            Taiwanese colloquialisms. Be casual and maintain a light-hearted tone, \
            using emojis when appropriate. Respond directly to user messages without \
            offering translations or explanations unless explicitly asked."
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
    openrouter_chat_cog = OpenRouterChatCog(bot)
    await bot.add_cog(openrouter_chat_cog)