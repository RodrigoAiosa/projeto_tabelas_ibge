"""
Aplicação Principal - SIDRA Downloader
Versão corrigida com suporte à API do IBGE
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import time
from io import StringIO
import ssl
import warnings
import sys
import os

# Desabilitar avisos SSL e warnings (apenas para desenvolvimento)
ssl._create_default_https_context = ssl._create_unverified_context
warnings.filterwarnings('ignore')

# Configuração da página deve ser a primeira chamada
st.set_page_config(
    page_title="SIDRA Downloader - IBGE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adicionar diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos do projeto
from src.sidra_api import SidraAPI
from src.download_manager import DownloadManager
from src.config import Config
from src.utils import logger

# Garantir diretórios
Config.ensure_directories()

# Carregar CSS
def load_css():
    """Carrega o arquivo CSS personalizado"""
    css_file = Path("assets/style.css")
    if css_file.exists():
        with open(css_file, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # CSS inline como fallback
        st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a0b2e 100%);
        }
        .hero-section {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, rgba(106, 13, 173, 0.1) 0%, rgba(0, 0, 0, 0.8) 100%);
            border-radius: 20px;
            margin-bottom: 2rem;
        }
        .hero-title {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff 0%, #b873ff 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        </style>
        """, unsafe_allow_html=True)

load_css()

# Inicializar componentes com cache
@st.cache_resource
def init_components():
    """Inicializa os componentes da aplicação"""
    try:
        sidra_api = SidraAPI()
        download_manager = DownloadManager()
        return sidra_api, download_manager
    except Exception as e:
        st.error(f"Erro ao inicializar componentes: {str(e)}")
        return None, None

sidra_api, download_manager = init_components()

if sidra_api is None or download_manager is None:
    st.error("❌ Falha ao inicializar a aplicação. Por favor, reinicie.")
    st.stop()

