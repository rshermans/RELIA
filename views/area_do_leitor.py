import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_echarts import st_echarts # type: ignore
import plotly.express as px              # type: ignore
import plotly.graph_objects as go        # type: ignore
import json
import os
from database import ( obter_roteiros_por_usuario, obter_obra_por_id,obter_categorias_unicas, 
                      obter_checkpoints, log_erro, salvar_feedback_automatizado, obter_roteiro_id_inicial,
                      get_db_connection, criar_ou_obter_roteiro, obter_perfil_por_id, atualizar_feedback_automatizado,
                      obter_roteiros_por_usuario , obter_nome_acao_por_id, determinar_nivel_bloom
                    )
import sqlitecloud #type: ignore
import requests
#from transformers import pipeline 
import pdfkit # type: ignore
import tempfile
import openai
from streamlit_elements import elements, mui, html  # type: ignore
import streamlit.components.v1 as components
from utils.email_utils import send_report_email
from streamlit_extras.stylable_container import stylable_container # type: ignore
import time
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import torch  # type: ignore
from nltk.corpus import stopwords
import networkx as nx
from wordcloud import WordCloud
from utils.criar_dataframes import inicializar_nltk
import markdown


# Definir estilos CSS personalizados
st.markdown("""
<style>
    .card-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: space-between;
    }
    .card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        flex: 1 1 45%;
        min-width: 300px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
        color: #00edfb;
    }
    .card-content {
        font-size: 14px;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar o  de análise de sentimento com PyTorch
#sentiment_analyzer = ("sentiment-analysis", grouped_entities=True ,framework="pt")

# Baixar e obter as stop words em português
inicializar_nltk()

# Definir variáveis globais
cores_niveis = {
    'Lembrar': '#00BFFF',
    'Compreender': '#00CED1',
    'Aplicar': '#000080',
    'Analisar': '#FF8C00',
    'Avaliar': '#C71585',
    'Criar': '#AF7AC5'
}

dados_conhecimento = {
    'Factual': {
        'Lembrar': ["Listar", "Reconhecer", "Identificar", "Definir", "Mencionar", "Recitar", "Enumerar"],
        'Compreender': ["Descrever", "Recordar", "Selecionar", "Resumir", "Esquematizar"],
        'Aplicar': ["Executar", "Demonstrar", "Utilizar"],
        'Analisar': ["Comparar", "Distinguir", "Investigar"],
        'Avaliar': ["Classificar", "Inferir", "Explorar"],
        'Criar': ["Criar", "Inventar", "Desenvolver"]
    },
    'Conceitual': {
        'Lembrar': ["Identificar", "Definir", "Relacionar", "Selecionar"],
        'Compreender': ["Inferir", "Parafrasear", "Associar", "Comparar"],
        'Aplicar': ["Calcular", "Classificar", "Implementar"],
        'Analisar': ["Diferenciar", "Integrar", "Identificar"],
        'Avaliar': ["Sintetizar", "Explorar", "Interpretar"],
        'Criar': ["Planejar", "Descobrir", "Produzir"]
    },
    'Procedural': {
        'Lembrar': ["Enumerar", "Recordar", "Selecionar"],
        'Compreender': ["Demonstrar", "Explicar", "Interpretar"],
        'Aplicar': ["Executar", "Utilizar", "Modificar"],
        'Analisar': ["Investigar", "Analisar", "Diferenciar"],
        'Avaliar': ["Integrar", "Explorar", "Desenvolver"],
        'Criar': ["Conceber", "Construir", "Propor"]
    },
    'Meta-Cognitivo': {
        'Lembrar': ["Reconhecer", "Identificar", "Definir"],
        'Compreender': ["Esquematizar", "Compreender", "Interpretar"],
        'Aplicar': ["Calcular", "Executar", "Modificar"],
        'Analisar': ["Analisar", "Investigar", "Diferenciar"],
        'Avaliar': ["Agir", "Explorar", "Inferir"],
        'Criar': ["Discorrer", "Inventar", "Elaborar"]
    }
}

def row_to_dict(row):
    return {key: row[key] for key in row.keys()}


def tela_area_leitor():
    # Cabeçalho do aplicativo
    st.header("Área do Leitor")
    st.title("Sua Jornada Literária 📚")

    # Barra de navegação
    tabs = st.tabs(["Meus Roteiros", "Conquistas", "Comunidade", "Desafios"])

    with tabs[0]:
        exibir_roteiros()

    with tabs[1]:
        exibir_conquistas()

    with tabs[2]:
        exibir_comunidade()

    with tabs[3]:
        exibir_desafios()
        
        
    with tabs[0]:
        st.subheader("")#Relatório de Desempenho
        
# Crie um espaço reservado no início da sua aplicação
popup_placeholder = st.empty()

        
def exibir_roteiros():
    st.subheader("Meus Roteiros")
    
     
    # Obter roteiros do usuário atual
    usuario_id = st.session_state.get('usuario_id')
    if not usuario_id:
        st.error("Usuário não identificado. Faça login novamente.")
        return

    roteiros = obter_roteiros_por_usuario(usuario_id)
    
    if not roteiros:
        st.info("Você ainda não possui roteiros. Comece uma nova leitura!")
        return
    
     # Obter categorias únicas do banco de dados
    categorias = obter_categorias_unicas(usuario_id)
    categorias = ["Todos"] + sorted(categorias)  # Adiciona "Todos" no início e ordena as demais

       
    # Filtros e busca
    col1, col2 = st.columns([2,1])
    with col1:
        busca = st.text_input("Buscar roteiros", placeholder="Digite o título ou autor...")
    with col2:
        categoria = st.selectbox("Categoria", categorias)
    
    
    # Aplicar filtros
    roteiros_filtrados = []

    for roteiro_row in roteiros:
        roteiro = row_to_dict(roteiro_row)
        obra_row = obter_obra_por_id(roteiro['obra_id'])
        if obra_row:
            obra = row_to_dict(obra_row)
            
            # Aplicar filtro de categoria (gênero)
            if categoria != "Todos" and obra.get('genero') != categoria:
                continue  # Pula para o próximo roteiro se o gênero não corresponder

            # Aplicar filtro de busca
            if busca:
                busca_lower = busca.lower()
                titulo = obra.get('titulo', '').lower()
                autor = obra.get('autor', '').lower()
                if busca_lower not in titulo and busca_lower not in autor:
                    continue  # Pula se a busca não corresponder ao título nem ao autor
            
            # Se passar por todos os filtros, adiciona à lista filtrada
            roteiros_filtrados.append(roteiro)
    
    
    if not roteiros_filtrados:
        st.info("Nenhum roteiro encontrado com os critérios selecionados.")
        return
         
    for roteiro in roteiros_filtrados:
        checkpoints = obter_checkpoints(roteiro['id'])
        obra_row = obter_obra_por_id(roteiro['obra_id'])
        
        if obra_row:
            obra = row_to_dict(obra_row)
            
            with st.container():
                col1, col2, col3 = st.columns([1,2,1])
                with col1:
                    st.image(f"https://via.placeholder.com/100x150?text={obra.get('titulo', 'Imagem')}")
                with col2:
                    st.subheader(obra.get('titulo', 'Título Desconhecido'))
                    st.write(f"Autor: {obra.get('autor', 'Desconhecido')}")
                    st.write(f"Gênero: {obra.get('genero', 'Não especificado')}")
                    
                    # Cálculo seguro da pontuação total
                    pontuacao_total = 0
                    if checkpoints:  # Verifica se há checkpoints
                        pontuacao_total = sum(
                            checkpoint.get('nota_llm', 0) or 0  # Use 0 se nota_llm for None
                            for checkpoint in checkpoints
                        )
                    
                    _, progresso = determinar_nivel_e_progresso(pontuacao_total)
                    
                    # Barra de progresso
                    st.progress(progresso)
                    st.write(f"{progresso*100:.0f}% concluído")
                   
                   
                with col3:
                    if st.button("Continuar", key=f"continuar_{roteiro['id']}", type="primary"):
                        # Confirmar que o roteiro está configurado e pronto para continuar
                        continuar_roteiro(roteiro)  # Função para continuar o roteiro

                    if st.button("Relatório", key=f"relatorio_{roteiro['id']}"):
                        mostrar_relatorio_popup(roteiro)
            
                # Placeholder para o popup do relatório
                popup_placeholder = st.empty()
                if 'relatorio_aberto' in st.session_state and st.session_state['relatorio_aberto'] == roteiro['id']:
                    with popup_placeholder.container():
                        #st.markdown("### Relatório")
                        exibir_relatorio(roteiro)
                        if st.button("✖️ Fechar Relatório", key=f"fechar_{roteiro['id']}", type="secondary", use_container_width=True ):
                            st.session_state['relatorio_aberto'] = None
                            st.rerun()
                st.divider()


def mostrar_relatorio_popup(roteiro):
    st.session_state['relatorio_aberto'] = roteiro['id']
    st.session_state['roteiro_id'] = roteiro['id']
    st.rerun()


def determinar_nivel_e_progresso(pontuacao):
    niveis = ['Lembrar', 'Compreender', 'Aplicar', 'Analisar', 'Avaliar', 'Criar']
    limites = [15, 45, 91, 153, 190, 253]
    for i, (nivel, limite) in enumerate(zip(niveis, limites)):
        if pontuacao <= limite:
            progresso = (pontuacao - (limites[i-1] if i > 0 else 0)) / (limite - (limites[i-1] if i > 0 else 0))
            return nivel, (i + progresso) / len(niveis)
    return 'Mestre', 1.0


def exibir_relatorio(roteiro):
    
     # Uso de containers e elementos de design para organização
    with st.container():
      
       # Criar mapeamentos
    # Mapeamento de acao_id para detalhes da ação
        conn = get_db_connection()
        if not conn:
            st.error("Falha na conexão com o banco de dados.")
            return

        try:
            cursor = conn.cursor()
            query = "SELECT id, nomes_acao, nivel_bloom FROM acoes"
            cursor.execute(query)
            rows = cursor.fetchall()

            # Converte cada linha para um dicionário usando os nomes das colunas
            columns = [column[0] for column in cursor.description]
            # Imprima as colunas para verificar se estão sendo identificadas corretamente
            print(columns)  # Deve resultar em algo como ['id', 'nomes_acao', 'nivel_bloom']
            # Agora, converta os resultados em dicionários usando zip()
            acoes_data = [dict(zip(columns, row)) for row in rows]
            
            for acao in acoes_data:
             print("acoes_data",acao)  # Verifique se 'id' está presente em cada dicionário
        except sqlitecloud.Error as e:
            st.error(f"Erro ao consultar a tabela 'acoes': {e}")
            conn.close()
            return

        acoes_map = {acao['id']: {'nomes_acao': acao['nomes_acao'], 'nivel_bloom': acao['nivel_bloom']} for acao in acoes_data}

        # Criar mapeamento reverso de nomes_acao para tipo_conhecimento
        action_to_conhecimento = {}
        for tipo, niveis in dados_conhecimento.items():
            for nivel, acoes in niveis.items():
                for acao in acoes:
                    action_to_conhecimento[acao.lower()] = tipo
      
    try:
        # Obter obra e checkpoint
        obra = obter_obra_por_id(roteiro['obra_id'])
        if not obra:
            st.error("Obra não encontrada.")
            return

        checkpoints = obter_checkpoints(roteiro['id'])
        if not checkpoints:
            st.warning("Nenhum checkpoint encontrado para este roteiro.")
            #checkpoints = []
            return
        else:
            # Converter cada checkpoint de sqlite3.Row para dicionário
            checkpoints = [row_to_dict(cp) for cp in checkpoints]
            

        # Informações do usuário
        usuario = st.session_state.get('usuario')
        if not usuario:
            st.error("Usuário não identificado.")
            return


        st.title(f"Relatório de Leitura: {obra['titulo']} de {obra['autor']}")
                
        # Informações do usuário e da obra
        # Layout Responsivo
        col1, col2 = st.columns([1, 3], gap="small")
        with col1:
            st.image("imagens/bit.ly_Zoho-RELIA.png", width=100, caption="Link inquérito sobre RELIA")
            st.markdown('[Inquérito sobre RELIA](https://bit.ly/Zoho-RELIA)')
            pass
        with col2:
            st.subheader(usuario['nome'])
            #pontuacao_total = sum(cp['nota_llm'] for cp in checkpoints if cp['nota_llm'] is not None)
            pontuacao_total = sum(cp['nota_llm'] for cp in checkpoints if isinstance(cp.get('nota_llm'), (int, float)))
            nivel_atual, progresso_total = determinar_nivel_e_progresso(pontuacao_total)
            st.write(f"**Nível Cognitivo Atual:** {nivel_atual}")
            st.write(f"**Pontuação Total:** {pontuacao_total} pts")

        # Progresso geral na obra baseado no nível cognitivo
        st.subheader("Progresso na Obra")
        progresso_bar = st.progress(progresso_total)
        st.write(f"{progresso_total * 100:.0f}% concluído")
        
        
        # Uso de Alt Text para Imagens e Gráficos
        #st.image("https://via.placeholder.com/100x150?text=Imagem", caption="Imagem da Obra", use_column_width=True)

        
        # Acessibilidade: Contraste e Tamanho da Fonte
        st.markdown(
            """
            <style>
                .reportview-container {
                    font-size: 18px;
                }
                
            </style>
            """,
            unsafe_allow_html=True
        )

        # Tabela de detalhes dos checkpoints
        st.subheader("Detalhes dos Checkpoints")

        try:
            df_checkpoints = pd.DataFrame([
                {
                    'Nível': cp['nivel_taxonomia'],
                    'Pergunta': cp['pergunta'],
                    'Resposta': cp['resposta'],
                    'Feedback': cp['feedback_llm']
                } for cp in checkpoints
            ])
            if not df_checkpoints.empty:
                st.markdown(
                    """
                    Nesta tabela, você pode revisar cada checkpoint alcançado durante a leitura da obra. 
                    Cada entrada detalha o nível cognitivo associado, a pergunta feita, sua resposta e o feedback recebido.
                    """
                )
                st.dataframe(df_checkpoints, use_container_width=True)  # Removendo o índice para melhor visualização
            else:
                st.write("Nenhum checkpoint para exibir.")

            # Verificar se há checkpoints suficientes
            if len(checkpoints) < 3:
                st.warning("Menos de 3 checkpoints disponíveis. Alguns recursos podem não estar disponíveis.")

            # Criar o DataFrame Enriquecido
            if checkpoints:
                df_enriquecido = criar_dataframe_enriquecido(checkpoints, acoes_map, action_to_conhecimento)
            else:
                df_enriquecido = pd.DataFrame()  # Garantir que a variável é inicializada

            st.markdown("---")

            # Criar duas colunas
            col1, col2 = st.columns(2)

            # Coluna 1: Texto explicativo
            with col1:
                with st.container(border=True):
                        st.markdown("#### Introdução")
                        st.markdown(
                            """
                            Detalhes dos Checkpoints Nesta tabela, você pode revisar cada checkpoint alcançado durante a leitura da obra. Cada entrada detalha o nível cognitivo associado, a pergunta feita, sua resposta e o feedback recebido.

                            #### Análise dos Checkpoints
                            Este DataFrame apresenta uma análise mais detalhada dos checkpoints, agregando informações sobre os tipos de conhecimento, níveis cognitivos, ações realizadas e pontuações atribuídas. Essa visão abrangente permite identificar áreas de força e oportunidades para desenvolvimento contínuo.

                            #### Insights Possíveis
                            - Desempenho Consistente: Se as pontuações se mantêm altas nos níveis superiores, isso indica uma forte capacidade de pensamento crítico e criativo.
                            - Áreas de Melhoria: Baixas pontuações em certos níveis cognitivos podem sinalizar a necessidade de foco adicional nessas áreas específicas.
                            - Feedback Utilizado: Analisar o feedback recebido pode ajudar a entender melhor como aprimorar respostas futuras e fortalecer conhecimentos.
                            """
                            )

            # Coluna 2: DataFrame
            with col2:
                with st.container(border=True):
                        st.markdown("#### Análise dos Checkpoints")
                        st.markdown(
                            """
                            Este DataFrame apresenta uma análise mais detalhada dos checkpoints, agregando informações sobre os tipos de conhecimento, níveis cognitivos, ações realizadas e pontuações atribuídas.
                            """
                        )

                        # Exibir o DataFrame no Streamlit
                        if not df_enriquecido.empty:
                            st.dataframe(df_enriquecido, use_container_width=True)  # Removendo o índice para melhor visualização
                        else:
                            st.write("Nenhum dado disponível para exibir.")
        
            
            if not df_enriquecido.empty:
                # Gráfico de Frequência de Palavras
                # Gráfico de Frequência de Palavras
                tematicas = extrair_tematicas(checkpoints)
                # Extração de entidades nomeadas
                entidades = extrair_entidades(checkpoints)
            
            st.markdown("---")
                
        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar o relatório: {e}")
            log_erro(usuario['id'], str(e))
        
        
                
       # Adicionar visualizações conforme planejado
        if not df_enriquecido.empty:
            
            # Visualizações
            st.markdown("### Visualizações")
            col1, col2 = st.columns(2)
            
            with col1:
                with st.container(border=True):
                        # Radar Chart com Explicação
                        st.markdown("#### Distribuição das Ações nas Dimensões de Conhecimento através dos Níveis de Bloom")
                        st.markdown("""
                        Este gráfico de radar ilustra como as diferentes dimensões de conhecimento (**Factual**, **Conceitual**, **Procedural**, **Meta-Cognitivo**) se distribuem através dos níveis da Taxonomia de Bloom (**Lembrar**, **Compreender**, **Aplicar**, **Analisar**, **Avaliar**, **Criar**). 
                        Cada linha representa uma dimensão de conhecimento, permitindo comparar como cada uma contribui para os diferentes níveis cognitivos.
                        """)
                        fig_radar = grafico_radar_bloom(df_enriquecido)
                        if fig_radar:
                            st.plotly_chart(fig_radar, use_container_width=True)

            with col2:
                with st.container(border=True):
                        # Heatmap Temporal com Explicação
                        st.markdown("#### Evolução das Ações nas Dimensões de Conhecimento e Níveis de Bloom ao Longo do Tempo")
                        st.markdown("""
                        Este heatmap apresenta a frequência das ações realizadas nas diferentes dimensões de conhecimento e níveis de Bloom ao longo dos checkpoints. 
                        As cores indicam a intensidade das ações, permitindo identificar tendências e padrões de desenvolvimento cognitivo ao longo do tempo.
                        """)
                        fig_heatmap = heatmap_bloom_temporal(df_enriquecido, checkpoints)
                        if fig_heatmap:
                            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            st.markdown("---")
            
            col3, col4 = st.columns(2)
            
            with col3:
                with st.container(border=True):
                    if not df_enriquecido.empty:
                        # Gráfico Interativo de Progresso nos Níveis Cognitivos (2D)
                        st.markdown("### Progresso nos Níveis Cognitivos")
                        
                        # Adicionando texto de introdução
                        st.markdown("""
                            Cada eixo representa um nível cognitivo específico, e a intensidade das cores indica a frequência ou pontuação das ações realizadas em cada nível.
                            """)
                        fig_2d, _ = criar_grafico_2d(checkpoints, nivel_atual)
                        st.plotly_chart(fig_2d, use_container_width=True)
           
            with col4:
                with st.container(border=True):
                        st.markdown("#### Nuvem de Palavras")
                        st.markdown("""
                        A nuvem de palavras destaca as ações mais comuns realizadas, proporcionando uma visão rápida das atividades predominantes.
                        
                        
                        """)
                        tematicas = extrair_tematicas(checkpoints)
                        fig_wordcloud = criar_grafico_wordcloud(tematicas)
                        st.pyplot(fig_wordcloud)
            
                
            st.markdown("---")
                                        
        else:
            st.write("Nenhum dado disponível para exibir.")
            
         
        # Conclusão com Feedback do Usuário
        #st.subheader("Conclusão")
        
        # Estilos CSS personalizados
        st.markdown("""
        <style>
            .feedback-card {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .feedback-title {
                color: #00edfb;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #00edfb;
            }
            .feedback-content {
                color: #000000;
                font-size: 16px;
                line-height: 1.6;
                white-space: pre-wrap;
            }
            .feedback-container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                padding: 10px;
            }
        </style>
        """, unsafe_allow_html=True)
        
        api_key = openai.api_key = st.secrets["OPENAI"]["OPENAI_API_KEY"]
        
                
        # Verificar se já existe feedback automatizado para o roteiro
        feedback_existente = obter_feedback_automatizado(roteiro['id'])

        # Seção de exibição do feedback
        if feedback_existente:
            st.markdown("## 🌟 Análise do Roteiro")
            
            # Criar quatro colunas com largura igual
            col1, col2, col3, col4 = st.columns(4)

            # Container: Resumo dos Checkpoints
            with col1:
                feedback_html1 = f"""
                <div class="feedback-card">
                    <div class="feedback-title">📋 Resumo dos Checkpoints</div>
                    <div class="feedback-content">{feedback_existente['resumo_checkpoints']}</div>
                </div>
                """
                st.markdown(feedback_html1, unsafe_allow_html=True)

            # Container: Recomendações
            with col2:
                feedback_html3 = f"""
                <div class="feedback-card">
                    <div class="feedback-title">🛠 Recomendações</div>
                    <div class="feedback-content">{formatar_recomendacoes(feedback_existente['recomendacoes'])}</div>
                </div>
                """
                st.markdown(feedback_html3, unsafe_allow_html=True)

            # Container: Leituras Relacionadas
            with col3:
                feedback_html4 = f"""
                <div class="feedback-card">
                    <div class="feedback-title">📚 Leituras Relacionadas</div>
                    <div class="feedback-content">{formatar_leituras_relacionadas(feedback_existente['insights'])}</div>
                </div>
                """
                st.markdown(feedback_html4, unsafe_allow_html=True)

            # Container: Feedback Motivacional
            with col4:
                feedback_html2 = f"""
                <div class="feedback-card">
                    <div class="feedback-title">🎉 Feedback</div>
                    <div class="feedback-content">{feedback_existente['feedback_motivacional']}</div>
                </div>
                """
                st.markdown(feedback_html2, unsafe_allow_html=True)

        else:
            try:
                # Gerar novos feedbacks
                resumo_checkpoints, feedback_motivacional, recomendacoes = gerar_conclusao(checkpoints, api_key)
                with st.spinner('Gerando insights...'):
                    insights = gerar_recomendacoes(obra['titulo'], api_key)

                # Garantir que o conteúdo está formatado em markdown
                resumo_checkpoints = markdown.markdown(resumo_checkpoints) if resumo_checkpoints else ""
                recomendacoes = markdown.markdown(recomendacoes) if recomendacoes else ""
                insights = markdown.markdown(insights) if insights else ""
                feedback_motivacional = markdown.markdown(feedback_motivacional) if feedback_motivacional else ""

                # Salvar o feedback formatado
                salvar_feedback_automatizado(roteiro['id'], resumo_checkpoints, feedback_motivacional, recomendacoes, insights)
                st.toast("Feedback automatizado gerado com sucesso!")

                # Recuperar o feedback salvo para exibição
                feedback_existente = obter_feedback_automatizado(roteiro['id'])

                # Exibir o novo feedback
                st.markdown("## 🌟 Análise do Roteiro")

                # Criar quatro colunas com largura igual
                col1, col2, col3, col4 = st.columns(4)

                # Container: Resumo dos Checkpoints
                with col1:
                    feedback_html1 = f"""
                    <div class="feedback-card">
                        <div class="feedback-title">📋 Resumo dos Checkpoints</div>
                        <div class="feedback-content">{feedback_existente['resumo_checkpoints']}</div>
                    </div>
                    """
                    st.markdown(feedback_html1, unsafe_allow_html=True)

                # Container: Recomendações
                with col2:
                    feedback_html3 = f"""
                    <div class="feedback-card">
                        <div class="feedback-title">🛠 Recomendações</div>
                        <div class="feedback-content">{feedback_existente['recomendacoes']}</div>
                    </div>
                    """
                    st.markdown(feedback_html3, unsafe_allow_html=True)

                # Container: Leituras Relacionadas
                with col3:
                    feedback_html4 = f"""
                    <div class="feedback-card">
                        <div class="feedback-title">📚 Leituras Relacionadas</div>
                        <div class="feedback-content">{feedback_existente['insights']}</div>
                    </div>
                    """
                    st.markdown(feedback_html4, unsafe_allow_html=True)

                # Container: Feedback Motivacional
                with col4:
                    feedback_html2 = f"""
                    <div class="feedback-card">
                        <div class="feedback-title">🎉 Feedback</div>
                        <div class="feedback-content">{feedback_existente['feedback_motivacional']}</div>
                    </div>
                    """
                    st.markdown(feedback_html2, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erro ao gerar conclusão automatizada: {e}")
                print(f"Erro detalhado: {str(e)}")            
            
               
        st.markdown("---") 
                      
               # Opção para exportar feedback
        email_para_envio = st.text_input("Digite o email para envio do relatório:", value=usuario['email'])
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(" 📨 Enviar Relatório para o Email", type="primary",key="email_button"):
                if email_para_envio:
                    enviar_relatorio_por_email(
                        usuario_id=usuario['id'],
                        obra_titulo=obra['titulo'],
                        resumo_checkpoints=feedback_existente['resumo_checkpoints'],
                        feedback_motivacional=feedback_existente['feedback_motivacional'],
                        recomendacoes = feedback_existente['recomendacoes'],
                        insights=feedback_existente['insights'],
                        progresso_total=progresso_total,
                        checkpoints=checkpoints,
                        nivel_atual=nivel_atual,
                        email_destino=email_para_envio
                    )
                else:
                    st.warning("Por favor, insira um email válido para o envio do relatório.")
                #st.success("Relatório enviado com sucesso!")
                    
        with col2:
            
            if st.button("⚠️ Gerar Novo Feedback",
                                key="feedback_button",
                                help="Clique para gerar um novo feedback automatizado",
                                type="secondary",
                                use_container_width=True,
                            ):
                if st.session_state.get('relatorio_aberto'):
                    with st.spinner("Gerando novo feedback automatizado..."):
                        try:
                            resumo_checkpoints, feedback_motivacional, recomendacoes = gerar_conclusao(checkpoints, api_key)
                            insights = gerar_recomendacoes(obra['titulo'], api_key)
                            atualizar_feedback_automatizado(roteiro['id'], resumo_checkpoints, feedback_motivacional, recomendacoes, insights)
                            st.toast("Novo feedback automatizado gerado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao gerar novo feedback: {str(e)}")
                            
                    # Limpar o estado de relatorio_aberto
                    st.session_state['relatorio_aberto'] = None
                    with st.spinner("Processando... Aguarde um momento!"):
                        time.sleep(6)  # Delay de 3 segundos 
                        st.session_state["tela"] = "area_leitor"
                        st.warning("Feche o relatório para validar a atualização.")
                        
                                                             
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o relatório: {e}")
        log_erro(usuario['id'], str(e))
       
   
                
    
def gerar_html_relatorio(usuario_nome, obra_titulo, progresso_total, resumo_checkpoints, feedback_motivacional, recomendacoes, insights, dados_nlp, checkpoints_df, graficos):
    html_conteudo = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            .section {{
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            .section-title {{
                color: #00edfb;
                font-size: 24px;
                margin-bottom: 15px;
                border-bottom: 2px solid #00edfb;
                padding-bottom: 5px;
            }}
            .progress-bar {{
                background-color: #e9ecef;
                border-radius: 5px;
                height: 20px;
                overflow: hidden;
            }}
            .progress {{
                background-color: #00edfb;
                height: 100%;
                width: {progresso_total * 100}%;
            }}
            .card-container {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }}
            .card {{
                background-color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .card-title {{
                color: #00edfb;
                font-size: 18px;
                margin-bottom: 10px;
            }}
            .graph-container {{
                margin: 20px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
                color: #00edfb;
            }}
            .topic-item {{
                margin: 10px 0;
                padding-left: 20px;
                position: relative;
            }}
            .topic-item:before {{
                content: "•";
                color: #00edfb;
                position: absolute;
                left: 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>Relatório de Leitura: {obra_titulo}</h1>
                <p>Leitor: {usuario_nome}</p>
            </div>
            <div class="progress-info">
                <p>Progresso Total: {progresso_total * 100:.0f}%</p>
                <div class="progress-bar">
                    <div class="progress"></div>
                </div>
            </div>
        </div>

        <!-- Detalhes dos Checkpoints -->
        <div class="section">
            <h2 class="section-title">Detalhes dos Checkpoints</h2>
            <div class="table-container">
                {checkpoints_df.to_html(classes='dataframe', index=False)}
            </div>
        </div>

        <!-- Análise NLP -->
        <div class="section">
            <h2 class="section-title">Análise de Linguagem</h2>
            <div class="card-container">
                {dados_nlp}
            </div>
        </div>

        <!-- Visualizações -->
        <div class="section">
            <h2 class="section-title">Visualizações</h2>
            <div class="graph-container">
                {graficos}
            </div>
        </div>

        <!-- Feedback e Recomendações -->
        <div class="section">
            <h2 class="section-title">Análise do Roteiro</h2>
            <div class="card-container">
                <div class="card">
                    <div class="card-title">📋 Resumo dos Checkpoints</div>
                    <div class="content">{resumo_checkpoints}</div>
                </div>
                <div class="card">
                    <div class="card-title">🎉 Feedback</div>
                    <div class="content">{feedback_motivacional}</div>
                </div>
                <div class="card">
                    <div class="card-title">🛠 Recomendações</div>
                    <div class="content">{recomendacoes}</div>
                </div>
                <div class="card">
                    <div class="card-title">📚 Leituras Relacionadas</div>
                    <div class="content">{insights}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_conteudo


def criar_grafico_3d(checkpoints):
    cores_niveis = {
        'Lembrar': '#A2D9CE',      # Azul Claro
        'Compreender': '#A9DFBF',  # Verde Claro
        'Aplicar': '#5499C7',      # Azul
        'Analisar': '#F5B041',     # Laranja Claro
        'Avaliar': '#EC7063',      # Vermelho
        'Criar': '#AF7AC5'         # Roxo
    }

    data = []
    for checkpoint in checkpoints:
        data.append({
            'Nível': checkpoint['nivel_taxonomia'],
            'Pontuação': checkpoint['nota_llm'],
            'Tipo de Conhecimento': checkpoint.get('tipo_conhecimento', 'Desconhecido')
        })

    df = pd.DataFrame(data)

    fig = go.Figure()

    for tipo in df['Tipo de Conhecimento'].unique():
        df_tipo = df[df['Tipo de Conhecimento'] == tipo]
        fig.add_trace(go.Scatter3d(
            x=df_tipo['Nível'],
            y=[tipo] * len(df_tipo),
            z=df_tipo['Pontuação'],
            mode='markers',
            marker=dict(size=10, opacity=0.8),
            name=tipo
        ))

    fig.update_layout(
        title='Progresso por Tipo de Conhecimento e Nível Cognitivo (3D)',
        scene=dict(
            xaxis_title='Nível Cognitivo',
            yaxis_title='Tipo de Conhecimento',
            zaxis_title='Pontuação'
        )
    )

    return fig


 # Definir cores para diferentes níveis e ações
cores_niveis = {
    'Lembrar': '#A2D9CE',      # Azul Claro
        'Compreender': '#A9DFBF',  # Verde Claro
        'Aplicar': '#5499C7',      # Azul
        'Analisar': '#F5B041',     # Laranja Claro
        'Avaliar': '#EC7063',      # Vermelho
        'Criar': '#AF7AC5'         # Roxo
}

# Dicionário com dados do conhecimento (Atualizado)
dados_conhecimento = {
    'Factual': {
        'Lembrar': ["Listar", "Reconhecer", "Identificar", "Definir", "Mencionar", "Recitar", "Enumerar"],
        'Compreender': ["Descrever", "Recordar", "Selecionar", "Resumir", "Esquematizar"],
        'Aplicar': ["Executar", "Demonstrar", "Utilizar"],
        'Analisar': ["Comparar", "Distinguir", "Investigar"],
        'Avaliar': ["Classificar", "Inferir", "Explorar"],
        'Criar': ["Criar", "Inventar", "Desenvolver"]
    },
    'Conceitual': {
        'Lembrar': ["Identificar", "Definir", "Relacionar", "Selecionar"],
        'Compreender': ["Inferir", "Parafrasear", "Associar", "Comparar"],
        'Aplicar': ["Calcular", "Classificar", "Implementar"],
        'Analisar': ["Diferenciar", "Integrar", "Identificar"],
        'Avaliar': ["Sintetizar", "Explorar", "Interpretar"],
        'Criar': ["Planejar", "Descobrir", "Produzir"]
    },
    'Procedural': {
        'Lembrar': ["Enumerar", "Recordar", "Selecionar"],
        'Compreender': ["Demonstrar", "Explicar", "Interpretar"],
        'Aplicar': ["Executar", "Utilizar", "Modificar", "Usar"],
        'Analisar': ["Investigar", "Analisar", "Diferenciar"],
        'Avaliar': ["Integrar", "Explorar", "Desenvolver"],
        'Criar': ["Conceber", "Construir", "Propor"]
    },
    'Meta-Cognitivo': {
        'Lembrar': ["Reconhecer", "Identificar", "Definir"],
        'Compreender': ["Esquematizar", "Compreender", "Interpretar"],
        'Aplicar': ["Calcular", "Executar", "Modificar"],
        'Analisar': ["Analisar", "Investigar", "Diferenciar"],
        'Avaliar': ["Agir", "Explorar", "Inferir"],
        'Criar': ["Discorrer", "Inventar", "Elaborar"]
    }
}

# Definir os tipos de conhecimento
tipos_conhecimento = ['Factual', 'Conceitual', 'Procedural', 'Meta-Cognitivo']


def criar_grafico_3d_com_acoes(checkpoints):
       
   # Dicionário com dados do conhecimento (Atualizado)
    dados_conhecimento = {
        'Factual': {
            'Lembrar': ["Listar", "Reconhecer", "Identificar", "Definir", "Mencionar", "Recitar", "Enumerar"],
            'Compreender': ["Descrever", "Recordar", "Selecionar", "Resumir", "Esquematizar"],
            'Aplicar': ["Executar", "Demonstrar", "Utilizar"],
            'Analisar': ["Comparar", "Distinguir", "Investigar"],
            'Avaliar': ["Classificar", "Inferir", "Explorar"],
            'Criar': ["Criar", "Inventar", "Desenvolver"]
        },
        'Conceitual': {
            'Lembrar': ["Identificar", "Definir", "Relacionar", "Selecionar"],
            'Compreender': ["Inferir", "Parafrasear", "Associar", "Comparar"],
            'Aplicar': ["Calcular", "Classificar", "Implementar"],
            'Analisar': ["Diferenciar", "Integrar", "Identificar"],
            'Avaliar': ["Sintetizar", "Explorar", "Interpretar"],
            'Criar': ["Planejar", "Descobrir", "Produzir"]
        },
        'Procedural': {
            'Lembrar': ["Enumerar", "Recordar", "Selecionar"],
            'Compreender': ["Demonstrar", "Explicar", "Interpretar"],
            'Aplicar': ["Executar", "Utilizar", "Modificar"],
            'Analisar': ["Investigar", "Analisar", "Diferenciar"],
            'Avaliar': ["Integrar", "Explorar", "Desenvolver"],
            'Criar': ["Conceber", "Construir", "Propor"]
        },
        'Meta-Cognitivo': {
            'Lembrar': ["Reconhecer", "Identificar", "Definir"],
            'Compreender': ["Esquematizar", "Compreender", "Interpretar"],
            'Aplicar': ["Calcular", "Executar", "Modificar"],
            'Analisar': ["Analisar", "Investigar", "Diferenciar"],
            'Avaliar': ["Agir", "Explorar", "Inferir"],
            'Criar': ["Discorrer", "Inventar", "Elaborar"]
        }
    }
        
    
    # Definir os tipos de conhecimento
    tipos_conhecimento = ['Factual', 'Conceitual', 'Procedural', 'Meta-Cognitivo']


    # Buscar lista de ações e níveis de Bloom da tabela 'acoes'
    conn = get_db_connection()
    query = "SELECT id, nomes_acao, nivel_bloom FROM acoes"
    cursor = conn.execute(query)
    acoes_data = cursor.fetchall()
    
    
    acoes_por_nivel = {}
    for acao in acoes_data:
        acao_id, nomes_acao, nivel_bloom = acao
        if nivel_bloom not in acoes_por_nivel:
            acoes_por_nivel[nivel_bloom] = []
        acoes_por_nivel[nivel_bloom].append((nomes_acao))

    # Inicializar os dados para o gráfico 3D
    data = []

    for checkpoint in checkpoints:
        nivel_taxonomia = checkpoint['nivel_taxonomia']
        acao_id = checkpoint['acao_id']  
        nota = checkpoint['nota_llm']

        # Buscar o nome da ação correspondente ao ID
        acao_info = next((acao for acao in acoes_data if acao[0] == acao_id), None)
        if acao_info:
            nome_acao = acao_info[1]

            # Determinar o tipo de conhecimento com base na ação usando o dicionário
            tipos_conhecimento = None
            for tipo, niveis in dados_conhecimento.items():
                for nivel, acoes in niveis.items():
                    if nome_acao in acoes:
                        tipo_conhecimento = tipo
                        break
                if tipo_conhecimento:
                    break

            if tipos_conhecimento and nivel_taxonomia in cores_niveis:
                data.append({
                    'Tipo de Conhecimento': tipos_conhecimento,
                    'Nível Cognitivo': nivel_taxonomia,
                    'Ação Realizada': nome_acao,
                    'Pontuação': nota
                })
                
     # Verificar se existem dados suficientes para o gráfico
    if not data:
        st.warning("Nenhum dado suficiente para gerar o gráfico 3D. Por favor, realize mais ações para ver o progresso.")
        return None
                
    df = pd.DataFrame(data)

    # Criar o gráfico 3D
    fig = go.Figure()
    
    for tipo in dados_conhecimento.keys():
        df_tipo = df[df['Tipo de Conhecimento'] == tipo]

        for nivel in cores_niveis.keys():
                df_nivel = df_tipo[df_tipo['Nível Cognitivo'] == nivel]

                # Adicionar trace para cada nível
                fig.add_trace(go.Scatter3d(
                    x=[nivel] * len(df_nivel),
                    y=[tipo] * len(df_nivel),
                    z=df_nivel['Pontuação'],
                    text=df_nivel['Ação Realizada'],
                    mode='markers+text',
                    marker=dict(
                        size=10,
                        color=cores_niveis[nivel],
                        opacity=0.8
                    ),
                    name=f"{tipo} - {nivel}"
                ))

    # Ajustar o layout do gráfico
    fig.update_layout(
        title='Progresso Cognitivo com Ações Específicas (3D)',
        scene=dict(
            xaxis_title='Nível Cognitivo',
            yaxis_title='Tipo de Conhecimento',
            zaxis_title='Pontuação'
        ),
        margin=dict(l=0, r=0, b=0, t=50)
    )
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.write_image(temp_file.name)

    return fig, temp_file.name


def determinar_nivel_e_progresso(pontuacao):
    niveis = ['Lembrar', 'Compreender', 'Aplicar', 'Analisar', 'Avaliar', 'Criar']
    limites = [15, 45, 91, 153, 190, 253]
    for i, (nivel, limite) in enumerate(zip(niveis, limites)):
        if pontuacao <= limite:
            progresso = (pontuacao - (limites[i-1] if i > 0 else 0)) / (limite - (limites[i-1] if i > 0 else 0))
            return nivel, (i + progresso) / len(niveis)
    return 'Mestre', 1.0


def gerar_conclusao(checkpoints, api_key):
    # Calcular a pontuação total
    total_pontos = sum(cp['nota_llm'] for cp in checkpoints if cp['nota_llm'] is not None)
    
   
    # Criar um resumo dos checkpoints
    resumo_checkpoints = [
        {
            "tipo_conhecimento": cp.get('tipo_conhecimento', 'Desconhecido'),
            "nivel_cognitivo": cp.get('nivel_taxonomia', 'Desconhecido'),
            "nota": cp.get('nota_llm', 'N/A'),
            "acao": cp.get('acao_id', 'N/A'),
            "pergunta": cp.get('pergunta', 'N/A'),
            "resposta": cp.get('resposta', 'N/A')
        }
        for cp in checkpoints
    ]

    # Mensagem para a LLM com a análise mais aprofundada
    prompt = f"""
    Você é um assistente de feedback educacional especializado em aprendizagem cognitiva. 
    Analisando os dados de um estudante que participou de atividades de leitura, forneça uma visão holística do seu progresso.

    Dados do estudante:
    - Pontuação total: {total_pontos}
    - Resumo dos checkpoints: {json.dumps(resumo_checkpoints, ensure_ascii=False)}

    Com base nesses dados, forneça uma análise detalhada no seguinte formato JSON estritamente:
    {{
        "Resumo dos Checkpoints": "Escreva um parágrafo conciso sobre o progresso do estudante baseado nos dados dos checkpoints. Adicione uma análise NLP.",
        "Feedback Motivacional": "Dê um feedback motivador sobre o progresso do estudante.",
        "Recomendações": [
            "Ação 1",
            "Ação 2",
            "Ação 3",
            "Ação 4"
        ]
    }}
    """
   
    try:
        # Usar a API do GPT-4 para obter a conclusão personalizada
        
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente de feedback educacional especializado."},
                {"role": "user", "content": prompt}
            ],
            temperature=0  # Para respostas mais determinísticas
        )

        # Verificar se a resposta contém o conteúdo esperado
        if response and 'choices' in response and len(response['choices']) > 0:
            resposta_gpt = response['choices'][0]['message']['content']
        else:
            raise ValueError("Resposta da API não contém o conteúdo esperado")

        # Debug: print a resposta da LLM
        print("Resposta GPT-4:", resposta_gpt)
        
        
        # Remover delimitadores de bloco de código, se existirem
        resposta_gpt = re.sub(r"```json", "", resposta_gpt)
        resposta_gpt = re.sub(r"```", "", resposta_gpt).strip()
            
        
        try:
            conclusao = json.loads(resposta_gpt)
        except json.JSONDecodeError as e:
            # Tentar corrigir pequenas inconsistências
            print(f"JSONDecodeError: {e}. Tentando corrigir a resposta.")
            # Substituir chaves com underscores por espaços
            resposta_corrigida = re.sub(r'"Resumo_dos_Checkpoints"', '"Resumo dos Checkpoints"', resposta_gpt)
            resposta_corrigida = re.sub(r'"Feedback_Motivacional"', '"Feedback Motivacional"', resposta_corrigida)
            resposta_corrigida = re.sub(r'"Recomendações"', '"Recomendações"', resposta_corrigida)
            try:
                conclusao = json.loads(resposta_corrigida)
            except json.JSONDecodeError:
                raise ValueError("A resposta da API não está em um formato JSON válido, mesmo após tentativas de correção.")

        
         # Extrair as partes específicas da conclusão
        resumo_checkpoints = conclusao.get("Resumo dos Checkpoints", "Erro ao processar o resumo dos checkpoints.")
        feedback_motivacional = conclusao.get("Feedback Motivacional", "Erro ao gerar feedback motivacional.")
        recomendacoes = conclusao.get("Recomendações", "Erro ao gerar recomendações.")

        # Se "Recomendações" for uma lista, converta para string formatada
        if isinstance(recomendacoes, list):
            recomendacoes = "\n".join([f"- {rec}" for rec in recomendacoes])

        # Debug: verificar o resultado de cada extração
        print(f"Resumo: {resumo_checkpoints}")
        print(f"Feedback: {feedback_motivacional}")
        print(f"Recomendações: {recomendacoes}")

        return resumo_checkpoints, feedback_motivacional, recomendacoes

    except Exception as e:
        print(f"Erro ao gerar conclusão: {str(e)}")
        return "Erro ao processar o resumo dos checkpoints.", "Erro ao gerar feedback motivacional.", "Erro ao gerar recomendações."



def exibir_conquistas():
    st.subheader("Suas Conquistas")
    
    conquistas = [
        {"nome": "Leitor Ávido", "descricao": "Leu 5 livros", "progresso": 80},
        {"nome": "Explorador de Gêneros", "descricao": "Leu livros de 3 gêneros diferentes", "progresso": 60},
        {"nome": "Mestre da Análise", "descricao": "Obteve pontuação máxima em análise", "progresso": 40}
    ]
    
    for conquista in conquistas:
        with st.container():
            col1, col2 = st.columns([1,3])
            with col1:
                st.image(f"https://via.placeholder.com/80x80?text={conquista['nome'][0]}")
            with col2:
                st.subheader(conquista['nome'])
                st.write(conquista['descricao'])
                st.progress(conquista['progresso']/100)
        st.divider()
        

def exibir_comunidade():
    st.subheader("Comunidade RELIA")
    
    # Fórum de discussão simulado
    st.write("### Fórum de Discussão")
    topicos = [
        "Interpretações de '1984' de George Orwell",
        "Simbolismo em 'Cem Anos de Solidão'",
        "O impacto de 'O Pequeno Príncipe' na literatura moderna"
    ]
    for topico in topicos:
        st.write(f"- [{topico}](#)")
    
    # Clubes do livro
    st.write("### Clubes do Livro")
    clubes = ["Ficção Científica", "Clássicos da Literatura", "Poesia Contemporânea"]
    for clube in clubes:
        if st.button(f"Participar: {clube}", key=f"clube_{clube}"):
            st.success(f"Você se juntou ao clube '{clube}'!")
            

def exibir_desafios():
    st.subheader("Desafios de Leitura")
    
    desafios = [
        {"nome": "Maratona Literária", "descricao": "Leia 3 livros em 30 dias", "recompensa": "Badge exclusivo"},
        {"nome": "Explorando Novos Horizontes", "descricao": "Leia um livro de um gênero que você nunca leu antes", "recompensa": "50 pontos de experiência"},
        {"nome": "Análise Profunda", "descricao": "Faça uma análise detalhada de um personagem complexo", "recompensa": "Desbloqueio de recursos premium por 1 semana"}
    ]
    
    for desafio in desafios:
        with st.expander(desafio['nome']):
            st.write(f"**Descrição:** {desafio['descricao']}")
            st.write(f"**Recompensa:** {desafio['recompensa']}")
            if st.button("Aceitar Desafio", key=f"desafio_{desafio['nome']}"):
                st.success(f"Desafio '{desafio['nome']}' aceito! Boa sorte!")
    

def obter_texto_traduzido(chave, idioma):
    traducoes = {
        "pt-br": {
            "relatorio_final": "Relatório Final",
            "lembrar": "Lembrar",
            "entender": "Entender",
            "aplicar": "Aplicar",
            "analisar": "Analisar",
            "avaliar": "Avaliar",
            "criar": "Criar",
            "pontuacao": "Pontuação",
            "recomendacoes": "Recomendações"
        },
        # Adicionar outros idiomas aqui
    }
    return traducoes[idioma][chave]


def extrair_dados_progresso(relatorio):
    # Extrair dados de progresso do relatório
    pass


def criar_grafico_2d(checkpoints, nivel_atual):
    # Definir cores específicas para cada nível de Bloom
    cores_niveis = {
        'Lembrar': '#A2D9CE',      # Azul Claro
        'Compreender': '#A9DFBF',  # Verde Claro
        'Aplicar': '#5499C7',      # Azul
        'Analisar': '#F5B041',     # Laranja Claro
        'Avaliar': '#EC7063',      # Vermelho
        'Criar': '#AF7AC5'         # Roxo
    }

    # Calcular progresso por nível a partir dos checkpoints
    niveis = ['Lembrar', 'Compreender', 'Aplicar', 'Analisar', 'Avaliar', 'Criar']
    pontuacao_maxima_niveis = [15, 45, 91, 153, 190, 253]

    progresso = {nivel: 0 for nivel in niveis}
    for checkpoint in checkpoints:
        if checkpoint['nivel_taxonomia'] in progresso:
            progresso[checkpoint['nivel_taxonomia']] += checkpoint['nota_llm']

    # Criar DataFrame para o gráfico
    dados_niveis_df = pd.DataFrame({
        'Nível': niveis,
        'Pontuação': [min(progresso[n], max_pont) for n, max_pont in zip(niveis, pontuacao_maxima_niveis)],
        'Cor': niveis
    })

    # Criar o gráfico de barras com Plotly
    fig = px.bar(
        dados_niveis_df,
        x='Nível',
        y='Pontuação',
        title='Progresso por Nível Cognitivo',
        labels={'Nível': 'Nível Cognitivo', 'Pontuação': 'Pontuação'},
        text='Pontuação',
        template='plotly_dark',
        color='Cor',
        color_discrete_map=cores_niveis
    )

    # Ajustar a posição do texto e a escala do eixo Y
    fig.update_traces(textposition='outside')
    fig.update_layout(
        yaxis=dict(range=[0, max(pontuacao_maxima_niveis)]),
        showlegend=False
    )

     # Salvar o gráfico em um arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.write_image(temp_file.name)
    
    return fig, temp_file.name


# Função para criar um card com título e conteúdo
def criar_card(titulo, conteudo, cor_fundo):
    card_html = f"""
    <div style="
        background-color: {cor_fundo}; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); 
        margin-bottom: 20px;
        font-family: Arial, sans-serif;">
        <h3 style="color: #ffffff;">{titulo}</h3>
        <p style="color: #ffffff; font-size: 16px;">{conteudo}</p>
    </div>
    """
    components.html(card_html, height=200)
                

def criar_card_horizontal(titulo, conteudo):
    return f"""
    <div class="card">
        <div class="card-title">{titulo}</div>
        <div class="card-content">{conteudo}</div>
    </div>
    """

                
def continuar_roteiro(roteiro):
    # Recuperar os dados da obra usando o ID do roteiro
    obra_id = roteiro.get('obra_id')  # Assumindo que o roteiro contém uma referência ao ID da obra
    usuario_id = st.session_state.get('usuario_id', None)
    
    if obra_id and usuario_id:
        obra = obter_obra_por_id(obra_id)  # Função para buscar a obra no banco de dados
        if obra:
            # Limpar o histórico antes de carregar o novo roteiro
            limpar_historico_chat()
            # Atualizar o session_state com os dados da obra e roteiro
            st.session_state['obra'] = obra['titulo']
            st.session_state['autor'] = obra['autor']
            st.session_state['obra_atual'] = obra_id
            st.session_state['obra_id'] = obra_id 
            roteiro_id = criar_ou_obter_roteiro(obra_id, usuario_id)
            
            if roteiro_id:
                st.session_state['roteiro_id'] = roteiro_id
                
                # Recuperar os checkpoints do roteiro
                checkpoints = obter_checkpoints(roteiro_id)
                
                 # Calcular a pontuação total do roteiro
                pontuacao_total = sum(cp['nota_llm'] for cp in checkpoints if cp['nota_llm'] is not None)
                st.session_state['pontuacao_total'] = pontuacao_total
                
                # Determinar o nível de Bloom com base na pontuação
                nivel_bloom = determinar_nivel_bloom(pontuacao_total)
                st.session_state['nivel_bloom'] = nivel_bloom
                
                st.session_state['tela'] = 'chat'
                st.session_state['resumo'] = None  # Garantir que o resumo não seja exibido automaticamente
                st.session_state['roteiro_atual'] = roteiro_id
                st.session_state['iniciar_roteiro'] = True  # Marca que o roteiro deve ser iniciado no chat
                
                st.toast("Roteiro recuperado ou criado com sucesso.")
                st.rerun()
            else:
                st.error("Erro ao criar ou recuperar o roteiro.")
        else:
            st.error(f"Obra com ID {obra_id} não encontrada.")
    else:
        st.error("Dados insuficientes para continuar o roteiro.")
        
        
# Função para obter feedback automatizado
def obter_feedback_automatizado(roteiro_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
        SELECT resumo_checkpoints, feedback_motivacional, recomendacoes, insights
        FROM feedback_automatizado
        WHERE roteiro_id = ?
        """
        cursor.execute(query, (roteiro_id,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultado:
            return {
                'resumo_checkpoints': resultado[0],
                'feedback_motivacional': resultado[1],
                'recomendacoes': resultado[2],
                'insights': resultado[3]
            }
        else:
            return None
    except Exception as e:
        print(f"Erro ao obter feedback automatizado do banco de dados: {e}")
        return None


 # Função para obter recomendações literárias baseadas em uma obra
def gerar_recomendacoes(titulo_obra, api_key):
    try:
        prompt = f"""
        Você é um especialista em literatura. Com base na obra intitulada '{titulo_obra}', forneça:
        1. Três recomendações de obras literárias relacionadas, incluindo título, autor e justificativa breve de porque são relevantes para quem está lendo '{titulo_obra}'.
        
        Retorne as informações no seguinte formato JSON:
        {{
            "leituras_recomendadas": [
                {{"titulo": "Título da obra 1", "autor": "Autor da obra 1", "justificativa": "Justificativa para a recomendação da obra 1"}},
                {{"titulo": "Título da obra 2", "autor": "Autor da obra 2", "justificativa": "Justificativa para a recomendação da obra 2"}},
                {{"titulo": "Título da obra 3", "autor": "Autor da obra 3", "justificativa": "Justificativa para a recomendação da obra 3"}}
            ]
        }}
        """

        # Chamar a API do GPT-4 e mostrar spinner enquanto carrega
        with st.spinner('Consultando a API de recomendações...'):
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente útil."},
                    {"role": "user", "content": prompt}
                ],
                api_key=api_key
            )

        resposta_gpt = response['choices'][0]['message']['content']

        # Debug: print a resposta da LLM
        print("Resposta GPT-4:", resposta_gpt)

        # Remover delimitadores de bloco de código, se existirem
        if resposta_gpt.startswith("```json"):
            resposta_gpt = resposta_gpt.strip("```json").strip("```")

        # Tentar carregar a resposta em formato JSON
        try:
            recomendacoes_data = json.loads(resposta_gpt)
        except json.JSONDecodeError:
            raise ValueError("A resposta da API não está em um formato JSON válido")

       # Formatar as recomendações
        leituras_recomendadas = recomendacoes_data.get("leituras_recomendadas", [])
        if not leituras_recomendadas:
            raise ValueError("Nenhuma recomendação encontrada na resposta da API")

        leituras_formatadas = [
            f"{obra['titulo']} - {obra['autor']}: {obra['justificativa']}" for obra in leituras_recomendadas
        ]
        leituras_recomendadas_str = "\n".join(leituras_formatadas)

        return leituras_recomendadas_str

    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON da resposta GPT-4: {e}")
        return "Erro ao gerar recomendações."
    
  
  
 #Função para salvar o gráfico como imagem
