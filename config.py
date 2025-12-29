"""
Discord Bot 設定檔
從 .env 檔案讀取設定
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Bot Token - 從 .env 檔案讀取
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

# Command Prefix
COMMAND_PREFIX = os.getenv("DISCORD_COMMAND_PREFIX", "!")

# Bot 設定
BOT_NAME = os.getenv("BOT_NAME", "Discord Bot")
BOT_DESCRIPTION = os.getenv("BOT_DESCRIPTION", "A Discord bot built with discord.py")

# 日誌設定
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")

# Cogs 設定
COGS_DIR = os.getenv("COGS_DIR", "cogs")
AUTO_LOAD_COGS = os.getenv("AUTO_LOAD_COGS", "True").lower() == "true"
CHIP_CHANNEL_ID = int(os.getenv("CHIP_CHANNEL_ID", ""))

# 籌碼分析頻道限制（逗號分隔的頻道 ID，空字串表示不限制）
CHIP_ALLOWED_CHANNELS_STR = os.getenv("CHIP_ALLOWED_CHANNELS", "")
CHIP_ALLOWED_CHANNELS = set(
    int(ch_id.strip()) for ch_id in CHIP_ALLOWED_CHANNELS_STR.split(",") 
    if ch_id.strip()
) if CHIP_ALLOWED_CHANNELS_STR else set()

# 排程器設定
SCHEDULER_TASKS_FILE = os.getenv("SCHEDULER_TASKS_FILE", "data/scheduled_tasks.json")

# TWSE API 服務設定 (for future microservice integration)
TWSE_API_URL = os.getenv("TWSE_API_URL", "http://twse-api:8000")


# LLM 設定
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")

# 金融資訊來源設定
YOUTUBE_SOURCE_ENDPOINT = os.getenv("YOUTUBE_SOURCE_ENDPOINT", "")
YOUTUBE_SOURCE_API_KEY = os.getenv("YOUTUBE_SOURCE_API_KEY", "")

# 摘要發送頻道 (Forum Channel ID)
# 如果未設定，預設使用 CHIP_CHANNEL_ID (或者您可以設定單獨的變數)
FINANCE_CHANNEL_ID = int(os.getenv("FINANCE_CHANNEL_ID") or os.getenv("CHIP_CHANNEL_ID", "0"))
