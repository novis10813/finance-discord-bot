"""
Admin Cog - External Cog Management
允許 Bot 擁有者透過 Discord 指令 load/unload/reload 外部 Cogs（external_cogs/）。
內建 Cogs（cogs/）不可被卸載或重載。
"""
from pathlib import Path

from discord.ext import commands

from config import OWNER_ID, EXTERNAL_COGS_DIR
from utils.logger import setup_logger

logger = setup_logger("cogs.admin")

# 內建 Cogs 前綴（不可被 !unload / !reload 操作）
_BUILTIN_PREFIX = "cogs."


class Admin(commands.Cog):
    """Bot 管理功能 - 動態管理外部插件模組"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._ext_prefix = Path(EXTERNAL_COGS_DIR).name + "."  # e.g. "external_cogs."

    def cog_check(self, ctx: commands.Context) -> bool:
        """只允許 Bot 擁有者使用管理指令"""
        if OWNER_ID == 0:
            logger.warning("OWNER_ID 未設定，管理指令已禁用")
            return False
        return ctx.author.id == OWNER_ID

    def _is_external(self, cog_name: str) -> bool:
        return cog_name.startswith(self._ext_prefix)

    def _full_ext_name(self, cog: str) -> str:
        """將簡短名稱轉換為完整 external_cogs extension 名稱"""
        prefix = self._ext_prefix  # e.g. "external_cogs."
        if cog.startswith(prefix):
            return cog
        return f"{prefix}{cog}"

    @commands.command(name="cogs")
    async def list_cogs(self, ctx: commands.Context):
        """列出已載入的 Cogs（區分內建 / 外部）"""
        loaded = sorted(self.bot.extensions.keys())
        builtin = [c for c in loaded if c.startswith(_BUILTIN_PREFIX)]
        external = [c for c in loaded if self._is_external(c)]
        other = [c for c in loaded if c not in builtin and c not in external]

        lines = []
        if builtin:
            lines.append("**📦 內建 Cogs：**")
            lines.extend(f"  • `{c}`" for c in builtin)
        if external:
            lines.append("**🔌 外部 Cogs（external_cogs）：**")
            lines.extend(f"  • `{c}`" for c in external)
        if other:
            lines.append("**🔧 其他：**")
            lines.extend(f"  • `{c}`" for c in other)

        await ctx.send("\n".join(lines) if lines else "📦 目前沒有載入任何模組")

    @commands.command(name="load")
    async def load_cog(self, ctx: commands.Context, cog: str):
        """載入外部 Cog: !load chip"""
        cog_name = self._full_ext_name(cog)
        try:
            await self.bot.load_extension(cog_name)
            self.bot.register_ai_tools()
            await ctx.send(f"✅ 已載入 `{cog_name}`")
            logger.info(f"External Cog loaded: {cog_name} (by {ctx.author})")
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"⚠️ `{cog_name}` 已經載入")
        except commands.ExtensionNotFound:
            await ctx.send(f"❌ 找不到 `{cog_name}`")
        except Exception as e:
            await ctx.send(f"❌ 載入失敗: {e}")
            logger.error(f"Failed to load {cog_name}: {e}")

    @commands.command(name="unload")
    async def unload_cog(self, ctx: commands.Context, cog: str):
        """卸載外部 Cog: !unload chip"""
        cog_name = self._full_ext_name(cog)

        if not self._is_external(cog_name):
            await ctx.send("❌ 無法卸載內建 Cog")
            return

        try:
            await self.bot.unload_extension(cog_name)
            self.bot.register_ai_tools()
            await ctx.send(f"✅ 已卸載 `{cog_name}`")
            logger.info(f"External Cog unloaded: {cog_name} (by {ctx.author})")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"⚠️ `{cog_name}` 未載入")
        except Exception as e:
            await ctx.send(f"❌ 卸載失敗: {e}")
            logger.error(f"Failed to unload {cog_name}: {e}")

    @commands.command(name="reload")
    async def reload_cog(self, ctx: commands.Context, cog: str):
        """重新載入外部 Cog: !reload chip"""
        cog_name = self._full_ext_name(cog)

        if not self._is_external(cog_name):
            await ctx.send("❌ 無法重載內建 Cog")
            return

        try:
            await self.bot.reload_extension(cog_name)
            self.bot.register_ai_tools()
            await ctx.send(f"✅ 已重新載入 `{cog_name}`")
            logger.info(f"External Cog reloaded: {cog_name} (by {ctx.author})")
        except commands.ExtensionNotLoaded:
            # 尚未載入，嘗試直接載入
            try:
                await self.bot.load_extension(cog_name)
                self.bot.register_ai_tools()
                await ctx.send(f"✅ 已載入 `{cog_name}` (原本未載入)")
                logger.info(f"External Cog loaded via reload: {cog_name} (by {ctx.author})")
            except Exception as e:
                await ctx.send(f"❌ 載入失敗: {e}")
                logger.error(f"Failed to load {cog_name}: {e}")
        except Exception as e:
            await ctx.send(f"❌ 重載失敗: {e}")
            logger.error(f"Failed to reload {cog_name}: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
