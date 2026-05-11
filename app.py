"""
Aplicação Principal - SIDRA Downloader
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import time
from io import StringIO

# Configuração da página deve ser a primeira chamada
st.set_page_config(
    page_title="SIDRA Downloader - IBGE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar módulos do projeto
from src.sidra_api import SidraAPI
from src.download_manager import DownloadManager
from src.config import Config
from src.utils import logger

# Garantir diretórios
Config.ensure_directories()

# Carregar CSS
def load_css():
    css_file = Path("assets/style.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Inicializar componentes
@st.cache_resource
def init_components():
    return SidraAPI(), DownloadManager()

sidra_api, download_manager = init_components()

# Inicializar estado da sessão
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'selected_table' not in st.session_state:
    st.session_state.selected_table = None
if 'downloading' not in st.session_state:
    st.session_state.downloading = False

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">📊 SIDRA Downloader</h1>
    <p class="hero-subtitle">Acesse e baixe dados oficiais do IBGE de forma simples e rápida</p>
    <div class="hero-badge">
        🔍 10.000+ tabelas | 📥 Downloads em CSV/JSON | 🚀 Atualizado em tempo real
    </div>
</div>
""", unsafe_allow_html=True)

# Stats Grid
st.markdown("""
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-number">10k+</div>
        <div class="stat-label">Tabelas Disponíveis</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">CSV/JSON</div>
        <div class="stat-label">Formatos de Exportação</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">FREE</div>
        <div class="stat-label">Acesso Gratuito</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">Dados</div>
        <div class="stat-label">Oficiais do IBGE</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Search Section
st.markdown("### 🔍 Buscar Tabelas")
col1, col2 = st.columns([3, 1])

with col1:
    search_term = st.text_input(
        "Digite o termo de busca",
        placeholder="Ex: população, PIB, IPCA, agropecuária, industrial...",
        label_visibility="collapsed",
        key="search_input"
    )

with col2:
    search_button = st.button("🔍 Buscar", type="primary", use_container_width=True)

# Resultados da busca
if search_button and search_term:
    with st.spinner("Buscando tabelas..."):
        try:
            tables = sidra_api.buscar_tabelas_por_termo(search_term)
            st.session_state.search_results = tables
            
            if tables:
                st.success(f"✅ Encontradas {len(tables)} tabelas!")
            else:
                st.warning("⚠️ Nenhuma tabela encontrada. Tente outro termo.")
                
        except Exception as e:
            st.error(f"❌ Erro na busca: {str(e)}")

# Exibir resultados
if st.session_state.search_results:
    st.markdown("### 📋 Resultados da Busca")
    
    for idx, table in enumerate(st.session_state.search_results):
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="result-code">
                    📌 {table['codigo']}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="result-name">
                    {table['nome'][:150]}...
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("👁️ Preview", key=f"preview_{table['codigo']}_{idx}"):
                        st.session_state.selected_table = table
                
                with col_btn2:
                    if st.button("⬇️ Baixar", key=f"download_{table['codigo']}_{idx}"):
                        st.session_state.selected_table = table
                        st.session_state.downloading = True
            
            # Exibir preview se selecionado
            if (st.session_state.selected_table and 
                st.session_state.selected_table['codigo'] == table['codigo'] and 
                not st.session_state.downloading):
                
                with st.expander(f"📊 Preview da Tabela {table['codigo']}", expanded=True):
                    df_preview = sidra_api.preview_tabela(table['codigo'])
                    if df_preview is not None:
                        st.dataframe(df_preview, use_container_width=True)
                        st.caption("Mostrando os primeiros registros")
                    else:
                        st.warning("Não foi possível carregar o preview")
            
            # Processar download
            if (st.session_state.selected_table and 
                st.session_state.selected_table['codigo'] == table['codigo'] and 
                st.session_state.downloading):
                
                with st.spinner(f"Baixando tabela {table['codigo']}..."):
                    # Escolher formato
                    formato = st.radio(
                        "Escolha o formato:",
                        ["CSV", "JSON", "Excel"],
                        horizontal=True,
                        key=f"format_{table['codigo']}"
                    )
                    
                    formato_lower = formato.lower()
                    
                    try:
                        filename, dados = sidra_api.baixar_tabela(table['codigo'], formato_lower)
                        
                        if dados:
                            # Salvar arquivo
                            filepath = Path(Config.DOWNLOADS_DIR) / filename
                            with open(filepath, 'wb') as f:
                                f.write(dados)
                            
                            # Se for Excel, converter
                            if formato == "Excel" and formato_lower == "csv":
                                excel_path = download_manager.converter_para_excel(str(filepath))
                                if excel_path:
                                    filepath = Path(excel_path)
                                    filename = filepath.name
                            
                            # Registrar no histórico
                            download_manager.save_download(
                                table['codigo'],
                                table['nome'][:100],
                                formato,
                                str(filepath)
                            )
                            
                            # Botão de download
                            with open(filepath, 'rb') as f:
                                st.download_button(
                                    label=f"📥 Clique para baixar ({formato})",
                                    data=f,
                                    file_name=filename,
                                    mime="application/octet-stream",
                                    use_container_width=True
                                )
                            
                            st.success(f"✅ Download concluído! Arquivo salvo como {filename}")
                            
                            # Resetar estado
                            st.session_state.downloading = False
                            st.session_state.selected_table = None
                            
                    except Exception as e:
                        st.error(f"❌ Erro no download: {str(e)}")
                        st.session_state.downloading = False

# Sidebar com informações
with st.sidebar:
    st.markdown("### 📊 Sobre o SIDRA")
    st.markdown("""
    O **SIDRA (Sistema IBGE de Recuperação Automática)** é a base de dados 
    oficial do IBGE com milhares de indicadores econômicos, sociais e demográficos.
    """)
    
    st.markdown("---")
    st.markdown("### 📁 Downloads Recentes")
    
    history = download_manager.get_history(5)
    if history:
        for item in history:
            with st.container():
                st.markdown(f"""
                <div style="background: #1a1a1a; padding: 0.5rem; border-radius: 5px; margin-bottom: 0.5rem;">
                    <small>📌 Tabela {item['codigo']}</small><br>
                    <small>📄 {item['formato'].upper()}</small><br>
                    <small>📅 {item['data'][:19]}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Nenhum download realizado ainda")
    
    st.markdown("---")
    st.markdown("### 🚀 Dicas")
    st.markdown("""
    - Use termos específicos para melhores resultados
    - Experimente: `PIB`, `IPCA`, `população`
    - Baixe em CSV para análise em Excel
    - Use JSON para desenvolvimento
    """)

# Footer
st.markdown("""
<div class="footer">
    <p>Desenvolvido por Data Analytics Team | Dados fornecidos pelo IBGE SIDRA</p>
    <p style="font-size: 0.8rem;">© 2024 - Todos os direitos reservados</p>
</div>
""", unsafe_allow_html=True)
