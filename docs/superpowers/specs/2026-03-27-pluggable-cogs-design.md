# Pluggable Cogs 設計文件

**日期：** 2026-03-27
**Branch：** `feat/pluggable-cogs`（從 `main` 切出）
**目標：** 將 `feat/agentic` 中的熱插拔 Cog 架構帶回 `main`，同時完全移除 Agentic 功能。

---

## 背景

`feat/agentic` branch 同時實作了兩件事：
1. 內建 cog 與可熱插拔外部 cog 的分層架構
2. 基於 PydanticAI 的 Agentic 功能（`!ask` 指令、@mention 觸發）

Agentic 功能未來將作為 home server 的獨立 layer 實作，不屬於這個 Discord bot 的責任範圍。因此本次設計只保留 Cog 架構，移除所有 Agentic 相關程式碼。

---

## 目標架構

```
cogs/           內建 cogs（隨 bot 一起部署，不可熱插拔）
external_cogs/  外部插件（可透過 Docker volume mount 動態掛載）
legacy_cogs/    原有 cogs（暫時保留，不做處理）
agent/          ❌ 刪除
```

### Cog 分層說明

| 層級 | 位置 | 特性 |
|------|------|------|
| 內建 Cog | `cogs/` | Bot 啟動時自動載入，不可被 `!unload` |
| 外部 Cog | `external_cogs/` | 可透過 volume mount 新增，支援 `!load`/`!unload`/`!reload` |
| 舊版 Cog | `legacy_cogs/` | 保留備份，本次不處理 |

---

## 實作步驟

### 1. 建立新 branch

從 `main` 最新 commit 建立 `feat/pluggable-cogs`。

### 2. Cherry-pick 四個 commits

按順序從 `feat/agentic` cherry-pick：

| Commit | 說明 |
|--------|------|
| `ee43cbc` | 把原 cogs 搬進 `legacy_cogs/` |
| `2093f69` | 更新 admin cog（支援 external cog 管理指令） |
| `6a33a48` | `bot.py` 加入 `load_external_cogs()` 機制 |
| `40f8706` | 建立 `external_cogs/` 資料夾與基本結構 |

Cherry-pick 過程中若有 conflict，以「保留 cog 機制、不引入 agentic」為原則解決。

### 3. 移除 Agentic 殘留

Cherry-pick 完成後，清理以下內容：

| 項目 | 動作 |
|------|------|
| `agent/` 目錄（`core.py`, `decorator.py`, `deps.py`）| 整個刪除 |
| `cogs/agent.py` | 刪除 |
| `bot.py` — `register_ai_tools()` 方法與呼叫 | 移除 |
| `bot.py` — `on_ready` 狀態文字中的 `!ask` 提示 | 清除 |
| `config.py` — `AGENT_MODEL`、`OPENROUTER_API_KEY` | 移除 |
| `pyproject.toml` — `pydantic-ai` 依賴 | 移除 |
| `.env.example` — Agentic 相關環境變數 | 移除 |

### 4. 改寫 `external_cogs/example.py`

移除 `@ai_tool` 示範，改寫為完整的外部插件開發參考模板，涵蓋：

- 基本 Cog 結構（`__init__`、事件監聽）
- 前綴指令示範（無參數、有參數）
- Cog 層級錯誤處理（`cog_command_error`）
- 設定讀取（從環境變數取值）
- Logger 正確用法
- 必要的 `async def setup(bot)` 入口

整個檔案附有清楚的中文註解，方便作為新插件的起點。

---

## 不在範圍內

- `legacy_cogs/` 的整理或刪除（留待後續）
- Agentic 系統的重新設計（將在 home server layer 另行規劃）
- 現有 `cogs/` 內容的功能修改

---

## 完成標準

- [ ] `feat/pluggable-cogs` branch 建立完成
- [ ] 四個 commits cherry-pick 完成，無殘留 conflict
- [ ] `agent/` 目錄不存在
- [ ] `cogs/agent.py` 不存在
- [ ] `bot.py` 中無 `register_ai_tools` 相關程式碼
- [ ] `pyproject.toml` 中無 `pydantic-ai`
- [ ] `external_cogs/example.py` 改寫完成，無 `@ai_tool` 引用
- [ ] Bot 可正常啟動（`python main.py` 無錯誤）
