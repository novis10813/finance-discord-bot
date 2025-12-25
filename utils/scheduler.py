"""
排程器工具
用於管理 Discord bot 的定時任務，支援固定時間間隔和 Cron 表達式
"""
import json
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
from discord.ext import commands

from utils.logger import setup_logger

logger = setup_logger("scheduler")


class TaskScheduler:
    """任務排程器類別，管理所有定時任務"""
    
    def __init__(self, bot: commands.Bot, tasks_file: str = "data/scheduled_tasks.json"):
        """
        初始化排程器
        
        Args:
            bot: Discord bot 實例
            tasks_file: 任務持久化檔案路徑
        """
        self.bot = bot
        self.tasks_file = Path(tasks_file)
        self.scheduler = AsyncIOScheduler()
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """確保資料目錄存在"""
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
    
    def start(self):
        """啟動排程器並載入保存的任務"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("排程器已啟動")
            self._load_tasks()
    
    def shutdown(self):
        """關閉排程器並保存任務"""
        if self.scheduler.running:
            self._save_tasks()
            self.scheduler.shutdown(wait=True)
            logger.info("排程器已關閉")
    
    def add_interval_task(
        self,
        task_id: str,
        func: Callable,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        args: Tuple = (),
        kwargs: Dict = None,
        enabled: bool = True,
        save: bool = True
    ) -> bool:
        """
        添加固定時間間隔任務
        
        Args:
            task_id: 任務唯一識別碼
            func: 要執行的異步函數
            seconds: 秒數間隔
            minutes: 分鐘間隔
            hours: 小時間隔
            days: 天數間隔
            args: 傳遞給函數的位置參數
            kwargs: 傳遞給函數的關鍵字參數
            enabled: 是否啟用任務
            save: 是否立即保存（載入任務時設為 False）
            
        Returns:
            bool: 是否成功添加
            
        Raises:
            ValueError: 任務 ID 已存在或參數無效
        """
        if task_id in self.tasks:
            raise ValueError(f"任務 ID '{task_id}' 已存在")
        
        if not (seconds or minutes or hours or days):
            raise ValueError("至少需要指定一個時間間隔參數")
        
        if kwargs is None:
            kwargs = {}
        
        # 創建觸發器
        trigger = IntervalTrigger(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days
        )
        
        # 包裝函數以添加錯誤處理和日誌
        wrapped_func = self._wrap_task_func(func, task_id)
        
        # 添加任務到排程器
        job = self.scheduler.add_job(
            wrapped_func,
            trigger=trigger,
            id=task_id,
            args=args,
            kwargs=kwargs,
            replace_existing=True
        )
        
        # 如果未啟用，暫停任務
        if not enabled:
            job.pause()
        
        # 保存任務配置
        self.tasks[task_id] = {
            "task_id": task_id,
            "type": "interval",
            "trigger": {
                "seconds": seconds,
                "minutes": minutes,
                "hours": hours,
                "days": days
            },
            "func": self._get_func_path(func),
            "args": list(args),
            "kwargs": kwargs,
            "enabled": enabled
        }
        
        if save:
            self._save_tasks()
        logger.info(f"已添加間隔任務: {task_id} (間隔: {days}天 {hours}小時 {minutes}分鐘 {seconds}秒)")
        
        return True
    
    def add_cron_task(
        self,
        task_id: str,
        func: Callable,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        week: Optional[int] = None,
        day_of_week: Optional[str] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: Optional[int] = None,
        args: Tuple = (),
        kwargs: Dict = None,
        enabled: bool = True,
        save: bool = True
    ) -> bool:
        """
        添加 Cron 任務
        
        Args:
            task_id: 任務唯一識別碼
            func: 要執行的異步函數
            year: 年份
            month: 月份 (1-12)
            day: 日期 (1-31)
            week: 週數
            day_of_week: 星期幾 (mon, tue, wed, thu, fri, sat, sun 或 0-6)
            hour: 小時 (0-23)
            minute: 分鐘 (0-59)
            second: 秒數 (0-59)
            args: 傳遞給函數的位置參數
            kwargs: 傳遞給函數的關鍵字參數
            enabled: 是否啟用任務
            save: 是否立即保存（載入任務時設為 False）
            
        Returns:
            bool: 是否成功添加
            
        Raises:
            ValueError: 任務 ID 已存在或參數無效
        """
        if task_id in self.tasks:
            raise ValueError(f"任務 ID '{task_id}' 已存在")
        
        if kwargs is None:
            kwargs = {}
        
        # 創建觸發器
        trigger = CronTrigger(
            year=year,
            month=month,
            day=day,
            week=week,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            second=second
        )
        
        # 包裝函數以添加錯誤處理和日誌
        wrapped_func = self._wrap_task_func(func, task_id)
        
        # 添加任務到排程器
        job = self.scheduler.add_job(
            wrapped_func,
            trigger=trigger,
            id=task_id,
            args=args,
            kwargs=kwargs,
            replace_existing=True
        )
        
        # 如果未啟用，暫停任務
        if not enabled:
            job.pause()
        
        # 保存任務配置
        self.tasks[task_id] = {
            "task_id": task_id,
            "type": "cron",
            "trigger": {
                "year": year,
                "month": month,
                "day": day,
                "week": week,
                "day_of_week": day_of_week,
                "hour": hour,
                "minute": minute,
                "second": second
            },
            "func": self._get_func_path(func),
            "args": list(args),
            "kwargs": kwargs,
            "enabled": enabled
        }
        
        if save:
            self._save_tasks()
        logger.info(f"已添加 Cron 任務: {task_id}")
        
        return True
    
    def remove_task(self, task_id: str) -> bool:
        """
        移除任務
        
        Args:
            task_id: 任務 ID
            
        Returns:
            bool: 是否成功移除
        """
        if task_id not in self.tasks:
            logger.warning(f"嘗試移除不存在的任務: {task_id}")
            return False
        
        try:
            self.scheduler.remove_job(task_id)
            del self.tasks[task_id]
            self._save_tasks()
            logger.info(f"已移除任務: {task_id}")
            return True
        except Exception as e:
            logger.error(f"移除任務 {task_id} 時發生錯誤: {e}")
            return False
    
    def pause_task(self, task_id: str) -> bool:
        """
        暫停任務
        
        Args:
            task_id: 任務 ID
            
        Returns:
            bool: 是否成功暫停
        """
        if task_id not in self.tasks:
            logger.warning(f"嘗試暫停不存在的任務: {task_id}")
            return False
        
        try:
            self.scheduler.pause_job(task_id)
            self.tasks[task_id]["enabled"] = False
            self._save_tasks()
            logger.info(f"已暫停任務: {task_id}")
            return True
        except Exception as e:
            logger.error(f"暫停任務 {task_id} 時發生錯誤: {e}")
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """
        恢復任務
        
        Args:
            task_id: 任務 ID
            
        Returns:
            bool: 是否成功恢復
        """
        if task_id not in self.tasks:
            logger.warning(f"嘗試恢復不存在的任務: {task_id}")
            return False
        
        try:
            self.scheduler.resume_job(task_id)
            self.tasks[task_id]["enabled"] = True
            self._save_tasks()
            logger.info(f"已恢復任務: {task_id}")
            return True
        except Exception as e:
            logger.error(f"恢復任務 {task_id} 時發生錯誤: {e}")
            return False
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        列出所有任務
        
        Returns:
            List[Dict]: 任務列表
        """
        return list(self.tasks.values())
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取指定任務的資訊
        
        Args:
            task_id: 任務 ID
            
        Returns:
            Optional[Dict]: 任務資訊，如果不存在則返回 None
        """
        return self.tasks.get(task_id)
    
    def _wrap_task_func(self, func: Callable, task_id: str) -> Callable:
        """
        包裝任務函數，添加錯誤處理和日誌
        
        Args:
            func: 原始函數
            task_id: 任務 ID
            
        Returns:
            Callable: 包裝後的函數
        """
        async def wrapped(*args, **kwargs):
            try:
                logger.debug(f"開始執行任務: {task_id}")
                await func(*args, **kwargs)
                logger.debug(f"任務執行完成: {task_id}")
            except Exception as e:
                logger.error(f"任務 {task_id} 執行時發生錯誤: {e}", exc_info=True)
        
        return wrapped
    
    def _get_func_path(self, func: Callable) -> str:
        """
        獲取函數的路徑字串（用於持久化）
        
        Args:
            func: 函數物件
            
        Returns:
            str: 函數路徑字串（例如：cogs.example.send_message）
        """
        module = func.__module__
        name = func.__name__
        return f"{module}.{name}"
    
    def _load_func_from_path(self, func_path: str) -> Optional[Callable]:
        """
        從路徑字串載入函數
        
        Args:
            func_path: 函數路徑字串（例如：cogs.example.send_message）
            
        Returns:
            Optional[Callable]: 函數物件，如果載入失敗則返回 None
        """
        try:
            module_path, func_name = func_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            return func
        except Exception as e:
            logger.error(f"載入函數 {func_path} 時發生錯誤: {e}")
            return None
    
    def _load_tasks(self):
        """從檔案載入任務"""
        if not self.tasks_file.exists():
            logger.info(f"任務檔案 {self.tasks_file} 不存在，跳過載入")
            return
        
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            tasks = data.get("tasks", [])
            loaded_count = 0
            
            for task_config in tasks:
                task_id = task_config.get("task_id")
                if not task_id:
                    logger.warning("跳過無效的任務配置（缺少 task_id）")
                    continue
                
                # 載入函數
                func_path = task_config.get("func")
                if not func_path:
                    logger.warning(f"任務 {task_id} 缺少函數路徑，跳過")
                    continue
                
                func = self._load_func_from_path(func_path)
                if func is None:
                    logger.warning(f"無法載入任務 {task_id} 的函數 {func_path}，跳過")
                    continue
                
                # 根據任務類型重新註冊
                task_type = task_config.get("type")
                trigger = task_config.get("trigger", {})
                args = tuple(task_config.get("args", []))
                kwargs = task_config.get("kwargs", {})
                enabled = task_config.get("enabled", True)
                
                try:
                    if task_type == "interval":
                        self.add_interval_task(
                            task_id=task_id,
                            func=func,
                            seconds=trigger.get("seconds", 0),
                            minutes=trigger.get("minutes", 0),
                            hours=trigger.get("hours", 0),
                            days=trigger.get("days", 0),
                            args=args,
                            kwargs=kwargs,
                            enabled=enabled,
                            save=False  # 載入時不立即保存
                        )
                    elif task_type == "cron":
                        self.add_cron_task(
                            task_id=task_id,
                            func=func,
                            year=trigger.get("year"),
                            month=trigger.get("month"),
                            day=trigger.get("day"),
                            week=trigger.get("week"),
                            day_of_week=trigger.get("day_of_week"),
                            hour=trigger.get("hour"),
                            minute=trigger.get("minute"),
                            second=trigger.get("second"),
                            args=args,
                            kwargs=kwargs,
                            enabled=enabled,
                            save=False  # 載入時不立即保存
                        )
                    else:
                        logger.warning(f"未知的任務類型: {task_type}，跳過任務 {task_id}")
                        continue
                    
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"載入任務 {task_id} 時發生錯誤: {e}")
            
            # 載入完成後統一保存一次
            if loaded_count > 0:
                self._save_tasks()
            logger.info(f"已載入 {loaded_count} 個任務")
            
        except json.JSONDecodeError as e:
            logger.error(f"解析任務檔案時發生錯誤: {e}")
        except Exception as e:
            logger.error(f"載入任務時發生錯誤: {e}", exc_info=True)
    
    def _save_tasks(self):
        """保存任務到檔案"""
        try:
            data = {
                "tasks": list(self.tasks.values()),
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"已保存 {len(self.tasks)} 個任務到 {self.tasks_file}")
        except Exception as e:
            logger.error(f"保存任務時發生錯誤: {e}", exc_info=True)


# 全域排程器實例字典
_schedulers: Dict[int, TaskScheduler] = {}


def get_scheduler(bot: commands.Bot) -> TaskScheduler:
    """
    獲取或創建排程器實例（每個 bot 實例對應一個排程器）
    
    Args:
        bot: Discord bot 實例
        
    Returns:
        TaskScheduler: 排程器實例
    """
    bot_id = id(bot)
    if bot_id not in _schedulers:
        from config import SCHEDULER_TASKS_FILE
        _schedulers[bot_id] = TaskScheduler(bot, SCHEDULER_TASKS_FILE)
    return _schedulers[bot_id]

