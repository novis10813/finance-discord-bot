"""
MOPS API Service
Handles calls to the mops-financial-api microservice
"""
import httpx
from typing import Optional, List, Union
import logging

from config import MOPS_API_URL

logger = logging.getLogger("services.mops")


class MOPSServiceError(Exception):
    """MOPS Service Error"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class MOPSService:
    """MOPS API Service Client"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or MOPS_API_URL
        self.timeout = 300.0  # 5 minutes - MOPS calls can be very slow for multi-year data
    
    async def get_comparison_chart(
        self, 
        stock_ids: List[str], 
        metric: str = "ROE", 
        years: int = 5
    ) -> Optional[bytes]:
        """
        Get comparison chart image bytes
        """
        stocks_str = ",".join(stock_ids)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/analysis/chart/compare",
                    params={
                        "stocks": stocks_str,
                        "metric": metric,
                        "years": years
                    }
                )
                
                if resp.status_code == 404:
                    logger.warning(f"No data found for stocks: {stocks_str}")
                    return None
                
                resp.raise_for_status()
                return resp.content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise MOPSServiceError(f"API Error: {e.response.status_code}", e.response.status_code)
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise MOPSServiceError(str(e))


# Singleton
_mops_service: Optional[MOPSService] = None

def get_mops_service() -> MOPSService:
    global _mops_service
    if _mops_service is None:
        _mops_service = MOPSService()
    return _mops_service
