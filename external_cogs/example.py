"""
外部插件開發參考模板
==================

此檔案示範外部 Cog（external_cog）的完整結構與常用模式。
開發新插件時，複製此檔案並修改 class 名稱與指令內容即可。

載入方式：
  - 啟動時自動載入：將 .py 檔案放入 EXTERNAL_COGS_DIR 目錄（預設 external_cogs/）
  - 手動載入：  !load <檔名（不含 .py）>
  - 手動卸載：  !unload <檔名>
  - 手動重載：  !reload <檔名>（修改程式碼後使用）
"""
import os

import discord
from discord.ext import commands

from utils.logger import setup_logger

logger = setup_logger("external_cogs.example")


class ExampleCog(commands.Cog, name="範例"):
    """
    範例插件 — 展示外部 Cog 的完整結構。

    包含：
      - 基本 Cog 結構（__init__、事件監聽）
      - 無參數指令
      - 有參數指令
      - Cog 層級錯誤處理
      - 從環境變數讀取設定
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 從環境變數讀取插件設定（在 .env 中定義，或保留預設值）
        self.example_setting = os.getenv("EXAMPLE_SETTING", "預設值")
        logger.info("ExampleCog 已載入")

    # ─── 事件監聽 ────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot 就緒後觸發一次，適合做初始化或日誌記錄。"""
        logger.info(f"ExampleCog 已就緒（設定值：{self.example_setting}）")

    # ─── 無參數指令 ─────────────────────────────────────────────────────

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """測試 Bot 是否在線並回報延遲。用法：!ping"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong！延遲 {latency}ms")

    @commands.command(name="status")
    async def status(self, ctx: commands.Context):
        """顯示 Bot 狀態摘要（使用 Embed）。用法：!status"""
        embed = discord.Embed(
            title="Bot 狀態",
            color=discord.Color.green(),
        )
        embed.add_field(name="延遲", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="伺服器數量", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="已載入模組", value=str(len(self.bot.extensions)), inline=True)
        await ctx.send(embed=embed)

    # ─── 有參數指令 ─────────────────────────────────────────────────────

    @commands.command(name="echo")
    async def echo(self, ctx: commands.Context, *, message: str):
        """
        回覆使用者輸入的訊息。

        用法：!echo <訊息>
        範例：!echo 你好世界
        """
        await ctx.send(f"📢 {message}")

    @commands.command(name="greet")
    async def greet(self, ctx: commands.Context, member: discord.Member = None):
        """
        向指定成員打招呼，未指定時打招呼給發言者。

        用法：!greet [@成員]
        範例：!greet @novis
        """
        target = member or ctx.author
        await ctx.send(f"👋 你好，{target.mention}！")

    # ─── Cog 層級錯誤處理 ────────────────────────────────────────────────

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        捕捉此 Cog 內所有指令拋出的錯誤。
        全域錯誤處理（bot.py on_command_error）不會再處理已在此處理的錯誤。
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ 缺少必要參數：`{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ 參數格式錯誤：{error}")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ 找不到指定的成員")
        else:
            logger.error(f"ExampleCog 指令錯誤：{error}", exc_info=error)
            await ctx.send("❌ 發生未預期的錯誤，請稍後再試")


# ─── 插件入口點（必要）────────────────────────────────────────────────────
# discord.py 在 load_extension() 時會呼叫此函式來安裝 Cog。

async def setup(bot: commands.Bot):
    await bot.add_cog(ExampleCog(bot))
