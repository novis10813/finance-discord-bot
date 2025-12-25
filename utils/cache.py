"""
快取工具模組
提供簡單的檔案快取機制，減少重複的 API 呼叫
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from utils.logger import setup_logger

logger = setup_logger("utils.cache")

# 預設設定
DEFAULT_CACHE_DIR = "data/cache"
DEFAULT_TTL_SECONDS = 3600  # 1 小時

# 台灣時區
TW_TZ = timezone(timedelta(hours=8))


class DataCache:
    """資料快取類別"""
    
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        """
        初始化快取
        
        Args:
            cache_dir: 快取目錄路徑
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """確保快取目錄存在"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_path(self, key: str) -> Path:
        """取得快取檔案路徑"""
        # 清理 key 中的非法字元
        safe_key = "".join(c if c.isalnum() or c in "_-" else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"
    
    def _is_today(self, date_str: str) -> bool:
        """檢查日期是否為今天"""
        today = datetime.now(TW_TZ).strftime("%Y%m%d")
        return date_str == today
    
    def get(self, key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Optional[Dict[str, Any]]:
        """
        取得快取資料
        
        Args:
            key: 快取鍵值（如 "BFI82U_20251224"）
            ttl_seconds: 快取有效期（秒）
            
        Returns:
            Dict: 快取資料，如果快取不存在或已過期則回傳 None
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                
            cached_at = datetime.fromisoformat(cache_data.get("cached_at", ""))
            data = cache_data.get("data")
            date_str = cache_data.get("date_str", "")
            
            # 判斷是否過期
            # 規則：如果是今天的資料，則使用 TTL 檢查；否則永不過期
            if self._is_today(date_str):
                now = datetime.now(TW_TZ)
                if (now - cached_at.replace(tzinfo=TW_TZ)).total_seconds() > ttl_seconds:
                    logger.debug(f"快取已過期: {key}")
                    return None
            
            logger.debug(f"命中快取: {key}")
            return data
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"讀取快取失敗: {key} - {e}")
            return None
    
    def set(self, key: str, data: Dict[str, Any], date_str: str = "") -> bool:
        """
        設定快取資料
        
        Args:
            key: 快取鍵值
            data: 要快取的資料
            date_str: 資料對應的日期（YYYYMMDD）
            
        Returns:
            bool: 是否成功
        """
        cache_path = self._get_cache_path(key)
        
        try:
            cache_data = {
                "data": data,
                "date_str": date_str,
                "cached_at": datetime.now(TW_TZ).isoformat()
            }
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"已快取: {key}")
            return True
            
        except Exception as e:
            logger.error(f"寫入快取失敗: {key} - {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """刪除快取"""
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"已刪除快取: {key}")
            return True
        return False
    
    def clear(self) -> int:
        """清除所有快取，回傳清除的數量"""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        logger.info(f"已清除 {count} 個快取檔案")
        return count


# 全域快取實例
_cache: Optional[DataCache] = None


def get_cache() -> DataCache:
    """取得快取實例（單例模式）"""
    global _cache
    if _cache is None:
        _cache = DataCache()
    return _cache
