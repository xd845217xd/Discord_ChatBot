# 文件路徑: components/operations.py

import discord

# 基本操作類
class Operation:
    def __init__(self, bot, interaction, channel=None):
        self.bot = bot
        self.interaction = interaction
        self.channel = channel

    async def execute(self, cog_name):
        raise NotImplementedError("This method should be implemented by subclasses.")

# 載入模組操作
class LoadOperation(Operation):
    async def execute(self, cog_name):
        await self.bot.load_extension(f'cogs.{cog_name}')
        await self.interaction.response.send_message(f'`{cog_name}` 模組載入成功。', ephemeral=True)

# 卸載模組操作
class UnloadOperation(Operation):
    async def execute(self, cog_name):
        await self.bot.unload_extension(f'cogs.{cog_name}')
        await self.interaction.response.send_message(f'`{cog_name}` 模組卸載成功。', ephemeral=True)

# 重載模組操作
class ReloadOperation(Operation):
    async def execute(self, cog_name):
        await self.bot.reload_extension(f'cogs.{cog_name}')
        await self.interaction.response.send_message(f'`{cog_name}` 模組重新載入成功。', ephemeral=True)

# 設定特定頻道
class ConfigureSetupOperation(Operation):
    async def execute(self, cog_name):
        guild_id = str(self.interaction.guild_id)
        if cog_name not in ['monopoly_cog', 'text_channel_cog']:  # 假設 message_cog 和 text_channel_cog 是可配置的 cog
            await self.interaction.response.send_message("不支援的 cog 名稱。", ephemeral=True)
            return

        # 保存設置
        if guild_id not in self.bot.config:
            self.bot.config[guild_id] = {}

        self.bot.config[guild_id][cog_name] = str(self.channel.id)
        self.bot.save_config()  # 確保有實現這個方法
        await self.interaction.response.send_message(f"已將 {self.channel.name} 設置為 {cog_name} 的特定頻道。", ephemeral=True)

# 移除特定頻道
class RemoveSetupOperation(Operation):
    async def execute(self, cog_name):
        guild_id = str(self.interaction.guild_id)
        if guild_id in self.bot.config:
            del self.bot.config[guild_id]
            self.bot.save_config()  # 確保有實現這個方法
            await self.interaction.response.send_message("已移除特定頻道設定。", ephemeral=True)
        else:
            await self.interaction.response.send_message("此伺服器尚未設置特定頻道。", ephemeral=True)

# 清除頻道操作
class ClearChannelOperation(Operation):
    async def execute(self):
        guild_id = str(self.interaction.guild_id)
        channel_id = str(self.channel.id)

        # 檢查頻道是否在設定檔中
        if guild_id in self.bot.config and any(channel_id == str(ch_id) for ch_id in self.bot.config[guild_id].values()):
            # 儲存原有的頻道 ID
            original_channel_id = channel_id

            # 複製並刪除原有的頻道
            new_channel = await self.channel.clone()
            await self.channel.delete()

            # 更新設定檔
            cog_to_reload = None
            for cog_name, ch_id in self.bot.config[guild_id].items():
                if str(ch_id) == original_channel_id:
                    self.bot.config[guild_id][cog_name] = str(new_channel.id)
                    cog_to_reload = cog_name
                    break

            self.bot.save_config()
            await self.interaction.followup.send(f"頻道已成功清除,新的頻道: {new_channel.mention}", ephemeral=True)

            # 重新載入對應的 Cog
            if cog_to_reload:
                await self.bot.reload_extension(f"cogs.{cog_to_reload}")
                await self.interaction.followup.send(f"`{cog_to_reload}` 模組已重新載入。", ephemeral=True)
        else:
            await self.interaction.followup.send("此頻道不是任何 Cog 的特定頻道。", ephemeral=True)

# 將所有操作類組織到一個字典中，便於根據名稱查詢和執行
OPERATIONS = {
    'load': LoadOperation,
    'unload': UnloadOperation,
    'reload': ReloadOperation,
    'configuresetup': ConfigureSetupOperation,
    'removesetup': RemoveSetupOperation,
    'clearchannel': ClearChannelOperation,
    # 未來還有的話，記得加上去，哭啊
}
