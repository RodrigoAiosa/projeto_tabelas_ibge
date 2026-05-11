"""
Configurações do Projeto
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações principais"""
    
    # API
    SIDRA_API_BASE = "https://apisidra.ibge.gov.br/values"
    TIMEOUT = 60
    MAX_RETRIES = 3
    
    # Cores do tema
    PRIMARY_COLOR = "#6a0dad"
    SECONDARY_COLOR = "#9b4dff"
    BACKGROUND_COLOR = "#0a0a0a"
    
    # Diretórios
    DOWNLOADS_DIR = "downloads"
    ASSETS_DIR = "assets"
    
    # Cache
    CACHE_TTL = 3600  # 1 hora
    
    # Formatos suportados
    SUPPORTED_FORMATS = ["csv", "json", "excel"]
    
    @classmethod
    def ensure_directories(cls):
        """Garante que os diretórios necessários existam"""
        if not os.path.exists(cls.DOWNLOADS_DIR):
            os.makedirs(cls.DOWNLOADS_DIR)
