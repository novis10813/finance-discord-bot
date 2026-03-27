"""
Analysis Cog
Financial analysis and charting commands
"""
import discord
from discord.ext import commands
import io
import logging

from services.mops import get_mops_service, MOPSServiceError

logger = logging.getLogger("cogs.analysis")


class Analysis(commands.Cog):
    """Financial Analysis Commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.mops = get_mops_service()
        
    @commands.command(name="plot", aliases=["compare", "chart", "分析"])
    async def plot(self, ctx: commands.Context, *args):
        """
        Plot financial metrics comparison.
        Usage: !plot 2330 2887 [Metric] [Years]
        Example: !plot 2330 2317 ROE 5
        Default: Metric=ROE, Years=5
        """
        stocks = []
        metric = "ROE"
        years = 5
        
        # Smart argument parsing
        for arg in args:
            clean_arg = arg.upper().replace(",", "").strip()
            if not clean_arg:
                continue
                
            if clean_arg.isdigit():
                val = int(clean_arg)
                # Heuristic: < 100 is likely years, >= 100 is stock code
                if val <= 20: 
                    years = val
                else: 
                    stocks.append(clean_arg)
            else:
                # Assume it's a metric name
                metric = clean_arg
        
        if not stocks:
            await ctx.send("❌ 請提供至少一個股票代號 (此功能僅支援台股, e.g. 2330)")
            return
            
        # Limit constraints
        if years > 10:
            years = 10
            await ctx.send("⚠️ 暫時限制最多查詢 10 年數據")

        # Status message
        msg = await ctx.send(f"📊 正在分析 {', '.join(stocks)} 的 {metric} (近 {years} 年)... 請稍候，這可能需要幾秒鐘。")
        
        try:
            image_bytes = await self.mops.get_comparison_chart(stocks, metric, years)
            
            if not image_bytes:
                await msg.edit(content=f"❌ 找不到數據 ({', '.join(stocks)})")
                return
            
            # Create file
            f = discord.File(io.BytesIO(image_bytes), filename="chart.png")
            
            await msg.delete()
            await ctx.send(
                content=f"📈 **財務指標分析: {metric}**",
                file=f
            )
            
        except MOPSServiceError as e:
            await msg.edit(content=f"❌ 分析失敗: {e.message}")
        except Exception as e:
            logger.error(f"Plot error: {e}")
            await msg.edit(content="❌ 發生未預期的錯誤")


async def setup(bot: commands.Bot):
    await bot.add_cog(Analysis(bot))
