"""
Integração com API do SIDRA/IBGE
"""
import requests
import pandas as pd
from typing import List, Dict, Optional, Tuple
from .config import Config
from .utils import logger, retry_on_failure

class SidraAPI:
    """Cliente para API do SIDRA"""
    
    def __init__(self):
        self.base_url = Config.SIDRA_API_BASE
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SIDRA Downloader/1.0',
            'Accept': 'application/json'
        })
    
    @retry_on_failure()
    def listar_tabelas(self) -> List[Dict]:
        """
        Lista todas as tabelas disponíveis
        
        Returns:
            Lista de dicionários com código e nome das tabelas
        """
        try:
            url = f"{self.base_url}/t"
            response = self.session.get(url, timeout=Config.TIMEOUT)
            response.raise_for_status()
            
            dados = response.json()
            tabelas = []
            
            for item in dados:
                if isinstance(item, list) and len(item) >= 2:
                    tabelas.append({
                        "codigo": str(item[0]),
                        "nome": str(item[1]),
                        "descricao": str(item[1])[:200]  # Limite para descrição
                    })
            
            logger.info(f"Listadas {len(tabelas)} tabelas")
            return tabelas
            
        except Exception as e:
            logger.error(f"Erro ao listar tabelas: {str(e)}")
            raise
    
    def buscar_tabelas_por_termo(self, termo: str) -> List[Dict]:
        """
        Busca tabelas pelo termo
        
        Args:
            termo: Termo de busca
            
        Returns:
            Lista de tabelas filtradas
        """
        if not termo or len(termo.strip()) < 2:
            return []
        
        all_tables = self.listar_tabelas()
        termo_lower = termo.lower()
        
        tabelas_filtradas = [
            tabela for tabela in all_tables
            if termo_lower in tabela['nome'].lower()
        ]
        
        logger.info(f"Busca por '{termo}' encontrou {len(tabelas_filtradas)} tabelas")
        return tabelas_filtradas
    
    def baixar_tabela(self, codigo: str, formato: str = "csv") -> Tuple[Optional[str], Optional[bytes]]:
        """
        Baixa dados de uma tabela específica
        
        Args:
            codigo: Código da tabela
            formato: Formato de download (csv, json)
            
        Returns:
            Tuple (filename, dados_em_bytes)
        """
        try:
            if formato == "csv":
                url = f"{self.base_url}/t/{codigo}/n1/all/v/all/p/last%201"
                filename = f"tabela_{codigo}.csv"
            elif formato == "json":
                url = f"{self.base_url}/t/{codigo}/n1/all/v/all/p/last%201?formato=json"
                filename = f"tabela_{codigo}.json"
            else:
                raise ValueError(f"Formato não suportado: {formato}")
            
            response = self.session.get(url, timeout=Config.TIMEOUT)
            response.raise_for_status()
            
            if formato == "json":
                dados = response.content
            else:
                # Para CSV, garantir encoding correto
                dados = response.content
            
            logger.info(f"Tabela {codigo} baixada com sucesso em {formato}")
            return filename, dados
            
        except Exception as e:
            logger.error(f"Erro ao baixar tabela {codigo}: {str(e)}")
            raise
    
    def preview_tabela(self, codigo: str, n_rows: int = 10) -> Optional[pd.DataFrame]:
        """
        Obtém preview dos dados da tabela
        
        Args:
            codigo: Código da tabela
            n_rows: Número de linhas para preview
            
        Returns:
            DataFrame com preview dos dados
        """
        try:
            url = f"{self.base_url}/t/{codigo}/n1/all/v/all/p/last%201?formato=json"
            response = self.session.get(url, timeout=Config.TIMEOUT)
            response.raise_for_status()
            
            dados = response.json()
            if isinstance(dados, list) and len(dados) > 1:
                cabecalho = dados[0]
                valores = dados[1:n_rows+1]
                df = pd.DataFrame(valores, columns=cabecalho)
                return df
            return None
            
        except Exception as e:
            logger.error(f"Erro no preview da tabela {codigo}: {str(e)}")
            return None
