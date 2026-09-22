import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_bagent_logger() -> logging.Logger:
    logger = logging.getLogger("BAgent_Core")
    logger.setLevel(logging.DEBUG)
    
    os.makedirs("logs", exist_ok=True)
    
    file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s')
    console_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
    
    file_handler = RotatingFileHandler('logs/bagent_core.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

logger = setup_bagent_logger()
