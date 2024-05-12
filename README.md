# Discord聊天機器人

## 專案目錄結構

```
DiscordBot/
│
├── bot_main.py
├── configs/
│   ├── api_module_config.json
│   ├── channel_setup_config.json
│   ├── cog_mapping_config.json
│   ├── prompt_config.json
│   └── scheduled_tasks_config.json
│
├── cogs/
│   ├── channel_setup_cog.py
│   ├── redis_cog.py
│   ├── scheduled_tasks_cog.py
│   └── text_channel_cog.py
│
├── cache/
│   └── text_channel_cache.py
│
├── components/
│   ├── channel_setup_view.py
│   ├── clear_confirm_view.py
│   ├── cog_control_view.py
│   ├── text_channel_view.py
│   └── operations.py
│
└── llms/
    ├── cohere_chat_cog.py
    ├── openrouter_chat_cog.py.py
    └── openai_chat_cog.py
```

## 主要檔案說明

- `bot_main.py`: 專案的主程式,負責初始化和啟動 Discord 機器人。它載入所有的設定檔,並提供一些通用的斜線指令,如 /load、/unload、/reload 等。
- `configs/`: 存放各種設定文件。
  - `api_module_config.json`: 儲存 AI 模型的設定
  - `channel_setup_config.json`: 儲存頻道與 AI 模型的對應關係
  - `cog_mapping_config.json`: 儲存 cog 與其他模組的對應關係
  - `prompt_config.json`: 儲存 AI 模型的提示詞設定
  - `scheduled_tasks_config.json`: 儲存定時任務和通知頻道的設置

## Cogs 說明

### text_channel_cog.py

這個 cog 主要負責處理與文字頻道相關的功能,包括:

- 設置特定頻道與 AI 模型的對應關係
- 處理用戶在指定頻道中的訊息,並調用相應的 AI 模型進行回覆
- 管理 AI 模型的對話記錄
- 提供手動清除所有對話記錄的指令

此 cog 引入了 Redis 緩存機制來優化 Embed 訊息按鈕的管理,並統一使用 Discord 提供的 `message.id` 作為 Embed 訊息的唯一標識符。它的核心功能包括處理用戶訊息、生成回應、更新 Embed 訊息和對話歷史等。

此 cog 依賴於以下設定檔案和模組:

- `api_module_config.json`: 儲存 AI 模型的設定
- `channel_setup_config.json`: 儲存頻道與 AI 模型的對應關係
- `discord.py`: Discord API 的 Python 庫
- `redis`: Redis 數據庫的 Python 庫
- `text_channel_cache.py`: 提供 Redis 緩存操作的類
- `operations.py`: 提供某些操作(如清除對話記錄)的類

此 cog 使用了以下 view 檔案:

- `text_channel_view.py`: 包含 `EmbedChatView`、`ChannelSetupView` 和 `ClearHistoryConfirmView` 等與文字頻道相關的 view。

### scheduled_tasks_cog.py

這個 cog 用於管理機器人的定時任務和通知功能,包括:

- 設置接收通知的文字頻道
- 選擇需要使用的定時任務(目前只有自動清除對話記錄)
- 定期執行選擇的定時任務

此 cog 依賴於以下模組和設定檔案:

- `text_channel_cog.py`: 提供清除對話記錄的方法
- `scheduled_tasks_config.json`: 儲存通知頻道和選擇的定時任務

此 cog 沒有使用任何 view 檔案和 operation 裡面的代碼。

### redis_cog.py

這個 cog 負責管理與 Redis 的連接和交互,提供了一些常用的 Redis 操作方法,包括:

- 建立與 Redis 的連接
- 設置鍵值對
- 獲取鍵對應的值
- 刪除鍵
- 檢查鍵是否存在
- 將值添加到集合中
- 從集合中移除值
- 檢查值是否在集合中

其他的 cog,如 `text_channel_cog.py`,可以導入 `redis_cog.py` 並使用其提供的方法來與 Redis 進行交互,實現數據的緩存和持久化。

此 cog 使用了以下環境變量:

- `REDIS_URL`: Redis 服務器的主機名、 IP 地址、端口號與數據庫編號。

此 cog 沒有依賴其他的設定檔案,也沒有使用任何 view 檔案和 operation 裡面的代碼。

## Cache 說明

### text_channel_cache.py

這個文件定義了 `TextChannelCache` 類,用於處理與文字頻道相關的 Redis 快取操作。它提供了以下方法:

