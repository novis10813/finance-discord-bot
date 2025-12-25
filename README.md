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

## 📚 參考資源

- [discord.py 官方文件](https://discordpy.readthedocs.io/)
- [discord.py API 參考](https://discordpy.readthedocs.io/en/stable/api.html)
- [Cogs 說明文件](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html)

## 📄 授權

本專案為開源專案，可自由使用和修改。

