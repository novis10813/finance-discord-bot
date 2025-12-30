"""
SourceItem Schema
統一的資料來源項目格式，用於接收 source-aggregator 的 webhook
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """資料來源類型"""
    RSS = "rss"
    YOUTUBE = "youtube"


class SourceItem(BaseModel):
    """
    統一的資料項目格式
    接收自 source-aggregator 的 webhook payload
    """
    id: str = Field(..., description="唯一識別碼")
    source_type: SourceType = Field(..., description="來源類型")
    source_name: str = Field(..., description="來源名稱")
    title: str = Field(..., description="標題")
    content: str = Field(..., description="原始內容")
    url: str = Field(..., description="原始連結")
    published_at: datetime = Field(..., description="發布時間")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外資訊")
