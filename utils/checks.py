"""
Discord.py 指令檢查工具
提供可重用的指令檢查函數
"""
import discord
from discord.ext import commands

from config import CHIP_ALLOWED_CHANNELS
from utils.logger import setup_logger

logger = setup_logger("utils.checks")


def is_chip_channel():
    """
    檢查指令是否在允許的籌碼分析頻道中執行
    
    Returns:
        commands.check: Discord.py check 裝飾器
    """
    async def predicate(ctx: commands.Context) -> bool:
        # 如果未設定限制，允許所有頻道
        if not CHIP_ALLOWED_CHANNELS:
            return True
        
        # DM 頻道不允許使用
        if isinstance(ctx.channel, discord.DMChannel):
            logger.debug(f"籌碼指令在 DM 中被拒絕: {ctx.author}")
            return False
        
        # 檢查頻道 ID 是否在允許清單中
        is_allowed = ctx.channel.id in CHIP_ALLOWED_CHANNELS
        
        if not is_allowed:
            logger.debug(
                f"籌碼指令在未授權頻道被拒絕: "
                f"頻道={ctx.channel.name} ({ctx.channel.id}), "
                f"使用者={ctx.author}"
            )
        
        return is_allowed
    
    return commands.check(predicate)
