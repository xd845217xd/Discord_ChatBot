import discord
import uuid
import traceback
import asyncio
from datetime import datetime, time
from discord.ext import commands
from typing import Optional, Dict, Any
from components.text_channel_view import EmbedChatView, ChannelSetupView, ClearHistoryConfirmView
from components import operations

class TextChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.EMBED_COLOR: int = 0xedff94

    class ConfigureSetupOperation:
        def __init__(self, cog, interaction: discord.Interaction, channel: discord.TextChannel):
            self.cog = cog
            self.interaction = interaction
            self.channel = channel

        async def execute(self, api: str, module: str, prompt_name: str):
            guild_id: str = str(self.interaction.guild_id)
            channel_id: str = str(self.channel.id)

            if guild_id not in self.cog.bot.channel:
                self.cog.bot.channel[guild_id] = {}

            prompt_content: str = next((prompt['content'] for prompt in self.cog.bot.prompt['prompts'] if prompt['name'] == prompt_name), self.cog.bot.prompt['default'])

            self.cog.bot.channel[guild_id][channel_id] = {
                'cog': self.cog.bot.api_module[api]["cog_name"],
                'api': api,
                'module': module,
                'prompt': prompt_name
            }
            self.cog.bot.save_config(self.cog.bot.channel, self.cog.bot.config_paths['channel'])

            await self.interaction.followup.send(
                f"已將頻道 {self.channel.mention} 的設置更新為:\n"
                f"API: {api}\n模組: {module}\n提示詞: {prompt_name}",
                ephemeral=False
            )
            
            try:
                await self.cog.bot.reload_extension(f"llms.{api.lower()}_chat_cog")
                await self.interaction.followup.send(f"`{self.cog.bot.api_module[api]['cog_name']}` 模組已重新載入。", ephemeral=False)
            except Exception as e:
                await self.interaction.followup.send(f"載入 `{self.cog.bot.api_module[api]['cog_name']}` 模組時發生錯誤: {str(e)}", ephemeral=True)
                print(f"Error reloading Cog for {api}: {str(e)}")

    async def get_channel_config_and_cog(self, guild_id: str, channel_id: str) -> tuple[Optional[Dict[str, Any]], Optional[commands.Cog]]:
        """
        根據給定的伺服器ID和頻道ID,獲取頻道配置和對應的Cog。

        :param guild_id: 伺服器ID。
        :param channel_id: 頻道ID。
        :return: 一個元組,包含頻道配置(如果存在)和對應的Cog(如果存在)。
        """
        if guild_id in self.bot.channel and channel_id in self.bot.channel[guild_id]:
            channel_config: Dict[str, Any] = self.bot.channel[guild_id][channel_id]
            cog_name: str = channel_config['cog']
            api_cog: Optional[commands.Cog] = self.bot.get_cog(cog_name)
            return channel_config, api_cog
        return None, None

    async def is_bot_mentioned(self, message: discord.Message) -> bool:
        return self.bot.user.mentioned_in(message)

    async def get_prompt_content(self, channel_config: Dict[str, Any]) -> str:
        return next((prompt['content'] for prompt in self.bot.prompt['prompts'] if prompt['name'] == channel_config['prompt']), self.bot.prompt['default'])

    async def send_response(self, message: discord.Message, response: str, user_id: int):
        """
        將機器人的回應發送到指定的頻道。

        :param message: 觸發回應的原始訊息。
        :param response: 要發送的回應內容。
        :param user_id: 觸發回應的使用者ID。
        """
        embed = discord.Embed(title="聊天對話", description="", color=self.EMBED_COLOR)
        embed.add_field(name=f"{message.author.display_name}", value=message.content, inline=False)

        response_chunks = [response[i:i+1000] for i in range(0, len(response), 1000)]

        for i, chunk in enumerate(response_chunks):
            field_name = f"{message.guild.me.display_name}" if i == 0 else f"回應內容 (Part {i+1})"
            embed.add_field(name=field_name, value=chunk, inline=False)

        unique_id: str = str(uuid.uuid4())
        embed.set_footer(text=f"EmbedChat_ID:{unique_id}/UserID:{user_id}")
        
        # 移除該用戶之前的所有 embed 訊息按鈕
        async for prev_msg in message.channel.history(limit=10): # 上限10則訊息,不然太高會被Discord API速率限制
            if prev_msg.author == self.bot.user and prev_msg.embeds:
                prev_embed: discord.Embed = prev_msg.embeds[0] 
                if prev_embed.footer:
                    footer_parts: list[str] = prev_embed.footer.text.split("/")
                    if len(footer_parts) == 2 and footer_parts[1] == f"UserID:{user_id}":
                        await prev_msg.edit(view=None)
                else:
                    print(f"發現没有預期 footer 的 embed 訊息: {prev_msg.id}")
        
        view = EmbedChatView(user_id, unique_id)
        embed_chat_message: discord.Message = await message.reply(embed=embed, view=view)
        view.message = embed_chat_message

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author == self.bot.user:
            return

        if await self.is_bot_mentioned(message):
            guild_id: str = str(message.guild.id)
            channel_id: str = str(message.channel.id)
            channel_config, api_cog = await self.get_channel_config_and_cog(guild_id, channel_id)

            if channel_config and api_cog:
                prompt_content: str = await self.get_prompt_content(channel_config)
                api_response: Optional[Dict[str, Any]] = await api_cog.process_message(message, channel_config['api'], channel_config['module'], prompt_content)
                
                if api_response and "response" in api_response:
                    response: str = api_response["response"]
                    await self.send_response(message, response, message.author.id)
                else:
                    await message.channel.send("對不起,我無法處理您的請求。")
            else:
                await message.channel.send("該頻道未設定機器人。")

    async def find_original_message(self, channel: discord.TextChannel, unique_id: str, user_id: int) -> Optional[discord.Message]:
        async for msg in channel.history(limit=10):
            if msg.author == self.bot.user and msg.embeds and msg.embeds[0].footer.text == f"EmbedChat_ID:{unique_id}/UserID:{user_id}":
                return msg
        return None
    
    async def regenerate_response(self, message: discord.Message, channel_id: str, user_id: int) -> bool:
        guild_id: str = str(message.guild.id)
        channel_config, api_cog = await self.get_channel_config_and_cog(guild_id, channel_id)

        if channel_config and api_cog:
            user_history: list[Dict[str, Any]] = api_cog.chat_history.get(channel_id, {}).get(user_id, {}).get("messages", [])

            if len(user_history) >= 2:
                last_user_message: Dict[str, Any] = user_history[-2]

                if last_user_message['role'] in ['USER', 'user']:
                    user_history = user_history[:-2]
                    full_message: discord.Message = await message.channel.fetch_message(message.id)
                    
                    # 根據不同的 Cog,設置 full_message.content 為正確的值
                    # 這樣可以確保在重新生成回應時,使用的是正確的使用者訊息
                    if channel_config['cog'] == 'CohereChatCog':
                        full_message.content = last_user_message['message']
                    else:
                        full_message.content = last_user_message['content']

                    api_response: Optional[Dict[str, Any]] = await api_cog.process_message(full_message, channel_config['api'], channel_config['module'], channel_config['prompt'], chat_history=user_history)
                    return await self.update_response(message, channel_id, user_id, api_cog, api_response, user_history)
        
        return False


    async def update_response(self, message: discord.Message, channel_id: str, user_id: str, api_cog: commands.Cog, api_response: Optional[Dict[str, Any]], user_history: list[Dict[str, Any]]) -> bool:
        try:
            if api_response and "response" in api_response:
                response: str = api_response["response"]
                footer_info: list[str] = message.embeds[0].footer.text.split("/")
                unique_id: str = footer_info[0].split("EmbedChat_ID:")[1]
                user_id: int = int(footer_info[1].split("UserID:")[1])

                last_embed_message: Optional[discord.Message] = await self.find_original_message(message.channel, unique_id, user_id)

                if last_embed_message:
                    embed: discord.Embed = last_embed_message.embeds[0]
                    embed.set_field_at(1, name=embed.fields[1].name, value=response, inline=False)
                    await last_embed_message.edit(embed=embed)
                    
                    # 更新 chat_history
                    api_cog.chat_history[channel_id][str(user_id)]["messages"] = user_history

                    return True
                else:
                    await message.channel.send("找不到原始訊息,重新生成失敗。")
        except Exception as e:
            print(f"update_response 發生異常: {str(e)}")
            traceback.print_exc()
        return False
    
    @discord.app_commands.command(name="clear_history", description="清理歷史訊息")
    async def clear_history(self, interaction: discord.Interaction):
        await operations.OPERATIONS['clearhistoryandrestartcog'](self.bot, interaction).execute()

    @discord.app_commands.command(name="chat_history", description="檢查你與機器人的聊天記錄")
    async def chat_history(self, interaction: discord.Interaction):
        guild_id: str = str(interaction.guild_id)
        channel_id: str = str(interaction.channel_id)
        user_id: str = str(interaction.user.id)
        channel_config, api_cog = await self.get_channel_config_and_cog(guild_id, channel_id)

        if not channel_config:
            await interaction.response.send_message("該頻道未設定機器人。")
            return

        if not api_cog or not hasattr(api_cog, 'chat_history'):
            await interaction.response.send_message(f"{channel_config['cog']} 尚未載入或沒有 chat_history 屬性。")
            return

        user_history: Optional[list[Dict[str, Any]]] = api_cog.chat_history.get(channel_id, {}).get(user_id, {}).get("messages", None)
        if not user_history:
            await interaction.response.send_message("找不到你與機器人的聊天記錄。")
            return
    
        recent_history: list[Dict[str, Any]] = user_history[-10:]
        embed = discord.Embed(title=f"{interaction.user.display_name} 與 {interaction.guild.me.display_name} 的聊天記錄", color=self.EMBED_COLOR)
        embed.description = "\N{WARNING SIGN} 只顯示最近十條訊息 \N{WARNING SIGN} 超過200個字元會被省略"
        
        if channel_config['cog'] == 'CohereChatCog':
            for msg in recent_history:
                field_value: str = (
                    msg['message'][:200] + "…（以下省略）"
                    if len(msg['message']) > 200 else msg['message']
                )
                embed.add_field(name=f"{msg['role'].capitalize()}:", value=field_value, inline=False)
        else:
            for msg in recent_history:
                field_value: str = (
                    msg['content'][:200] + "…（以下省略）" 
                    if len(msg['content']) > 200 else msg['content']
                )
                embed.add_field(name=f"{msg['role'].capitalize()}:", value=field_value, inline=False)

        await interaction.response.send_message(embed=embed)
    
    @discord.app_commands.command(name='configuresetup', description='設定特定頻道、語言模型、模組和提示詞')
    async def configure_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        view = ChannelSetupView(self.bot, channel)
        await interaction.response.send_message("請選擇要配置的語言模型、模組和提示詞:", view=view, ephemeral=True)

        await view.wait()

        if view.api and view.module and view.prompt_name:
            await interaction.delete_original_response()
            followup_message: discord.WebhookMessage = await interaction.followup.send("正在應用設置,請稍候...", ephemeral=True)
            operation = self.ConfigureSetupOperation(self, interaction, channel)
            await operation.execute(view.api, view.module, view.prompt_name)
            await followup_message.delete()

    @discord.app_commands.command(name="clear_all_history", description="手動清除所有用戶與機器人的對話歷史記錄")
    async def clear_all_history_command(self, interaction: discord.Interaction):
        # 創建確認視圖
        view = ClearHistoryConfirmView(self.bot)

        # 發送確認訊息
        await interaction.response.defer(ephemeral=True)
        confirm_message = await interaction.followup.send("您確定要清除所有用戶與機器人的對話歷史記錄嗎?", view=view, ephemeral=True)

        # 等待用戶確認
        await view.wait()

        if view.confirmed:
            # 用戶確認清除歷史記錄
            try:
                processing_message = await interaction.followup.send("正在清除所有用戶與機器人的對話歷史記錄...", ephemeral=True)
                cleared_cogs = await self.clear_all_history(manual=True, interaction=interaction)
                
                embed = discord.Embed(
                    title="手動清除對話記錄完成",
                    description=f"已成功清除以下 Cog 的對話記錄:\n{', '.join(cleared_cogs)}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                await self.send_notification_to_all_channels(embed, guild_id=interaction.guild_id, delete_after=43200)
                
                # 刪除 ephemeral 訊息
                await confirm_message.delete()
                await processing_message.delete()
            except Exception as e:
                embed = discord.Embed(
                    title="手動清除對話記錄時發生錯誤",
                    description=f"錯誤訊息: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                print(f"手動清除對話記錄時發生錯誤: {str(e)}")
        else:
            # 用戶取消清除歷史記錄
            await interaction.followup.send("已取消清除對話歷史記錄。", ephemeral=True)
            await confirm_message.delete()
    
    async def send_notification_to_all_channels(self, embed: discord.Embed, guild_id: int = None, delete_after: float = None):
        """
        在所有已設定的頻道中發送通知訊息。

        :param embed: 要發送的 Embed 訊息。
        :param guild_id: 要發送通知的伺服器 ID。如果為 None,則在所有已設定的頻道中發送通知。
        :param delete_after: 訊息自動刪除的延遲時間,以秒為單位。如果為 None,則不自動刪除訊息。
        """
        for guild_id_str, guild_data in self.bot.channel.items():
            if guild_id is None or int(guild_id_str) == guild_id:
                for channel_id in guild_data.keys():
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        await channel.send(embed=embed, delete_after=delete_after)

    async def send_clear_history_notification(self, cleared_cogs: list, error: Exception = None, manual: bool = False, interaction: discord.Interaction = None):
        if error:
            embed = discord.Embed(title="清除對話歷史記錄時發生錯誤", description=f"錯誤詳情: {str(error)}", color=discord.Color.red())
        else:
            embed = discord.Embed(title="清除對話歷史記錄完成", description=f"已成功清除以下 Cog 的對話歷史記錄:\n{', '.join(cleared_cogs)}", color=discord.Color.green())
        
        if manual and interaction:
            await self.send_notification_to_all_channels(embed, guild_id=interaction.guild_id, delete_after=43200)
        else:
            await self.send_notification_to_all_channels(embed, delete_after=43200)

    async def clear_all_history(self, manual: bool = False, interaction: discord.Interaction = None):
        try:
            cleared_cogs = []
            for cog_name, cog in self.bot.cogs.items():
                if hasattr(cog, 'chat_history') and hasattr(cog.chat_history, 'clear'):
                    cog.chat_history.clear()
                    cleared_cogs.append(cog_name)
            await self.send_clear_history_notification(cleared_cogs, manual=manual, interaction=interaction)
            return cleared_cogs
        except Exception as e:
            await self.send_clear_history_notification([], error=e, manual=manual, interaction=interaction)
            raise

async def setup(bot):
    text_channel_cog = TextChannelCog(bot)
    await bot.add_cog(text_channel_cog)