import logging

logger = logging.getLogger("aisha_bot")

def get_logger(name: str = None) -> logging.Logger:
    """Возвращает логгер по имени (или общий логгер по умолчанию)"""
    if name:
        return logging.getLogger(name)
    return logger 