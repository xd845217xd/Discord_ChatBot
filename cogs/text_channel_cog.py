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
    
    @discord.app_commands.command(name="chat_history", description="檢查你與機器人的聊天記錄")
    async def chat_history(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        user_id = str(interaction.user.id)

        # 簡化條件判斷，提前返回以減少嵌套深度
        if guild_id not in self.bot.channel or channel_id not in self.bot.channel[guild_id]:
            await interaction.response.send_message("該頻道未配置機器人。")
            return

        channel_config = self.bot.channel[guild_id][channel_id]
        cog_name = channel_config['cog']
        api_cog = self.bot.get_cog(cog_name)

        # 檢查cog是否加載及是否具有所需屬性
        if not api_cog or not hasattr(api_cog, 'chat_history'):
            await interaction.response.send_message(f"{cog_name} 尚未加載或沒有 chat_history 屬性。")
            return

        # 獲取用戶聊天記錄
        user_history = api_cog.chat_history.get(channel_id, {}).get(user_id, {}).get("messages", None)
        if not user_history:
            await interaction.response.send_message("找不到你與機器人的聊天記錄。")
            return

        # 組合聊天記錄文本並回應
        history_text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in user_history)
        await interaction.response.send_message(f"你與機器人的聊天記錄:\n{history_text}")

async def setup(bot):
    await bot.add_cog(TextChannelCog(bot))