- `get_latest_message_id`: 從 Redis 中獲取指定用戶在指定頻道中最新的 Embed 訊息 ID。
- `update_latest_message_id`: 更新 Redis 中指定用戶在指定頻道中最新的 Embed 訊息 ID。
- `delete_latest_message_id`: 從 Redis 中刪除指定用戶在指定頻道中最新的 Embed 訊息 ID。

`TextChannelCache` 類依賴於 `redis_cog.py` 提供的 Redis 操作方法,使用 `RedisCog` 實例來執行實際的 Redis 命令。

通過使用 `TextChannelCache`,`text_channel_cog.py` 可以更高效地管理用戶在不同頻道中的 Embed 訊息,減少對 Discord API 的請求次數,提高機器人的性能。

## Components 說明

### text_channel_view.py

此檔案包含與文字頻道相關的 UI 組件,包括:

- `RegenerateButton`: 重新生成對話訊息的按鈕。
- `ResendButton`: 重新發送對話訊息的按鈕。
- `ClearHistoryConfirmView`: 確認清除對話記錄的視圖。
- `EmbedChatView`: 用於顯示聊天記錄的嵌入式視圖。
- `ChannelSetupView`: 設置頻道的視圖。
- `APISelect`: 選擇語言模型 API 的下拉選單。
- `ModuleSelect`: 選擇模組的下拉選單。
- `PromptSelect`: 選擇提示詞的下拉選單。

這些 UI 組件與 `text_channel_cog.py` 緊密配合,實現了用戶與機器人的交互功能。

### channel_setup_view.py

此檔案包含與頻道設置相關的 view,包括:

- `ChannelSelectView`: 選擇要移除設置的頻道的視圖。
- `ChannelSelect`: 選擇頻道的下拉選單。

這些 view 主要由 `channel_setup_cog.py` 使用。

### clear_confirm_view.py

此檔案包含確認清除頻道的視圖:

- `ClearConfirmView`: 確認清除頻道的視圖,包含 "確認" 和 "取消" 兩個按鈕。

此 view 由 `operations.py` 中的 `ClearChannelOperation` 使用。

### cog_control_view.py

此檔案包含控制 cog 的視圖:

- `CogControlView`: 控制 cog 的視圖,包含一個選擇模組的下拉選單。
- `CogSelect`: 選擇模組的下拉選單。

這些 view 主要用於 `bot_main.py` 中的 `load_cog`、`unload_cog` 和 `reload_cog` 指令。

### operations.py

此檔案包含各種操作的類別,例如:

- `LoadOperation`: 載入模組的操作。
- `UnloadOperation`: 卸載模組的操作。
- `ReloadOperation`: 重新載入模組的操作。
- `RemoveSetupOperation`: 移除特定頻道設置的操作。
- `ClearChannelOperation`: 清除頻道的操作。
- `ClearHistoryAndRestartCogOperation`: 清除大型語言模型的對話記錄的操作。

這些操作類別由不同的 cog 和 view 使用,例如 `text_channel_cog.py`、`channel_setup_cog.py` 和 `clear_confirm_view.py`。


## LLMs 說明

- `openrouter_chat_cog.py`: 負責透過 OpenRouter API 處理一般對話的功能。
- `openai_chat_cog.py`: 負責透過 OpenAI API 處理一般對話的功能。
- `cohere_chat_cog.py`: 負責透過 Cohere API 處理一般對話的功能。

## 如何運行

1. 安裝Python 3.12或更高版本。
2. 安裝必要的支援套件: `pip install -r requirements.txt`
3. 設置和配置 Redis 服務器:
   - 安裝 Redis 服務器
   - 在 `.env` 文件中正確設置 Redis 的連接信息(`REDIS_URL`)
4. 在Discord Developer Portal創建一個新的Bot,並將其Token添加到`.env`中。
5. 啟動 Redis 服務器
6. 運行`bot_main.py`: `python bot_main.py`

## 未來計劃

- 進一步優化代碼結構和風格,提高代碼的可讀性和可維護性。
- 擴展機器人的功能,支持更多的 AI 模型和服務。
- 改進錯誤處理和日誌記錄機制,提高機器人的穩定性和可調試性。
- 編寫更詳細的文檔和註釋,方便其他開發者理解和參與項目。
- 優化 Redis 中的數據結構和格式,提高數據的可讀性和檢索效率。


