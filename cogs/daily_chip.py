"""
每日台股籌碼分析 Cog
"""
import httpx
import discord
from discord.ext import commands, tasks
from datetime import datetime, time, timezone, timedelta
from typing import Optional, Dict, Any

from config import CHIP_CHANNEL_ID
from utils.logger import setup_logger

logger = setup_logger("cogs.daily_chip")

# 定義台灣時區 (UTC+8)
TW_TZ = timezone(timedelta(hours=8))

class DailyChip(commands.Cog):
    """每日台股籌碼分析功能"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = CHIP_CHANNEL_ID
        self.target_tag_name = "籌碼異動"
        
    async def cog_load(self):
        """Cog 載入時執行"""
        self.daily_report_task.start()
        logger.info(f"Daily Chip 每日排程已啟動 (預定執行時間: {self.daily_report_task.time})")
        
    async def cog_unload(self):
        """Cog 卸載時執行"""
        self.daily_report_task.cancel()
            
    async def fetch_chip_data(self, date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        抓取三大法人買賣金額統計表 (BFI82U)
        
        Args:
            date_str: 日期字串 (YYYYMMDD)，預設為當天
            
        Returns:
            Dict: API 回傳的 JSON 資料，失敗回傳 None
        """
        if not date_str:
            date_str = datetime.now(TW_TZ).strftime("%Y%m%d")
            
        # 注意：使用 dayDate 參數而非 date（TWSE 網站使用此參數名）
        url = f"https://www.twse.com.tw/fund/BFI82U?response=json&dayDate={date_str}"
        
        try:
            # TWSE 有時會有 SSL 驗證問題，這裡暫時忽略驗證
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if data.get("stat") != "OK":
                    logger.warning(f"取得籌碼資料失敗: {data.get('stat')} (日期: {date_str})")
                    return None
                    
                return data
        except Exception as e:
            logger.error(f"抓取籌碼資料發生錯誤: {e}")
            return None

    async def fetch_stock_chip_data(self, date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        抓取個股三大法人買賣超 (T86)
        
        Args:
            date_str: 日期字串 (YYYYMMDD)
            
        Returns:
            Dict: API 回傳的 JSON 資料
        """
        if not date_str:
            date_str = datetime.now(TW_TZ).strftime("%Y%m%d")
            
        # selectType=ALL (所有證券)，使用 dayDate 參數
        url = f"https://www.twse.com.tw/fund/T86?response=json&selectType=ALL&dayDate={date_str}"
        
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(url, timeout=30.0) # T86 資料較大，增加 timeout
                response.raise_for_status()
                data = response.json()
                
                if data.get("stat") != "OK":
                    logger.warning(f"取得個股籌碼資料失敗: {data.get('stat')} (日期: {date_str})")
                    return None
                    
                return data
        except Exception as e:
            logger.error(f"抓取個股籌碼資料發生錯誤: {e}")
            return None

    def format_stock_rank_embed(self, stock_data: Dict[str, Any], embed: discord.Embed) -> discord.Embed:
        """
        將個股排名資料加入 Embed
        
        Args:
            stock_data: T86 API 回傳資料
            embed: 現有的 Embed 物件
        """
        # data 格式: [證券代號, 證券名稱, ..., 三大法人買賣超股數]
        # 三大法人買賣超股數 為最後一個欄位 (index -1)
        records = stock_data.get("data", [])
        
        # 解析並排序
        # list of (code, name, net_buy_sell)
        parsed_records = []
        for record in records:
            try:
                code = record[0].strip()
                name = record[1].strip()
                # 移除逗號並轉為 int
                net_buy_sell = int(record[-1].replace(",", ""))
                parsed_records.append((code, name, net_buy_sell))
            except (ValueError, IndexError):
                continue
                
        # 排序：買超前十 (由大到小)
        top_buy = sorted(parsed_records, key=lambda x: x[2], reverse=True)[:10]
        # 排序：賣超前十 (由小到大)
        top_sell = sorted(parsed_records, key=lambda x: x[2])[:10]
        
        # 格式化買超列表
        buy_text = ""
        for i, (code, name, count) in enumerate(top_buy, 1):
            count_str = f"{count:,}"
            buy_text += f"{i}. **{name}** ({code}): `+{count_str}`\n"
            
        # 格式化賣超列表
        sell_text = ""
        for i, (code, name, count) in enumerate(top_sell, 1):
            count_str = f"{count:,}"
            sell_text += f"{i}. **{name}** ({code}): `{count_str}`\n"
            
        embed.add_field(name="🏆 三大法人買超前十名 (股)", value=buy_text or "無資料", inline=True)
        embed.add_field(name="📉 三大法人賣超前十名 (股)", value=sell_text or "無資料", inline=True)
        
        return embed

    def format_chip_embed(self, data: Dict[str, Any]) -> discord.Embed:
        """
        將籌碼資料格式化為 Embed
        
        Args:
            data: API 回傳的資料
            
        Returns:
            discord.Embed: 格式化後的 Embed
        """
        title = data.get("title", "無法取得標題")
        date_str = data.get("date", "")
        
        # 建立 Embed
        embed = discord.Embed(
            title=f"📊 {title}",
            description=f"日期: {date_str}",
            color=discord.Color.green(),
            timestamp=datetime.now(TW_TZ)
        )
        
        # 處理資料表格
        records = data.get("data", [])
        
        # 找出重點資料
        summary_text = ""
        total_diff = 0
        
        for record in records:
            name = record[0]
            buy = record[1]
            sell = record[2]
            diff = record[3]
            
            # 清理數字格式
            try:
                diff_val = float(diff.replace(",", ""))
                total_diff += diff_val
            except ValueError:
                pass
                
            status = "🔴" if diff.startswith("-") else "🟢"
            
            summary_text += f"> **{name}**\n"
            summary_text += f"買進: {buy}\n"
            summary_text += f"賣出: {sell}\n"
            summary_text += f"差額: {status} `{diff}`\n\n"
            
        embed.add_field(name="三大法人買賣超細節", value=summary_text, inline=False)
        
        # 總結
        total_status_emoji = "🔴" if total_diff < 0 else "🟢"
        total_status_text = "賣超" if total_diff < 0 else "買超"
        embed.set_footer(text=f"總計呈現{total_status_text}狀態 {total_status_emoji}")
        
        return embed

    # 設定每日 16:00 (UTC+8) 執行
    @tasks.loop(time=time(hour=16, minute=0, tzinfo=TW_TZ))
    async def daily_report_task(self):
        """每日排程任務"""
        # 跳過週末 (週六=5, 週日=6)
        today = datetime.now(TW_TZ)
        if today.weekday() >= 5:
            return

        logger.info("開始執行每日籌碼分析報告")
        
        # 1. 取得整體資料 (BFI82U)
        today_str = today.strftime("%Y%m%d")
        bfi_data = await self.fetch_chip_data(today_str)
        t86_data = await self.fetch_stock_chip_data(today_str)
        
        if not bfi_data:
            logger.info(f"今日 ({today_str}) 無籌碼資料或休市，跳過報告")
            return
            
        # 額外檢查：確認回傳資料的日期是否真的是今天
        data_date = bfi_data.get("date", "")
        if data_date != today_str:
            logger.info(f"今日 ({today_str}) 資料尚未更新 (回傳日期: {data_date})，跳過報告")
            return
            
        # 2. 格式化訊息 (基本資訊)
        embed = self.format_chip_embed(bfi_data)
        
        # 3. 加入個股排名 (如果有資料)
        if t86_data and t86_data.get("stat") == "OK":
            embed = self.format_stock_rank_embed(t86_data, embed)
        
        date_display = f"{data_date[:4]}/{data_date[4:6]}/{data_date[6:]}"
        
        # 3. 發送到 Forum Channel
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            logger.error(f"找不到頻道 ID: {self.channel_id}")
            return
            
        if not isinstance(channel, discord.ForumChannel):
            logger.error(f"頻道 ID {self.channel_id} 不是 Forum Channel")
            # Fallback
            if hasattr(channel, "send"):
                await channel.send(embed=embed)
            return

        # 4. 尋找標籤
        target_tag = None
        for tag in channel.available_tags:
            if tag.name == self.target_tag_name:
                target_tag = tag
                break
        
        tags = [target_tag] if target_tag else []
        if not target_tag:
            logger.warning(f"找不到標籤 '{self.target_tag_name}'，將發送無標籤貼文")

        # 5. 建立貼文
        thread_name = f"📅 {date_str} 三大法人籌碼日報"
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
    async def manual_chip(self, ctx: commands.Context, date_str: str = None):
        """
        手動觸發籌碼分析查詢
        
        Args:
            date_str: 日期 (YYYYMMDD)，預設為今日
        """
        await ctx.send("正在查詢籌碼資料...")
        
        data = await self.fetch_chip_data(date_str)
        t86_data = await self.fetch_stock_chip_data(date_str)
        
        if not data:
            await ctx.send(f"查無資料 (日期: {date_str or '今日'})")
            return
            
        embed = self.format_chip_embed(data)
        if t86_data and t86_data.get("stat") == "OK":
            embed = self.format_stock_rank_embed(t86_data, embed)
            
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(DailyChip(bot))
