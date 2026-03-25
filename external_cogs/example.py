"""
範例 Cog（外部插件）- 可作為新插件的模板
示範如何同時撰寫 Discord 指令和 @ai_tool 標記的 AI 工具。
"""
import discord
from discord.ext import commands
from utils.logger import setup_logger
from agent.decorator import ai_tool

logger = setup_logger("external_cogs.example")


class Example(commands.Cog):
    """範例 Cog 類別"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("Example Cog 已載入")
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Example Cog 已就緒")

    # ─── PydanticAI Tool ─────────────────────────────────────────────────

    @ai_tool("取得 Bot 的基本資訊，例如延遲、伺服器數量等。")
    async def get_bot_info(self) -> str:
        """取得 Bot 基本資訊"""
        return (
            f"Bot 名稱: {self.bot.user}\n"
            f"延遲: {round(self.bot.latency * 1000)}ms\n"
            f"伺服器數量: {len(self.bot.guilds)}\n"
            f"已載入模組: {len(self.bot.extensions)} 個"
        )

    # ─── 指令 ────────────────────────────────────────────────────────────

    @commands.command(name="ping", aliases=["p"])
    async def ping(self, ctx: commands.Context):
        """測試 Bot 是否在線"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! 延遲: {latency}ms")
    
    @commands.command(name="hello", aliases=["hi"])
    async def hello(self, ctx: commands.Context, *, member: discord.Member = None):
        """打招呼指令"""
        if member is None:
            member = ctx.author
        await ctx.send(f"你好，{member.mention}！")
    
    @commands.command(name="info")
    async def info(self, ctx: commands.Context):
        """顯示 Bot 資訊"""
        embed = discord.Embed(
            title="Bot 資訊",
            description="這是一個使用 discord.py + PydanticAI 建立的機器人",
            color=discord.Color.blue()
        )
        embed.add_field(name="伺服器數量", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="延遲", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="已載入模組", value=len(self.bot.extensions), inline=True)
        embed.set_footer(text=f"由 {self.bot.user} 提供")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Example(bot))
    logger.info("Example Cog 已註冊")
