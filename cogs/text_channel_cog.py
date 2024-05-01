import discord
import uuid
from discord.ext import commands
from components.text_channel_view import EmbedChatView
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

        if self.bot.user.mentioned_in(message):
            guild_id = str(message.guild.id)
            channel_id = str(message.channel.id)

            if guild_id in self.bot.channel and channel_id in self.bot.channel[guild_id]:
                channel_config = self.bot.channel[guild_id][channel_id]
                cog_name = channel_config['cog']
                api = channel_config['api']
                module = channel_config['module']
                prompt_name = channel_config['prompt']

                prompt_content = next((prompt['content'] for prompt in self.bot.prompt['prompts'] if prompt['name'] == prompt_name), self.bot.prompt['default'])

                api_cog = self.bot.get_cog(cog_name)
                if api_cog:
                    result = await api_cog.process_message(message, api, module, prompt_content)
                    if result and "response" in result:
                        response = result["response"]
                        embed = discord.Embed(title="Chat Session", description="", color=0x1a1a1a)
                        embed.add_field(name=f"{message.author.display_name}", value=message.content, inline=False)
                        embed.add_field(name=f"{message.guild.me.display_name}", value=response, inline=False)

                        # 生成UUID作為特殊標記
                        unique_id = str(uuid.uuid4())
                        print(f"Generated UUID for new message: {unique_id}")
                        embed.set_footer(text=f"regenerate_id:{unique_id}")
                        
                        view = EmbedChatView(message.author.id)
                        await message.reply(embed=embed, view=view)
                    else:
                        await message.channel.send("對不起,我無法處理您的請求。")
                else:
                    await message.channel.send(f"{cog_name} 尚未加載。")
            else:
                await message.channel.send("該頻道未設定機器人。")
    
    async def regenerate_response(self, message, channel_id, user_id):
        try:
            guild_id = str(message.guild.id)

            if guild_id in self.bot.channel and channel_id in self.bot.channel[guild_id]:
                channel_config = self.bot.channel[guild_id][channel_id]
                cog_name = channel_config['cog']
                api_cog = self.bot.get_cog(cog_name)

                if api_cog:
                    user_history = api_cog.chat_history.get(channel_id, {}).get(user_id, {}).get("messages", [])

                    if len(user_history) >= 2:
                        last_user_message = user_history[-2]

                        if last_user_message['role'] in ['USER', 'user']:
                            user_history = user_history[:-2]

                            # Fetch the full message object
                            full_message = await message.channel.fetch_message(message.id)
                            
                            if cog_name == 'CohereChatCog':
                                full_message.content = last_user_message['message']
                            else:
                                full_message.content = last_user_message['content']

                            result = await api_cog.process_message(full_message, channel_config['api'], channel_config['module'], channel_config['prompt'], chat_history=user_history)

                            return await self.update_response(message, channel_id, user_id, api_cog, result, user_history)
                        else:
                            print("The second to last message is not a User message.")
                    else:
                        print("User history does not contain enough messages.")
                else:
                    print(f"無法獲取 {cog_name} 實例")
            else:
                print(f"頻道 {channel_id} 未設置機器人")
        except Exception as e:
            print(f"regenerate_response 發生異常: {str(e)}")
        return False

    async def update_response(self, message, channel_id, user_id, api_cog, result, user_history):
        if result and "response" in result:
            response = result["response"]

            # 找到要編輯的Embed訊息
            unique_id = message.embeds[0].footer.text.split("regenerate_id:")[1]
            async for msg in message.channel.history(limit=100):
                if msg.author == self.bot.user and msg.embeds and msg.embeds[0].footer.text == f"regenerate_id:{unique_id}":
                    last_embed_message = msg
                    break
            else:
                # 如果找不到要編輯的Embed訊息,發送一條新的訊息告知用戶
                await message.channel.send("找不到原始訊息,重新生成失敗。")
                return False

            # 編輯Embed訊息
            embed = last_embed_message.embeds[0]
            embed.set_field_at(1, name=embed.fields[1].name, value=response, inline=False)
            await last_embed_message.edit(embed=embed)

            # 更新 chat_history
            api_cog.chat_history[channel_id][user_id]["messages"] = user_history

            return True
        else:
            print("API returned no response.")
            return False

    @discord.app_commands.command(name="chat_history", description="檢查你與機器人的聊天記錄")
    async def chat_history(self, interaction: discord.Interaction):
        # 獲取伺服器ID、頻道ID和用戶ID
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        user_id = str(interaction.user.id)

        # 檢查是否為當前頻道設定了機器人
        if guild_id not in self.bot.channel or channel_id not in self.bot.channel[guild_id]:
            await interaction.response.send_message("該頻道未設定機器人。")
            return

        # 獲取當前頻道的設定和指令集
        channel_config = self.bot.channel[guild_id][channel_id]
        cog_name = channel_config['cog']
        api_cog = self.bot.get_cog(cog_name)

        # 檢查指令集是否載入和包含chat_history屬性
        if not api_cog or not hasattr(api_cog, 'chat_history'):
            await interaction.response.send_message(f"{cog_name} 尚未載入或沒有 chat_history 屬性。")
            return

        # 嘗試獲取用戶的聊天記錄
        user_history = api_cog.chat_history.get(channel_id, {}).get(user_id, {}).get("messages", None)
        if not user_history:
            await interaction.response.send_message("找不到你與機器人的聊天記錄。")
            return
    
        # 只獲取最近的 10 條訊息
        recent_history = user_history[-10:]
    
        # 創建嵌入消息來展示聊天記錄
        embed = discord.Embed(title=f"{interaction.user.display_name} 與 {interaction.guild.me.display_name} 的聊天記錄", color=0x1a1a1a)
        
        # 增加提醒訊息
        embed.description = "\N{WARNING SIGN} 只顯示最近十條訊息 \N{WARNING SIGN} 超過200個字元會被省略"
    
        # 增加聊天訊息到嵌入中
        for msg in recent_history:
            role = msg['role']
            content = msg['content'] if 'content' in msg else msg['message']
        
            # 如果訊息過長，進行截斷處理
            if len(content) > 200:
                content = content[:200] + "…（以下省略）"
        
            embed.add_field(name=f"{role.capitalize()}:", value=content, inline=False)

        # 發送嵌入消息
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    text_channel_cog = TextChannelCog(bot)
    await bot.add_cog(text_channel_cog)