"""
Prompt Service
載入和管理各來源的 prompt 設定
"""
from pathlib import Path
from typing import Dict, Optional
import yaml

from utils.logger import setup_logger

logger = setup_logger("services.prompt")

# 預設 prompt
DEFAULT_PROMPTS = {
    "system": "你是一位財經分析師。請用繁體中文摘要以下內容。",
    "user": "請摘要以下內容：\n\n{content}"
}


class PromptService:
    """Prompt 設定管理服務"""
    
    def __init__(self, config_path: str = None):
        """
        初始化 Prompt 服務
        
        Args:
            config_path: prompts.yaml 檔案路徑
        """
        self.config_path = Path(config_path or "prompts.yaml")
        self.prompts: Dict[str, Dict[str, str]] = {}
        self._load()
    
    def _load(self) -> None:
        """載入 prompts.yaml"""
        if not self.config_path.exists():
            logger.warning(f"Prompts file not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            self.prompts = data.get("prompts", {})
            logger.info(f"Loaded {len(self.prompts)} prompt configurations")
            
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
    
    def get_prompts(self, source_name: str) -> Dict[str, str]:
        """
        取得特定來源的 prompt 設定
        
        Args:
            source_name: 來源名稱
            
        Returns:
            包含 'system' 和 'user' 的 dict
        """
        # 優先使用來源專用的 prompt
        if source_name in self.prompts:
            return self.prompts[source_name]
        
        # 使用預設 prompt
        if "_default" in self.prompts:
            return self.prompts["_default"]
        
        return DEFAULT_PROMPTS
    
    def format_user_prompt(self, source_name: str, content: str) -> str:
        """
        格式化 user prompt，將 {content} 替換為實際內容
        
        Args:
            source_name: 來源名稱
            content: 要摘要的內容
            
        Returns:
            格式化後的 user prompt
        """
        prompts = self.get_prompts(source_name)
        user_template = prompts.get("user", DEFAULT_PROMPTS["user"])
        return user_template.format(content=content)
    
    def reload(self) -> None:
        """重新載入設定"""
        self._load()


# Singleton instance
_prompt_service: Optional[PromptService] = None


def get_prompt_service() -> PromptService:
    """取得 Prompt 服務實例 (singleton)"""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service
