import discord
import os
import asyncio
import logging
import json
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from components.cog_control_view import CogControlView
from components.clear_confirm_view import ClearConfirmView
from components import operations
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
        self.config_paths = {
            'channel': 'configs/channel_setup_config.json',
            'cogs_config': 'configs/cog_mapping_config.json',
            'api_module': 'configs/api_module_config.json',
            'prompt': 'configs/prompt_config.json'
        }
        self.config_defaults = {
            'channel': {},
            'cogs_config': {"cogs_mapping": {}},
            'api_module': {},
            'prompt': {
                "default": "你是一個得力的助手,致力於提供詳盡且有幫助的回答。",
                "prompts": []
            }
        }
        self.load_all_configs()

    def load_all_configs(self):
        for config_key, file_path in self.config_paths.items():
            try:
                if not os.path.exists(file_path):
                    self.create_config(file_path, self.config_defaults[config_key])
                with open(file_path, 'r', encoding='utf-8') as f:
                    setattr(self, config_key, json.load(f))
            except IOError as e:
                print(f"Error loading {file_path}: {str(e)}")

    def create_config(self, file_path, default_config):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
        except IOError as e:
            print(f"Error creating {file_path}: {str(e)}")

    def save_config(self, config, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving {file_path}: {str(e)}")

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
    print("已加載的 Cog:", [cog_name for cog_name in bot.cogs], flush=True)

# 定義斜線指令
@bot.tree.command(name="load", description="載入模組")
async def load_cog(interaction: discord.Interaction):
    view = CogControlView(bot, title="load")
    await interaction.response.send_message("請選擇要載入的模組:", view=view, ephemeral=True)

@bot.tree.command(name="unload", description="卸載模組")
async def unload_cog(interaction: discord.Interaction):
    view = CogControlView(bot, title="unload")
    await interaction.response.send_message("請選擇要卸載的模組:", view=view, ephemeral=True)

@bot.tree.command(name="reload", description="重新載入模組")
async def reload_cog(interaction: discord.Interaction):
    view = CogControlView(bot, title="reload")
    await interaction.response.send_message("請選擇要重新載入的模組:", view=view, ephemeral=True)

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
    mapping = "\n".join(f"{key}: {value}" for key, value in interaction.client.cogs_config['cogs_mapping'].items())
    
    # 發送最終回應
    await interaction.followup.send(f"目前的 cog 映射表：\n{mapping}")

@bot.tree.command(name="clear_history", description="清理歷史訊息")
async def clear_history(interaction: discord.Interaction):
    await operations.OPERATIONS['clearhistoryandrestartcog'](bot, interaction).execute()

# 自動載入 cogs跟llms 目錄下的所有擴展
async def load_extensions(directory):
    for filename in os.listdir(f"./{directory}"):
        if filename.endswith(".py"):
            await bot.load_extension(f"{directory}.{filename[:-3]}")

async def main():
    await load_extensions("cogs")
    await load_extensions("llms")
    await bot.start(discord_token)

if __name__ == '__main__':
    asyncio.run(main())
