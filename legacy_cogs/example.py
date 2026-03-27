"""
範例 Cog - 可作為開發新功能的模板
"""
import discord
from discord.ext import commands
from utils.logger import setup_logger

logger = setup_logger("cogs.example")


class Example(commands.Cog):
    """範例 Cog 類別"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("Example Cog 已載入")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Cog 準備就緒時觸發"""
        logger.info("Example Cog 已就緒")
    
    @commands.command(name="ping", aliases=["p"])
    async def ping(self, ctx: commands.Context):
        """測試 Bot 是否在線"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! 延遲: {latency}ms")
    
    @commands.command(name="hello", aliases=["hi"])
    async def hello(self, ctx: commands.Context, *, member: discord.Member = None):
        """打招呼指令
        
        Args:
            member: 要打招呼的成員（可選）
        """
        if member is None:
            member = ctx.author
        
        await ctx.send(f"你好，{member.mention}！")
    
    @commands.command(name="info")
    async def info(self, ctx: commands.Context):
        """顯示 Bot 資訊"""
        embed = discord.Embed(
            title="Bot 資訊",
            description="這是一個使用 discord.py 建立的機器人",
            color=discord.Color.blue()
        )
        embed.add_field(name="伺服器數量", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="延遲", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="使用者數量", value=len(self.bot.users), inline=True)
        embed.set_footer(text=f"由 {self.bot.user} 提供")
        
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Cog 載入函數 - discord.py 會自動呼叫此函數"""
    await bot.add_cog(Example(bot))
    logger.info("Example Cog 已註冊")

