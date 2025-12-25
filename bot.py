"""
Discord Bot 主類別
"""
import discord
from discord.ext import commands
import asyncio
import os
from pathlib import Path
from typing import Optional

from config import BOT_TOKEN, COMMAND_PREFIX, COGS_DIR, AUTO_LOAD_COGS
from utils.logger import setup_logger

logger = setup_logger()


class DiscordBot(commands.Bot):
    """自訂 Bot 類別，繼承 discord.ext.commands.Bot"""
    
    def __init__(self):
        # 設定 intents
        intents = discord.Intents.default()
        intents.message_content = True  # 需要讀取訊息內容
        
        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            description="A Discord bot built with discord.py",
            help_command=commands.DefaultHelpCommand()
        )
    
    async def setup_hook(self):
        """Bot 啟動前的設定"""
        logger.info("正在載入 Cogs...")
        if AUTO_LOAD_COGS:
            await self.load_cogs()
        logger.info("Cogs 載入完成")
    
    async def load_cogs(self):
        """自動載入 cogs 資料夾中的所有 cog"""
        cogs_path = Path(COGS_DIR)
        
        if not cogs_path.exists():
            logger.warning(f"Cogs 資料夾 {COGS_DIR} 不存在")
            return
        
        # 載入所有 .py 檔案（排除 __init__.py）
        for file in cogs_path.glob("*.py"):
            if file.name == "__init__.py":
                continue
            
            cog_name = f"{COGS_DIR}.{file.stem}"
            try:
                await self.load_extension(cog_name)
                logger.info(f"已載入 Cog: {cog_name}")
            except Exception as e:
                logger.error(f"載入 Cog {cog_name} 時發生錯誤: {e}")
    
    async def on_ready(self):
        """Bot 準備就緒時觸發"""
        logger.info(f"Bot 已上線: {self.user}")
        logger.info(f"Bot ID: {self.user.id}")
        logger.info(f"已連接到 {len(self.guilds)} 個伺服器")
        
        # 設定 Bot 狀態
        activity = discord.Game(name=f"使用 {COMMAND_PREFIX}help 查看指令")
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """全域指令錯誤處理"""
        if isinstance(error, commands.CommandNotFound):
            return  # 忽略不存在的指令
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ 缺少必要參數: `{error.param.name}`")
            return
        
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ 參數格式錯誤: {error}")
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 你沒有執行此指令的權限")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ Bot 缺少執行此指令所需的權限")
            return
        
        # 其他錯誤記錄到日誌
        logger.error(f"指令錯誤: {error}", exc_info=error)
        await ctx.send("❌ 執行指令時發生錯誤，請稍後再試")
    
    async def on_message(self, message: discord.Message):
        """處理所有訊息"""
        # 忽略 Bot 自己的訊息
        if message.author.bot:
            return
        
        # 處理指令
        await self.process_commands(message)
    
    async def close(self):
        """Bot 關閉時的清理工作"""
        logger.info("Bot 正在關閉...")
        await super().close()

