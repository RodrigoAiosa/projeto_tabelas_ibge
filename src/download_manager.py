"""
Gerenciador de Downloads
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from .config import Config
from .utils import logger

class DownloadManager:
    """Gerencia downloads e histórico"""
    
    def __init__(self):
        self.history_file = os.path.join(Config.DOWNLOADS_DIR, "history.json")
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """Garante que o arquivo de histórico existe"""
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def save_download(self, codigo: str, nome: str, formato: str, filename: str) -> None:
        """
        Salva informação do download no histórico
        
        Args:
            codigo: Código da tabela
            nome: Nome da tabela
            formato: Formato do arquivo
            filename: Nome do arquivo salvo
        """
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            
            history.append({
                "codigo": codigo,
                "nome": nome,
                "formato": formato,
                "filename": filename,
                "data": datetime.now().isoformat(),
                "tamanho": os.path.getsize(filename) if os.path.exists(filename) else 0
            })
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Download registrado: {filename}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {str(e)}")
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Retorna histórico de downloads"""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            return history[-limit:][::-1]  # Mais recentes primeiro
        except:
            return []
    
    def converter_para_excel(self, csv_filename: str) -> Optional[str]:
        """
        Converte CSV para Excel
        
        Args:
            csv_filename: Nome do arquivo CSV
            
        Returns:
            Nome do arquivo Excel gerado
        """
        try:
            excel_filename = csv_filename.replace('.csv', '.xlsx')
            df = pd.read_csv(csv_filename)
            df.to_excel(excel_filename, index=False)
            logger.info(f"Convertido {csv_filename} para Excel")
            return excel_filename
        except Exception as e:
            logger.error(f"Erro na conversão para Excel: {str(e)}")
            return None
    
    def limpar_arquivos_antigos(self, dias: int = 7):
        """Remove arquivos de download mais antigos que X dias"""
        try:
            import time
            now = time.time()
            cutoff = now - (dias * 86400)
            
            for filename in os.listdir(Config.DOWNLOADS_DIR):
                if filename.endswith(('.csv', '.json', '.xlsx')):
                    filepath = os.path.join(Config.DOWNLOADS_DIR, filename)
                    if os.path.getmtime(filepath) < cutoff:
                        os.remove(filepath)
                        logger.info(f"Removido arquivo antigo: {filename}")
                        
        except Exception as e:
            logger.error(f"Erro ao limpar arquivos: {str(e)}")
