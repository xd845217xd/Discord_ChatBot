import discord
from discord.ext import commands
import os
import requests
import json

class DifyChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('DIFY_API_KEY')  # 從環境變數中獲取 Dify API 金鑰
        self.api_url = os.getenv('DIFY_API_URL')  # 從環境變數中獲取 Dify API URL
        self.chat_history = {}  # 用於存儲聊天記錄的字典

    async def process_message(self, message):
        user_id = str(message.author.id)  # 獲取用戶 ID
        channel_id = message.channel.id  # 獲取頻道 ID

        if channel_id not in self.chat_history:
            self.chat_history[channel_id] = {}  # 如果該頻道還沒有聊天記錄,則創建一個新的字典項
        if user_id not in self.chat_history[channel_id]:
            # 如果該用戶在該頻道還沒有聊天記錄,則創建一個新的字典項
            self.chat_history[channel_id][user_id] = {
                "conversation_id": ""
            }

        conversation_id = self.chat_history[channel_id][user_id]["conversation_id"]  # 獲取該用戶在該頻道的對話 ID

        async with message.channel.typing():
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            data = {
                'inputs': {},
                'query': message.content,
                'response_mode': 'streaming',
                'conversation_id': conversation_id,
                'user': user_id
            }

            response = requests.post(self.api_url, headers=headers, json=data)  # 發送 API 請求

            if response.status_code == 200 and response.text:
                await self.handle_sse_response(response.text, message.channel, channel_id, user_id)  # 處理 SSE 回應
            else:
                print(f"Failed API request with status {response.status_code}: {response.text}")  # 如果 API 請求失敗,則輸出錯誤訊息

    # Dify 的 Agent 目前只能用串流模式，然後 Discord 很明顯的不吃這套，所以需要這段代碼，可悲
    async def handle_sse_response(self, response_text, channel, channel_id, user_id):
        answer_fragments = []  # 用於存儲答案片段的列表
        full_message = ""  # 用於存儲完整訊息的字符串
        events = response_text.strip().split("\n\n")  # 將 SSE 回應拆分為事件
        for event in events:
            if event.startswith("data: "):
                data_json = event[5:].strip()  # 獲取事件數據的 JSON 字符串
                try:
                    data_dict = json.loads(data_json)  # 將 JSON 字符串解析為字典
                    event_type = data_dict["event"]  # 獲取事件類型

                    if event_type == "agent_message":
                        answer_fragments.append(data_dict["answer"])  # 將答案片段添加到列表中
                    elif event_type == "agent_thought":
                        thought = data_dict["thought"]  # 獲取代理的思考內容
                        if thought:
                            full_message = thought  # 更新完整訊息
                    elif event_type == "message_end":
                        self.chat_history[channel_id][user_id]["conversation_id"] = data_dict["conversation_id"]  # 更新對話 ID
                except json.JSONDecodeError:
                    print(f"Failed to decode JSON: {data_json}")  # 如果 JSON 解析失敗,則輸出錯誤訊息

        if not full_message and answer_fragments:
            full_message = "".join(answer_fragments)  # 如果沒有完整訊息,則將答案片段拼接為完整訊息

        if full_message:
            await channel.send(full_message)  # 發送完整訊息

    @commands.command()
    async def reset_conversation(self, ctx):
        channel_id = ctx.channel.id  # 獲取頻道 ID
        user_id = str(ctx.author.id)  # 獲取用戶 ID
        if channel_id in self.chat_history and user_id in self.chat_history[channel_id]:
            self.chat_history[channel_id][user_id]["conversation_id"] = ""  # 重置對話 ID
            await ctx.send(f"Conversation ID has been reset for {ctx.author.name}.")  # 發送重置成功的訊息
        else:
            await ctx.send(f"No conversation found for {ctx.author.name}.")  # 發送沒有找到對話的訊息

async def setup(bot):
    dify_chat_cog = DifyChatCog(bot)
    await bot.add_cog(dify_chat_cog)