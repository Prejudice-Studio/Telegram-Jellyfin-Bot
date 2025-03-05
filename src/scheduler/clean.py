from src.logger import scheduler_logger


def clean_memory():
    """
    清理内存
    """
    import gc
    gc.collect()
    scheduler_logger.info("Memory cleaned")
