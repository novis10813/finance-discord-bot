# Pluggable Cogs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 從 `main` 建立 `feat/pluggable-cogs` branch，cherry-pick 熱插拔 cog 架構，手動補上 `load_external_cogs()` 機制，並移除所有 agentic 殘留。

**Architecture:** 內建 cogs（`cogs/`）隨 bot 部署，外部 cogs（`external_cogs/`）可透過 Docker volume mount 動態掛載並透過 `!load`/`!unload`/`!reload` 管理。原有 cogs 移至 `legacy_cogs/` 保留。`agent/` 目錄及所有 agentic 相關程式碼完全移除。

**Tech Stack:** Python 3.13, discord.py, uv (package manager)

---

## 重要前置說明

`load_external_cogs()` 和 `EXTERNAL_COGS_DIR` 是在 `b85ceec`（agentic commit，不 cherry-pick）中引入的，因此 cherry-pick 完成後**需手動補上**這兩項。

---

## 檔案變動總覽

| 動作 | 路徑 | 說明 |
|------|------|------|
| Rename | `cogs/{analysis,chip,example,finance,webhook}.py` → `legacy_cogs/` | cherry-pick ee43cbc |
| Modify | `cogs/admin.py` | cherry-pick 2093f69，再移除 register_ai_tools() 呼叫 |
| Create | `external_cogs/__init__.py` | cherry-pick 6a33a48 |
| Rewrite | `external_cogs/example.py` | cherry-pick 後改寫為參考模板 |
| Modify | `Dockerfile` | cherry-pick 40f8706 |
| Modify | `config.py` | 手動新增 EXTERNAL_COGS_DIR |
| Modify | `bot.py` | 手動新增 load_external_cogs()，移除 import asyncio/os/Optional |
| Modify | `.env.example` | 新增外部 cog 設定區段 |

---

## Task 1: 建立 feat/pluggable-cogs branch

**Files:**
- No file changes — git operation only

- [ ] **Step 1: 確認目前在 main 且工作區乾淨**

```bash
git status
git branch
```

Expected: on branch `main`, nothing to commit.

- [ ] **Step 2: 建立並切換到新 branch**

```bash
git checkout -b feat/pluggable-cogs
```

Expected output: `Switched to a new branch 'feat/pluggable-cogs'`

---

## Task 2: Cherry-pick ee43cbc（移動 cogs → legacy_cogs）

**Files:**
- Rename: `cogs/{analysis,chip,example,finance,webhook}.py` → `legacy_cogs/`

- [ ] **Step 1: Cherry-pick**

```bash
git cherry-pick ee43cbc
```

Expected output:
```
[feat/pluggable-cogs xxxxxxx] turn current cogs into legacy ones
 5 files changed, 0 insertions(+), 0 deletions(-)
 rename {cogs => legacy_cogs}/analysis.py (100%)
 ...
```

如果出現 conflict，手動解決後執行 `git cherry-pick --continue`。

- [ ] **Step 2: 確認結果**

```bash
ls legacy_cogs/
ls cogs/
```

Expected: `legacy_cogs/` 有 analysis.py, chip.py, example.py, finance.py, webhook.py；`cogs/` 只剩 admin.py（和 `__init__.py` 若有的話）。

---

## Task 3: Cherry-pick 2093f69（升級 cogs/admin.py）

**Files:**
- Modify: `cogs/admin.py`

- [ ] **Step 1: Cherry-pick**

```bash
git cherry-pick 2093f69
```

Expected: clean apply，`cogs/admin.py` 更新為支援 external cog 管理的版本。

如果出現 conflict（兩邊都有修改 admin.py），解決原則：**保留 2093f69 的目標版本**（區分內建/外部 cog、`!cogs` 列表分群、`!load`/`!unload`/`!reload` 限定外部 cog）。

- [ ] **Step 2: 確認 admin.py 有新版結構**

