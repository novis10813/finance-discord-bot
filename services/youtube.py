"""
YouTube Service
Handles calls to the youtube-transcript-api microservice
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from utils.logger import setup_logger
from config import YOUTUBE_SOURCE_ENDPOINT

logger = setup_logger("services.youtube")

class YouTubeServiceError(Exception):
    """YouTube Service Error"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class YouTubeService:
    """YouTube API Service Client"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or YOUTUBE_SOURCE_ENDPOINT
        self.timeout = 30.0
    
    async def get_latest_video(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest live stream video from a channel
        
        Args:
            channel_id: Channel ID (starts with UC)
        
        Returns:
            Dict: Video information or None if not found
        
        Note:
            Filters for videos with titles starting with YYYY/MM/DD pattern (live streams)
        """
        import re
        date_pattern = re.compile(r'^\d{4}/\d{2}/\d{2}')
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Fetch more videos to find a live stream
                resp = await client.get(
                    f"{self.base_url}/api/v1/channel/{channel_id}/videos",
                    params={"limit": 10, "content_type": "streams"}
                )
                
                resp.raise_for_status()
                data = resp.json()
                
                if not data.get("success") or not data.get("videos"):
                    return None
                
                # Filter for live streams (title starts with YYYY/MM/DD)
                for video in data["videos"]:
                    title = video.get("title", "")
                    if date_pattern.match(title):
                        logger.info(f"Found live stream: {title}")
                        return video
                
                logger.warning("No live stream found in recent videos")
                return None
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            raise YouTubeServiceError(f"HTTP error: {e.response.status_code}", e.response.status_code)
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise YouTubeServiceError(str(e))


    async def get_video_transcript(self, video_id: str) -> Optional[str]:
        """
        Get video transcript text
        
        Args:
            video_id: YouTube Video ID
        
        Returns:
            str: Full transcript text or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Use the text endpoint to get formatted text directly
                resp = await client.post(
                    f"{self.base_url}/api/v1/transcript/text",
                    json={"youtube_url": f"https://www.youtube.com/watch?v={video_id}"}
                )
                
                resp.raise_for_status()
                data = resp.json()
                
                if not data.get("success"):
                    return None
                    
                return data.get("text")
                
        except httpx.HTTPStatusError as e:
            # Handle transcript not found or disabled specifically if needed
            logger.error(f"HTTP error fetching transcript: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise YouTubeServiceError(str(e))

# Singleton instance
_youtube_service: Optional[YouTubeService] = None

def get_youtube_service() -> YouTubeService:
    """Get YouTube service instance (singleton)"""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service
