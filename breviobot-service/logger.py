import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

logger = setup_logger('breviobot')
