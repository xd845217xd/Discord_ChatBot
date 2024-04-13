import discord
from discord.ext import commands
from openai import OpenAI
import os
import json

class TextChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None or message.author == self.bot.user:
            return

        guild_id = str(message.guild.id)
        channel_id = message.channel.id

        if (guild_id in self.bot.channel and
                channel_id == int(self.bot.channel[guild_id]) and
                self.bot.user.mentioned_in(message)):
            api_cog_name = self.bot.api.get(guild_id)
            if api_cog_name:
                print(f"正在嘗試獲取 Cog: {api_cog_name}")
                api_cog = self.bot.get_cog(api_cog_name)
                if api_cog:
                    print(f"成功獲取 Cog: {api_cog_name}")
                    await api_cog.process_message(message)
                else:
                    print(f"無法獲取 Cog: {api_cog_name}")
                    await message.channel.send(f"{api_cog_name} 尚未加載。")
            else:
                await message.channel.send("請先選擇一個 API 進行對話。")

async def setup(bot):
    await bot.add_cog(TextChannelCog(bot))