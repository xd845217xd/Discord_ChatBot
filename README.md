# Discord聊天機器人

Python跟Discord.py，可以讓用戶在discord上跟大型語言模組尬聊的BOT。

## 專案目錄結構

```
DiscordBot/
│
├── bot_main.py
├── configs/
│   ├── api_module_config.json
│   ├── channel_setup_config.json
│   ├── cog_mapping_config.json
│   └── prompt_config.json
│
├── cogs/
│   ├── channel_setup_cog.py
│   ├── message_cog.py
│   └── text_channel_cog.py
│
├── components/
│   ├── channel_setup_view.py
│   ├── clear_confirm_view.py
│   ├── cog_control_view.py
│   └── operations.py
│
└── llms/
    ├── cohere_chat_cog.py
    ├── openrouter_chat_cog.py.py
    └── openai_chat_cog.py
```

## 主要檔案說明

- `bot_main.py`: 專案的主程式,負責初始化和啟動 Discord 機器人。
- `configs/`: 存放各種設定文件。
  - `api_module_config.json`: 不同的 API 有不同可以選擇的 Module ，在這裡可以預先寫好讓用戶選擇。
  - `channel_setup_config.json`: 儲存 Cog 應用頻道、包含使用的 API 、 Module 與 Prompt 的設定。
  - `cog_mapping_config.json`: 儲存 Cog 對應中文名稱的設定。
  - `prompt_config.json`: 儲存 Prompt ， Name 是用戶的選擇， Content 則是實際上要給 API 的提示詞。

## Cogs 說明

- `channel_setup_cog.py`: 負責設定 Cog 對應頻道與使用的 API 、 Module 與 Prompt 。
- `message_cog.py`: 可以使用 "/chat" 呼叫對話框,與 OpenAI API 對話。
- `text_channel_cog.py`: 負責在文字頻道上,透過選擇的 API 處理一般對話的功能。

## Components 說明

- `channel_setup_view.py`: 實現 channel_setup_cog.py 的 Discord 互動介面。
- `clear_confirm_view.py`: 實現清空指定頻道指令 /clear_channel 所有訊息的 Discord 互動介面。
- `cog_control_view.py`: 實現 /load 、 /reload 跟 /unload 指令選擇對應Cog 的 Discord 互動介面。
- `operations.py`: 各個 _view.py 裡面斜線指令對應的程式邏輯都在這裡。

## LLMs 說明

- `openrouter_chat_cog.py`: 負責透過 OpenRouter API 處理一般對話的功能。
- `openai_chat_cog.py`: 負責透過 OpenAI API 處理一般對話的功能。
- `cohere_chat_cog.py`: 負責透過 Cohere API 處理一般對話的功能。

## 如何運行

1. 安裝Python 3.12或更高版本。
2. 安裝必要的支援套件: `pip install -r requirements.txt`
3. 在Discord Developer Portal創建一個新的Bot,並將其Token添加到`.env`中。
4. 運行`bot_main.py`: `python bot_main.py`