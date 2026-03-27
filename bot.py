"""
Discord Bot 主類別
"""
import sys
import discord
from discord.ext import commands
from pathlib import Path

from config import BOT_TOKEN, COMMAND_PREFIX, COGS_DIR, AUTO_LOAD_COGS, EXTERNAL_COGS_DIR
from utils.logger import setup_logger

logger = setup_logger()


class DiscordBot(commands.Bot):
    """自訂 Bot 類別，繼承 discord.ext.commands.Bot"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

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
            await self.load_external_cogs()
        logger.info("Cogs 載入完成")

    async def load_cogs(self):
        """自動載入內建 cogs 資料夾中的所有 cog"""
        cogs_path = Path(COGS_DIR)

        if not cogs_path.exists():
            logger.warning(f"Cogs 資料夾 {COGS_DIR} 不存在")
            return

        for file in sorted(cogs_path.glob("*.py")):
            if file.name == "__init__.py":
                continue

            cog_name = f"{COGS_DIR}.{file.stem}"
            try:
                await self.load_extension(cog_name)
                logger.info(f"已載入 Cog: {cog_name}")
            except Exception as e:
                logger.error(f"載入 Cog {cog_name} 時發生錯誤: {e}")

    async def load_external_cogs(self):
        """
        載入外部 Cogs 資料夾（EXTERNAL_COGS_DIR）中的所有 cog。
        外部 cog 可透過 Docker volume mount 動態添加，
        並使用 !load / !reload 手動管理。
        """
        ext_path = Path(EXTERNAL_COGS_DIR)

        if not ext_path.exists():
            logger.info(f"外部 Cogs 資料夾 {EXTERNAL_COGS_DIR} 不存在，跳過")
            return

        ext_abs = str(ext_path.resolve().parent)
        if ext_abs not in sys.path:
            sys.path.insert(0, ext_abs)

        ext_dir_name = ext_path.name
        for file in sorted(ext_path.glob("*.py")):
            if file.name == "__init__.py":
                continue

            cog_name = f"{ext_dir_name}.{file.stem}"
            try:
                await self.load_extension(cog_name)
                logger.info(f"已載入外部 Cog: {cog_name}")
            except Exception as e:
                logger.error(f"載入外部 Cog {cog_name} 時發生錯誤: {e}")

    async def on_ready(self):
        """Bot 準備就緒時觸發"""
        logger.info(f"Bot 已上線: {self.user}")
        logger.info(f"Bot ID: {self.user.id}")
        logger.info(f"已連接到 {len(self.guilds)} 個伺服器")

        activity = discord.Game(name=f"使用 {COMMAND_PREFIX}help 查看指令")
        await self.change_presence(activity=activity)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """全域指令錯誤處理"""
        if isinstance(error, commands.CommandNotFound):
            return

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

        logger.error(f"指令錯誤: {error}", exc_info=error)
        await ctx.send("❌ 執行指令時發生錯誤，請稍後再試")

    async def on_message(self, message: discord.Message):
        """處理所有訊息"""
        if message.author.bot:
            return
        await self.process_commands(message)

    async def close(self):
        """Bot 關閉時的清理工作"""
        logger.info("Bot 正在關閉...")
        await super().close()