def salvar_grafico_como_imagem(figura, caminho):
    figura.savefig(caminho, format='png')

# Função para gerar e salvar gráficos como PNG
def gerar_graficos(checkpoints, nivel_atual):
    # Gráfico 2D
    fig_2d = criar_grafico_2d(checkpoints, nivel_atual)
    caminho_2d = "/tmp/grafico_2d.png"
    fig_2d.write_image(caminho_2d)

    # Gráfico 3D
    fig_3d = criar_grafico_3d_com_acoes(checkpoints)
    caminho_3d = "/tmp/grafico_3d.png"
    fig_3d.write_image(caminho_3d)

    return caminho_2d, caminho_3d


# Obter as configurações de email dos segredos do Streamlit
EMAIL_HOST = st.secrets["EMAIL"]["EMAIL_HOST"]
EMAIL_PORT = st.secrets["EMAIL"]["EMAIL_PORT"]
EMAIL_HOST_USER = st.secrets["EMAIL"]["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = st.secrets["EMAIL"]["EMAIL_HOST_PASSWORD"]  # Use a senha de aplicativo aqui
EMAIL_USE_TLS = st.secrets["EMAIL"].get("EMAIL_USE_TLS", True)


def enviar_relatorio_por_email(usuario_id, obra_titulo, resumo_checkpoints, feedback_motivacional,  
                              recomendacoes, insights, progresso_total, checkpoints, nivel_atual, 
                              email_destino):
    try:
        print("Usuario ID email:", usuario_id)
        # Obter o perfil do usuário
        perfil = obter_perfil_por_id(usuario_id)
        print("Perfil", perfil)
        if not perfil:
            st.error("Perfil do usuário não encontrado.")
            return

         # Verificar se "checkpoints" é uma lista de tuplas
        if checkpoints and isinstance(checkpoints, list) and isinstance(checkpoints[0], tuple):
            # Assumir que "checkpoints" é uma lista de tuplas obtida do banco de dados
            # Obter os nomes das colunas dinamicamente para converter cada tupla em um dicionário
            columns = ['nivel_taxonomia', 'pergunta', 'resposta', 'nota_llm', 'feedback_llm']
            checkpoints_dict = [dict(zip(columns, cp)) for cp in checkpoints]
        else:
            checkpoints_dict = checkpoints

        # Preparar DataFrame dos checkpoints
        checkpoints_df = pd.DataFrame([{
            'Nível': cp['nivel_taxonomia'],
            'Pergunta': cp['pergunta'],
            'Resposta': cp['resposta'],
            'Pontuação': cp['nota_llm'],
            'Feedback': cp['feedback_llm']
        } for cp in checkpoints_dict])

        # Criar mapeamentos necessários para o DataFrame enriquecido
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nomes_acao, nivel_bloom FROM acoes")
        acoes_data = cursor.fetchall()
        
        # Ajustar para funcionar corretamente com os dados obtidos
        acoes_map = {
            row[0]: {
                'nomes_acao': row[1],
                'nivel_bloom': row[2]
            }
            for row in acoes_data
        }

        action_to_conhecimento = {}
        for tipo, niveis in dados_conhecimento.items():
            for nivel, acoes in niveis.items():
                for acao in acoes:
                    action_to_conhecimento[acao.lower()] = tipo

        # Criar DataFrame enriquecido
        df_enriquecido = criar_dataframe_enriquecido(checkpoints_dict, acoes_map, action_to_conhecimento)

        # Gerar gráficos e salvar temporariamente
        fig_2d, temp_2d = criar_grafico_2d(checkpoints_dict, nivel_atual)
        fig_radar = grafico_radar_bloom(df_enriquecido) if not df_enriquecido.empty else None

        # Extrair temáticas e criar nuvem de palavras
        tematicas = extrair_tematicas(checkpoints_dict)
        fig_wordcloud = criar_grafico_wordcloud(tematicas) if tematicas else None

        # Salvar gráficos temporariamente
        graficos_temp = []
        graficos_temp.append({"path": temp_2d, "cid": "grafico_2d"})
        
        if fig_radar:
            temp_radar = "temp_radar.png"
            fig_radar.write_image(temp_radar)
            graficos_temp.append({"path": temp_radar, "cid": "grafico_radar"})
            
        if fig_wordcloud:
            temp_wordcloud = "temp_wordcloud.png"
            plt.figure(fig_wordcloud)
            plt.savefig(temp_wordcloud)
            plt.close()
            graficos_temp.append({"path": temp_wordcloud, "cid": "grafico_wordcloud"})

        # Gerar HTML do relatório
        html_conteudo = gerar_html_relatorio(
            usuario_nome=perfil['nome'],
            obra_titulo=obra_titulo,
            progresso_total=progresso_total,
            resumo_checkpoints=resumo_checkpoints,
            feedback_motivacional=feedback_motivacional,
            recomendacoes=recomendacoes,
            insights=insights,
            dados_nlp={'tematicas': tematicas},
            checkpoints_df=checkpoints_df,
            graficos=graficos_temp
        )

        # Enviar email
        send_report_email(
            to_email=email_destino,
            subject=f"Relatório de Leitura: {obra_titulo}",
            html_content=html_conteudo,
            image_attachments=graficos_temp
        )

        # Limpar arquivos temporários
        for grafico in graficos_temp:
            if os.path.exists(grafico["path"]):
                os.remove(grafico["path"])

        st.toast("Relatório enviado para seu email com sucesso!")

    except Exception as e:
        st.error(f"Ocorreu um erro ao enviar o relatório: {e}")
        print(f"Erro detalhado: {str(e)}")  # Para debug
    finally:
        if 'conn' in locals():
            conn.close()
        
########### -----------  Funções auxiliares para envio por email -------------------------

def gerar_html_analise_nlp(tematicas, entidades):
    return f"""
        <div class="card">
            <div class="card-title">Temáticas Principais</div>
            <div class="content">
                {''.join(f'<div class="topic-item">{tema}: {", ".join(palavras)}</div>' for tema, palavras in tematicas.items())}
            </div>
        </div>
        <div class="card">
            <div class="card-title">Entidades Identificadas</div>
            <div class="content">
                {''.join(f'<div class="topic-item">{entidade}</div>' for entidade in entidades)}
            </div>
        </div>
    """
    
def gerar_html_graficos():
    return """
        <img src="cid:grafico_2d" alt="Progresso por Nível Cognitivo" style="width: 100%; margin-bottom: 20px;">
        <img src="cid:grafico_radar" alt="Distribuição das Ações" style="width: 100%; margin-bottom: 20px;">
        <img src="cid:grafico_wordcloud" alt="Nuvem de Palavras" style="width: 100%; margin-bottom: 20px;">
    """    
 
#### --------------- Funções para NLP ----------------

stop_words = [
    'a', 'à', 'ao', 'aos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aquilo',
    'as', 'às', 'até', 'com', 'como', 'da', 'das', 'de', 'dela', 'delas', 'dele',
    'deles', 'demais', 'depois', 'desde', 'dessa', 'dessas', 'desse', 'desses',
    'desta', 'destas', 'deste', 'detrás', 'deu', 'devagar', 'dever', 'deverá', 
    'deveriam', 'deveríamos', 'devemos', 'devia', 'deviam', 'devíamos', 'devo', 
    'diariamente', 'diante', 'dizer', 'dizemos', 'e', 'ela', 'elas', 'ele', 'eles', 
    'em', 'entre', 'era', 'eram', 'éramos', 'essa', 'essas', 'esse', 'esses', 'esta', 
    'estas', 'estava', 'estavam', 'estávamos', 'este', 'estes', 'estou', 'eu', 'foi', 
    'for', 'foram', 'fôramos', 'fosse', 'fossem', 'fôssemos', 'há', 'haja', 'hão', 
    'havendo', 'hei', 'hoje', 'isso', 'isto', 'já', 'lhe', 'lhes', 'lá', 'mais', 'mas', 
    'me', 'mesma', 'mesmas', 'mesmo', 'mesmos', 'meu', 'meus', 'minha', 'minhas', 'muito', 
    'na', 'nas', 'nem', 'no', 'nos', 'nossa', 'nossas', 'nosso', 'nossos', 'nós', 
    'num', 'numa', 'nunca', 'o', 'os', 'ou', 'onde', 'para', 'pela', 'pelas', 'pelo', 
    'pelos', 'perante', 'pode', 'pude', 'podemos', 'podia', 'podiam', 'poderá', 'poderiam', 
    'por', 'porque', 'quais', 'qual', 'quando', 'quanto', 'que', 'quem', 'se', 'sem', 
    'sempre', 'ser', 'seu', 'seus', 'só', 'sob', 'sobre', 'sou', 'sua', 'suas', 'também', 
    'tanto', 'te', 'tem', 'têm', 'temos', 'tenha', 'ter', 'teu', 'teus', 'tive', 'tivemos', 
    'tiver', 'tivesse', 'tivéssemos', 'toda', 'todas', 'todo', 'todos', 'tu', 'tua', 
    'tuas', 'um', 'uma', 'umas', 'uns', 'vai', 'vão', 'você', 'vocês', 'vos', 'vou', 
    'era', 'eram', 'está', 'estão', 'foi', 'será', 'não', 'já', 'tudo', 'nada', 'bem', 
    'mal', 'hoje', 'amanhã', 'ontem', 'algum', 'alguma', 'alguns', 'nenhum', 'nenhuma', 
    'sempre', 'muitas', 'muitos', 'poucos', 'poucas', 'cada', 'assim', 'isso', 'isto', 
    'depois', 'antes', 'durante', 'aí', 'mesmo', 'outros', 'outras', 'quem', 'qual', 
    'quais', 'onde', 'quanto', 'quantos', 'tão', 'tal', 'tais', 'pois', 'aí', 'cá', 
    'ainda', 'tanto', 'porque', 'como', 'tudo', 'todo', 'dos', 'sem', 'só', 'daquela',
    'daqueles', 'outra', 'seja', 'sejam', 'tenho', 'têm', 'tenhamos', 'vai', 'ver', 
    'veja', 'venha', 'vir', 'ainda', 'todos', 'nenhum', 'nunca'
]

vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words=stop_words)


