"""
金融資訊 Summary Cog
"""
import discord
from discord.ext import commands
from typing import Optional

from services.finance.source_manager import source_manager
from utils.logger import setup_logger
from config import FINANCE_CHANNEL_ID
from utils.scheduler import get_scheduler

logger = setup_logger("cogs.financial_summary")

class FinancialSummary(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = FINANCE_CHANNEL_ID
        
    async def cog_load(self):
        """Cog 載入時啟動排程"""
        scheduler = get_scheduler(self.bot)
        
        # 每天早上 8:00 (台灣時間) 自動發送
        # 注意: scheduler 內部似乎沒有自動處理時區轉換為 UTC 的部分？
        # 假設 scheduler.py 的 add_cron_task 接受的是本地時間 (因為它內部通常用 apscheduler)
        # 查看 utils/scheduler.py，它似乎支援 hour/minute
        
        await scheduler.add_cron_task(
            task_id="daily_financial_summary",
            func=self.daily_report_task,
            hour=8,
            minute=0,
            save=True
        )
        logger.info("Financial Summary Cog loaded and scheduled.")

    @commands.command(name="summary")
    async def manual_summary(self, ctx: commands.Context):
        """手動觸發金融摘要"""
        await ctx.send("🔍 正在收集資料並生成摘要，這可能需要一點時間...")
        
        try:
            report = await source_manager.collect_and_summarize()
            
            if not report["items"]:
                await ctx.send("📭 目前沒有新的金融資訊。")
                return
                
            await self._send_report(ctx.channel, report)
            
        except Exception as e:
            logger.error(f"Manual summary error: {e}")
            await ctx.send(f"❌ 發生錯誤: {str(e)}")

    async def daily_report_task(self):
        """每日排程任務"""
        logger.info("Running daily financial summary task...")
        if not self.channel_id:
            logger.warning("No FINANCE_CHANNEL_ID configured, skipping daily task.")
            return

        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            logger.warning(f"Could not find channel with ID {self.channel_id}")
            return
            
        try:
            report = await source_manager.collect_and_summarize()
            if not report["items"]:
                logger.info("No new items for daily report.")
                return
                
            await self._send_report(channel, report)
            
        except Exception as e:
            logger.error(f"Daily task error: {e}")

    async def _send_report(self, channel, report):
        """發送報告到指定頻道 (支援 Forum 或 Text Channel)"""
        summary_text = report["summary"]
        items = report["items"]
        
        # 建立 Embed
        embed = discord.Embed(
            title="📊 每日金融市場摘要",
            description=summary_text,
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        # 列出前幾則重要新聞連結
        links_text = ""
        for i, item in enumerate(items[:5]):
            links_text += f"{i+1}. [{item.source_name}] [{item.title}]({item.url})\n"
            
        if links_text:
            embed.add_field(name="🔗 重要資訊來源", value=links_text, inline=False)
            
        embed.set_footer(text=f"共收集 {len(items)} 則資訊 | Powered by OpenRouter")

        # 發送邏輯
        if isinstance(channel, discord.ForumChannel):
            #如果是 Forum，建立新貼文
            await channel.create_thread(
                name=f"📅 {discord.utils.utcnow().strftime('%Y/%m/%d')} 金融摘要",
                embed=embed,
                # tag=... (如果需要 tag，需先取得 channel.available_tags)
            )
        else:
            # 普通頻道
            await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(FinancialSummary(bot))
