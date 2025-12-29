"""
RSS 資料來源實作
"""
import asyncio
import feedparser
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from email.utils import parsedate_to_datetime

from services.finance.sources.base import FinancialSource, NewsItem
from utils.logger import setup_logger
from utils.http import fetch_json

logger = setup_logger("services.finance.sources.rss")

class RSSSource(FinancialSource):
    """RSS 新聞來源"""
    
    def __init__(self, name: str, feed_urls: List[str]):
        self._name = name
        self.feed_urls = feed_urls
        # 快取 (簡單的記憶體快取，避免短時間重複解析)
        # 實際應用可能依賴外部快取或直接每次抓取
        
    @property
    def name(self) -> str:
        return self._name

    async def fetch_data(self) -> List[NewsItem]:
        """抓取所有設定的 RSS feed"""
        all_items: List[NewsItem] = []
        
        # 並行抓取所有 feed
        tasks = [self._fetch_single_feed(url) for url in self.feed_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"RSS fetch error: {result}")
                
        # 依時間排序 (新到舊)
        all_items.sort(key=lambda x: x.published_at, reverse=True)
        return all_items

    async def _fetch_single_feed(self, url: str) -> List[NewsItem]:
        """抓取單個 RSS feed"""
        logger.info(f"Fetching RSS: {url}")
        try:
            # feedparser 雖然是同步的，但通常很快。
            # 若需非阻塞，可跑在 executor 中 (如果是大型 feed)
            # 這裡我們用 run_in_executor 確保不卡住 loop
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            
            if feed.bozo:
                logger.warning(f"RSS path error for {url}: {feed.bozo_exception}")
                # 有些 bozo exception 只是編碼警告，仍可能有資料
                
            items: List[NewsItem] = []
            for entry in feed.entries:
                # 處理發布時間
                published_at = datetime.now(timezone.utc)
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    # struct_time to datetime
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    
                item = NewsItem(
                    title=entry.title,
                    url=entry.link,
                    source_name=f"{self.name}", # 或是 entry.get('source', {}).get('title', self.name)
                    published_at=published_at,
                    summary=self._clean_summary(entry.get("summary", "") or entry.get("description", "")),
                    content=None, # RSS 通常只給摘要
                    metadata={"guid": entry.get("id", entry.link)}
                )
                items.append(item)
                
            logger.info(f"Fetched {len(items)} items from {url}")
            return items
            
        except Exception as e:
            logger.error(f"Failed to fetch RSS {url}: {e}")
            raise

    def _clean_summary(self, summary: str) -> str:
        """清理摘要文字 (移除 HTML tags 等)"""
        # 簡單移除 HTML tags，可改用 BeautifulSoup
        import re
        clean = re.sub('<[^<]+?>', '', summary)
        return clean.strip()

# Factory function for Common configurations
def create_street_insider_source() -> RSSSource:
    return RSSSource(
        name="StreetInsider",
        feed_urls=[
            # FED / Economics
            "https://www.streetinsider.com/rss/feed.php?type=cat&id=55", # Fed
            # Cryptocurrency
            "https://www.streetinsider.com/cryptocurrency/feed/"
        ]
    )