```bash
grep -n "external\|_is_external\|_full_ext_name\|register_ai_tools" cogs/admin.py
```

Expected: 看到 `_is_external`, `_full_ext_name` 等方法，以及多個 `register_ai_tools` 呼叫（下一個 Task 會移除）。

---

## Task 4: Cherry-pick 6a33a48（建立 external_cogs/）

**Files:**
- Create: `external_cogs/__init__.py`
- Create: `external_cogs/example.py` (暫時含 @ai_tool，Task 9 會改寫)

- [ ] **Step 1: Cherry-pick**

```bash
git cherry-pick 6a33a48
```

Expected: 建立 `external_cogs/` 目錄及兩個新檔案。

- [ ] **Step 2: 確認**

```bash
ls external_cogs/
```

Expected: `__init__.py`, `example.py`

---

## Task 5: Cherry-pick 40f8706（Dockerfile 更新）

**Files:**
- Modify: `Dockerfile`

- [ ] **Step 1: Cherry-pick**

```bash
git cherry-pick 40f8706
```

Expected: Dockerfile 更新，加入 external_cogs volume mount 相關設定。

---

## Task 6: 新增 EXTERNAL_COGS_DIR 至 config.py 和 .env.example

**Files:**
- Modify: `config.py`
- Modify: `.env.example`

- [ ] **Step 1: 在 config.py 末尾加入 EXTERNAL_COGS_DIR**

在 `config.py` 末尾（`OWNER_ID` 那行之後）加入：

```python
# 外部 Cogs 設定
EXTERNAL_COGS_DIR = os.getenv("EXTERNAL_COGS_DIR", "external_cogs")
```

- [ ] **Step 2: 在 .env.example 末尾加入說明**

在 `.env.example` 末尾加入：

```
# ─── 外部 Cogs 熱插拔設定 ─────────────────────────────────────────────
# 外部 Cogs 資料夾路徑（Docker 佈署時可 mount 此目錄以動態添加插件）
EXTERNAL_COGS_DIR=external_cogs

# Bot 擁有者的 Discord User ID（用於管理指令權限）
OWNER_ID=your_discord_user_id
```

- [ ] **Step 3: 確認 import 正確**

```bash
python -c "from config import EXTERNAL_COGS_DIR; print(EXTERNAL_COGS_DIR)"
```

Expected output: `external_cogs`

- [ ] **Step 4: Commit**

```bash
git add config.py .env.example
git commit -m "feat: add EXTERNAL_COGS_DIR config for external cog support"
```

---

## Task 7: 更新 bot.py — 加入 load_external_cogs()

**Files:**
- Modify: `bot.py`

- [ ] **Step 1: 完整取代 bot.py 為以下內容**

