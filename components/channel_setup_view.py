import discord
from .operations import ConfigureSetupOperation
from .operations import OPERATIONS

class ChannelSelectView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.add_item(ChannelSelect(bot))

class ChannelSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label=f"#{bot.get_channel(int(channel_id)).name}", value=channel_id)
            for guild_id, channel_dict in bot.channel.items()
            for channel_id in channel_dict.keys()
        ]
        super().__init__(placeholder="請選擇一個頻道...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        channel_id = self.values[0]
        guild_id = str(interaction.guild_id)

        if guild_id in self.bot.channel and channel_id in self.bot.channel[guild_id]:
            del self.bot.channel[guild_id][channel_id]
            self.bot.save_config(self.bot.channel, self.bot.config_paths['channel'])
            await interaction.response.send_message(f"已移除頻道 <#{channel_id}> 的設置。", ephemeral=False)
        else:
            await interaction.response.send_message(f"頻道 <#{channel_id}> 尚未設置。", ephemeral=False)

class ChannelSetupView(discord.ui.View):
    def __init__(self, bot, channel=None):
        super().__init__()
        self.bot = bot
        self.channel = channel
        self.api = None  # 添加一個屬性來儲存選擇的 API
        self.add_item(APISelect(bot))

class APISelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label=api, value=api)
            for api in bot.api_module.keys()
        ]
        super().__init__(placeholder="請選擇一個語言模型 API...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        api = self.values[0]
        print(f"選擇的 API: {api}")
        view = self.view
        view.api = api  # 將選擇的 API 儲存在視圖中
        view.clear_items()
        view.add_item(ModuleSelect(self.bot, api))
        await interaction.response.edit_message(view=view)

class ModuleSelect(discord.ui.Select):
    def __init__(self, bot, api):
        self.bot = bot
        self.api = api  # 儲存選擇的 API
        options = [
            discord.SelectOption(label=module['name'], value=module['value'])
            for module in bot.api_module[api]['modules']
        ]
        super().__init__(placeholder="請選擇一個模組...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        module = self.values[0]
        print(f"選擇的模組: {module}")
        view = self.view
        view.clear_items()
        view.add_item(PromptSelect(self.bot, self.api, module))  # 傳遞 self.api 而不是 self.view.api
        await interaction.response.edit_message(view=view)

class PromptSelect(discord.ui.Select):
    def __init__(self, bot, api, module):
        self.bot = bot
        self.api = api
        self.module = module
        options = [
            discord.SelectOption(label=prompt['name'], value=prompt['name'])
            for prompt in bot.prompt['prompts']
        ]
        super().__init__(placeholder="請選擇一個提示詞...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        prompt_name = self.values[0]
        print(f"選擇的提示詞: {prompt_name}")
        channel = self.view.channel
        await interaction.response.defer()
        operation = ConfigureSetupOperation(self.bot, interaction, channel)
        await operation.execute(self.api, self.module, prompt_name)
        
        await interaction.delete_original_response()
        
        self.view.stop()