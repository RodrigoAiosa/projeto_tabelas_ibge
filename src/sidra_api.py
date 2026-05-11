"""
Integração com API do SIDRA/IBGE - Versão Corrigida com Formatação de Colunas
"""
import requests
import pandas as pd
from typing import List, Dict, Optional, Tuple
import json
import re
from io import StringIO
from .config import Config
from .utils import logger, retry_on_failure

class SidraAPI:
    """Cliente para API do SIDRA - Versão com formatação de colunas"""
    
    def __init__(self):
        self.base_url = "https://sidra.ibge.gov.br"
        self.api_url = "https://apisidra.ibge.gov.br"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        })
    
    def listar_tabelas(self) -> List[Dict]:
        """
        Lista tabelas disponíveis usando busca simulada
        
        Returns:
            Lista de dicionários com código e nome das tabelas
        """
        # Lista de tabelas populares pré-definidas
        tabelas_populares = [
            {"codigo": "7060", "nome": "População residente - Projeção"},
            {"codigo": "200", "nome": "População nos Censos Demográficos"},
            {"codigo": "202", "nome": "População residente - Sexo e idade"},
            {"codigo": "203", "nome": "População residente - Grandes Regiões"},
            {"codigo": "593", "nome": "População residente - Municípios"},
            {"codigo": "1612", "nome": "PIB - Produto Interno Bruto"},
            {"codigo": "1737", "nome": "PIB per capita"},
            {"codigo": "1419", "nome": "IPCA - Índice de Preços"},
            {"codigo": "7066", "nome": "IPCA - Variação mensal"},
            {"codigo": "1734", "nome": "Exportações e Importações"},
            {"codigo": "7441", "nome": "Desemprego - PNAD Contínua"},
            {"codigo": "6386", "nome": "Taxa de desocupação"},
            {"codigo": "543", "nome": "Produção Agropecuária"},
            {"codigo": "3939", "nome": "Produção Industrial"},
            {"codigo": "8709", "nome": "Comércio Varejista"},
            {"codigo": "7155", "nome": "IDH - Índice de Desenvolvimento"},
            {"codigo": "1738", "nome": "Educação - Matrículas"},
            {"codigo": "1001", "nome": "Saúde - Estabelecimentos"},
            {"codigo": "3388", "nome": "Turismo - Atividades"},
            {"codigo": "216", "nome": "Domicílios - Características"},
        ]
        
        return tabelas_populares
    
    def buscar_tabelas_por_termo(self, termo: str) -> List[Dict]:
        """
        Busca tabelas pelo termo usando busca local
        
        Args:
            termo: Termo de busca
            
        Returns:
            Lista de tabelas filtradas
        """
        if not termo or len(termo.strip()) < 2:
            return []
        
        # Lista expandida de tabelas com palavras-chave
        tabelas_completas = self._get_tabelas_completas()
        
        termo_lower = termo.lower()
        
        tabelas_filtradas = []
        for tabela in tabelas_completas:
            # Busca no nome e nas palavras-chave
            relevancia = 0
            if termo_lower in tabela['nome'].lower():
                relevancia += 3
            if 'palavras_chave' in tabela and any(termo_lower in kw.lower() for kw in tabela['palavras_chave']):
                relevancia += 2
            
            if relevancia > 0:
                tabelas_filtradas.append({
                    "codigo": tabela['codigo'],
                    "nome": tabela['nome'],
                    "descricao": tabela.get('descricao', ''),
                    "relevancia": relevancia
                })
        
        # Ordenar por relevância
        tabelas_filtradas.sort(key=lambda x: x['relevancia'], reverse=True)
        
        logger.info(f"Busca por '{termo}' encontrou {len(tabelas_filtradas)} tabelas")
        return tabelas_filtradas
    
    def _get_tabelas_completas(self) -> List[Dict]:
        """
        Retorna lista completa de tabelas com palavras-chave
        """
        return [
            # População
            {"codigo": "7060", "nome": "População residente - Estimativas e Projeções", 
             "palavras_chave": ["população", "habitantes", "residentes", "demografia", "censos"],
             "descricao": "Estimativas da população residente para municípios e Unidades da Federação"},
            
            {"codigo": "200", "nome": "População residente por sexo e idade - Censos", 
             "palavras_chave": ["população", "sexo", "idade", "homens", "mulheres"],
             "descricao": "Distribuição da população por faixa etária e gênero"},
            
            {"codigo": "202", "nome": "População residente por Grandes Regiões e Unidades da Federação",
             "palavras_chave": ["população", "regiões", "estados", "distribuição regional"],
             "descricao": "Distribuição populacional por regiões brasileiras"},
            
            # PIB
            {"codigo": "1612", "nome": "Produto Interno Bruto - PIB", 
             "palavras_chave": ["pib", "economia", "produto interno", "crescimento"],
             "descricao": "Valores do PIB por setor econômico"},
            
            {"codigo": "1737", "nome": "PIB per capita", 
             "palavras_chave": ["pib per capita", "renda", "economia per capita"],
             "descricao": "Relação entre PIB e população residente"},
            
            # IPCA
            {"codigo": "1419", "nome": "IPCA - Índice Nacional de Preços ao Consumidor Amplo",
             "palavras_chave": ["ipca", "inflação", "preços", "custos"],
             "descricao": "Índice oficial de inflação do Brasil"},
            
            {"codigo": "7066", "nome": "IPCA - Variação mensal e acumulada",
             "palavras_chave": ["ipca", "inflação", "variação", "mensal"],
             "descricao": "Variações mensais do IPCA por grupos de produtos"},
            
            # Trabalho e Desemprego
            {"codigo": "7441", "nome": "PNAD Contínua - Taxa de desocupação",
             "palavras_chave": ["desemprego", "desocupação", "trabalho", "emprego", "pnad"],
             "descricao": "Taxas de desemprego por região e período"},
            
            {"codigo": "6386", "nome": "Rendimento médio real do trabalho",
             "palavras_chave": ["salário", "renda", "trabalho", "remuneração"],
             "descricao": "Rendimentos médios da população ocupada"},
            
            # Agropecuária
            {"codigo": "543", "nome": "Produção Agrícola Municipal - PAM",
             "palavras_chave": ["agropecuária", "agricultura", "produção", "lavoura", "colheita"],
             "descricao": "Dados de produção agrícola por município"},
            
            {"codigo": "845", "nome": "Pecuária Municipal - PPM",
             "palavras_chave": ["pecuária", "gado", "rebanho", "animais", "bovinos"],
             "descricao": "Efetivos da produção pecuária"},
            
            # Indústria
            {"codigo": "3939", "nome": "Pesquisa Industrial Mensal - PIM",
             "palavras_chave": ["indústria", "produção industrial", "fabricação"],
             "descricao": "Produção física da indústria brasileira"},
            
            # Comércio
            {"codigo": "8709", "nome": "Pesquisa Mensal de Comércio - PMC",
             "palavras_chave": ["comércio", "vendas", "varejo", "faturamento"],
             "descricao": "Volume de vendas do comércio varejista"},
            
            # Serviços
            {"codigo": "8840", "nome": "Pesquisa Mensal de Serviços - PMS",
             "palavras_chave": ["serviços", "prestação", "terceiros", "atendimento"],
             "descricao": "Volume de serviços prestados no Brasil"},
            
            # Educação
            {"codigo": "1738", "nome": "Censo Escolar - Matrículas",
             "palavras_chave": ["educação", "escolas", "matrículas", "alunos", "ensino"],
             "descricao": "Estatísticas da educação básica"},
            
            # Saúde
            {"codigo": "1001", "nome": "Cadastro Nacional de Estabelecimentos de Saúde - CNES",
             "palavras_chave": ["saúde", "hospitais", "postos", "médicos", "atendimento"],
             "descricao": "Rede assistencial de saúde no Brasil"},
            
            # Construção Civil
            {"codigo": "8966", "nome": "Pesquisa Nacional de Saneamento Básico",
             "palavras_chave": ["construção", "saneamento", "infraestrutura", "obras"],
             "descricao": "Indicadores de construção civil"},
        ]
    
    def _formatar_dados_para_csv(self, dados_json: list) -> str:
        """
        Formata os dados do SIDRA em CSV com colunas organizadas
        
        Args:
            dados_json: Dados no formato JSON retornado pela API
            
        Returns:
            String formatada em CSV
        """
        try:
            if not dados_json or len(dados_json) < 2:
                return ""
            
            # Primeira linha contém os cabeçalhos
            cabecalhos = dados_json[0]
            
            # Demais linhas são os dados
            dados = dados_json[1:]
            
            # Criar DataFrame
            df = pd.DataFrame(dados, columns=cabecalhos)
            
            # Limpar nomes das colunas
            df.columns = [str(col).strip().replace('"', '').replace('\n', ' ') for col in df.columns]
            
            # Converter para CSV
            output = StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig', sep=';')
            csv_string = output.getvalue()
            output.close()
            
            return csv_string
            
        except Exception as e:
            logger.error(f"Erro ao formatar dados para CSV: {str(e)}")
            # Fallback: retornar os dados originais
            return dados_json
    
    def baixar_tabela(self, codigo: str, formato: str = "csv") -> Tuple[Optional[str], Optional[bytes]]:
        """
        Baixa dados de uma tabela específica e formata em colunas
        
        Args:
            codigo: Código da tabela
            formato: Formato de download (csv, json)
            
        Returns:
            Tuple (filename, dados_em_bytes)
        """
        try:
            # Sempre buscar em JSON primeiro para formatar
            url_json = f"{self.api_url}/values/t/{codigo}/n1/all/v/all/p/last%201?formato=json"
            
            logger.info(f"Baixando dados da tabela {codigo}")
            
            response = self.session.get(url_json, timeout=Config.TIMEOUT, verify=False)
            
            if response.status_code != 200:
                logger.error(f"Falha no download: Status {response.status_code}")
                return None, None
            
            dados_json = response.json()
            
            # Verificar se os dados são válidos
            if not dados_json or len(dados_json) < 2:
                raise Exception("Dados retornados estão vazios ou em formato inválido")
            
            if formato == "json":
                # Para JSON, manter formato original mas organizado
                df = self._converter_para_dataframe(dados_json)
                json_output = df.to_json(orient='records', force_ascii=False, indent=2)
                filename = f"tabela_{codigo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                return filename, json_output.encode('utf-8')
                
            else:  # CSV formatado
                csv_string = self._formatar_dados_para_csv(dados_json)
                filename = f"tabela_{codigo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                return filename, csv_string.encode('utf-8-sig')
            
        except Exception as e:
            logger.error(f"Erro ao baixar tabela {codigo}: {str(e)}")
            raise Exception(f"Erro no download: {str(e)}. Verifique se o código da tabela está correto.")
    
    def _converter_para_dataframe(self, dados_json: list) -> pd.DataFrame:
        """
        Converte dados JSON do SIDRA para DataFrame organizado
        
        Args:
            dados_json: Dados no formato da API do SIDRA
            
        Returns:
            DataFrame estruturado
        """
        if not dados_json or len(dados_json) < 2:
            return pd.DataFrame()
        
        cabecalhos = dados_json[0]
        dados = dados_json[1:]
        
        df = pd.DataFrame(dados, columns=cabecalhos)
        
        # Limpar nomes das colunas
        df.columns = [str(col).strip().replace('"', '').replace('\n', ' ') for col in df.columns]
        
        # Tentar converter colunas numéricas
        for col in df.columns:
            try:
                if col not in ['Variável', 'Categoria', 'Nível Territorial', 'Território']:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        
        return df
    
    def preview_tabela(self, codigo: str, n_rows: int = 10) -> Optional[pd.DataFrame]:
        """
        Obtém preview dos dados da tabela já formatado em colunas
        
        Args:
            codigo: Código da tabela
            n_rows: Número de linhas para preview
            
        Returns:
            DataFrame com preview dos dados
        """
        try:
            url = f"{self.api_url}/values/t/{codigo}/n1/all/v/all/p/last%201?formato=json"
            response = self.session.get(url, timeout=Config.TIMEOUT, verify=False)
            response.raise_for_status()
            
            if response.status_code == 200:
                dados_json = response.json()
                df = self._converter_para_dataframe(dados_json)
                
                if not df.empty:
                    return df.head(n_rows)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro no preview da tabela {codigo}: {str(e)}")
            return None