```python
"""
Discord Bot 主類別
"""
import sys
import discord
from discord.ext import commands
from pathlib import Path

from config import BOT_TOKEN, COMMAND_PREFIX, COGS_DIR, AUTO_LOAD_COGS, EXTERNAL_COGS_DIR
from utils.logger import setup_logger

logger = setup_logger()


class DiscordBot(commands.Bot):
    """自訂 Bot 類別，繼承 discord.ext.commands.Bot"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            description="A Discord bot built with discord.py",
            help_command=commands.DefaultHelpCommand()
        )

    async def setup_hook(self):
        """Bot 啟動前的設定"""
        logger.info("正在載入 Cogs...")
        if AUTO_LOAD_COGS:
            await self.load_cogs()
            await self.load_external_cogs()
        logger.info("Cogs 載入完成")

    async def load_cogs(self):
        """自動載入內建 cogs 資料夾中的所有 cog"""
        cogs_path = Path(COGS_DIR)

        if not cogs_path.exists():
            logger.warning(f"Cogs 資料夾 {COGS_DIR} 不存在")
            return

        for file in sorted(cogs_path.glob("*.py")):
            if file.name == "__init__.py":
                continue

            cog_name = f"{COGS_DIR}.{file.stem}"
            try:
                await self.load_extension(cog_name)
                logger.info(f"已載入 Cog: {cog_name}")
            except Exception as e:
                logger.error(f"載入 Cog {cog_name} 時發生錯誤: {e}")

    async def load_external_cogs(self):
        """
        載入外部 Cogs 資料夾（EXTERNAL_COGS_DIR）中的所有 cog。
        外部 cog 可透過 Docker volume mount 動態添加，
        並使用 !load / !reload 手動管理。
        """
        ext_path = Path(EXTERNAL_COGS_DIR)

        if not ext_path.exists():
            logger.info(f"外部 Cogs 資料夾 {EXTERNAL_COGS_DIR} 不存在，跳過")
            return

        ext_abs = str(ext_path.resolve().parent)
        if ext_abs not in sys.path:
            sys.path.insert(0, ext_abs)

        ext_dir_name = ext_path.name
        for file in sorted(ext_path.glob("*.py")):
            if file.name == "__init__.py":
                continue

            cog_name = f"{ext_dir_name}.{file.stem}"
            try:
                await self.load_extension(cog_name)
                logger.info(f"已載入外部 Cog: {cog_name}")
            except Exception as e:
                logger.error(f"載入外部 Cog {cog_name} 時發生錯誤: {e}")

    async def on_ready(self):
        """Bot 準備就緒時觸發"""
        logger.info(f"Bot 已上線: {self.user}")
        logger.info(f"Bot ID: {self.user.id}")
        logger.info(f"已連接到 {len(self.guilds)} 個伺服器")

        activity = discord.Game(name=f"使用 {COMMAND_PREFIX}help 查看指令")
        await self.change_presence(activity=activity)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """全域指令錯誤處理"""
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ 缺少必要參數: `{error.param.name}`")
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ 參數格式錯誤: {error}")
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 你沒有執行此指令的權限")
            return

        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ Bot 缺少執行此指令所需的權限")
            return

        logger.error(f"指令錯誤: {error}", exc_info=error)
        await ctx.send("❌ 執行指令時發生錯誤，請稍後再試")

    async def on_message(self, message: discord.Message):
        """處理所有訊息"""
        if message.author.bot:
            return
        await self.process_commands(message)

    async def close(self):
        """Bot 關閉時的清理工作"""
        logger.info("Bot 正在關閉...")
        await super().close()
```

- [ ] **Step 2: 確認語法正確且 import 成功**

```bash
python -c "import bot; print('OK')"
```

Expected output: `OK`（若報 ImportError 表示相依模組有缺，檢查 config.py）

- [ ] **Step 3: Commit**

```bash
git add bot.py
git commit -m "feat: add load_external_cogs() to bot startup"
```

---

## Task 8: 移除 cogs/admin.py 中的 register_ai_tools() 呼叫

**Files:**
- Modify: `cogs/admin.py`

- [ ] **Step 1: 確認目前有幾處 register_ai_tools 呼叫**

```bash
grep -n "register_ai_tools" cogs/admin.py
```

Expected: 3 處，分別在 `load_cog`、`unload_cog`、`reload_cog` 方法內。

- [ ] **Step 2: 移除 load_cog 中的呼叫**

找到以下模式並刪除 `self.bot.register_ai_tools()` 這行：

```python
    @commands.command(name="load")
    async def load_cog(self, ctx: commands.Context, cog: str):
        """載入外部 Cog: !load chip"""
        cog_name = self._full_ext_name(cog)
        try:
            await self.bot.load_extension(cog_name)
            self.bot.register_ai_tools()        # ← 刪除此行
            await ctx.send(f"✅ 已載入 `{cog_name}`")
```

改為：

```python
    @commands.command(name="load")
    async def load_cog(self, ctx: commands.Context, cog: str):
        """載入外部 Cog: !load chip"""
        cog_name = self._full_ext_name(cog)
        try:
            await self.bot.load_extension(cog_name)
            await ctx.send(f"✅ 已載入 `{cog_name}`")
```

