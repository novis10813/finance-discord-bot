"""
TWSE API Service
Handles calls to the twse-api microservice
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from utils.logger import setup_logger
from config import TWSE_API_URL

logger = setup_logger("services.twse")

# Taiwan timezone
TW_TZ = timezone(timedelta(hours=8))


class TWSEServiceError(Exception):
    """TWSE Service Error"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class TWSEService:
    """TWSE API Service Client"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or TWSE_API_URL
        self.timeout = 30.0
    
    def _get_today_date(self) -> str:
        """Get today's date in YYYYMMDD format"""
        return datetime.now(TW_TZ).strftime("%Y%m%d")
    
    async def get_chip_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        取得三大法人買賣金額統計
        
        Args:
            date_str: 日期 (YYYYMMDD)，預設今日
        
        Returns:
            Dict: 籌碼統計資料
        """
        if not date_str:
            date_str = self._get_today_date()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/chip/summary",
                    params={"date": date_str}
                )
                
                if resp.status_code == 404:
                    logger.warning(f"No data available for date: {date_str}")
                    return None
                
                resp.raise_for_status()
                return resp.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            raise TWSEServiceError(f"HTTP error: {e.response.status_code}", e.response.status_code)
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise TWSEServiceError(str(e))
    
    async def get_stock_chip_list(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        取得個股三大法人買賣超列表
        
        Args:
            date_str: 日期 (YYYYMMDD)
        
        Returns:
            Dict: 個股籌碼列表
        """
        if not date_str:
            date_str = self._get_today_date()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/chip/stocks",
                    params={"date": date_str}
                )
                
                if resp.status_code == 404:
                    logger.warning(f"No stock data available for date: {date_str}")
                    return None
                
                resp.raise_for_status()
                return resp.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            raise TWSEServiceError(f"HTTP error: {e.response.status_code}", e.response.status_code)
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise TWSEServiceError(str(e))
    
    async def get_stock_chip_detail(self, code: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        取得個股籌碼詳情
        
        Args:
            code: 股票代碼
            date_str: 日期 (YYYYMMDD)
        
        Returns:
            Dict: 個股籌碼詳情
        """
        if not date_str:
            date_str = self._get_today_date()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/chip/stock/{code}",
                    params={"date": date_str}
                )
                
                if resp.status_code == 404:
                    logger.warning(f"Stock {code} not found for date: {date_str}")
                    return None
                
                resp.raise_for_status()
                return resp.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            raise TWSEServiceError(f"HTTP error: {e.response.status_code}", e.response.status_code)
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise TWSEServiceError(str(e))


# Singleton instance
_twse_service: Optional[TWSEService] = None


def get_twse_service() -> TWSEService:
    """Get TWSE service instance (singleton)"""
    global _twse_service
    if _twse_service is None:
        _twse_service = TWSEService()
    return _twse_service
