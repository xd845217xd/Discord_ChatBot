# Discord聊天機器人

Python跟Discord.py，可以讓用戶在discord上跟大型語言模組尬聊的BOT。

## 專案目錄結構

```
DiscordBot/
│
├── bot_main.py
├── channel_setup_config.json
├── cog_mapping_config.json
│
├── cogs/
│   ├── channel_setup_cog.py
│   ├── message_cog.py
│   └── text_channel_cog.py
│ 
└── components/
    ├── cog_select_view.py
    └── operations.py
```

## 主要檔案說明

- `bot_main.py`: 專案的主程式,負責初始化和啟動Discord機器人。
- `channel_setup_config.json`: 儲存Cog應用頻道的設定文件。
- `cog_mapping_config.json`: 儲存Cog對應中文名稱的設定文件。

## Cogs說明

- `channel_setup_cog.py`: 負責設定Cog對應頻道。
- `message_cog.py`: 可以使用"/chat"呼叫對話框，與OpenAI API對話。
- `text_channel_cog.py`: 負責在文字頻道上，透過OpenAI API處理一般對話的功能。

## Components說明

- `clear_confirm_view.py`: 實現清空指定頻道所有訊息的discord互動介面。
- `cog_select_view.py`: 實現幫cog選擇指定使用頻道的discord互動介面。
- `operations.py`: bot_main.py裡面斜線指令對應的程式邏輯都在這裡。

## 如何運行

1. 安裝Python 3.12或更高版本。
2. 安裝必要的支援套件: `pip install -r requirements.txt`
3. 在Discord Developer Portal創建一個新的Bot,並將其Token添加到`.env`中。
4. 運行`bot_main.py`: `python bot_main.py`