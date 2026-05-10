import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="IBGE SIDRA Downloader",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Baixador de Tabelas do IBGE SIDRA")
st.markdown("---")

# Criar pasta de downloads se não existir
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Função para buscar tabelas
@st.cache_data(ttl=3600)
def buscar_tabelas(termo_busca):
    """Busca tabelas no SIDRA por termo"""
    try:
        # Lista todas as tabelas disponíveis
        url = "https://apisidra.ibge.gov.br/values/t"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Converter para lista de dicionários
            tabelas = []
            for item in dados:
                if isinstance(item, list) and len(item) >= 2:
                    codigo = item[0]
                    nome = item[1]
                    tabelas.append({
                        "Código": codigo,
                        "Nome": nome,
                        "Termo_Busca": nome.lower()
                    })
            
            # Filtrar por termo de busca
            if termo_busca:
                termo_lower = termo_busca.lower()
                tabelas_filtradas = [
                    t for t in tabelas 
                    if termo_lower in t["Termo_Busca"]
                ]
                return tabelas_filtradas
            return tabelas
        
        return []
    
    except Exception as e:
        st.error(f"Erro ao buscar tabelas: {str(e)}")
        return []

# Função para baixar dados da tabela
def baixar_tabela(codigo_tabela, formato="csv"):
    """Baixa dados de uma tabela específica"""
    try:
        if formato == "csv":
            url = f"https://apisidra.ibge.gov.br/values/t/{codigo_tabela}/n1/all/v/all/p/last%201"
        elif formato == "json":
            url = f"https://apisidra.ibge.gov.br/values/t/{codigo_tabela}/n1/all/v/all/p/last%201?formato=json"
        
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            if formato == "csv":
                # Salvar CSV
                filename = f"downloads/tabela_{codigo_tabela}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return filename, response.text
            else:
                # Salvar JSON
                filename = f"downloads/tabela_{codigo_tabela}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(response.json(), f, ensure_ascii=False, indent=2)
                return filename, response.json()
        
        return None, None
    
    except Exception as e:
        st.error(f"Erro ao baixar tabela: {str(e)}")
        return None, None

# Função para visualizar dados
def visualizar_dados(codigo_tabela):
    """Visualiza os primeiros registros da tabela"""
    try:
        url = f"https://apisidra.ibge.gov.br/values/t/{codigo_tabela}/n1/all/v/all/p/last%201?formato=json"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            dados = response.json()
            if isinstance(dados, list) and len(dados) > 1:
                # Extrair cabeçalho e dados
                cabecalho = dados[0]
                valores = dados[1:]
                
                # Criar DataFrame
                df = pd.DataFrame(valores, columns=cabecalho)
                return df.head(10)
        return None
    
    except Exception as e:
        st.error(f"Erro ao visualizar dados: {str(e)}")
        return None

# Interface principal
col1, col2 = st.columns([2, 1])

with col1:
    termo_busca = st.text_input(
        "🔍 Digite o termo de busca:",
        placeholder="Ex: população, PIB, IPCA, agropecuária..."
    )

with col2:
    buscar_btn = st.button("🔍 Buscar Tabelas", type="primary", use_container_width=True)

