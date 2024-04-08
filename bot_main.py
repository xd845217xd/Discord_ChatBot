import discord
import os
import asyncio
import logging
import json
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from components.cog_select_view import CogSelectView
from components.clear_confirm_view import ClearConfirmView
from dotenv import load_dotenv

# 從 .env 檔案載入環境設定檔，token那類的
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger('discord')

discord_token = os.getenv('DISCORD_TOKEN')

# 載入設定檔，就是那些json檔案
class Bot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix, intents=intents)
        self.config = self.load_config('channel_setup_config.json')
        self.cogs_mapping = self.load_config('cog_mapping_config.json').get('cogs_mapping', {})

    def load_config(self, config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}  # 如果配置檔案不存在，則建立一個空的配置檔案

    def save_config(self):
        with open('channel_setup_config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)  # 保存配置到檔案當中

    async def setup_hook(self):
        # 加載 cogs 或其他啟動設定
        pass

# 初始化 Intents
intents = discord.Intents.all()

# 建立一個 commands.Bot 實例
bot = Bot(command_prefix='!', intents=intents)

# 註冊斜線指令前，必須在 on_ready 事件中同步指令
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user.name} 已經連接到 Discord!', flush=True)
    print("已載入的模組:", bot.extensions.keys(), flush=True)

# 定義斜線指令
@bot.tree.command(name="load", description="載入模組")
async def load_cog(interaction: discord.Interaction):
    # 發送帶有下拉選單的訊息讓用戶選擇要載入的模組
    view = CogSelectView(bot, title="load")
    await interaction.response.send_message("請選擇要載入的模組：", view=view, ephemeral=True)

@bot.tree.command(name="unload", description="卸載模組")
async def unload_cog(interaction: discord.Interaction):
    # 發送帶有下拉選單的訊息讓用戶選擇要卸載的模組
    view = CogSelectView(bot, title="unload")
    await interaction.response.send_message("請選擇要卸載的模組：", view=view, ephemeral=True)

@bot.tree.command(name="reload", description="重新載入模組")
async def reload_cog(interaction: discord.Interaction):
    # 發送帶有下拉選單的訊息讓用戶選擇要重新載入的模組
    view = CogSelectView(bot, title="reload")
    await interaction.response.send_message("請選擇要重新載入的模組：", view=view, ephemeral=True)

@bot.tree.command(name="test", description="測試指令")
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("測試成功", ephemeral=False)

@bot.tree.command(name="clear_channel", description="清除指定頻道的對話紀錄")
@app_commands.describe(channel="選擇要清除的頻道")
async def clear_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    # 創建確認視圖
    view = ClearConfirmView(bot, interaction, channel)

    # 發送確認訊息
    view.message = await interaction.response.send_message(
        f"您確定要清除頻道 {channel.mention} 的對話紀錄嗎?",
        view=view,
        ephemeral=True
    ) 

@bot.tree.command(name='show_mapping', description='顯示目前的 cog 映射表')
async def show_mapping(interaction: discord.Interaction):
    # 發送暫時回應
    await interaction.response.defer()

    # 生成映射表的字符串表示
    mapping = "\n".join(f"{key}: {value}" for key, value in interaction.client.cogs_mapping.items())
    
    # 發送最終回應
    await interaction.followup.send(f"目前的 cog 映射表：\n{mapping}")

# 自動載入 cogs 目錄下的所有擴展
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    await load_extensions()
    await bot.start(discord_token)

if __name__ == '__main__':
    asyncio.run(main())
