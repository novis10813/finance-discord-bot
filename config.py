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

# 排程器設定
SCHEDULER_TASKS_FILE = os.getenv("SCHEDULER_TASKS_FILE", "data/scheduled_tasks.json")
