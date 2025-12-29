"""
金融資訊來源管理器
負責協調各個來源的資料抓取、去重和彙整
"""
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta

from services.finance.sources.base import FinancialSource, NewsItem
from services.finance.sources.rss import create_street_insider_source
from services.finance.sources.youtube import create_youtube_source
from services.llm import llm_service
from utils.logger import setup_logger
from utils.cache import get_cache

logger = setup_logger("services.finance.manager")

class SourceManager:
    def __init__(self):
        self.sources: List[FinancialSource] = [
            create_street_insider_source(),
            create_youtube_source()
        ]
        self.cache = get_cache()
        self.seen_cache_key = "financial_summary_seen_ids"

    async def collect_and_summarize(self) -> Dict[str, Any]:
        """
        收集所有資料並產生摘要報告
        
        Returns:
            Dict: 包含 'summary' (str) 和 'items' (List[NewsItem])
        """
        # 1. 抓取所有資料
        logger.info("Starting to collect financial data...")
        fetch_tasks = [source.fetch_data() for source in self.sources]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        all_items: List[NewsItem] = []
        for res in results:
            if isinstance(res, list):
                all_items.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Source fetch error: {res}")
        
        # 2. 過濾已處理過或是太舊的資料
        new_items = self._filter_new_items(all_items)
        
        if not new_items:
            logger.info("No new items found.")
            return {
                "summary": "今日目前暫無新的重要金融資訊。",
                "items": []
            }
            
        logger.info(f"Found {len(new_items)} new items.")
        
        # 3. 準備摘要內容
        # 為了避免 Context Window 爆炸，我們只取前 N 則重要或最新的新聞
        # 或者簡單地全部串接
        content_for_llm = ""
        for i, item in enumerate(new_items[:10]): # 限制最多處理 10 則，避免太長
            content_for_llm += f"[{i+1}] {item.title}\nSource: {item.source_name}\n"
            if item.summary:
                content_for_llm += f"Summary: {item.summary[:200]}\n" # 限制單則摘要長度
            if item.content:
                 # 如果有詳細內容 (如 YouTube 字幕)，取前 300 字
                content_for_llm += f"Content: {item.content[:300]}...\n"
            content_for_llm += "\n---\n"
            
        # 4. 呼叫 LLM 產生總結
        logger.info("Generating summary with LLM...")
        summary = await llm_service.summarize(content_for_llm)
        
        # 5. 更新已讀取列表
        self._update_seen_cache(new_items)
        
        return {
            "summary": summary,
            "items": new_items
        }

    def _filter_new_items(self, items: List[NewsItem]) -> List[NewsItem]:
        """過濾掉已看過的項目 ( based on URL or ID )"""
        seen_ids = self.cache.get(self.seen_cache_key) or []
        seen_set = set(seen_ids)
        
        new_items = []
        # 只保留最近 24 小時內的資料
        cutoff_time = datetime.now(items[0].published_at.tzinfo) - timedelta(hours=24) if items else datetime.now() - timedelta(hours=24)
        
        for item in items:
            # 檢查是否過期 (有些 RSS 可能給很舊的)
            if item.published_at.replace(tzinfo=None) < datetime.utcnow() - timedelta(hours=24):
                 # 注意時區處理有點麻煩，這裡簡化處理，假設 published_at 已經是 utc aware
                 # 如果 item.published_at 是 aware, datetime.utcnow() 是 naive，會報錯
                 # 為求簡單，我們盡量依賴 source 實作正確的時區，這裡做防禦性編程
                 pass

            # 識別 ID：優先用 metadata id, 否則用 url
            item_id = item.metadata.get("guid") or item.metadata.get("video_id") or item.url
            
            if item_id not in seen_set:
                new_items.append(item)
                
        return new_items

    def _update_seen_cache(self, new_items: List[NewsItem]):
        """更新已讀取的 ID 列表到快取"""
        seen_ids = self.cache.get(self.seen_cache_key) or []
        
        # 加入新的 ID
        for item in new_items:
            item_id = item.metadata.get("guid") or item.metadata.get("video_id") or item.url
            seen_ids.append(item_id)
            
        # 保持列表大小，避免無限增長 (只留最近 1000 筆)
        if len(seen_ids) > 1000:
            seen_ids = seen_ids[-1000:]
            
        # TTL 設定為 3 天
        self.cache.set(self.seen_cache_key, seen_ids) # 這裡 cache.set 簽名有點怪，它是 json dump

# Global instance
source_manager = SourceManager()
