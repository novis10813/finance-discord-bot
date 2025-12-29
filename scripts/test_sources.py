"""
測試金融資訊來源腳本
無法直接測試 Discord Cog，但可測試底層 Service
"""
import asyncio
import sys
import os
from pathlib import Path

# 將專案根目錄加入 Path 以便 import 模組
sys.path.append(str(Path(__file__).parent.parent))

from services.finance.sources.rss import create_street_insider_source
from services.finance.sources.youtube import create_youtube_source
from services.llm import llm_service
from services.finance.source_manager import source_manager
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

async def test_rss():
    print("--- Testing RSS Source ---")
    rss = create_street_insider_source()
    try:
        items = await rss.fetch_data()
        print(f"Fetched {len(items)} items from RSS.")
        if items:
            print(f"Sample Item: {items[0].title} ({items[0].url})")
            print(f"Time: {items[0].published_at}")
    except Exception as e:
        print(f"RSS Test Failed: {e}")

async def test_youtube():
    print("\n--- Testing YouTube Source ---")
    # 注意：如果沒有配置 Endpoint URL，這裡會失敗或跳過
    yt = create_youtube_source()
    if not yt.endpoint:
        print("YouTube Endpoint not configured in .env, skipping.")
        return

    try:
        print(f"Monitoring channels: {[c['name'] for c in yt.channels]}")
        items = await yt.fetch_data()
        print(f"Fetched {len(items)} items from YouTube.")
        if items:
            print(f"Sample Item: {items[0].title}")
            print(f"Summary Preview: {items[0].summary[:50]}...")
    except Exception as e:
        print(f"YouTube Test Failed: {e}")

async def test_llm():
    print("\n--- Testing LLM Service ---")
    if not llm_service.client:
        print("OpenRouter API Key not configured, skipping LLM test.")
        return
        
    try:
        summary = await llm_service.summarize("Bitcoin price reached $100,000 today due to institutional adoption.")
        print(f"LLM Summary Result: {summary}")
    except Exception as e:
        print(f"LLM Test Failed: {e}")

async def main():
    await test_rss()
    await test_youtube()
    await test_llm()

if __name__ == "__main__":
    asyncio.run(main())
