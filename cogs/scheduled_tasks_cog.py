import discord
from discord.ext import commands, tasks
from datetime import datetime, time

class ScheduledTasksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_clear_history_task = ScheduledTasksCog.AutoClearHistoryTask(self)
        self.auto_clear_history.start()

    class AutoClearHistoryTask:
        def __init__(self, cog):
            self.cog = cog
            self.bot = cog.bot

        async def execute(self):
            try:
                cleared_cogs = await self.cog.clear_all_history()
                await self.send_notification(cleared_cogs)
            except Exception as e:
                print(f"自動清除對話記錄時發生錯誤: {str(e)}")

        async def send_notification(self, cleared_cogs):
            for guild_id, guild_data in self.bot.scheduled_tasks.items():
                if "notification_channel" in guild_data and "task" in guild_data and guild_data["task"] == "auto_clear_history":
                    channel_id = guild_data["notification_channel"]
                    channel = self.bot.get_channel(int(channel_id))
                    
                    if channel:
                        embed = discord.Embed(
                            title="自動清除對話記錄完成",
                            description=f"已成功清除以下 Cog 的對話記錄:\n{', '.join(cleared_cogs)}",
                            color=discord.Color.green(),
                            timestamp=datetime.now()
                        )
                        await channel.send(embed=embed)
                    else:
                        print(f"找不到 ID 為 {channel_id} 的文字頻道")

    @discord.app_commands.command(name="task_notify_channel", description="設定接收通知的文字頻道")
    async def task_notify_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        channel_id = str(channel.id)

        try:
            if guild_id not in self.bot.scheduled_tasks:
                self.bot.scheduled_tasks[guild_id] = {}

            self.bot.scheduled_tasks[guild_id]["notification_channel"] = channel_id
            self.bot.save_config(self.bot.scheduled_tasks, self.bot.config_paths['scheduled_tasks'])

            embed = discord.Embed(
                title="設定接收通知的文字頻道",
                description=f"已將 {channel.mention} 設置為接收通知的文字頻道。",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="設定接收通知的文字頻道時發生錯誤",
                description=f"錯誤訊息: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"設定接收通知的文字頻道時發生錯誤: {str(e)}")

    @discord.app_commands.command(name="task_sched_set", description="選擇需要使用的定時任務")
    @discord.app_commands.choices(task=[
        discord.app_commands.Choice(name="自動清除對話紀錄", value="auto_clear_history")
    ])
    async def task_sched_set(self, interaction: discord.Interaction, task: discord.app_commands.Choice[str]):
        guild_id = str(interaction.guild_id)

        try:
            if guild_id not in self.bot.scheduled_tasks:
                self.bot.scheduled_tasks[guild_id] = {}

            self.bot.scheduled_tasks[guild_id]["task"] = task.value
            self.bot.save_config(self.bot.scheduled_tasks, self.bot.config_paths['scheduled_tasks'])

            embed = discord.Embed(
                title="選擇需要使用的定時任務",
                description=f"已將 {task.name} 設置為需要使用的定時任務。",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="選擇需要使用的定時任務時發生錯誤",
                description=f"錯誤訊息: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"選擇需要使用的定時任務時發生錯誤: {str(e)}")

    @tasks.loop(time=[time(hour=4), time(hour=16)])
    async def auto_clear_history(self):
        await self.auto_clear_history_task.execute()

    @auto_clear_history.before_loop
    async def before_auto_clear_history(self):
        await self.bot.wait_until_ready()

    async def clear_all_history(self):
        try:
            cleared_cogs = []
            for cog_name, cog in self.bot.cogs.items():
                if hasattr(cog, 'chat_history') and hasattr(cog.chat_history, 'clear'):
                    cog.chat_history.clear()
                    cleared_cogs.append(cog_name)
            return cleared_cogs
        except Exception as e:
            print(f"清除對話記錄時發生錯誤: {str(e)}")
            raise

async def setup(bot):
    scheduled_tasks_cog = ScheduledTasksCog(bot)
    await bot.add_cog(scheduled_tasks_cog)