def analisar_sentimento(resposta):
    try:
        resultado = sentiment_analyzer(resposta[:512])  # Limitar a 512 tokens
        return resultado[0]['label'], resultado[0]['score']
    except Exception as e:
        return "Indeterminado", 0.0

def extrair_tematicas(checkpoints, n_topics=3):
    respostas = [cp['resposta'] for cp in checkpoints if cp['resposta']]
    num_documentos = len(respostas)
    
    #st.write(f"**Número de Respostas Disponíveis para Análise:** {num_documentos}")
    
    if num_documentos < 2:
        st.warning("Não há respostas suficientes para realizar a análise de temas. Por favor, adicione mais respostas.")
        return {}
    
    # Ajustar min_df dinamicamente
    min_df = 2 if num_documentos >= 2 else 1
    
    vectorizer = CountVectorizer(max_df=0.95, min_df=min_df, stop_words=stop_words)
    try:
        dtm = vectorizer.fit_transform(respostas)
    except ValueError as ve:
        st.error(f"Erro ao aplicar CountVectorizer: {ve}")
        return {}
    
    if dtm.shape[1] == 0:
        st.warning("Nenhum termo atende aos critérios de min_df e max_df. Ajuste os parâmetros ou adicione mais dados.")
        return {}
    
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(dtm)
    
    tematicas = {}
    for idx, topic in enumerate(lda.components_):
        top_features = [vectorizer.get_feature_names_out()[i] for i in topic.argsort()[-10:]]
        tematicas[f'Tema {idx+1}'] = top_features
    return tematicas


