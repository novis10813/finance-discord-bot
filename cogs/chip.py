"""
籌碼分析 Cog
"""
import discord
from discord.ext import commands, tasks
from datetime import datetime, time, timezone, timedelta
from typing import Optional, Dict, Any

from config import CHIP_CHANNEL_ID
from utils.logger import setup_logger
from utils.checks import is_chip_channel
from services.twse import get_twse_service, TWSEServiceError

logger = setup_logger("cogs.chip")

# 定義台灣時區 (UTC+8)
TW_TZ = timezone(timedelta(hours=8))


class Chip(commands.Cog):
    """台股籌碼分析功能"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = CHIP_CHANNEL_ID
        self.target_tag_name = "籌碼異動"
        self.twse = get_twse_service()
        
    async def cog_load(self):
        """Cog 載入時執行"""
        self.daily_report_task.start()
        logger.info(f"Chip Cog 每日排程已啟動 (預定執行時間: {self.daily_report_task.time})")
        
    async def cog_unload(self):
        """Cog 卸載時執行"""
        self.daily_report_task.cancel()
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """處理指令錯誤"""
        if ctx.command and ctx.command.cog != self:
            return
        
        if isinstance(error, commands.CheckFailure):
            await ctx.send("❌ 此指令只能在特定頻道使用")
            return
        
        raise error
    
    def _format_chip_embed(self, data: Dict[str, Any]) -> discord.Embed:
        """將籌碼資料格式化為 Embed"""
        date_str = data.get("date", "")
        title = data.get("title", "三大法人買賣金額統計表")
        
        embed = discord.Embed(
            title=f"📊 {title}",
            description=f"日期: {date_str}",
            color=discord.Color.green(),
            timestamp=datetime.now(TW_TZ)
        )
        
        investors = data.get("investors", [])
        summary_text = ""
        
        for inv in investors:
            name = inv.get("name", "")
            diff = inv.get("diff", 0)
            buy = inv.get("buy", 0)
            sell = inv.get("sell", 0)
            
            status = "🔴" if diff < 0 else "🟢"
            diff_str = f"{diff:,}"
            
            summary_text += f"> **{name}**\n"
            summary_text += f"買進: {buy:,}\n"
            summary_text += f"賣出: {sell:,}\n"
            summary_text += f"差額: {status} `{diff_str}`\n\n"
        
        embed.add_field(name="三大法人買賣超細節", value=summary_text or "無資料", inline=False)
        
        total_diff = data.get("total_diff", 0)
        total_status_emoji = "🔴" if total_diff < 0 else "🟢"
        total_status_text = "賣超" if total_diff < 0 else "買超"
        embed.set_footer(text=f"總計呈現{total_status_text}狀態 {total_status_emoji}")
        
        return embed
    
    def _format_stock_rank_embed(self, data: Dict[str, Any], embed: discord.Embed) -> discord.Embed:
        """將個股排名資料加入 Embed"""
        top_foreign_buy = data.get("top_foreign_buy", [])[:10]
        top_foreign_sell = data.get("top_foreign_sell", [])[:10]
        
        # 格式化買超列表
        buy_text = ""
        for i, stock in enumerate(top_foreign_buy, 1):
            diff = stock.get("foreign_diff", 0)
            buy_text += f"{i}. **{stock['name']}** ({stock['code']}): `+{diff:,}`\n"
        
        # 格式化賣超列表
        sell_text = ""
        for i, stock in enumerate(top_foreign_sell, 1):
            diff = stock.get("foreign_diff", 0)
            sell_text += f"{i}. **{stock['name']}** ({stock['code']}): `{diff:,}`\n"
        
        embed.add_field(name="🏆 外資買超前十名 (股)", value=buy_text or "無資料", inline=True)
        embed.add_field(name="📉 外資賣超前十名 (股)", value=sell_text or "無資料", inline=True)
        
        return embed
    
    # 設定每日 16:00 (UTC+8) 執行
    @tasks.loop(time=time(hour=16, minute=0, tzinfo=TW_TZ))
    async def daily_report_task(self):
        """每日排程任務"""
        today = datetime.now(TW_TZ)
        if today.weekday() >= 5:  # 週末跳過
            return

        logger.info("開始執行每日籌碼分析報告")
        
        today_str = today.strftime("%Y%m%d")
        
        try:
            summary_data = await self.twse.get_chip_summary(today_str)
            stock_data = await self.twse.get_stock_chip_list(today_str)
        except TWSEServiceError as e:
            logger.error(f"取得籌碼資料失敗: {e.message}")
            return
        
        if not summary_data:
            logger.info(f"今日 ({today_str}) 無籌碼資料或休市，跳過報告")
            return
        
        # 檢查資料日期
        data_date = summary_data.get("date", "")
        if data_date != today_str:
            logger.info(f"今日 ({today_str}) 資料尚未更新 (回傳日期: {data_date})，跳過報告")
            return
        
        # 格式化訊息
        embed = self._format_chip_embed(summary_data)
        
        if stock_data:
            embed = self._format_stock_rank_embed(stock_data, embed)
        
        date_display = f"{data_date[:4]}/{data_date[4:6]}/{data_date[6:]}"
        
        # 發送到 Forum Channel
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            logger.error(f"找不到頻道 ID: {self.channel_id}")
            return
        
        if not isinstance(channel, discord.ForumChannel):
            logger.error(f"頻道 ID {self.channel_id} 不是 Forum Channel")
            if hasattr(channel, "send"):
                await channel.send(embed=embed)
            return

        # 尋找標籤
        target_tag = None
        for tag in channel.available_tags:
            if tag.name == self.target_tag_name:
                target_tag = tag
                break
        
        tags = [target_tag] if target_tag else []
        
        # 建立貼文
        thread_name = f"📅 {date_display} 三大法人籌碼日報"
        try:
            await channel.create_thread(
                name=thread_name,
                content="每日籌碼數據更新",
                embed=embed,
                applied_tags=tags
            )
            logger.info(f"已發送籌碼日報: {thread_name}")
        except Exception as e:
            logger.error(f"發送籌碼日報失敗: {e}")
    
    @daily_report_task.before_loop
    async def before_daily_report(self):
        await self.bot.wait_until_ready()

    @commands.command(name="daily_chip", aliases=["chip"])
    @is_chip_channel()
    async def manual_chip(self, ctx: commands.Context, date_str: str = None):
        """手動觸發籌碼分析查詢"""
        await ctx.send("正在查詢籌碼資料...")
        
        try:
            summary_data = await self.twse.get_chip_summary(date_str)
            stock_data = await self.twse.get_stock_chip_list(date_str)
        except TWSEServiceError as e:
            await ctx.send(f"❌ 查詢失敗: {e.message}")
            return
        
        if not summary_data:
            await ctx.send(f"查無資料 (日期: {date_str or '今日'})")
            return
        
        embed = self._format_chip_embed(summary_data)
        if stock_data:
            embed = self._format_stock_rank_embed(stock_data, embed)
        
        await ctx.send(embed=embed)

    @commands.command(name="chip_stock", aliases=["chip_detail", "股票籌碼"])
    @is_chip_channel()
    async def stock_chip_detail(self, ctx: commands.Context, stock_code: str, date_str: str = None):
        """查詢個股籌碼詳情"""
        if not stock_code:
            await ctx.send("請提供股票代碼，例如：`!chip_stock 2330`")
            return
        
        await ctx.send(f"正在查詢 {stock_code} 的籌碼資料...")
        
        try:
            stock_data = await self.twse.get_stock_chip_detail(stock_code, date_str)
        except TWSEServiceError as e:
            await ctx.send(f"❌ 查詢失敗: {e.message}")
            return
        
        if not stock_data:
            await ctx.send(f"找不到股票代碼 {stock_code} 的籌碼資料")
            return
        
        date = stock_data.get("date", "")
        date_display = f"{date[:4]}/{date[4:6]}/{date[6:]}" if len(date) == 8 else date
        
        def format_num(val: int) -> str:
            if val > 0:
                return f"+{val:,}"
            return f"{val:,}"
        
        embed = discord.Embed(
            title=f"📊 {stock_data['name']} ({stock_data['code']}) 籌碼詳情",
            description=f"日期: {date_display}",
            color=discord.Color.blue(),
            timestamp=datetime.now(TW_TZ)
        )
        
        # 外資
        foreign_diff = stock_data.get("foreign_diff", 0)
        foreign_emoji = "🟢" if foreign_diff >= 0 else "🔴"
        embed.add_field(
            name=f"{foreign_emoji} 外資",
            value=f"買進: {stock_data.get('foreign_buy', 0):,}\n"
                  f"賣出: {stock_data.get('foreign_sell', 0):,}\n"
                  f"買賣超: `{format_num(foreign_diff)}`",
            inline=True
        )
        
        # 投信
        trust_diff = stock_data.get("trust_diff", 0)
        trust_emoji = "🟢" if trust_diff >= 0 else "🔴"
        embed.add_field(
            name=f"{trust_emoji} 投信",
            value=f"買進: {stock_data.get('trust_buy', 0):,}\n"
                  f"賣出: {stock_data.get('trust_sell', 0):,}\n"
                  f"買賣超: `{format_num(trust_diff)}`",
            inline=True
        )
        
        # 自營商
        dealer_diff = stock_data.get("dealer_diff", 0)
        dealer_emoji = "🟢" if dealer_diff >= 0 else "🔴"
        embed.add_field(
            name=f"{dealer_emoji} 自營商",
            value=f"買賣超: `{format_num(dealer_diff)}`",
            inline=True
        )
        
        # 三大法人合計
        total_diff = stock_data.get("total_diff", 0)
        total_emoji = "🟢" if total_diff >= 0 else "🔴"
        embed.add_field(
            name=f"{total_emoji} 三大法人合計",
            value=f"`{format_num(total_diff)}` 股",
            inline=False
        )
        
        embed.set_footer(text="資料來源: twse-api")
        
        await ctx.send(embed=embed)

    @commands.command(name="chip_compare", aliases=["籌碼對比"])
    @is_chip_channel()
    async def chip_compare(self, ctx: commands.Context, date1: str, date2: str):
        """對比兩個日期的籌碼資料"""
        await ctx.send(f"正在對比 {date1} 和 {date2} 的籌碼資料...")
        
        try:
            data1 = await self.twse.get_chip_summary(date1)
            data2 = await self.twse.get_chip_summary(date2)
        except TWSEServiceError as e:
            await ctx.send(f"❌ 查詢失敗: {e.message}")
            return
        
        if not data1 or not data2:
            await ctx.send("無法取得完整資料，請確認日期是否正確")
            return
        
        date1_display = f"{date1[:4]}/{date1[4:6]}/{date1[6:]}"
        date2_display = f"{date2[:4]}/{date2[4:6]}/{date2[6:]}"
        
        embed = discord.Embed(
            title="📊 籌碼資料對比",
            description=f"對比 {date1_display} vs {date2_display}",
            color=discord.Color.purple(),
            timestamp=datetime.now(TW_TZ)
        )
        
        investors1 = {inv["name"]: inv for inv in data1.get("investors", [])}
        investors2 = {inv["name"]: inv for inv in data2.get("investors", [])}
        
        compare_text = ""
        for name in investors1.keys():
            if name in investors2:
                diff1 = investors1[name].get("diff", 0)
                diff2 = investors2[name].get("diff", 0)
                change = diff2 - diff1
                
                emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                compare_text += f"{emoji} **{name}**\n"
                compare_text += f"  {date1_display}: `{diff1:,}`\n"
                compare_text += f"  {date2_display}: `{diff2:,}`\n"
                compare_text += f"  變化: `{change:+,}`\n\n"
        
        embed.add_field(name="三大法人買賣超變化", value=compare_text or "無資料", inline=False)
        embed.set_footer(text="資料來源: twse-api")
        
        await ctx.send(embed=embed)

    @commands.command(name="chip_trend", aliases=["籌碼趨勢"])
    @is_chip_channel()
    async def chip_trend(self, ctx: commands.Context, stock_code: str, investor_type: str = "全部", days: int = 5):
        """查詢個股籌碼趨勢"""
        investor_map = {
            "外資": "foreign_diff",
            "外": "foreign_diff",
            "foreign": "foreign_diff",
            "投信": "trust_diff",
            "信": "trust_diff",
            "trust": "trust_diff",
            "自營商": "dealer_diff",
            "自營": "dealer_diff",
            "自": "dealer_diff",
            "dealer": "dealer_diff",
            "全部": "total_diff",
            "合計": "total_diff",
            "all": "total_diff",
        }
        
        investor_key = investor_type.lower()
        if investor_key not in investor_map:
            await ctx.send(f"❌ 無效的法人類型: {investor_type}\n請使用：外資、投信、自營商、全部")
            return
        
        field_name = investor_map[investor_key]
        investor_name = {
            "foreign_diff": "外資",
            "trust_diff": "投信",
            "dealer_diff": "自營商",
            "total_diff": "三大法人合計"
        }[field_name]
        
        if days > 10:
            days = 10
        
        await ctx.send(f"正在查詢 {stock_code} 近 {days} 天的【{investor_name}】籌碼趨勢...")
        
        today = datetime.now(TW_TZ)
        trend_data = []
        seen_dates = set()
        check_date = today
        attempts = 0
        max_attempts = days * 3
        
        while len(trend_data) < days and attempts < max_attempts:
            date_str = check_date.strftime("%Y%m%d")
            
            try:
                stock_data = await self.twse.get_stock_chip_detail(stock_code, date_str)
                
                if stock_data:
                    actual_date = stock_data.get("date", "")
                    if actual_date and actual_date not in seen_dates:
                        seen_dates.add(actual_date)
                        trend_data.append({
                            "date": actual_date,
                            "net": stock_data.get(field_name, 0),
                            "name": stock_data.get("name", stock_code)
                        })
            except TWSEServiceError:
                pass
            
            check_date -= timedelta(days=1)
            attempts += 1
        
        if not trend_data:
            await ctx.send(f"找不到 {stock_code} 的籌碼資料")
            return
        
        trend_data.reverse()
        stock_name = trend_data[0].get("name", stock_code)
        
        embed = discord.Embed(
            title=f"📈 {stock_name} ({stock_code}) 【{investor_name}】籌碼趨勢",
            description=f"近 {len(trend_data)} 個交易日",
            color=discord.Color.gold(),
            timestamp=datetime.now(TW_TZ)
        )
        
        trend_text = ""
        prev_net = None
        for item in trend_data:
            date_display = f"{item['date'][4:6]}/{item['date'][6:]}"
            net = item["net"]
            
            if prev_net is None:
                trend_emoji = "⏺️"
            elif net > prev_net:
                trend_emoji = "📈"
            elif net < prev_net:
                trend_emoji = "📉"
            else:
                trend_emoji = "➡️"
            
            status_emoji = "🟢" if net >= 0 else "🔴"
            trend_text += f"{trend_emoji} {date_display}: {status_emoji} `{net:+,}` 股\n"
            prev_net = net
        
        embed.add_field(name=f"{investor_name}買賣超趨勢", value=trend_text, inline=False)
        
        total = sum(item["net"] for item in trend_data)
        avg = total / len(trend_data)
        
        stats_text = f"合計: `{total:+,}` 股\n平均: `{avg:+,.0f}` 股/日"
        embed.add_field(name="📊 統計", value=stats_text, inline=False)
        
        embed.set_footer(text="資料來源: twse-api")
        
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Chip(bot))
