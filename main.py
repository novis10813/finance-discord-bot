"""
Discord Bot 程式進入點
"""
import asyncio
import sys
from bot import DiscordBot
from config import BOT_TOKEN, LOG_LEVEL
from utils.logger import setup_logger

# 初始化日誌系統
logger = setup_logger("main", LOG_LEVEL)


async def main():
    """主函數"""
    # 檢查 Token
    if not BOT_TOKEN:
        logger.error("未設定 BOT_TOKEN！請在 .env 檔案中設定 DISCORD_BOT_TOKEN")
        sys.exit(1)
    
    # 建立 Bot 實例
    bot = DiscordBot()
    
    try:
        # 啟動 Bot
        logger.info("正在啟動 Bot...")
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("收到中斷訊號，正在關閉 Bot...")
    except Exception as e:
        logger.error(f"Bot 執行時發生錯誤: {e}", exc_info=True)
    finally:
        # 關閉 Bot
        await bot.close()
        logger.info("Bot 已關閉")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程式已終止")
        sys.exit(0)