- [ ] **Step 3: 移除 unload_cog 中的呼叫**

找到：

```python
        try:
            await self.bot.unload_extension(cog_name)
            self.bot.register_ai_tools()        # ← 刪除此行
            await ctx.send(f"✅ 已卸載 `{cog_name}`")
```

改為：

```python
        try:
            await self.bot.unload_extension(cog_name)
            await ctx.send(f"✅ 已卸載 `{cog_name}`")
```

- [ ] **Step 4: 移除 reload_cog 中的兩處呼叫**

`reload_cog` 有兩處 `register_ai_tools()`：一在成功 reload 後，一在 fallback load 後，各刪除一行。

找到：

```python
        try:
            await self.bot.reload_extension(cog_name)
            self.bot.register_ai_tools()        # ← 刪除此行
            await ctx.send(f"✅ 已重新載入 `{cog_name}`")
```

以及：

```python
            try:
                await self.bot.load_extension(cog_name)
                self.bot.register_ai_tools()    # ← 刪除此行
                await ctx.send(f"✅ 已載入 `{cog_name}` (原本未載入)")
```

- [ ] **Step 5: 確認清理完成**

```bash
grep -n "register_ai_tools" cogs/admin.py
```

Expected: 無輸出（0 筆）

- [ ] **Step 6: 確認語法**

```bash
python -c "import ast; ast.parse(open('cogs/admin.py').read()); print('syntax OK')"
```

Expected: `syntax OK`

- [ ] **Step 7: Commit**

```bash
git add cogs/admin.py
git commit -m "fix: remove register_ai_tools() calls from admin cog"
```

---

## Task 9: 改寫 external_cogs/example.py 為完整參考模板

**Files:**
- Rewrite: `external_cogs/example.py`

- [ ] **Step 1: 完整取代 external_cogs/example.py 為以下內容**

```python
"""
外部插件開發參考模板
==================

此檔案示範外部 Cog（external_cog）的完整結構與常用模式。
開發新插件時，複製此檔案並修改 class 名稱與指令內容即可。

載入方式：
  - 啟動時自動載入：將 .py 檔案放入 EXTERNAL_COGS_DIR 目錄（預設 external_cogs/）
  - 手動載入：  !load <檔名（不含 .py）>
  - 手動卸載：  !unload <檔名>
  - 手動重載：  !reload <檔名>（修改程式碼後使用）
"""
import os

import discord
from discord.ext import commands

from utils.logger import setup_logger

logger = setup_logger("external_cogs.example")


class ExampleCog(commands.Cog, name="範例"):
    """
    範例插件 — 展示外部 Cog 的完整結構。

    包含：
      - 基本 Cog 結構（__init__、事件監聽）
      - 無參數指令
      - 有參數指令
      - Cog 層級錯誤處理
      - 從環境變數讀取設定
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 從環境變數讀取插件設定（在 .env 中定義，或保留預設值）
        self.example_setting = os.getenv("EXAMPLE_SETTING", "預設值")
        logger.info("ExampleCog 已載入")

    # ─── 事件監聽 ────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot 就緒後觸發一次，適合做初始化或日誌記錄。"""
        logger.info(f"ExampleCog 已就緒（設定值：{self.example_setting}）")

    # ─── 無參數指令 ─────────────────────────────────────────────────────

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """測試 Bot 是否在線並回報延遲。用法：!ping"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong！延遲 {latency}ms")

    @commands.command(name="status")
    async def status(self, ctx: commands.Context):
        """顯示 Bot 狀態摘要（使用 Embed）。用法：!status"""
        embed = discord.Embed(
            title="Bot 狀態",
            color=discord.Color.green(),
        )
        embed.add_field(name="延遲", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="伺服器數量", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="已載入模組", value=str(len(self.bot.extensions)), inline=True)
        await ctx.send(embed=embed)

    # ─── 有參數指令 ─────────────────────────────────────────────────────

    @commands.command(name="echo")
    async def echo(self, ctx: commands.Context, *, message: str):
        """
        回覆使用者輸入的訊息。

        用法：!echo <訊息>
        範例：!echo 你好世界
        """
        await ctx.send(f"📢 {message}")

    @commands.command(name="greet")
    async def greet(self, ctx: commands.Context, member: discord.Member = None):
        """
        向指定成員打招呼，未指定時打招呼給發言者。

        用法：!greet [@成員]
        範例：!greet @novis
        """
        target = member or ctx.author
        await ctx.send(f"👋 你好，{target.mention}！")

    # ─── Cog 層級錯誤處理 ────────────────────────────────────────────────

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        捕捉此 Cog 內所有指令拋出的錯誤。
        全域錯誤處理（bot.py on_command_error）不會再處理已在此處理的錯誤。
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ 缺少必要參數：`{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ 參數格式錯誤：{error}")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ 找不到指定的成員")
        else:
            logger.error(f"ExampleCog 指令錯誤：{error}", exc_info=error)
            await ctx.send("❌ 發生未預期的錯誤，請稍後再試")


