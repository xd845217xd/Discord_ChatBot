import discord
import json

# 基本的操作類
class Operation:
    def __init__(self, bot, interaction, channel=None):
        self.bot = bot
        self.interaction = interaction
        self.channel = channel

    async def execute(self, cog_name):
        raise NotImplementedError("This method should be implemented by subclasses.")

# 載入模組的操作
class LoadOperation(Operation):
    async def execute(self, cog_name):
        if f'cogs.{cog_name}' in self.bot.extensions:
            return f'`{cog_name}` 模組已經被載入了。'
        else:
            await self.bot.load_extension(f'cogs.{cog_name}')
            return f'`{cog_name}` 模組載入成功。'

# 卸載模組的操作
class UnloadOperation(Operation):
    async def execute(self, cog_name):
        if f'cogs.{cog_name}' not in self.bot.extensions:
            return f'`{cog_name}` 模組尚未被載入。'
        else:
            await self.bot.unload_extension(f'cogs.{cog_name}')
            return f'`{cog_name}` 模組卸載成功。'

# 重載模組的操作
class ReloadOperation(Operation):
    async def execute(self, cog_name):
        if f'cogs.{cog_name}' not in self.bot.extensions:
            return f'`{cog_name}` 模組尚未被載入。'
        else:
            await self.bot.reload_extension(f'cogs.{cog_name}')
            return f'`{cog_name}` 模組重新載入成功。'

# 設定特定頻道的操作
class ConfigureSetupOperation(Operation):
    async def execute(self, api, module, prompt_name):
        guild_id = str(self.interaction.guild_id)
        channel_id = str(self.channel.id)

        if guild_id not in self.bot.channel:
            self.bot.channel[guild_id] = {}

        prompt_content = next((prompt['content'] for prompt in self.bot.prompt['prompts'] if prompt['name'] == prompt_name), self.bot.prompt['default'])

        self.bot.channel[guild_id][channel_id] = {
            'cog': self.bot.api_module[api]["cog_name"],
            'api': api,
            'module': module,
            'prompt': prompt_name
        }
        self.bot.save_config(self.bot.channel, self.bot.config_paths['channel'])

        await self.interaction.followup.send(f"已將頻道 {self.channel.mention} 的設置更新為:\nAPI: {api}\n模組: {module}\n提示詞: {prompt_name}", ephemeral=False)
        
        try:
            await self.bot.reload_extension(f"llms.{api.lower()}_chat_cog")
            await self.interaction.followup.send(f"`{self.bot.api_module[api]['cog_name']}` 模組已重新載入。", ephemeral=False)
        except Exception as e:
            await self.interaction.followup.send(f"載入 `{self.bot.api_module[api]['cog_name']}` 模組時發生錯誤: {str(e)}", ephemeral=True)
            print(f"Error reloading Cog for {api}: {str(e)}")
        
# 移除特定頻道
class RemoveSetupOperation(Operation):
    async def execute(self, cog_name):
        guild_id = str(self.interaction.guild_id)
        if guild_id in self.bot.channel:
            del self.bot.channel[guild_id]
            self.bot.save_config(self.bot.channel, self.bot.config_paths['channel'])
            await self.interaction.response.send_message("已移除特定頻道設定。", ephemeral=False)

            # 重新載入對應的 Cog
            await self.bot.reload_extension(f"cogs.{cog_name}")
            await self.interaction.followup.send(f"`{cog_name}` 模組已重新載入。", ephemeral=False)
        else:
            await self.interaction.response.send_message("此伺服器尚未設置特定頻道。", ephemeral=False)

# 清除頻道的操作
class ClearChannelOperation(Operation):
    async def execute(self):
        guild_id = str(self.interaction.guild_id)
        channel_id = str(self.channel.id)

        try:
            new_channel = await self.channel.clone()
            await self.channel.delete()

            if guild_id in self.bot.channel and channel_id in self.bot.channel[guild_id]:
                cog_name = self.bot.channel[guild_id][channel_id]['cog']
                api = self.bot.channel[guild_id][channel_id]['api']
                module = self.bot.channel[guild_id][channel_id]['module']
                prompt_name = self.bot.channel[guild_id][channel_id]['prompt']

                self.bot.channel[guild_id][str(new_channel.id)] = {
                    'cog': cog_name,
                    'api': api,
                    'module': module,
                    'prompt': prompt_name
                }
                del self.bot.channel[guild_id][channel_id]
                self.bot.save_config(self.bot.channel, self.bot.config_paths['channel'])

                await self.bot.reload_extension(f"llms.{cog_name.lower()}")
                await self.interaction.followup.send(f"`{cog_name}` 模組已重新載入。", ephemeral=True)

            await self.interaction.followup.send(f"頻道已成功清除,新的頻道: {new_channel.mention}", ephemeral=True)

        except Exception as e:
            await self.interaction.followup.send(f"清除頻道時發生錯誤: {str(e)}", ephemeral=True)

# 清除大型語言模型的對話歷史
class ClearHistoryAndRestartCogOperation(Operation):
    async def execute(self):
        guild_id = str(self.interaction.guild_id)
        channel_id = str(self.interaction.channel_id)  # 獲取 channel_id
        print(f"正在嘗試為 guild_id {guild_id} 清除對話歷史...")

        # 從 api_module 獲取 API Cog 名稱，注意這裡假設 api_module 使用 channel_id 索引
        api_cog_name = self.bot.channel[guild_id].get(channel_id, {}).get('cog')
        print(f"從 api_module 獲取的 API Cog 名稱: {api_cog_name}")

        if api_cog_name:
            try:
                api_cog = self.bot.get_cog(api_cog_name)
                if api_cog:
                    api_cog.chat_history.clear()
                    await self.interaction.response.send_message(f"已清除 {api_cog_name} 的歷史消息。", ephemeral=False)
            except Exception as e:
                await self.interaction.response.send_message(f"清除歷史消息時出現錯誤: {str(e)}", ephemeral=True)
        else:
            await self.interaction.response.send_message("請先使用 /configuresetup 選擇要使用的 API。", ephemeral=True)

# 將所有的操作類組織到一個字典中，便於根據名稱查詢和執行
OPERATIONS = {
    'load': LoadOperation,
    'unload': UnloadOperation,
    'reload': ReloadOperation,
    'configuresetup': ConfigureSetupOperation,
    'removesetup': RemoveSetupOperation,
    'clearchannel': ClearChannelOperation,
    'clearhistoryandrestartcog': ClearHistoryAndRestartCogOperation,
    # 未來還有的話，記得加上去，哭啊
}