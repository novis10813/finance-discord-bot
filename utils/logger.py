"""
日誌系統設定
使用 TimedRotatingFileHandler 實現日誌輪轉
"""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

def setup_logger(name: str = "bot", log_level: str = "INFO", backup_count: int = 14) -> logging.Logger:
    """
    設定並返回 logger 實例，使用日誌輪轉功能
    
    Args:
        name: Logger 名稱
        log_level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        backup_count: 保留的日誌檔案數量（天數），預設 14 天
    
    Returns:
        logging.Logger: 設定好的 logger 實例
    """
    # 建立 logs 資料夾
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 設定日誌格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 建立 logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 避免重複添加 handler
    if logger.handlers:
        return logger
    
    # 檔案 handler - 使用 TimedRotatingFileHandler 實現日誌輪轉
    log_file = log_dir / f"{name}.log"
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when='D',  # 按天輪轉
        interval=1,  # 每 1 天輪轉一次
        backupCount=backup_count,  # 保留 14 個備份檔案（14 天）
        encoding='utf-8',
        delay=False
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    
    # 設定後綴格式（用於檔案命名）
    file_handler.suffix = "%Y%m%d"
    
    # 終端 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # 添加 handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