# Buscar tabelas
if buscar_btn or termo_busca:
    if termo_busca:
        with st.spinner("Buscando tabelas..."):
            tabelas_encontradas = buscar_tabelas(termo_busca)
        
        if tabelas_encontradas:
            st.success(f"✅ Encontradas {len(tabelas_encontradas)} tabelas!")
            
            # Exibir tabelas encontradas
            for tabela in tabelas_encontradas:
                with st.container():
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        st.metric("📋 Código", tabela["Código"])
                    
                    with col2:
                        st.markdown(f"**📌 Nome:** {tabela['Nome'][:100]}...")
                    
                    with col3:
                        # Botão para visualizar
                        if st.button(f"👁️ Visualizar", key=f"view_{tabela['Código']}"):
                            st.session_state['codigo_visualizar'] = tabela['Código']
                        
                        # Botão para baixar
                        if st.button(f"⬇️ Baixar CSV", key=f"csv_{tabela['Código']}"):
                            st.session_state['codigo_baixar'] = tabela['Código']
                            st.session_state['formato'] = 'csv'
                        
                        if st.button(f"📄 Baixar JSON", key=f"json_{tabela['Código']}"):
                            st.session_state['codigo_baixar'] = tabela['Código']
                            st.session_state['formato'] = 'json'
                    
                    # Mostrar preview expandido
                    with st.expander(f"📊 Detalhes da Tabela {tabela['Código']}"):
                        st.write(f"**Nome completo:** {tabela['Nome']}")
                        
                        # Botão de visualização rápida
                        if st.button(f"Ver primeiros dados", key=f"preview_{tabela['Código']}"):
                            df_preview = visualizar_dados(tabela['Código'])
                            if df_preview is not None:
                                st.dataframe(df_preview, use_container_width=True)
                            else:
                                st.warning("Não foi possível carregar os dados para visualização")
        else:
            st.warning("⚠️ Nenhuma tabela encontrada para este termo. Tente outro termo.")
    else:
        st.info("ℹ️ Digite um termo de busca para encontrar tabelas.")

# Processar download
if 'codigo_baixar' in st.session_state:
    with st.spinner(f"Baixando tabela {st.session_state['codigo_baixar']}..."):
        filename, dados = baixar_tabela(
            st.session_state['codigo_baixar'], 
            st.session_state['formato']
        )
        
        if filename:
            st.success(f"✅ Tabela baixada com sucesso!")
            
            # Botão para download
            with open(filename, 'rb') as f:
                file_data = f.read()
                
                st.download_button(
                    label=f"📥 Clique aqui para baixar o arquivo ({st.session_state['formato'].upper()})",
                    data=file_data,
                    file_name=os.path.basename(filename),
                    mime='text/csv' if st.session_state['formato'] == 'csv' else 'application/json'
                )
            
            # Mostrar preview dos dados
            if st.session_state['formato'] == 'csv' and isinstance(dados, str):
                st.subheader("📊 Preview dos dados:")
                from io import StringIO
                df_preview = pd.read_csv(StringIO(dados), nrows=10)
                st.dataframe(df_preview, use_container_width=True)
            
            del st.session_state['codigo_baixar']
        else:
            st.error("❌ Erro ao baixar a tabela. Tente novamente.")

# Processar visualização
if 'codigo_visualizar' in st.session_state:
    df = visualizar_dados(st.session_state['codigo_visualizar'])
    if df is not None:
        st.subheader(f"📊 Visualização da Tabela {st.session_state['codigo_visualizar']}")
        st.dataframe(df, use_container_width=True)
        st.caption("Mostrando apenas os primeiros 10 registros")
    del st.session_state['codigo_visualizar']

# Sidebar com informações
with st.sidebar:
    st.header("ℹ️ Sobre")
    st.markdown("""
    Este aplicativo permite buscar e baixar tabelas do **SIDRA (IBGE)**.
    
    ### Como usar:
    1. Digite um termo de busca (ex: população, PIB, IPCA)
    2. Clique em buscar
    3. Selecione a tabela desejada
    4. Escolha baixar em CSV ou JSON
    
    ### Exemplos de busca:
    - população
    - PIB
    - IPCA
    - agropecuária
    - industrial
    - comércio
    
    ### Formatos disponíveis:
    - **CSV**: Para análise em Excel/Python
    - **JSON**: Para desenvolvimento/APIs
    
    ### Dados:
    Fonte oficial: [IBGE SIDRA](https://sidra.ibge.gov.br)
    """)
    
    st.header("📁 Downloads")
    if os.path.exists("downloads"):
        arquivos = [f for f in os.listdir("downloads") if f.endswith(('.csv', '.json'))]
        if arquivos:
            for arquivo in arquivos[-5:]:  # Mostra últimos 5
                st.text(f"📄 {arquivo}")
        else:
            st.text("Nenhum arquivo baixado ainda")

# Rodapé
st.markdown("---")
st.markdown(
    "Desenvolvido com ❤️ usando Streamlit | "
    "Dados fornecidos pelo IBGE SIDRA"
)