# ─── 插件入口點（必要）────────────────────────────────────────────────────
# discord.py 在 load_extension() 時會呼叫此函式來安裝 Cog。

async def setup(bot: commands.Bot):
    await bot.add_cog(ExampleCog(bot))
```

- [ ] **Step 2: 確認無 agent 相關 import**

```bash
grep -n "agent\|ai_tool\|pydantic" external_cogs/example.py
```

Expected: 無輸出

- [ ] **Step 3: 確認語法**

```bash
python -c "import ast; ast.parse(open('external_cogs/example.py').read()); print('syntax OK')"
```

Expected: `syntax OK`

- [ ] **Step 4: Commit**

```bash
git add external_cogs/example.py
git commit -m "refactor: rewrite external_cogs/example.py as comprehensive plugin template"
```

---

## Task 10: 最終驗證

**Files:** No changes

- [ ] **Step 1: 確認 agent/ 目錄不存在**

```bash
ls agent/ 2>/dev/null && echo "ERROR: agent/ still exists" || echo "OK: agent/ not found"
```

Expected: `OK: agent/ not found`

- [ ] **Step 2: 確認 cogs/agent.py 不存在**

```bash
ls cogs/agent.py 2>/dev/null && echo "ERROR: cogs/agent.py still exists" || echo "OK"
```

Expected: `OK`

- [ ] **Step 3: 確認無任何 register_ai_tools 殘留**

```bash
grep -rn "register_ai_tools\|from agent\|import agent\|pydantic.ai\|pydantic_ai" --include="*.py" . --exclude-dir=.venv
```

Expected: 無輸出

- [ ] **Step 4: 確認 bot.py 可正常 import**

```bash
python -c "import bot; print('bot.py OK')"
```

Expected: `bot.py OK`

- [ ] **Step 5: 確認完成標準**

```bash
echo "=== Branch ===" && git branch --show-current
echo "=== agent/ ===" && ls agent/ 2>/dev/null || echo "不存在（正確）"
echo "=== cogs/agent.py ===" && ls cogs/agent.py 2>/dev/null || echo "不存在（正確）"
echo "=== external_cogs/ ===" && ls external_cogs/
echo "=== legacy_cogs/ ===" && ls legacy_cogs/
echo "=== pyproject pydantic-ai ===" && grep "pydantic-ai" pyproject.toml 2>/dev/null || echo "不存在（正確）"
```

- [ ] **Step 6: 查看最終 git log**

```bash
git log --oneline -12
```

---

## 完成後

Branch `feat/pluggable-cogs` 可直接 merge 進 `main`：

```bash
git checkout main
git merge feat/pluggable-cogs --no-ff -m "feat: pluggable cog architecture with external_cogs support"
```