# Inicializar estado da sessão
session_defaults = {
    'search_results': [],
    'selected_table': None,
    'downloading': False,
    'preview_table': None,
    'error_message': None,
    'success_message': None
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Função para limpar mensagens temporárias
def clear_temp_messages():
    """Limpa mensagens temporárias após 3 segundos"""
    time.sleep(3)
    if st.session_state.success_message:
        st.session_state.success_message = None
    if st.session_state.error_message:
        st.session_state.error_message = None

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">📊 SIDRA Downloader</h1>
    <p class="hero-subtitle" style="color: #b0b0b0; margin-top: 1rem;">
        Acesse e baixe dados oficiais do IBGE de forma simples e rápida
    </p>
    <div class="hero-badge" style="display: inline-block; padding: 0.5rem 1rem; background: rgba(106, 13, 173, 0.2); border-radius: 50px; margin-top: 1rem;">
        🔍 100+ tabelas | 📥 CSV/JSON | 🚀 Download rápido
    </div>
</div>
""", unsafe_allow_html=True)

# Stats Grid
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: rgba(106, 13, 173, 0.1); border-radius: 10px; border: 1px solid rgba(106, 13, 173, 0.3);">
        <div style="font-size: 2rem; font-weight: 800; color: #b873ff;">100+</div>
        <div style="color: #b0b0b0;">Tabelas</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: rgba(106, 13, 173, 0.1); border-radius: 10px; border: 1px solid rgba(106, 13, 173, 0.3);">
        <div style="font-size: 2rem; font-weight: 800; color: #b873ff;">CSV/JSON</div>
        <div style="color: #b0b0b0;">Formatos</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: rgba(106, 13, 173, 0.1); border-radius: 10px; border: 1px solid rgba(106, 13, 173, 0.3);">
        <div style="font-size: 2rem; font-weight: 800; color: #b873ff;">Grátis</div>
        <div style="color: #b0b0b0;">Acesso</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: rgba(106, 13, 173, 0.1); border-radius: 10px; border: 1px solid rgba(106, 13, 173, 0.3);">
        <div style="font-size: 2rem; font-weight: 800; color: #b873ff;">IBGE</div>
        <div style="color: #b0b0b0;">Oficial</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Search Section
st.markdown("### 🔍 Buscar Tabelas")
st.markdown("Digite um tema para encontrar tabelas relacionadas no SIDRA")

col_search1, col_search2 = st.columns([3, 1])

with col_search1:
    search_term = st.text_input(
    "Termo de busca",
    placeholder="Ex: população, PIB, IPCA, agropecuária, industrial, desemprego...",
    label_visibility="collapsed",
    key="search_input"
)

with col_search2:
    search_button = st.button("🔍 Buscar", type="primary", use_container_width=True)

# Mostrar dicas de busca
with st.expander("💡 Dicas de busca"):
    st.markdown("""
    - **População** → Tabelas sobre população residente, censos, projeções
    - **PIB** → Produto Interno Bruto e indicadores econômicos
    - **IPCA** → Índice de inflação oficial
    - **Desemprego** → Taxas de desocupação e mercado de trabalho
    - **Agropecuária** → Produção agrícola e pecuária
    - **Indústria** → Produção industrial
    - **Comércio** → Vendas do comércio varejista
    """)

# Resultados da busca
if search_button and search_term:
    with st.spinner(f"🔍 Buscando tabelas sobre '{search_term}'..."):
        try:
            tables = sidra_api.buscar_tabelas_por_termo(search_term)
            
            if tables and len(tables) > 0:
                st.session_state.search_results = tables
                st.balloons()
                st.success(f"✅ Encontradas {len(tables)} tabelas relacionadas a '{search_term}'!")
                
                # Log de sucesso
                logger.info(f"Busca bem sucedida: {len(tables)} resultados para '{search_term}'")
            else:
                st.session_state.search_results = []
                st.warning(f"⚠️ Nenhuma tabela encontrada para '{search_term}'.")
                
                # Sugerir termos alternativos
                st.info("💡 **Sugestões:** Tente termos como 'população', 'PIB', 'IPCA', 'desemprego', 'agropecuária'")
                
                # Mostrar algumas tabelas disponíveis como exemplo
                with st.expander("📊 Exemplo de tabelas disponíveis"):
                    exemplos = sidra_api.listar_tabelas()
                    for ex in exemplos[:8]:
                        st.markdown(f"- **{ex['codigo']}** - {ex['nome'][:80]}...")
                
        except Exception as e:
            st.error(f"❌ Erro na busca: {str(e)}")
            st.session_state.search_results = []
            logger.error(f"Erro na busca por '{search_term}': {str(e)}")

# Exibir resultados encontrados
if st.session_state.search_results:
    st.markdown(f"### 📋 Resultados da Busca ({len(st.session_state.search_results)} tabelas)")
    
    for idx, table in enumerate(st.session_state.search_results):
        # Container para cada tabela
        with st.container():
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 3, 1.5])
            
            with col1:
                st.markdown(f"""
                <div style="padding: 0.5rem;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #b873ff; font-family: monospace;">
                        📌 {table['codigo']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="padding: 0.5rem;">
                    <div style="color: #e0e0e0; font-weight: 500; margin-bottom: 0.3rem;">
                        {table['nome'][:150]}
                    </div>
                    {f'<div style="color: #808080; font-size: 0.85rem; margin-top: 0.3rem;">{table.get("descricao", "")[:120]}...</div>' if table.get("descricao") else ''}
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Botões de ação
                btn_preview = st.button("👁️ Preview", key=f"preview_{table['codigo']}_{idx}", use_container_width=True)
                btn_download = st.button("⬇️ Baixar", key=f"download_{table['codigo']}_{idx}", type="primary", use_container_width=True)
                
                if btn_preview:
                    st.session_state.preview_table = table
                    st.session_state.selected_table = None
                    st.session_state.downloading = False
                
                if btn_download:
                    st.session_state.downloading = True
                    st.session_state.selected_table = table
                    st.session_state.preview_table = None
            
            # Mostrar preview se selecionado
            if st.session_state.preview_table and st.session_state.preview_table['codigo'] == table['codigo']:
                with st.spinner(f"Carregando preview da tabela {table['codigo']}..."):
                    try:
                        df_preview = sidra_api.preview_tabela(table['codigo'], n_rows=8)
                        if df_preview is not None and not df_preview.empty:
                            st.markdown(f"#### 📊 Preview da Tabela {table['codigo']}")
                            st.dataframe(df_preview, use_container_width=True)
                            st.caption("ℹ️ Mostrando os primeiros registros da tabela")
                            
                            # Botão para fechar preview
                            if st.button("Fechar Preview", key=f"close_preview_{table['codigo']}"):
                                st.session_state.preview_table = None
                                st.rerun()
                        else:
                            st.warning("Não foi possível carregar o preview desta tabela")
                    except Exception as e:
                        st.error(f"Erro ao carregar preview: {str(e)[:100]}")
            
            # Processar download
            if (st.session_state.downloading and 
                st.session_state.selected_table and 
                st.session_state.selected_table['codigo'] == table['codigo']):
                
                st.markdown(f"#### 📥 Download da Tabela {table['codigo']}")
                
                # Seleção de formato
                formato = st.radio(
                    "Escolha o formato para download:",
                    ["CSV", "JSON"],
                    horizontal=True,
                    key=f"format_{table['codigo']}_{idx}"
                )
                
                col_download1, col_download2 = st.columns(2)
                
                with col_download1:
                    if st.button("✅ Confirmar Download", key=f"confirm_{table['codigo']}_{idx}", type="primary", use_container_width=True):
                        with st.spinner(f"Baixando tabela {table['codigo']} em {formato}..."):
                            try:
                                formato_lower = formato.lower()
                                filename, dados = sidra_api.baixar_tabela(table['codigo'], formato_lower)
                                
                                if dados and filename:
                                    # Salvar arquivo
                                    filepath = Path(Config.DOWNLOADS_DIR) / filename
                                    with open(filepath, 'wb') as f:
                                        f.write(dados)
                                    
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
                                            label=f"📥 Baixar Arquivo ({formato})",
                                            data=f,
                                            file_name=filename,
                                            mime="application/octet-stream",
                                            use_container_width=True
                                        )
                                    
                                    st.success(f"✅ Download concluído com sucesso! Arquivo: {filename}")
                                    st.balloons()
                                    
                                    # Resetar estado do download
                                    st.session_state.downloading = False
                                    st.session_state.selected_table = None
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("❌ Falha no download. A tabela pode não estar disponível.")
                                    
                            except Exception as e:
                                st.error(f"❌ Erro no download: {str(e)}")
                                logger.error(f"Erro download tabela {table['codigo']}: {str(e)}")
                
                with col_download2:
                    if st.button("❌ Cancelar", key=f"cancel_{table['codigo']}_{idx}", use_container_width=True):
                        st.session_state.downloading = False
                        st.session_state.selected_table = None
                        st.rerun()
                
                st.info("💡 Dica: Para tabelas grandes, o download pode levar alguns segundos. Aguarde.")

# Mensagem quando não há resultados
if search_button and search_term and not st.session_state.search_results:
    st.info("🎯 **Não encontrou o que procurava?**")
    st.markdown("""
    - Tente usar termos mais genéricos como 'população' ou 'economia'
    - Verifique a ortografia do termo buscado
    - Consulte a [página oficial do SIDRA](https://sidra.ibge.gov.br) para explorar todas as tabelas
    """)

# Sidebar com informações
with st.sidebar:
    st.markdown("### 📊 Sobre o SIDRA")
    st.markdown("""
    O **SIDRA (Sistema IBGE de Recuperação Automática)** é a base de dados 
    oficial do IBGE com indicadores econômicos, sociais e demográficos do Brasil.
    """)
    
    st.markdown("---")
    st.markdown("### 📁 Downloads Recentes")
    
    history = download_manager.get_history(5)
    if history:
        for item in history:
            with st.container():
                st.markdown(f"""
                <div style="background: #1a1a1a; padding: 0.6rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #6a0dad;">
                    <small style="color: #b873ff;">📌 Tabela {item['codigo']}</small><br>
                    <small style="color: #b0b0b0;">📄 {item['formato'].upper()}</small><br>
                    <small style="color: #808080;">📅 {item['data'][:10]}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ Nenhum download realizado ainda")
    
    st.markdown("---")
    st.markdown("### 🚀 Dicas de Uso")
    st.markdown("""
    ✅ **Termos recomendados:**
    - População
    - PIB
    - IPCA
    - Desemprego
    - Agropecuária
    - Indústria
    - Comércio
    
    📥 **Formatos:**
    - **CSV**: Para Excel, Planilhas
    - **JSON**: Para desenvolvedores
    
    ⚡ **Dicas:**
    - Use o preview antes de baixar
    - Verifique se o código da tabela está correto
    - Aguarde o processamento de tabelas grandes
    """)
    
    st.markdown("---")
    st.markdown("### 🔗 Links Úteis")
    st.markdown("""
    - [Portal SIDRA](https://sidra.ibge.gov.br)
    - [IBGE Oficial](https://www.ibge.gov.br)
    - [Documentação API](https://sidra.ibge.gov.br/ajuda)
    """)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <small style="color: #808080;">Versão 2.0 | Atualizado em 2024</small>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.markdown("""
    <div style="text-align: center;">
        <small>📊 Dados oficiais do IBGE</small>
    </div>
    """, unsafe_allow_html=True)

with col_footer2:
    st.markdown("""
    <div style="text-align: center;">
        <small>🔍 SIDRA - Sistema IBGE de Recuperação Automática</small>
    </div>
    """, unsafe_allow_html=True)

with col_footer3:
    st.markdown("""
    <div style="text-align: center;">
        <small>✨ Desenvolvido com ❤️ e Streamlit</small>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; padding: 1rem; margin-top: 1rem; color: #808080; border-top: 1px solid rgba(106, 13, 173, 0.3);">
    <small>© 2024 SIDRA Downloader - Todos os direitos reservados</small>
</div>
""", unsafe_allow_html=True)
