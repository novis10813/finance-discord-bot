"""
Admin Cog - Dynamic Cog Management
Allows bot owner to load/unload/reload cogs via Discord commands.
"""
from discord.ext import commands

from config import OWNER_ID
from utils.logger import setup_logger

logger = setup_logger("cogs.admin")


class Admin(commands.Cog):
    """Bot 管理功能 - 動態載入/卸載模組"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_check(self, ctx: commands.Context) -> bool:
        """只允許 Bot 擁有者使用管理指令"""
        if OWNER_ID == 0:
            logger.warning("OWNER_ID 未設定，管理指令已禁用")
            return False
        return ctx.author.id == OWNER_ID

    @commands.command(name="cogs")
    async def list_cogs(self, ctx: commands.Context):
        """列出已載入的 Cogs"""
        loaded = list(self.bot.extensions.keys())
        if loaded:
            cog_list = "\n".join(f"• `{cog}`" for cog in sorted(loaded))
            await ctx.send(f"📦 **已載入的模組：**\n{cog_list}")
        else:
            await ctx.send("📦 目前沒有載入任何模組")

    @commands.command(name="load")
    async def load_cog(self, ctx: commands.Context, cog: str):
        """載入 Cog: !load finance"""
        cog_name = f"cogs.{cog}"
        try:
            await self.bot.load_extension(cog_name)
            await ctx.send(f"✅ 已載入 `{cog_name}`")
            logger.info(f"Cog loaded: {cog_name} (by {ctx.author})")
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"⚠️ `{cog_name}` 已經載入")
        except commands.ExtensionNotFound:
            await ctx.send(f"❌ 找不到 `{cog_name}`")
        except Exception as e:
            await ctx.send(f"❌ 載入失敗: {e}")
            logger.error(f"Failed to load {cog_name}: {e}")

    @commands.command(name="unload")
    async def unload_cog(self, ctx: commands.Context, cog: str):
        """卸載 Cog: !unload finance"""
        cog_name = f"cogs.{cog}"

        # 防呆：禁止卸載 Admin Cog
        if cog == "admin":
            await ctx.send("❌ 無法卸載 Admin 模組")
            return

        try:
            await self.bot.unload_extension(cog_name)
            await ctx.send(f"✅ 已卸載 `{cog_name}`")
            logger.info(f"Cog unloaded: {cog_name} (by {ctx.author})")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"⚠️ `{cog_name}` 未載入")
        except Exception as e:
            await ctx.send(f"❌ 卸載失敗: {e}")
            logger.error(f"Failed to unload {cog_name}: {e}")

    @commands.command(name="reload")
    async def reload_cog(self, ctx: commands.Context, cog: str):
        """重新載入 Cog: !reload finance"""
        cog_name = f"cogs.{cog}"
        try:
            await self.bot.reload_extension(cog_name)
            await ctx.send(f"✅ 已重新載入 `{cog_name}`")
            logger.info(f"Cog reloaded: {cog_name} (by {ctx.author})")
        except commands.ExtensionNotLoaded:
            # 如果尚未載入，嘗試載入
            try:
                await self.bot.load_extension(cog_name)
                await ctx.send(f"✅ 已載入 `{cog_name}` (原本未載入)")
                logger.info(f"Cog loaded (via reload): {cog_name} (by {ctx.author})")
            except Exception as e:
                await ctx.send(f"❌ 載入失敗: {e}")
                logger.error(f"Failed to load {cog_name}: {e}")
        except Exception as e:
            await ctx.send(f"❌ 重載失敗: {e}")
            logger.error(f"Failed to reload {cog_name}: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
