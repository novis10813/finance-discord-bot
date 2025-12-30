"""
LLM Service
Handles calls to OpenRouter API (OpenAI compatible)
"""
from openai import AsyncOpenAI
from typing import Optional

from utils.logger import setup_logger
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

logger = setup_logger("services.llm")

class LLMService:
    """LLM Service Client"""
    
    def __init__(self):
        if not OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY is not set")
            
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        self.model = OPENROUTER_MODEL
        
    async def generate_summary(
        self, 
        text: str, 
        system_prompt: str,
        user_prompt: str = None
    ) -> Optional[str]:
        """
        Generate summary using LLM
        
        Args:
            text: Input text to summarize
            system_prompt: System prompt for the LLM
            user_prompt: Optional custom user prompt. If not provided, uses default.
            
        Returns:
            str: Generated summary
        """
        if not text:
            return None
            
        try:
            logger.info(f"Generating summary with model: {self.model}")
            
            # 如果沒有提供自定義 user prompt，使用預設的
            if user_prompt is None:
                user_prompt = f"""請你幫我整理以下文字的重點，整個過程可以分為以下幾個重點： 

## 辨識核心主題與架構

### 核心主題提煉

- **以經濟基本指標定義標題：**
	- 請找出文章中涵蓋了核心觀點的幾個**涉及經濟基本面**的**主要「大分類」或「核心主題」** 。
    - 此標題需**力求精煉**，限制在 10 個字以內，必須和文章中提到的特定市場情況有關。
    - 請以 Markdown 二級標題**做為每一個段落的標題**。

### 子主題歸納

- **找出核心主題下的相關論述：**
    - 在提煉出多個核心主題後，請找出文章中**能涵蓋核心主題**的論述。
    - 請為每個核心主題設定一個清晰的 Markdown 三級標題。
    - 在每個子主題標題下方，**使用 bullet points 和粗體先列出簡短一句話**，並在**縮排後使用 bullet points 條列出與該主題相關的關鍵資訊**。
    - **bullet point 最多縮排一次**。

## 提取關鍵資訊與數據 

### 抓出關鍵的「人、事、時、地、物」和「因果關係」

- **抓重點：** 
	- 提到投資策略，抓出「早期策略 vs. 現在策略」的轉變
	- 提煉出那句最經典的核心想法。 
- **抓數據：** 
	- 看到股市表現，記下具體的指數漲跌幅、本益比、日期等硬數據。 
- **抓因果：** 
	- 特別注意「因為...所以...」的邏輯。
	- 例如，因為「美元貶值」，所以「美國科技巨頭有匯兌收益」
	- 因為「台幣強升」，所以「台灣出口商壓力巨大」。 

## 精煉語言與歸納 

### 整理「線索」和「資訊」

- **移除贅詞：**
	- 過濾掉口語中的贅詞、重複的語句和感嘆詞（例如「哦」、「對不對」、「哎」），讓內容更精簡。 
- **重新組織：** 
	- 將零散的資訊點，用**更有邏輯、更易讀的方式**重新組織起來。 
- **精準下標：** 
	- 為每一個段落下一個一目了然的標題，快速抓住重點。

### 輸出格式梳理

- **只輸出必要文字：**
	- 不必有你的回應或是思考內容。
- 使用 Markdown 二級標題作為核心主題標題。
- 使用 Markdown 三級標題作為子主題標題。
- 每個子主題下先用粗體列出一句話重點，再用 bullet points 條列關鍵資訊。

{text}"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],

                temperature=0,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None

# Singleton instance
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get LLM service instance (singleton)"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
