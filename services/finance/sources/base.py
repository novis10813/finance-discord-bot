"""
金融資訊來源基礎類別
定義所有資料來源必須實作的介面
"""
import abc
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class NewsItem:
    """單則金融新聞/資訊"""
    title: str
    url: str
    source_name: str
    published_at: datetime
    summary: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_markdown(self) -> str:
        """轉換為 Markdown 格式"""
        date_str = self.published_at.strftime("%Y-%m-%d %H:%M")
        md = f"**[{self.source_name}] {self.title}**\n"
        md += f"🕒 {date_str} | [連結]({self.url})\n"
        if self.summary:
            md += f"> {self.summary}\n"
        return md


class FinancialSource(abc.ABC):
    """金融資訊來源抽象基類"""
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """來源名稱"""
        pass

    @abc.abstractmethod
    async def fetch_data(self) -> List[NewsItem]:
        """
        抓取最新資料
        
        Returns:
            List[NewsItem]: 新聞項目列表
        """
        pass
