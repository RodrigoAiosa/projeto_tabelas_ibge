"""
Funções utilitárias
"""
import logging
from functools import wraps
from typing import Callable
import time
from .config import Config

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = Config.MAX_RETRIES, delay: int = 1):
    """Decorator para retry em caso de falha"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}. Tentando novamente...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def formatar_tamanho(bytes_tamanho: int) -> str:
    """Formata tamanho de arquivo para exibição"""
    for unidade in ['B', 'KB', 'MB', 'GB']:
        if bytes_tamanho < 1024.0:
            return f"{bytes_tamanho:.1f} {unidade}"
        bytes_tamanho /= 1024.0
    return f"{bytes_tamanho:.1f} TB"
