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
CHIP_CHANNEL_ID = int(os.getenv("CHIP_CHANNEL_ID", "0"))

# 籌碼分析頻道限制（逗號分隔的頻道 ID，空字串表示不限制）
CHIP_ALLOWED_CHANNELS_STR = os.getenv("CHIP_ALLOWED_CHANNELS", "")
CHIP_ALLOWED_CHANNELS = set(
    int(ch_id.strip()) for ch_id in CHIP_ALLOWED_CHANNELS_STR.split(",") 
    if ch_id.strip()
) if CHIP_ALLOWED_CHANNELS_STR else set()

# TWSE API 服務設定
TWSE_API_URL = os.getenv("TWSE_API_URL", "http://twse-api:8000")
