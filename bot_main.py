import discord
import os
import asyncio
import logging
import json
import signal
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from components.cog_control_view import CogControlView
from components.clear_confirm_view import ClearConfirmView
from dotenv import load_dotenv

# 從 .env 檔案載入環境設定檔,例如Discord機器人的Token
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger('discord')

discord_token = os.getenv('DISCORD_TOKEN')

# 載入設定檔,例如JSON格式的配置文件
class Bot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix, intents=intents)
        self.config_paths = {
            'channel': 'configs/channel_setup_config.json',
            'cogs_config': 'configs/cog_mapping_config.json',
            'api_module': 'configs/api_module_config.json',
            'prompt': 'configs/prompt_config.json',
            'scheduled_tasks': 'configs/scheduled_tasks_config.json'
        }
        self.config_defaults = {
            'channel': {},
            'cogs_config': {"cogs_mapping": {}},
            'api_module': {},
            'prompt': {
                "default": "你是一個得力的助手,致力於提供詳盡且有幫助的回答。",
                "prompts": []
            },
            'scheduled_tasks': {}
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
        await load_extensions("cogs")
        await load_extensions("llms")

        # 同步斜線命令
        await self.tree.sync()
        print("已同步斜線命令。")

        # 打印已加載的模組、Cog和斜線命令
        print(f'{self.user.name} 已經連接到 Discord!', flush=True)
        print("已載入的模組:", self.extensions.keys(), flush=True)
        print("已加載的 Cog:", [cog_name for cog_name in self.cogs], flush=True)
        print("已加載的斜線命令:", [cmd.name for cmd in self.tree.get_commands()])
    
    async def close(self):
        print("正在關閉 Redis 連接...")
        if hasattr(self, 'redis_cog') and self.redis_cog.redis_client:
            await self.redis_cog.redis_close()
        print("Redis 連接已關閉。")
        await super().close()  # 確保調用父類的 close 方法來處理其他清理工作

# 初始化 Intents
intents = discord.Intents.all()

# 建立一個 commands.Bot 實例
bot = Bot(command_prefix='!', intents=intents)

# 定義斜線命令
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

# 自動載入 cogs跟llms 目錄下的所有擴展
async def load_extensions(directory):
    for filename in os.listdir(f"./{directory}"):
        if filename.endswith(".py"):
            await bot.load_extension(f"{directory}.{filename[:-3]}")

def handle_shutdown_signal():
    print("收到終止信號，正在關閉 bot...")
    asyncio.create_task(bot.close())

async def main():
    try:
        await bot.start(discord_token)
    except KeyboardInterrupt:
        print('收到 Ctrl+C，正在關閉 bot...')
    finally:
        await bot.close()
        print('Bot 已安全關閉。')

if __name__ == '__main__':
    signal.signal(signal.SIGINT, lambda x, y: handle_shutdown_signal())
    asyncio.run(main())