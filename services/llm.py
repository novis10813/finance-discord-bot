"""
LLM 服務模組
負責與 OpenRouter API 互動，進行文字摘要
"""
import os
import openai
from typing import Optional
from utils.logger import setup_logger
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

logger = setup_logger("services.llm")

class LLMService:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not set. LLM service will not work.")
            self.client = None
        else:
            self.client = openai.AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )

    async def summarize(self, content: str, prompt_template: str = None) -> str:
        """
        生成摘要
        
        Args:
            content: 要摘要的原始文本
            prompt_template: 可選的自定義提示詞
            
        Returns:
            str: 摘要結果
        """
        if not self.client:
            return "⚠️ LLM 服務未設定 API Key，無法產生摘要。"

        if not content:
            return ""

        # 預設提示詞
        if not prompt_template:
            prompt_template = (
                "請將以下金融資訊進行重點摘要，使用繁體中文回答。\n"
                "重點在於市場趨勢、關鍵數據和未來的影響。\n"
                "請使用條列式呈現，保持簡潔。\n\n"
                "內容如下：\n{content}"
            )
            
        prompt = prompt_template.format(content=content)
        
        try:
            # 限制內容長度以免爆 token (簡單截斷)
            # 視模型而定，通常 10k-20k chars 是安全的起始值
            if len(prompt) > 20000:
                prompt = prompt[:20000] + "\n...(內容過長已截斷)"

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一個專業的金融市場分析師，擅長從雜亂的資訊中提取關鍵的市場洞察。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM Summarization failed: {e}")
            return f"⚠️ 摘要生成失敗: {str(e)}"

# Global instance
llm_service = LLMService()
