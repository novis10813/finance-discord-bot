# Discord Bot 專案

這是一個使用 [discord.py](https://discordpy.readthedocs.io/) 建立的 Discord 機器人專案，採用官方建議的 **Cogs** 架構，支援模組化功能開發。

## 📁 專案結構

```
discord_bot/
├── main.py                 # 程式進入點
├── bot.py                  # Bot 主類別（繼承 commands.Bot）
├── config.py               # 設定檔（從 .env 讀取設定）
├── .env                    # 環境變數設定檔（需自行建立）
├── .env.example            # 環境變數範例檔案
├── cogs/                   # Cogs 模組資料夾
│   ├── __init__.py
│   └── example.py         # 範例 cog（可作為模板）
├── utils/                  # 工具函數資料夾
│   ├── __init__.py
│   └── logger.py          # 日誌系統設定
├── logs/                   # 日誌檔案資料夾（自動建立）
├── pyproject.toml          # 專案設定與依賴
└── README.md               # 本檔案
```

## 🏗️ 架構說明

### 核心檔案

#### `main.py`
程式進入點，負責：
- 初始化日誌系統
- 檢查 Bot Token
- 啟動 Bot 實例
- 處理關閉流程

#### `bot.py`
Bot 主類別 (`DiscordBot`)，繼承自 `discord.ext.commands.Bot`，包含：
- **自動載入 Cogs**：啟動時自動載入 `cogs/` 資料夾中的所有 cog
- **錯誤處理**：全域指令錯誤處理機制
- **事件監聽**：`on_ready`、`on_message` 等事件處理
- **Intents 設定**：包含 `message_content` intent（讀取訊息內容）

#### `config.py`
從 `.env` 檔案讀取設定，集中管理所有配置：
- `BOT_TOKEN`：Discord Bot Token（必填）
- `COMMAND_PREFIX`：指令前綴（預設 `!`）
- `LOG_LEVEL`：日誌級別
- 其他 Bot 設定選項

所有設定都從 `.env` 檔案讀取，使用 `python-dotenv` 套件自動載入。

### Cogs 架構

Cogs 是 discord.py 推薦的模組化架構，每個功能模組都是獨立的 cog。

#### 如何新增 Cog

1. 在 `cogs/` 資料夾中建立新的 Python 檔案（例如 `my_feature.py`）

2. 使用以下模板：

```python
"""
功能描述
"""
import discord
from discord.ext import commands
from utils.logger import setup_logger

logger = setup_logger("cogs.my_feature")


class MyFeature(commands.Cog):
    """功能類別"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("MyFeature Cog 已載入")
    
    @commands.command(name="mycommand")
    async def my_command(self, ctx: commands.Context):
        """指令描述"""
        await ctx.send("Hello!")
    
    # 可以添加更多指令和事件監聽器


async def setup(bot: commands.Bot):
    """Cog 載入函數 - discord.py 會自動呼叫此函數"""
    await bot.add_cog(MyFeature(bot))
    logger.info("MyFeature Cog 已註冊")
```

3. Bot 啟動時會自動載入新的 cog，無需手動修改其他檔案

#### 範例 Cog

`cogs/example.py` 提供了一個完整的範例，包含：
- `ping` 指令：測試 Bot 延遲
- `hello` 指令：打招呼功能
- `info` 指令：顯示 Bot 資訊（使用 Embed）

### 工具模組

#### `utils/logger.py`
日誌系統設定，提供：
- 檔案日誌：自動建立 `logs/` 資料夾，按日期記錄
- 終端輸出：即時顯示日誌訊息
- 可配置的日誌級別

## 🚀 快速開始

### 1. 安裝依賴

使用 `uv` 安裝依賴（專案使用 uv 作為依賴管理工具）：

```bash
uv sync
```

或使用 pip：

```bash
pip install -e .
```

### 2. 設定環境變數

複製 `.env.example` 為 `.env` 並填入實際值：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，設定你的 Bot Token：

```env
DISCORD_BOT_TOKEN=your_bot_token_here
```

**重要**：`.env` 檔案已加入 `.gitignore`，不會被提交到版本控制系統。

### 3. 執行 Bot

```bash
python main.py
```

或使用 uv：

```bash
uv run python main.py
```

## 📝 開發指南

### 新增功能

1. 在 `cogs/` 資料夾中建立新的 cog 檔案
2. 參考 `cogs/example.py` 的結構
3. 實作你的功能指令和事件監聽器
4. Bot 會自動載入新的 cog

### 指令開發

使用 `@commands.command()` 裝飾器建立指令：

```python
@commands.command(name="command_name", aliases=["alias1", "alias2"])
async def command_function(self, ctx: commands.Context, arg1: str, arg2: int = 10):
    """指令描述（會顯示在 help 指令中）"""
    await ctx.send(f"參數1: {arg1}, 參數2: {arg2}")
```

### 事件監聽

使用 `@commands.Cog.listener()` 監聽事件：

```python
@commands.Cog.listener()
async def on_member_join(self, member: discord.Member):
    """成員加入伺服器時觸發"""
    logger.info(f"{member} 加入了伺服器")
```

### 錯誤處理

Bot 已包含全域錯誤處理，但也可以在 cog 中自訂：

```python
@commands.command()
async def my_command(self, ctx: commands.Context):
    try:
        # 你的程式碼
        pass
    except Exception as e:
        logger.error(f"錯誤: {e}")
        await ctx.send("發生錯誤！")
```

## 🔧 設定選項

在 `.env` 檔案中可以調整以下設定：

- `DISCORD_BOT_TOKEN`：Discord Bot Token（必填）
- `DISCORD_COMMAND_PREFIX`：指令前綴（預設 `!`）
- `BOT_NAME`：Bot 名稱（選填）
- `BOT_DESCRIPTION`：Bot 描述（選填）
- `LOG_LEVEL`：日誌級別（DEBUG, INFO, WARNING, ERROR, CRITICAL，預設 `INFO`）
- `LOG_FILE`：日誌檔案路徑（預設 `logs/bot.log`）
- `COGS_DIR`：Cogs 資料夾路徑（預設 `cogs`）
- `AUTO_LOAD_COGS`：是否自動載入 cogs（預設 `True`）

詳細說明請參考 `.env.example` 檔案。

## 🗺️ Roadmap

以下是專案未來的開發計劃：

### 1. 每日收盤籌碼分析 ✅ 已完成

- ✅ 自動抓取每日收盤後的籌碼資料
- ✅ 分析主力、外資、投信等資金流向
- ✅ 提供籌碼集中度、買賣超等統計資訊
- ✅ 透過 Discord 指令查詢特定股票的籌碼分析結果
- ✅ 支援每日定時推送重要籌碼異動通知
- ✅ 個股籌碼詳細查詢
- ✅ 歷史資料對比
- ✅ 籌碼趨勢分析

**使用方式**：詳見 [docs/chip.md](docs/chip.md)

### 2. 金融資訊 Summary ✅ 已完成

- ✅ 自動從 YouTube 頻道（游庭皓的財經皓角）獲取最新直播影片
- ✅ 使用 AI（OpenRouter）自動摘要影片內容
- ✅ 結構化 Markdown 格式輸出（核心主題、子主題、關鍵數據）
- ✅ 週一至週五 12:00 PM（台灣時間）自動發送到 Discord
- ✅ 支援手動觸發指令 `!daily_finance`
- ✅ 支援 Forum Channel 自動建立討論串

**環境變數設定**：
```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=tngtech/deepseek-r1t2-chimera:free
YOUTUBE_SOURCE_ENDPOINT=http://yt-transcript-api:8001
FINANCE_CHANNEL_ID=your_channel_id
```


### 3. 因子回測平台

- 建立因子回測框架，支援自訂策略測試
- 提供歷史資料回測功能
- 計算策略績效指標（夏普比率、最大回撤、勝率等）
- 視覺化回測結果（收益曲線、因子分析圖表）
- 支援多因子組合與優化建議

## 📱 Discord 頻道架構

本專案的 Discord 伺服器採用以下架構設計，區分自動推送資訊與指令查詢功能：

### 📊 資訊推送區（Forum Channel）

**📰 市場資訊論壇**
- **類型**：Forum Channel（論壇）
- **用途**：所有 Bot 自動推送的資訊統一在此發布
- **內容**：
  - 📊 市場數據摘要（每日收盤數據、指數、成交量等）
  - 📰 財經新聞（重大財經新聞、政策公告等）
  - 🔔 籌碼異動通知（重要籌碼異動提醒）
- **標籤分類**：
  - `📊 市場數據` - 結構化數據與統計
  - `📰 財經新聞` - 新聞事件與動態
  - `🔔 籌碼異動` - 籌碼異動通知
- **特色**：每則推送自動建立獨立討論主題，方便針對特定資訊進行深入討論

### 🔍 查詢與指令（普通文字頻道）

**📊 籌碼分析**
- `🔍-籌碼查詢` - 使用指令查詢特定股票的籌碼分析結果
  - 範例：`!籌碼 2330` 查詢台積電籌碼分析

**📈 金融資訊**
- `🔎-個股查詢` - 使用指令查詢個股/標的資訊
  - 範例：`!查詢 2330` 查詢台積電資訊

**🧪 回測平台**
- `⚙️-回測指令` - 使用指令進行因子回測
  - 範例：`!回測 factor1` 執行因子回測

**特色**：所有指令查詢使用普通文字頻道，Bot 即時回應查詢結果，互動簡單直接。

### 💬 社群交流

**🗣️ 一般討論**
- `💬-一般聊天` - 自由討論區
- `❓-問題求助` - 使用 Bot 或技術問題求助
- `💡-功能建議` - 功能建議與回饋

**📚 資源分享**
- `📖-教學資源` - 分享相關教學與資源
- `📊-策略分享` - 分享交易策略與心得

### 架構優勢

1. **資訊推送集中**：所有自動推送資訊統一在論壇管理，易於搜尋與分類
2. **討論獨立**：每個推送都有獨立討論空間，不會互相干擾
3. **指令簡單**：查詢指令在普通頻道，互動直接即時
4. **職責分明**：自動推送 vs 指令查詢，功能區分清楚

## 📚 參考資源

- [discord.py 官方文件](https://discordpy.readthedocs.io/)
- [discord.py API 參考](https://discordpy.readthedocs.io/en/stable/api.html)
- [Cogs 說明文件](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html)

## 📄 授權

本專案為開源專案，可自由使用和修改。

