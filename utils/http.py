"""
HTTP 工具模組
提供帶有重試機制和錯誤處理的 HTTP 請求功能
"""
import httpx
import asyncio
from typing import Optional, Dict, Any
from functools import wraps

from utils.logger import setup_logger

logger = setup_logger("utils.http")

# 預設設定
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # 初始延遲秒數
DEFAULT_MAX_DELAY = 10.0  # 最大延遲秒數


class HTTPError(Exception):
    """HTTP 請求錯誤"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class APIError(Exception):
    """API 回傳錯誤（stat != OK）"""
    def __init__(self, message: str, stat: Optional[str] = None):
        self.message = message
        self.stat = stat
        super().__init__(self.message)


async def fetch_json(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    verify_ssl: bool = False,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    發送 HTTP GET 請求並回傳 JSON 資料，帶有指數退避重試機制
    
    Args:
        url: 請求 URL
        timeout: 請求逾時秒數
        max_retries: 最大重試次數
        base_delay: 初始延遲秒數
        max_delay: 最大延遲秒數
        verify_ssl: 是否驗證 SSL 證書
        headers: 額外的 HTTP 標頭
        
    Returns:
        Dict: JSON 回應資料
        
    Raises:
        HTTPError: HTTP 請求失敗
        APIError: API 回傳錯誤狀態
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # 驗證 TWSE API 回應格式
                if "stat" in data and data.get("stat") != "OK":
                    raise APIError(
                        f"API 回傳錯誤狀態: {data.get('stat')}",
                        stat=data.get("stat")
                    )
                
                return data
                
        except httpx.TimeoutException as e:
            last_exception = HTTPError(f"請求逾時: {url}")
            logger.warning(f"請求逾時 (嘗試 {attempt + 1}/{max_retries}): {url}")
            
        except httpx.HTTPStatusError as e:
            last_exception = HTTPError(
                f"HTTP 錯誤: {e.response.status_code}",
                status_code=e.response.status_code
            )
            logger.warning(f"HTTP 錯誤 {e.response.status_code} (嘗試 {attempt + 1}/{max_retries}): {url}")
            
        except httpx.RequestError as e:
            last_exception = HTTPError(f"請求錯誤: {str(e)}")
            logger.warning(f"請求錯誤 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
            
        except APIError as e:
            # API 錯誤不重試（通常是資料問題，不是網路問題）
            raise e
            
        except Exception as e:
            last_exception = HTTPError(f"未知錯誤: {str(e)}")
            logger.warning(f"未知錯誤 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
        
        # 計算延遲時間（指數退避）
        if attempt < max_retries - 1:
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.info(f"將在 {delay:.1f} 秒後重試...")
            await asyncio.sleep(delay)
    
    # 所有重試都失敗
    logger.error(f"請求失敗，已達最大重試次數 ({max_retries}): {url}")
    raise last_exception or HTTPError("請求失敗")


async def fetch_twse_data(
    endpoint: str,
    params: Dict[str, str],
    use_rwd: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    專門用於 TWSE API 的請求函數
    
    Args:
        endpoint: API 端點名稱（如 "BFI82U", "T86"）
        params: 查詢參數
        use_rwd: 是否使用 RWD 端點（支援歷史資料，使用 date 參數）
        **kwargs: 傳遞給 fetch_json 的額外參數
        
    Returns:
        Dict: API 回應資料
    """
    # 根據 use_rwd 選擇端點
    if use_rwd:
        # RWD 端點：支援歷史資料，使用 date 參數
        base_url = "https://www.twse.com.tw/rwd/zh/fund"
    else:
        # 舊端點：使用 dayDate 參數
        base_url = "https://www.twse.com.tw/fund"
    
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{base_url}/{endpoint}?response=json&{param_str}"
    
    return await fetch_json(url, **kwargs)
