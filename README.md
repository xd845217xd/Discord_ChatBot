# Discord大富翁的機器人

這是一個使用Discord.py庫開發的機器人,可以讓用戶在discord文字頻道上玩大富翁。

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
│   ├── monopoly_cog.py
│   ├── text_channel_cog.py
│   │
│   └── monopoly/
│       ├── bank.py
│       ├── board.py
│       ├── card.py
│       ├── game.py
│       ├── player.py
│       ├── property.py
│       ├── transport.py
│       ├── utility.py
│       └── asset_view.py
│ 
├── components/
│   ├── cog_select_view.py
│   └── operations.py
│
└── monopoly_data/
    ├── board_config.json
    ├── card_config.json
    └── monopoly_state.json
```

## 主要檔案說明

- `bot_main.py`: 專案的主程式,負責初始化和啟動Discord機器人。
- `channel_setup_config.json`: 儲存Cog應用頻道的設定文件。
- `cog_mapping_config.json`: 儲存Cog對應中文名稱的設定文件。

## Cogs說明

- `channel_setup_cog.py`: 負責設定Cog對應頻道。
- `message_cog.py`: 可以使用"/chat"呼叫對話框，與OpenAI API對話。
- `monopoly_cog.py`: 大富翁遊戲的主要Cog,負責處理遊戲指令和遊戲流程。
- `text_channel_cog.py`: 負責在文字頻道上，透過OpenAI API處理一般對話的功能。

## Components說明

- `clear_confirm_view.py`: 實現清空指定頻道所有訊息的discord互動介面。
- `cog_select_view.py`: 實現幫cog選擇指定使用頻道的discord互動介面。
- `operations.py`: bot_main.py裡面斜線指令對應的程式邏輯都在這裡。

## Monopoly模組說明

- `bank.py`: 實現大富翁遊戲中的銀行功能，也是負責金流的流動。
- `board.py`: 表示大富翁遊戲的棋盤。
- `card.py`: 實現大富翁遊戲中的機會卡和公共基金卡功能。
- `game.py`: 大富翁遊戲的核心邏輯,控制遊戲流程。
- `player.py`: 表示大富翁遊戲中的玩家。
- `property.py`: 表示大富翁遊戲中的房地產。
- `transport.py`: 表示大富翁遊戲中的交通事業。
- `utility.py`: 表示大富翁遊戲中的公共事業。
- `asset_view.py`: 給玩家用來選擇要不要購買的按鈕。未來如果有其他互動介面，可能也會在這裡實現。

## 資料檔案說明

- `board_config.json`: 儲存大富翁遊戲棋盤的設定資料。
- `card_config.json`: 儲存大富翁遊戲卡片的設定資料。
- `monopoly_state.json`: 儲存大富翁遊戲的狀態資料。

## Monopoly遊戲流程額外說明

`monopoly_cog.py`是整個專案的核心,它負責處理所有與大富翁遊戲相關的指令和遊戲流程。大富翁遊戲的核心邏輯由`game.py`控制,其他的模組如`player.py`,`property.py`等則表示遊戲中的各種實體。

遊戲的設定資料通過JSON檔案儲存,在程式啟動時載入。這樣可以方便地修改遊戲設置,而無需修改程式碼。

## 如何運行

1. 安裝Python 3.12或更高版本。
2. 安裝必要的支援套件: `pip install -r requirements.txt`
3. 在Discord Developer Portal創建一個新的Bot,並將其Token添加到`.env`中。
4. 運行`bot_main.py`: `python bot_main.py`