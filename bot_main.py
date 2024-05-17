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
import traceback
import atexit

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger('discord')

discord_token = os.getenv('DISCORD_TOKEN')

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
        self.client_sessions = []
        self.client_sessions_closed = False
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
        await load_extensions("cogs")
        await load_extensions("llms")
        await self.tree.sync()
        print("已同步斜線命令。")
        print(f'{self.user.name} 已經連接到 Discord!', flush=True)
        print("已載入的模組:", self.extensions.keys(), flush=True)
        print("已加載的 Cog:", [cog_name for cog_name in self.cogs], flush=True)
        print("已加載的斜線命令:", [cmd.name for cmd in self.tree.get_commands()])

    async def close_client_sessions(self):
        if not self.client_sessions_closed:
            print("正在關閉 aiohttp ClientSessions...")
            for session in self.client_sessions:
                await session.close()
                await session.connector.close()
            print("所有 aiohttp ClientSessions 已關閉。")
            self.client_sessions_closed = True

    async def on_disconnect(self):
        if not self.is_closed():
            print("Bot 已斷開連接,正在關閉 aiohttp ClientSessions...")
            await self.close_client_sessions()

    async def close(self):
        await self.close_client_sessions()
        print("正在關閉 Redis 連接...")
        if hasattr(self, 'redis_cog') and self.redis_cog.redis_client:
            await self.redis_cog.redis_close()
        print("Redis 連接已關閉。")
        await super().close()

intents = discord.Intents.all()
bot = Bot(command_prefix='!', intents=intents)

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
    view = ClearConfirmView(bot, interaction, channel)
    view.message = await interaction.response.send_message(
        f"您確定要清除頻道 {channel.mention} 的對話紀錄嗎?",
        view=view,
        ephemeral=True
    ) 

@bot.tree.command(name='show_mapping', description='顯示目前的 cog 映射表')
async def show_mapping(interaction: discord.Interaction):
    await interaction.response.defer()
    mapping = "\n".join(f"{key}: {value}" for key, value in interaction.client.cogs_config['cogs_mapping'].items())
    await interaction.followup.send(f"目前的 cog 映射表：\n{mapping}")

async def load_extensions(directory):
    for filename in os.listdir(f"./{directory}"):
        if filename.endswith(".py"):
            await bot.load_extension(f"{directory}.{filename[:-3]}")

def handle_shutdown_signal():
    print("收到終止信號,正在關閉 bot...")
    if not bot.is_closed():
        asyncio.create_task(bot.close())

def resource_warning(loop, context):
    print(f"未關閉的資源警告: {context}")
    traceback.print_stack()

async def close_sessions():
    if not bot.is_closed():
        print("程序退出,正在關閉 aiohttp ClientSessions...")
        await bot.close_client_sessions()

atexit.register(lambda: asyncio.run(close_sessions()))

async def main():
    asyncio.get_event_loop().set_exception_handler(resource_warning)
    try:
        await bot.start(discord_token)
    except KeyboardInterrupt:
        print('收到 Ctrl+C,正在關閉 bot...')
    finally:
        if not bot.is_closed():
            await bot.close()
        await asyncio.sleep(1)
        print('Bot 已安全關閉。')

if __name__ == '__main__':
    signal.signal(signal.SIGINT, lambda x, y: handle_shutdown_signal())
    asyncio.run(main())