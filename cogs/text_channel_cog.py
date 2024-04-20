import discord
from discord.ext import commands
import os
import json

class TextChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # 判斷是否為私人訊息或由機器人本身發出的訊息
        if message.guild is None or message.author == self.bot.user:
            return

        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        # 同時檢查訊息是否提及機器人以及頻道是否配置於設定中
        if self.bot.user in message.mentions and guild_id in self.bot.channel and channel_id in self.bot.channel[guild_id]:
            channel_config = self.bot.channel[guild_id][channel_id]
            cog_name = channel_config['cog']
            api = channel_config['api']
            module = channel_config['module']
            prompt_name = channel_config['prompt']

            # 根據提示詞的名稱獲取對應的內容
            prompt_content = next((prompt['content'] for prompt in self.bot.prompt['prompts'] if prompt['name'] == prompt_name), self.bot.prompt['default'])

            # 獲取指定名稱的 cog
            api_cog = self.bot.get_cog(cog_name)
            if api_cog:
                # 如果 cog 存在,則呼叫該 cog 的 process_message 方法處理訊息
                await api_cog.process_message(message, api, module, prompt_content)
            else:
                await message.channel.send(f"{cog_name} 尚未加載。")
        else:
            return  # 如果條件不符,則不執行任何操作

async def setup(bot):
    await bot.add_cog(TextChannelCog(bot))