def criar_dataframe_enriquecido(checkpoints: list, acoes_map: dict, action_to_conhecimento: dict) -> pd.DataFrame:
    """
    Cria um DataFrame enriquecido a partir dos checkpoints.
    
    Parâmetros:
    - checkpoints (list): Lista de checkpoints.
    - acoes_map (dict): Mapeamento de acao_id para detalhes da ação.
    - action_to_conhecimento (dict): Mapeamento de nomes_acao para tipo_conhecimento.
    
    Retorna:
    - DataFrame enriquecido.
    """
    dados = []
    for cp in checkpoints:
        nivel_taxonomia = cp.get('nivel_taxonomia')
        acao_id = cp.get('acao_id')
        nota = cp.get('nota_llm')
        resposta = cp.get('resposta')
        
        acao_info = acoes_map.get(acao_id, None)
        if not acao_info:
            st.warning(f"Ação ID {acao_id} não encontrada.")
            continue

        nome_acao = acao_info['nomes_acao']
        nivel_bloom = acao_info['nivel_bloom']

        tipo_conhecimento = action_to_conhecimento.get(nome_acao.lower(), 'Desconhecido')

        dados.append({
            'Tipo de Conhecimento': tipo_conhecimento,
            'Nível Cognitivo': nivel_taxonomia,
            'Ação Realizada': nome_acao,
            'Pontuação': nota
        })

    df = pd.DataFrame(dados)
    return df


