"""
YouTube 字幕資料來源實作
使用自定義的 YTtranscript API 獲取字幕
"""
import asyncio
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from config import YOUTUBE_SOURCE_ENDPOINT, YOUTUBE_SOURCE_API_KEY
from services.finance.sources.base import FinancialSource, NewsItem
from utils.logger import setup_logger

logger = setup_logger("services.finance.sources.youtube")

class YouTubeSource(FinancialSource):
    """YouTube 字幕來源"""
    
    def __init__(self, name: str, channels: List[Dict[str, str]]):
        """
        Args:
            name: 來源名稱
            channels: 頻道列表，格式 [{"id": "CHANNEL_ID", "name": "頻道名稱"}]
        """
        self._name = name
        self.channels = channels
        self.endpoint = YOUTUBE_SOURCE_ENDPOINT
        
    @property
    def name(self) -> str:
        return self._name

    async def fetch_data(self) -> List[NewsItem]:
        """
        流程：
        1. 透過 RSS 監控頻道是否有新影片
        2. 若有新影片，呼叫 Transcript API 獲取字幕
        3. 回傳 NewsItem
        """
        if not self.endpoint:
            logger.warning("YouTube Endpoint not configured, skipping.")
            return []

        all_items: List[NewsItem] = []
        
        # 1. 取得最近影片列表
        video_tasks = [self._get_latest_videos(ch["id"], ch["name"]) for ch in self.channels]
        channel_results = await asyncio.gather(*video_tasks, return_exceptions=True)
        
        videos_to_process = []
        for res in channel_results:
            if isinstance(res, list):
                videos_to_process.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Error fetching channel videos: {res}")
                
        # 2. 針對每個影片抓取字幕 (並發限制，避免打爆 API)
        # 這裡假設我們要抓取最近 N 小時內的影片，或者就全部抓回來交給 Manager 去重
        # Manager 負責去重，所以這裡我們只管抓
        
        # 限制並發數
        semaphore = asyncio.Semaphore(3)
        
        async def process_video(video: Dict):
            async with semaphore:
                return await self._fetch_transcript_and_create_item(video)

        transcript_tasks = [process_video(v) for v in videos_to_process]
        transcript_results = await asyncio.gather(*transcript_tasks, return_exceptions=True)
        
        for item in transcript_results:
            if isinstance(item, NewsItem):
                all_items.append(item)
            elif isinstance(item, Exception):
                # 字幕獲取失敗是常見的 (例如無字幕)，紀錄為 Warning 即可
                logger.warning(f"Failed to get transcript: {item}")
                
        return all_items

    async def _get_latest_videos(self, channel_id: str, channel_name: str) -> List[Dict]:
        """從 YouTube RSS 取得該頻道最新影片"""
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        import feedparser
        
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, rss_url)
        
        videos = []
        for entry in feed.entries: # 通常 RSS 只會有最新的 15 部
            # entry.link 格式通常是 https://www.youtube.com/watch?v=VIDEO_ID
            # entry.published / entry.published_parsed
            published_at = datetime.now(timezone.utc)
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                
            videos.append({
                "video_id": entry.yt_videoid,
                "title": entry.title,
                "url": entry.link,
                "published_at": published_at,
                "channel_name": channel_name
            })
        return videos

    async def _fetch_transcript_and_create_item(self, video: Dict) -> Optional[NewsItem]:
        """呼叫自定義 API 獲取字幕"""
        url = f"{self.endpoint}/api/v1/transcript/text"
        payload = {
            "youtube_url": video["url"],
            "language": "zh-TW"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                
                if not data.get("success"):
                    logger.warning(f"Transcript API failed for {video['url']}: {data.get('message')}")
                    return None
                    
                transcript_text = data.get("text", "")
                if not transcript_text:
                    return None
                    
                # 建立 NewsItem
                # 因為字幕可能很長，我們把完整字幕放在 content，summary 留空或放前段
                return NewsItem(
                    title=video["title"],
                    url=video["url"],
                    source_name=f"YouTube ({video['channel_name']})",
                    published_at=video["published_at"],
                    summary=transcript_text[:200] + "...", # 預覽
                    content=transcript_text,
                    metadata={"video_id": video["video_id"], "type": "video"}
                )
                
        except Exception as e:
            logger.warning(f"Error calling transcript API for {video['url']}: {e}")
            return None

# Factory
def create_youtube_source() -> YouTubeSource:
    # 範例頻道 (需由使用者提供或配置)
    # 這裡先放入幾個常見的財經頻道 ID 作為測試
    # 比如: FED 相關，或 CNBC 等 (使用者雖說是 YouTube 字幕，但沒給頻道，我們先留空或給個範例)
    # 
    # 此處我們暫時給一個空的列表，等待使用者提供頻道 ID
    # 或者我們可以寫一個簡單的 config 讀取
    # 
    # TODO: 將頻道列表移至設定檔
    return YouTubeSource(
        name="YouTubeFinance",
        channels=[
            # 游庭皓的財經皓角 (ID: UC0lbAQVpenvfA2QqzsRtL_g)
            {"id": "UC0lbAQVpenvfA2QqzsRtL_g", "name": "游庭皓的財經皓角"} 
        ]
    )
