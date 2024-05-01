import discord
import uuid
from discord.ext import commands
from components.text_channel_view import EmbedChatView

class TextChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.EMBED_COLOR = 0xedff94

    async def get_channel_config_and_cog(self, guild_id, channel_id):
        if guild_id in self.bot.channel and channel_id in self.bot.channel[guild_id]:
            channel_config = self.bot.channel[guild_id][channel_id]
            cog_name = channel_config['cog']
            api_cog = self.bot.get_cog(cog_name)
            return channel_config, api_cog
        return None, None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None or message.author == self.bot.user:
            return

        if self.bot.user.mentioned_in(message):
            guild_id = str(message.guild.id)
            channel_id = str(message.channel.id)
            channel_config, api_cog = await self.get_channel_config_and_cog(guild_id, channel_id)

            if channel_config and api_cog:
                prompt_content = next((prompt['content'] for prompt in self.bot.prompt['prompts'] if prompt['name'] == channel_config['prompt']), self.bot.prompt['default'])
                result = await api_cog.process_message(message, channel_config['api'], channel_config['module'], prompt_content)
                if result and "response" in result:
                    response = result["response"]
                    embed = discord.Embed(title="聊天對話", description="", color=self.EMBED_COLOR)
                    embed.add_field(name=f"{message.author.display_name}", value=message.content, inline=False)
                    embed.add_field(name=f"{message.guild.me.display_name}", value=response, inline=False)

                    unique_id = str(uuid.uuid4())
                    embed.set_footer(text=f"EmbedChat_ID:{unique_id}")
                    
                    async for prev_msg in message.channel.history(limit=10):
                        if prev_msg.author == self.bot.user and prev_msg.embeds:
                            await prev_msg.edit(view=None)
                            break
                    
                    view = EmbedChatView(message.author.id)
                    embed_chat_message = await message.reply(embed=embed, view=view)
                    view.message = embed_chat_message  # 設置 message 屬性
                else:
                    await message.channel.send("對不起,我無法處理您的請求。")
            else:
                await message.channel.send("該頻道未設定機器人。")

    async def find_original_message(self, channel, unique_id):
        async for msg in channel.history(limit=100):
            if msg.author == self.bot.user and msg.embeds and msg.embeds[0].footer.text == f"EmbedChat_ID:{unique_id}":
                return msg
        return None
    
    async def regenerate_response(self, message, channel_id, user_id):
        try:
            guild_id = str(message.guild.id)
            channel_config, api_cog = await self.get_channel_config_and_cog(guild_id, channel_id)

            if channel_config and api_cog:
                user_history = api_cog.chat_history.get(channel_id, {}).get(user_id, {}).get("messages", [])

                if len(user_history) >= 2:
                    last_user_message = user_history[-2]

                    if last_user_message['role'] in ['USER', 'user']:
                        user_history = user_history[:-2]
                        full_message = await message.channel.fetch_message(message.id)
                        
                        if channel_config['cog'] == 'CohereChatCog':
                            full_message.content = last_user_message['message']
                        else:
                            full_message.content = last_user_message['content']

                        result = await api_cog.process_message(full_message, channel_config['api'], channel_config['module'], channel_config['prompt'], chat_history=user_history)
                        return await self.update_response(message, channel_id, user_id, api_cog, result, user_history)
        except Exception as e:
            print(f"regenerate_response 發生異常: {str(e)}")
        return False

    async def update_response(self, message, channel_id, user_id, api_cog, result, user_history):
        try:
            if result and "response" in result:
                response = result["response"]
                unique_id = message.embeds[0].footer.text.split("EmbedChat_ID:")[1]

                last_embed_message = await self.find_original_message(message.channel, unique_id)

                if last_embed_message:
                    embed = last_embed_message.embeds[0]
                    embed.set_field_at(1, name=embed.fields[1].name, value=response, inline=False)
                    await last_embed_message.edit(embed=embed)
                    
                    # 更新 chat_history
                    api_cog.chat_history[channel_id][user_id]["messages"] = user_history

                    return True
                else:
                    await message.channel.send("找不到原始訊息,重新生成失敗。")
        except Exception as e:
            print(f"update_response 發生異常: {str(e)}")
        return False

    @discord.app_commands.command(name="chat_history", description="檢查你與機器人的聊天記錄")
    async def chat_history(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        user_id = str(interaction.user.id)
        channel_config, api_cog = await self.get_channel_config_and_cog(guild_id, channel_id)

        if not channel_config:
            await interaction.response.send_message("該頻道未設定機器人。")
            return

        if not api_cog or not hasattr(api_cog, 'chat_history'):
            await interaction.response.send_message(f"{channel_config['cog']} 尚未載入或沒有 chat_history 屬性。")
            return

        user_history = api_cog.chat_history.get(channel_id, {}).get(user_id, {}).get("messages", None)
        if not user_history:
            await interaction.response.send_message("找不到你與機器人的聊天記錄。")
            return
    
        recent_history = user_history[-10:]
        embed = discord.Embed(title=f"{interaction.user.display_name} 與 {interaction.guild.me.display_name} 的聊天記錄", color=self.EMBED_COLOR)
        embed.description = "\N{WARNING SIGN} 只顯示最近十條訊息 \N{WARNING SIGN} 超過200個字元會被省略"
        
        if channel_config['cog'] == 'CohereChatCog':
            for msg in recent_history:
                field_value = msg['message'][:200] + "…（以下省略）" if len(msg['message']) > 200 else msg['message']
                embed.add_field(name=f"{msg['role'].capitalize()}:", value=field_value, inline=False)
        else:
            for msg in recent_history:
                field_value = msg['content'][:200] + "…（以下省略）" if len(msg['content']) > 200 else msg['content']
                embed.add_field(name=f"{msg['role'].capitalize()}:", value=field_value, inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    text_channel_cog = TextChannelCog(bot)
    await bot.add_cog(text_channel_cog)