def grafico_pontuacao_por_nivel(df):
    """
    Cria um gráfico de barras mostrando a pontuação média de sentimento por nível cognitivo.
    
    Parâmetros:
    - df (pd.DataFrame): DataFrame enriquecido contendo as colunas 'Nível Cognitivo' e 'Score Sentimento'.
    
    Retorna:
    - fig (plotly.graph_objects.Figure): Objeto Figura do Plotly para o gráfico.
    """
    if df.empty:
        st.warning("DataFrame vazio. Não há dados para criar o gráfico de pontuação por nível cognitivo.")
        return None
    
    # Calcular a pontuação média por nível cognitivo
    df_media = df.groupby('Nível Cognitivo')['Score Sentimento'].mean().reset_index()
    
    # Verificar se há dados após o agrupamento
    if df_media.empty:
        st.warning("Nenhum dado disponível após o agrupamento para criar o gráfico.")
        return None
    
    # Criar o gráfico de barras usando Plotly Express
    fig = px.bar(
        df_media,
        x='Nível Cognitivo',
        y='Score Sentimento',
        title='Pontuação Média de Sentimento por Nível Cognitivo',
        labels={
            'Nível Cognitivo': 'Nível Cognitivo',
            'Score Sentimento': 'Pontuação Média de Sentimento'
        },
        color='Nível Cognitivo',
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    
      # Atualizar layout para melhor visualização
    fig.update_layout(
        xaxis_title="Nível Cognitivo",
        yaxis_title="Pontuação Média de Sentimento",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig
    
    # Atualizar layout para melhor visualização
    fig.update_layout(
        xaxis_title="Nível Cognitivo",
        yaxis_title="Pontuação Média de Sentimento",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig



def nuvem_palavras(temas):
    texto = ' '.join([' '.join(v) for v in temas.values()])
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(texto)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig


def grafico_sentimento(df):
    df_sentimento = df['Sentimento'].value_counts().reset_index()
    df_sentimento.columns = ['Sentimento', 'Contagem']
    
    fig = px.pie(df_sentimento, names='Sentimento', values='Contagem',
                 title='Distribuição de Sentimentos nas Respostas',
                 color='Sentimento',
                 color_discrete_map={'POSITIVE':'#2ECC71', 'NEGATIVE':'#E74C3C', 'NEUTRAL':'#95A5A6'})
    return fig


def exibir_grafico_pontuacao(df):
    fig = grafico_pontuacao_por_nivel(df)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

def exibir_nuvem_palavras(temas):
    fig = nuvem_palavras(temas)
    if fig:
        st.pyplot(fig)
        
def grafico_radar_bloom(df: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico de radar aprimorado mostrando a distribuição das ações nas dimensões de conhecimento através dos níveis de Bloom.
    
    Parâmetros:
    - df: DataFrame enriquecido contendo 'Tipo de Conhecimento', 'Nível Cognitivo', 'Ação Realizada', 'Pontuação'.
    
    Retorna:
    - Objeto Figure do Plotly.
    """
    if df.empty:
        st.warning("DataFrame vazio. Não há dados para criar o gráfico de radar aprimorado.")
        return None

    niveis_bloom = ['Lembrar', 'Compreender', 'Aplicar', 'Analisar', 'Avaliar', 'Criar']
    dimensoes = df['Tipo de Conhecimento'].unique()
    
    # Calcular a contagem de ações por dimensão e nível de Bloom
    contagem = df.groupby(['Tipo de Conhecimento', 'Nível Cognitivo']).size().reset_index(name='Contagem')
    contagem = contagem.pivot(index='Tipo de Conhecimento', columns='Nível Cognitivo', values='Contagem').reindex(columns=niveis_bloom, fill_value=0)
    
    # Criar o gráfico de radar
    fig = go.Figure()

    for dimensao in dimensoes:
        if dimensao not in contagem.index:
            continue  # Evitar erros se a dimensão não estiver presente
        valores = contagem.loc[dimensao].tolist()
        fig.add_trace(go.Scatterpolar(
            r=valores + [valores[0]],  # Fecha o loop do radar
            theta=niveis_bloom + [niveis_bloom[0]],
            fill='toself',
            name=dimensao
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, contagem.values.max() + 1]
            )
        ),
        title='Distribuição das Ações nas Dimensões de Conhecimento através dos Níveis de Bloom',
        legend_title="Dimensões de Conhecimento",
        showlegend=True
    )
    
    return fig


def extrair_entidades(checkpoints):
    """
    Extrai entidades nomeadas das respostas dos checkpoints.
    
    Parâmetros:
    - checkpoints (list of sqlite3.Row): Lista de checkpoints.
    
    Retorna:
    - entidades (list): Lista de entidades extraídas.
    """
  
    
    #ner_pipeline = pipeline("ner", framework="pt")
    entidades = []
    
    #for cp in checkpoints:
     #   resposta = cp['resposta']
      #  if resposta:
       #     resultado = ner_pipeline(resposta)
        #    for entidade in resultado:
         #       entidades.append(entidade['word'])
    
    return entidades

     
def heatmap_bloom_temporal(df: pd.DataFrame, checkpoints: list) -> px.imshow:
    """
    Cria um heatmap temporal mostrando a frequência das ações nas dimensões de conhecimento e níveis de Bloom ao longo do tempo.
    
    Parâmetros:
    - df: DataFrame enriquecido contendo 'Tipo de Conhecimento', 'Nível Cognitivo', 'Ação Realizada', 'Pontuação'.
    - checkpoints: Lista de checkpoints contendo informações de tempo.
    
    Retorna:
    - Objeto Figure do Plotly.
    """
    if df.empty:
        st.warning("DataFrame vazio. Não há dados para criar o heatmap temporal.")
        return None

    # Converter checkpoints para DataFrame para extrair tempos
    checkpoints_df = pd.DataFrame(checkpoints)
    
    # Verificar se existe uma coluna de timestamp
    if 'data_hora' not in checkpoints_df.columns:
        st.warning("A coluna 'data_hora' não foi encontrada nos checkpoints.")
        return None
    
    checkpoints_df['data_hora'] = pd.to_datetime(checkpoints_df['data_hora'])  # Ajuste conforme o formato real
    
    checkpoints_df = checkpoints_df.sort_values('data_hora')
    
    # Adicionar coluna de tempo ao DataFrame enriquecido
    # Supondo que a ordem de 'checkpoints' corresponda à ordem de 'df'
    # Caso contrário, é necessário uma correspondência mais precisa
    if len(checkpoints_df) < len(df):
        st.warning("Número de checkpoints é menor que o número de registros no DataFrame.")
        return None
    df['data_hora'] = checkpoints_df['data_hora'].values[:len(df)]
    
    # Agregar dados por período de tempo, dimensão e nível de Bloom
    # Escolha a granularidade temporal (e.g., mês)
    df['mes'] = df['data_hora'].dt.to_period('M').astype(str)
    
    agregacao = df.groupby(['mes', 'Tipo de Conhecimento', 'Nível Cognitivo']).size().reset_index(name='Contagem')
    
    # Pivot para criar uma matriz com dimensões no eixo Y, níveis de Bloom no eixo X, e tempo como uma série de heatmaps
    pivot_table = agregacao.pivot_table(index=['Tipo de Conhecimento', 'Nível Cognitivo'], columns='mes', values='Contagem', fill_value=0)
    
    # Criar o heatmap
    fig = px.imshow(
        pivot_table,
        labels=dict(x="Mês", y="Dimensão e Nível de Bloom", color="Frequência"),
        x=pivot_table.columns,
        y=["{} - {}".format(idx[0], idx[1]) for idx in pivot_table.index],
        aspect="auto",
        title='Frequência das Ações nas Dimensões e Níveis de Bloom ao Longo do Tempo',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        xaxis_nticks=len(pivot_table.columns),
        yaxis_nticks=len(pivot_table.index)
    )
    
    return fig


def criar_grafico_wordcloud(temas: dict) -> plt.Figure:
    """
    Gera uma nuvem de palavras a partir das temáticas principais.
    
    Parâmetros:
    - temas (dict): Dicionário mapeando temas para listas de palavras.
    
    Retorna:
    - Figura Matplotlib contendo a nuvem de palavras ou None se não houver dados suficientes.
    """
    if not temas:
        st.warning("Nenhuma temática disponível para gerar a nuvem de palavras.")
        return None

    texto = ' '.join([palavra for sublist in temas.values() for palavra in sublist])

    if not texto.strip():
        st.warning("Texto vazio após concatenar as temáticas. Nuvem de palavras não pode ser gerada.")
        return None

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap='viridis',
        stopwords=set(),  # Assumindo que as stopwords já foram removidas
        max_words=200,
        max_font_size=100,
        random_state=42
    ).generate(texto)

    fig, ax = plt.subplots(figsize=(15, 7.5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')  # Remover eixos

    return fig


def processar_conteudo_markdown(conteudo):
    """
    Processa o conteúdo recuperado do banco de dados para garantir 
    formatação markdown adequada.
    """
    if not conteudo:
        return ""
    
    # Remover possíveis tags HTML residuais
    conteudo = re.sub(r'<[^>]+>', '', conteudo)
    
    # Garantir que listas estejam formatadas corretamente
    conteudo = re.sub(r'^[\s-]*([^\n]+)$', r'- \1', conteudo, flags=re.MULTILINE)
    
    # Garantir que parágrafos tenham espaçamento adequado
    conteudo = re.sub(r'\n{2,}', '\n\n', conteudo)
    
    return markdown.markdown(conteudo)


def formatar_recomendacoes(recomendacoes):
    """
    Formata as recomendações em tópicos com destaques, removendo caracteres especiais
    e formatação JSON indesejada.
    """
    try:
        # Se o texto vier como string de lista JSON, converte para lista
        if isinstance(recomendacoes, str):
            if recomendacoes.startswith('[') and recomendacoes.endswith(']'):
                import json
                recomendacoes = json.loads(recomendacoes)

        # Se for lista, processa cada item
        if isinstance(recomendacoes, list):
            formatted_items = []
            for item in recomendacoes:
                # Limpa o texto
                clean_text = (item
                    .replace('\u00e7', 'ç')
                    .replace('\u00f5', 'õ')
                    .replace('\u00e3', 'ã')
                    .replace('\u00e9', 'é')
                    .replace('\u00ed', 'í')
                    .replace('\u00e1', 'á')
                    .strip('\"')
                    .strip())
                formatted_items.append(f'<div class="topic-item">• {clean_text}</div>')
            return '\n'.join(formatted_items)
        
        # Se for string simples, divide por quebras de linha
        lines = recomendacoes.split('\n')
        formatted_items = []
        for line in lines:
            if line.strip():
                # Limpa o texto
                clean_text = (line
                    .replace('\u00e7', 'ç')
                    .replace('\u00f5', 'õ')
                    .replace('\u00e3', 'ã')
                    .replace('\u00e9', 'é')
                    .replace('\u00ed', 'í')
                    .replace('\u00e1', 'á')
                    .strip('\"')
                    .strip('- ')
                    .strip())
                formatted_items.append(f'<div class="topic-item">• {clean_text}</div>')
        
        return '\n'.join(formatted_items)

    except Exception as e:
        print(f"Erro ao formatar recomendações: {e}")
        return recomendacoes  # Retorna o texto original em caso de erro


def formatar_leituras_relacionadas(insights):
    """Formata as leituras relacionadas com títulos em destaque"""
    lines = insights.split('\n')
    formatted_items = []
    for line in lines:
        if ':' in line:
            title, description = line.split(':', 1)
            formatted_items.append(f'<div class="topic-item"><span class="highlight"><strong>{title}</strong></span>: {description}</div>'
)
        elif line.strip():
            formatted_items.append(f'<div class="topic-item">{line.strip()}</div>')
    return '\n'.join(formatted_items)


# Primeiro, vamos criar uma função para limpar o histórico do chat
def limpar_historico_chat():
    """
    Limpa o histórico de mensagens e estados relacionados ao chat.
    """
    # Limpar mensagens do chat
    st.session_state.messages = []
    # Resetar outros estados relacionados ao chat
    st.session_state.chat_iniciado = False
    st.session_state.llm_response = None
    st.session_state.resumo = None
    st.session_state.resumo_exibido = False
    
    
