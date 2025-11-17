from inspect import isframe
import streamlit as st
from utils.api import get_anthropic_response, get_openai_response
from database import ( 
                      obter_obra_por_id,inserir_mensagem_chat,
                      obter_mensagens_chat,criar_novo_roteiro,criar_ou_obter_roteiro, 
                      inserir_log_uso, registrar_log_uso
                      )
import time
import re
import openai
import json
import random  # Import necessário para seleção aleatória
#from views.area_do_leitor import exibir_relatorio
import streamlit.components.v1 as components
import tempfile
import os


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    """, unsafe_allow_html=True)

# Inicialização do estado da sessão
for key in ['messages', 'chat_iniciado', 'obra_id', 'usuario', 'roteiro_id', 'obra_atual', 'llm_response', 'resumo_exibido']:
    if key not in st.session_state:
        if key == 'messages':
            st.session_state[key] = []
        elif key == 'chat_iniciado':
            st.session_state[key] = False
        elif key == 'obra':
            st.session_state[key] = {"titulo": "", "autor": ""}
        elif key == 'resumo_exibido':
            st.session_state[key] = False
        elif key == 'language':
            st.session_state[key] = False
        elif 'tela' not in st.session_state:
            st.session_state['tela'] = 'chat'
        elif 'etapa_atual' not in st.session_state:
            st.session_state['etapa_atual'] = 0  # Começa no nível 'Lembrar'
        else:
            st.session_state[key] = None
        


def sanitize_input(text):
    """
    Sanitiza a entrada removendo caracteres especiais indesejados.
    
    Args:
        text (str): Texto de entrada do usuário.
        
    Returns:
        str: Texto sanitizado.
    """
    return re.sub(r'[^\w\s]', '', text).strip()


# Mapeamento dos botões para os níveis da Taxonomia de Bloom
TAXONOMY_MAP = {
    "Contexto Histórico": ["Entender", "Analisar"],
    "Curiosidades": ["Lembrar", "Entender"],
    "Impacto Cultural": ["Analisar", "Avaliar"],
    "Estilo": ["Entender", "Aplicar"],
    "Questões Intrigantes": ["Analisar", "Avaliar"],
    "Moral": ["Avaliar", "Criar"],
    "Personagens": ["Entender", "Analisar"]
}

# Ícones para os botões
ICON_MAP = {
    "Contexto Histórico": "📜",
    "Curiosidades": "🎭",
    "Impacto Cultural": "🌍",
    "Estilo": "✒️",
    "Questões Intrigantes": "❓",
    "Moral": "⚖️",
    "Personagens": "👥",
    "Mais": "➕"
}

# Lista de ações para gerar questões aleatórias
ACOES = [
    "Explorar Temas Profundos",
    "Análise de Personagens Secundários",
    "Comparação com Outras Obras",
    "Interpretações Alternativas",
    "Contexto Social da Época",
    "Influência em Outras Mídias",
    "Detalhes Simbólicos",
    "Estilos Narrativos",
    "Relevância Atual",
    "Perspectivas Críticas"
]

# Definir mensagens do sistema em diferentes idiomas
SYSTEM_MESSAGES = {
    'pt-br': "Você é RELIA, um assistente empático e útil especializado em literatura. Responda de forma clara e envolvente.",
    'pt-pt': "Você é RELIA, um assistente empático e útil especializado em literatura. Responda de forma clara e envolvente.",
    'en': "You are RELIA, an empathetic and helpful assistant specialized in literature. Respond clearly and engagingly.",
    'es': "Eres RELIA, un asistente empático y útil especializado en literatura. Responde de manera clara y atractiva."
}


def inicializar_session_state():
    """Initializes session state variables."""
    if 'botoes_pressionados' not in st.session_state:
        st.session_state.botoes_pressionados = []
    if 'acoes_adicionais' not in st.session_state:
        st.session_state.acoes_adicionais = []

def registrar_botao(botao, niveis):
    """Registers the pressed button with its corresponding levels."""
    st.session_state.botoes_pressionados.append({
        "botao": botao,
        "niveis": niveis
    })


def exibir_botoes_interesses():
    """Exibe os botões de interesse de forma aprimorada."""
    interesses = [
        ("Contexto Histórico", "Clique para saber mais sobre o contexto histórico da obra"),
        ("Curiosidades", "Clique para descobrir curiosidades sobre a obra"),
        ("Impacto Cultural", "Clique para entender o impacto cultural da obra"),
        ("Estilo", "Clique para saber sobre a linguagem e estilos desta obra"),
        ("Questões Intrigantes", "Clique para explorar questões instigantes sobre a obra"),
        ("Moral", "Clique para entender a moral da história da obra"),
        ("Personagens", "Clique para conhecer os personagens da obra")
    ]

    # Sempre manter os 7 botões principais visíveis
    botoes_visiveis = interesses.copy()
    
    # Gerar ações adicionais aleatórias ao clicar em "Mais"
    if st.session_state.get('mostrar_acoes_adicionais', False):
        acoes_disponiveis = [acao for acao in ACOES if acao not in [interesse[0] for interesse in botoes_visiveis]]
        acoes_selecionadas = random.sample(acoes_disponiveis, min(3, len(acoes_disponiveis)))
        for acao in acoes_selecionadas:
           pass # botoes_visiveis.append((acao, f"Clique para {acao.lower()}"))
            

 
    # Exibir botões dentro da barra de diálogo
    
    with st.container(border=True):
        
        cols = st.columns(len(botoes_visiveis) + 1)
        for idx, (interesse, help_text) in enumerate(botoes_visiveis):
            with cols[idx]:
                icon = ICON_MAP.get(interesse, "🔹")
                if st.button(f"{icon} {interesse}", key=f"interest_{idx}", help=help_text):
                    registrar_botao(interesse, TAXONOMY_MAP.get(interesse, ["Desconhecido", "Desconhecido"]))
                    gerar_resposta_interesse(interesse)
        # Botão "Mais" para gerar novas ações
        with cols[-1]:
            
            if st.button(f"{ICON_MAP['Mais']} Mais", key="more_button", help="Clique para ver mais tópicos"):
                registrar_botao(interesse, TAXONOMY_MAP.get(interesse, ["Desconhecido", "Desconhecido"]))
                gerar_resposta_interesse(interesse)
                st.rerun()
                
        
                            
                
def gerar_resposta_interesse(interesse):
    """Gera a resposta para o tópico de interesse."""
    obra_id = st.session_state['obra_id']
    obra = obter_obra_por_id(obra_id) 

    if obra:
        titulo = obra['titulo']
        autor = obra['autor']
        usuario = st.session_state['usuario']
        language_code = st.session_state.get('language', 'pt-br')
        system_message = SYSTEM_MESSAGES.get(language_code, SYSTEM_MESSAGES['pt-br'])


        prompt_map = {
                    "Contexto Histórico": (
                            f"Como um excelente tutor em literatura, forneça uma explicação detalhada sobre o contexto histórico da obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua os eventos significativos que influenciaram a narrativa. Além disso, descreva brevemente as principais influências e temas nas obras de {st.session_state['autor']}. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                                ),
                    
                    "Curiosidades": (
                            f"Como um excelente tutor em literatura, compartilhe algumas curiosidades fascinantes sobre a obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua fatos interessantes sobre o processo de escrita, as influências do autor ou quaisquer detalhes peculiares que possam capturar a atenção do leitor. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Faça as curiosidades cativantes e divertidas. Use formatação Markdown no texto, e diversifique a apresentação com tabelas ou gráficos quando necessário. "
                            f"OUTPUT: Máximo de 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                                ),
                    "Impacto Cultural": (
                            f"Como um excelente tutor em literatura, explique o impacto cultural da obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Discuta como a obra influenciou a sociedade, outras obras literárias e a cultura popular. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Faça o impacto cultural inspirador e informativo. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"OUTPUT: Máximo de 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                    ),
                    "Estilo": (
                            f"Como um excelente tutor em literatura, forneça uma análise detalhada da linguagem e do estilo da obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Descreva como o autor utiliza elementos linguísticos como metáforas, simbolismos e figuras de linguagem, e explique o impacto que isso tem na narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Faça a análise envolvente e educativa, destacando como a escolha da linguagem e do estilo do autor contribuem para a compreensão e apreciação da obra. Use formatação Markdown no texto, e utilize tabelas ou gráficos para ilustrar conceitos quando apropriado. "
                            f"OUTPUT: Máximo de 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                    ),
                    "Questões Intrigantes": (
                            f"Como um excelente tutor em literatura, levante algumas questões intrigantes sobre a obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua perguntas que façam o leitor refletir sobre os temas e personagens da obra, promovendo uma análise mais profunda. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Faça as questões provocativas e reflexivas. Use formatação Markdown no texto, e varie a apresentação com listas ou tabelas quando necessário. "
                            f"OUTPUT: Máximo de 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                    ),
                    "Moral": (
                            f"Como um excelente tutor em literatura, explique a moral da história na obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua uma análise sobre as lições e mensagens que o autor pretende transmitir através da narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Faça a moral da história clara e inspiradora. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos chave quando apropriado. "
                            f"OUTPUT: Máximo de 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                    ),
                    "Personagens": (
                            f"Como um excelente tutor em literatura, forneça uma descrição detalhada dos personagens principais e secundários da obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua informações sobre suas características, motivações e evolução ao longo da narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Faça a descrição dos personagens envolvente e informativa. Use formatação Markdown no texto, e diversifique a apresentação com tabelas ou gráficos quando necessário. "
                            f"OUTPUT: Máximo de 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                    ),
                    "Exploração de Temas Profundos": (
                            f"Como um excelente tutor em literatura, forneça uma análise detalhada dos temas profundos presentes na obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua uma discussão sobre os subtextos e mensagens subjacentes que o autor quis transmitir. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        ),
                    "Análise de Personagens Secundários": (
                            f"Como um excelente tutor em literatura, forneça uma análise detalhada dos personagens secundários da obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua informações sobre suas características, motivações e contribuições para a narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        ),
                    "Comparação com Outras Obras": (
                            f"Como um excelente tutor em literatura, forneça uma comparação detalhada da obra '{st.session_state['obra']}' de {st.session_state['autor']} com outras obras do mesmo autor ou de autores diferentes. "
                            f"Inclua semelhanças e diferenças em temas, estilos e narrativas. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        ),
                    "Interpretações Alternativas": (
                            f"Como um excelente tutor em literatura, forneça uma análise das interpretações alternativas da obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua diferentes leituras e perspectivas que os leitores podem ter sobre a narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        ),
                    "Contexto Social da Época": (
                            f"Como um excelente tutor em literatura, forneça uma explicação detalhada sobre o contexto social da época em que a obra '{st.session_state['obra']}' de {st.session_state['autor']} foi escrita. "
                            f"Inclua os eventos significativos que influenciaram a narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        ),
                    "Influência em Outras Mídias": (
                            f"Como um excelente tutor em literatura, forneça uma análise da influência da obra '{st.session_state['obra']}' de {st.session_state['autor']} em outras mídias, como filmes, séries, jogos, etc. "
                            f"Inclua adaptações, referências e impactos culturais. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        ),
                    "Detalhes Simbólicos": (
                            f"Como um excelente tutor em literatura, forneça uma análise detalhada dos elementos simbólicos presentes na obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua a interpretação dos símbolos e suas representações na narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        ),
                    "Estilos Narrativos": (
                            f"Como um excelente tutor em literatura, forneça uma análise detalhada dos estilos narrativos utilizados na obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua a descrição das técnicas narrativas e seu impacto na narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        ),
                    "Relevância Atual": (
                            f"Como um excelente tutor em literatura, forneça uma análise da relevância atual da obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua como a obra se relaciona com temas contemporâneos e sua mensagem para a sociedade atual. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        ),
                    "Perspectivas Críticas": (
                            f"Como um excelente tutor em literatura, forneça uma análise das perspectivas críticas sobre a obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                            f"Inclua críticas positivas e negativas, bem como diferentes interpretações críticas da obra. "
                            f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                            f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                            f"Por favor, responda em português. "
                            f"Identifique-se como RELIA, quando necessário. Use formatação Markdown no texto, e inclua tabelas ou gráficos para ilustrar pontos importantes. "
                            f"Limite sua resposta a aproximadamente 250 tokens, sempre centrado na obra '{st.session_state['obra']}' e no autor {st.session_state['autor']}."
                        )
         
            }
    
        # Caso seja uma ação adicional não mapeada
        if interesse not in prompt_map:
            prompt = (
                f"Como um excelente tutor em literatura, forneça informações sobre '{st.session_state['usuario']['interesses']}' relacionado à obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
                f"Adapte o texto para um leitor com as seguintes características: Nome: {st.session_state['usuario']['nome']}, Idade: {st.session_state['usuario']['idade']} anos, "
                f"Cidade: {st.session_state['usuario']['cidade']}, Interesses: {st.session_state['usuario']['interesses']}. "
                f"Identifique-se como RELIA, quando necessário,. Use formatação Markdown no texto. Limite sua resposta a aproximadamente 250 tokens."
            )
        else:
            prompt = prompt_map[interesse]

        enviar_pergunta(prompt)
    else:
        st.error(f"Obra com ID {obra_id} não encontrada.")


def extrair_opcoes_links(texto):
    """
    Extrai opções de links do texto no formato Markdown.

    Args:
        texto (str): Texto contendo links em Markdown.

    Returns:
        list of tuples: Lista de tuplas contendo o texto do link e o destino.
    """
    if not isinstance(texto, str):
        raise TypeError("Esperado uma string, mas recebeu um valor do tipo: {}".format(type(texto).__name__))

    padrao = r'\d+\.\s*\[(.*?)\]\((.*?)\)'
    matches = re.findall(padrao, texto)
    return matches
  
         
 # Função para registrar respostas do RELIA
def registrar_resposta_relai(resposta_text):
    st.session_state.messages.append({"role": "RELIA", "content": resposta_text})
    inserir_mensagem_chat(
        roteiro_id=st.session_state['roteiro_id'],
        role='RELIA',
        content=resposta_text
    )
 
    
def enviar_pergunta(prompt):
    """Envia a pergunta do usuário ou a pergunta de interesse para a LLM."""
    language_code = st.session_state.get('language', 'pt-br')
    system_message = SYSTEM_MESSAGES.get(language_code)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7,
            n=1
        )
        response_text = response.choices[0].message.content.strip()
    except Exception as e:
        response_text = "Erro ao gerar resposta do modelo."
        st.error(f"Erro ao se comunicar com o modelo: {e}")

    st.session_state.messages.append({"role": "RELIA", "content": response_text})
    inserir_mensagem_chat(
        roteiro_id=st.session_state['roteiro_id'],
        role='RELIA',
        content=response_text
    )
    st.rerun()
    

# Registrar a mensagem do usuário no banco de dados
def registrar_mensagem_usuario(sanitized_prompt):
    user ={st.session_state['usuario']['nome']}
    st.session_state.messages.append({"role": "user", "content": sanitized_prompt})
    inserir_mensagem_chat(
        roteiro_id=st.session_state['roteiro_id'],
        role='user',  # Role padronizado
        content=sanitized_prompt
    )
    
    
@st.cache_data(show_spinner=True)
def gerar_resumo_obra(obra_id, usuario):
    obra = obter_obra_por_id(obra_id)
    if obra:
        titulo = obra['titulo']
        autor = obra['autor']
        language_code = st.session_state.get('language', 'pt-br')
        system_message = SYSTEM_MESSAGES.get(language_code, SYSTEM_MESSAGES['pt-br'])
        
        prompt_resumo_obra = (
            f"Como um excelente tutor em literatura, forneça um resumo conciso da obra \"{titulo}\" "
            f"e uma breve biografia do autor {autor}. Este resumo deve ter aproximadamente 250 tokens. "
            f"Use uma linguagem adequada para um leitor com as seguintes características: Nome: {usuario['nome']}, Idade: {usuario['idade']}, "
            f"Cidade: {usuario['cidade']}, Interesses: {usuario['interesses']}. "
            f"O resumo deve ser cativante e despertar a curiosidade do leitor. No final do resumo, inclua uma seção com uma chamada para ação que apresente diversos tópicos de interesse relacionados à obra. "
            f"Formate esses tópicos como uma lista numerada em Markdown sem links.\n"
            f"Sempre assine como **RELIA**. Use formatação Markdown no texto."
        )
        
        try:
            response = get_openai_response(prompt_resumo_obra)
            return response if response else "Erro ao gerar resposta do modelo."
        except Exception as e:
            st.error(f"Erro ao se comunicar com o modelo: {e}")
            return "Erro ao gerar resposta do modelo."
    else:
        st.error(f"Obra com ID {obra_id} não encontrada.")
        return "Obra não encontrada."
 
 
# Exemplo de uso ao iniciar um roteiro
def iniciar_roteiro(obra_id, usuario_id):
    st.session_state["roteiro_id"] = criar_novo_roteiro(obra_id, usuario_id)
    registrar_log_uso("Início do roteiro", st.session_state['usuario']['id'])
      

#Perguntas do resumo
def enviar_pergunta_personalizada(pergunta):
    """
    Simula o envio de uma pergunta pelo usuário ao clicar em um botão de link.

    Args:
        pergunta (str): A pergunta a ser enviada.
    """
    sanitized_prompt = sanitize_input(pergunta)
    user = st.session_state['usuario']['nome']
    if not sanitized_prompt:
        st.warning("Pergunta inválida.")
    else:
        st.chat_message(user).markdown(sanitized_prompt)
        st.session_state.messages.append({"role": "user", "content": sanitized_prompt})
        inserir_mensagem_chat(
            roteiro_id=st.session_state['roteiro_id'],
            role='user',
            content=sanitized_prompt
        )
        language_code = st.session_state.get('language', 'pt-br')
        system_message = SYSTEM_MESSAGES.get(language_code, SYSTEM_MESSAGES['pt-br'])
        prompt_full = (
            f"Você está interagindo com um leitor interessado na obra '{st.session_state['obra']}' de {st.session_state['autor']}. "
            f"Informações do usuário: Nome: {st.session_state['usuario']['nome']}, "
            f"Idade: {st.session_state['usuario']['idade']}, Cidade: {st.session_state['usuario']['cidade']}, "
            f"Interesses: {st.session_state['usuario']['interesses']}. "
            f"Histórico da conversa: {st.session_state['historico_conversa']}. "
            f"Pergunta do usuário: {sanitized_prompt}. "
            f"Responda de forma empática e envolvente, mantendo o foco na obra e no autor. Limite a resposta a 250 tokens."
        )
        
        try:
            resposta = get_openai_response(prompt_full)
        except Exception as e:
            resposta = "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente mais tarde."
            st.error("Ocorreu um erro ao se comunicar com o modelo. Por favor, tente novamente.")
            print(f"Erro na comunicação com o modelo: {e}")
        
        resposta_text = resposta if resposta else "Desculpe, não consegui gerar uma resposta no momento."
        
        # Update message history
        st.session_state.messages.append({"role": "RELIA", "content": resposta_text})
                
        # Register the response in the database
        inserir_mensagem_chat(
            roteiro_id=st.session_state['roteiro_id'],
            role='RELIA',
            content=resposta_text
        )
         
        # Displays the LLM's response in the chat
        with st.chat_message("RELIA"):
            # Display the response with visual highlight
            st.markdown('<div class="chat-message-relia">', unsafe_allow_html=True)
            st.markdown(f"**🤖 RELIA:** {resposta_text}")
            st.markdown('</div>', unsafe_allow_html=True)
        st.rerun()
        


def exibir_checkpoint():
    """Exibe os botões pressionados durante a sessão."""
    st.subheader("Ponto de Reflexão: Interações Registradas")
    if st.session_state.botoes_pressionados:
        for idx, registro in enumerate(st.session_state.botoes_pressionados, 1):
            st.write(f"{idx}. **{registro['botao']}** - Níveis: {', '.join(registro['niveis'])}")
    else:
        st.write("Nenhuma interação registrada até o momento.")

 #--------------------- teste sobre barra de dialogo -----------------
 

def enhanced_chat_input(placeholder="Faça uma pergunta sobre a obra ou clique nos botões de interesse"):
    """
    Cria uma barra de chat melhorada com estilo personalizado.
    """
          
   # Criar layout centralizado usando colunas
    col1, col2, col3 = st.columns([1, 4, 1])

    with col2:
               
        # Campo de entrada de chat
        prompt = st.chat_input(placeholder)
        return prompt

  
    
def tela_chat():
    
    """
    Controla o fluxo da tela do chat, exibindo o resumo, os botões de interesse, o checkpoint e a caixa de diálogo.
    """
    
    # Definição do CSS personalizado
     #/* Ocultar cabeçalho e rodapé padrão do Streamlit */
            #header {visibility: hidden;}
            #footer {visibility: hidden;}
   
                 
   # Seleção de idioma
    idiomas_disponiveis = {
        'Português (Brasil)': 'pt-br',
        'Português (Portugal)': 'pt-pt',
        'Inglês': 'en',
        'Espanhol': 'es'
    }

    if st.session_state.get("tela") in ["chat", "pesquisa_obra"]:
        #st.sidebar.header("Configurações")
        idioma_selecionado = st.sidebar.selectbox(
            "Selecione seu idioma:",
            options=list(idiomas_disponiveis.keys()),
            index=list(idiomas_disponiveis.values()).index(st.session_state['language']) if st.session_state['language'] in idiomas_disponiveis.values() else 0,
            disabled=True
        )
        selected_language_code = idiomas_disponiveis[idioma_selecionado]
        if selected_language_code != st.session_state['language']:
            st.session_state['language'] = selected_language_code
            print("idioma_selecionado")
            #st.rerun()
    
    
    roteiro_id = st.session_state.get('roteiro_id')
    if not roteiro_id:
        st.error("Roteiro não encontrado. Por favor, inicie um novo roteiro.")
        return

    # Verifica e inicializa a obra corretamente
    obra_id = st.session_state.get('obra_id')
    if not obra_id:
        st.error("Obra não encontrada. Por favor, selecione uma obra válida para continuar.")
        st.session_state['tela'] = 'pesquisa_obra'
        st.rerun()
        return
    
    usuario = st.session_state.get('usuario')
    if not usuario:
        st.error("Informações do usuário não encontradas. Por favor, faça login novamente.")
        return

    usuario_id = usuario.get('id')
    if not usuario_id:
        st.error("ID do usuário não encontrado. Por favor, faça login novamente.")
        return


    # Verifica se a obra atual mudou
    if 'obra_atual' not in st.session_state or st.session_state['obra_atual'] != obra_id:
        # Atualiza o estado da obra
        obra = obter_obra_por_id(obra_id)
        if obra:
            st.session_state['obra'] = obra['titulo']
            st.session_state['autor'] = obra['autor']
            roteiro_id = criar_ou_obter_roteiro(obra_id, usuario_id)
            if roteiro_id:
                st.session_state['roteiro_id'] = roteiro_id
                st.session_state['obra_atual'] = obra_id
                # Limpa o resumo anterior
                st.session_state['resumo'] = None
                st.toast("Roteiro recuperado ou criado com sucesso.")
                time.sleep(1.5)
            else:
                st.error("Erro ao criar ou recuperar o roteiro.")
        else:
            st.error(f"Obra com ID {obra_id} não encontrada.")
            
  #--------------------------------------------------------------------------------------------------------------------------
    
    

    #----------------------------------------------------------------------------------------------------------------
    st.markdown(
        f"<p class='titulo-destaque'> RELIA - Roteiro Empático de Leitura: {st.session_state.obra}</p>",
        unsafe_allow_html=True, help="Aqui você percorre o roteiro de leitura personalizado, passando pelos botões de interesses.")
 
   # Gerar e exibir o resumo
    if 'resumo' not in st.session_state or st.session_state.get('resumo') is None:
        resumo = gerar_resumo_obra(st.session_state['obra_atual'], st.session_state['usuario'])
        st.session_state['resumo'] = resumo if isinstance(resumo, str) else "Resumo não disponível."
        print("Resumo:" , resumo)
         # Exibir o resumo em um container com borda
        st.markdown(f'<div class="bordered-container">{st.session_state["resumo"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bordered-container">{st.session_state["resumo"]}</div>', unsafe_allow_html=True)

   
    # Extrair opções de links do resumo, garantindo que é uma string
    if isinstance(st.session_state['resumo'], str):
        opcoes_links = extrair_opcoes_links(st.session_state['resumo'])
    else:
        opcoes_links = []
    
    # Renderizar botões para cada opção de link dentro de um container com borda
    if opcoes_links:
       # st.markdown('<div class="bordered-container">', unsafe_allow_html=True)
        st.markdown("**Sobre os tópicos:** escolha uma das opções abaixo ou siga para o roteiro:")
        
        # Define o número de colunas por linha (ajuste conforme necessário)
        num_colunas = 2
        colunas = st.columns(num_colunas)
        
        for idx, (texto_link, destino) in enumerate(opcoes_links):
            coluna = colunas[idx % num_colunas]
            with coluna:
                # Adicionar margens ao botão
                #st.markdown('<div style="margin-bottom: 10px;">', unsafe_allow_html=True)
                if st.button(texto_link, key=f"link_{idx}", help="Esse botão é como você pode fazer a questão recomendada pelo rsumo do RELIA"):
                    enviar_pergunta_personalizada(texto_link)
                    
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
                # Transformar o destino em uma pergunta correspondente
                pergunta = texto_link  # Você pode customizar como deseja transformar o link em pergunta
                enviar_pergunta_personalizada(pergunta)
                
    
    # Recuperar mensagens do banco de dados se ainda não estiverem na sessão
    if not st.session_state.messages:
        try:
            mensagens = obter_mensagens_chat(roteiro_id)
            if mensagens:
                st.session_state.messages = [{"role": role, "content": content} for role, content, _ in mensagens]
                print(f"{len(mensagens)} mensagens recuperadas do banco de dados.")
            else:
                st.session_state.messages = []
                st.toast("Este é um novo chat. Comece fazendo uma pergunta ou selecionando um dos tópicos de interesse abaixo.")
                time.sleep(1)
                print("Nenhuma mensagem encontrada no banco de dados. Iniciando um novo chat.")
        except Exception as e:
            st.error(f"Erro ao recuperar mensagens do banco de dados: {e}")
            print(f"Erro ao recuperar mensagens: {e}")


            
    with st.container(border=False):
                 
        for message in st.session_state.messages:
            role = message.get("role", "")  # Usar .get para evitar KeyError
            content = message.get("content", "")
            
             # Verificar se role é uma string
            if isinstance(role, str):
                role_lower = role.lower()
            else:
                role_lower = ""
                print(f"Role inválido: {role}")

            if role_lower == "relia":
                icon = "🤖"  # Ícone para RELIA
                display_role = "RELIA"
                css_class = "chat-message-relia"
            elif role_lower == "user":
                icon = "👤"  # Ícone para o usuário
                display_role = st.session_state['usuario']['nome']
                css_class = "chat-message-user"
            else:
                # Caso role não seja reconhecido, tratar como usuário genérico
                icon = "👤"
                display_role = "Usuário"
                css_class = "chat-message-user"

            st.markdown(f'<div class="{css_class}">**{icon} {display_role}:** {content}</div>', unsafe_allow_html=True)
            print(f"Mensagem exibida: {display_role}: {content}")
            
         

            #with st.chat_message(display_role):
             #   st.markdown(f"**{icon} {display_role}:** {content}")
              #  print(f"Mensagem exibida: {display_role}: {content}")
        
        # Container fixo inferior
        st.markdown('<div class="fixed-bottom-container">', unsafe_allow_html=True)

        # Criar um placeholder para inserir componentes dentro da div
        container = st.empty()

        with container.container():
            # Área de botões de interesse
            
             # Botões de interesse
            #st.markdown('<div class="interest-buttons-container">', unsafe_allow_html=True)
            #exibir_botoes_interesses()
            #st.markdown('</div>', unsafe_allow_html=True)
            
            # Input e botões de ação
            st.markdown('<div class="action-buttons-container" ">', unsafe_allow_html=True)
    
            if prompt := enhanced_chat_input():
                sanitized_prompt = sanitize_input(prompt)
                user ={st.session_state['usuario']['nome']}
                
                if not sanitized_prompt:
                    st.warning("Por favor, insira uma pergunta válida.")
                else:
                    # Exibe a pergunta do usuário no chat dentro de um container com bordas
                    with st.container():
                        st.markdown('<div class="chat-message-user">', unsafe_allow_html=True)
                        st.markdown(f"**👤 {user}:** {sanitized_prompt}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.session_state.messages.append({"role": "user", "content": sanitized_prompt})  # Role padronizado
                    
                    # Registrar a mensagem do usuário no banco de dados
                    inserir_mensagem_chat(
                        roteiro_id=roteiro_id,
                        role='user',  # Role padronizado
                        content=sanitized_prompt
                    )
                    
                    #REVISAR1
                    # Monta o prompt para a LLM com base no contexto
                    prompt_full = (
                            f"Considere que a pergunta abaixo se refere a obra {st.session_state['obra']} e autor {st.session_state['autor']}. "
                            f"Considere que quem está questionando é um leitor com as seguintes características: Seu nome é {usuario['nome']}, "
                            f"tem a idade de {usuario['idade']} anos, vive na cidade de {usuario['cidade']} e tem interesse em {usuario['interesses']}. "
                            f"Considere o que já foi conversado. E a pergunta é essa: {sanitized_prompt}. Use um tom persuasivo e crie uma retorica."
                            f"Use Markfown e diversifique a resposta com tabela, grafico, info, lista itens, icones e figuras. Use o dialogo socratico para dar continuidade ao chat."
                            f"OUTPUT: Máximo 250 Tokens e sempre entorno da obra {st.session_state['obra']} e autor {st.session_state['autor']}."
                    )
                    try:
                        #resposta = get_openai_response(prompt_full)
                        resposta = get_openai_response(prompt_full)
                    except Exception as e:
                        resposta = "Erro ao gerar resposta do modelo."
                        st.error(f"Erro ao se comunicar com o modelo: {e}")
                        print(f"Exception ao se comunicar com o modelo: {e}")
                        
                    resposta_text = resposta if resposta else "Erro ao gerar resposta do modelo."
                    st.session_state.messages.append({"role": "RELIA", "content": resposta_text})
                    # Registrar a mensagem do assistente no banco de dados
                    inserir_mensagem_chat(
                        roteiro_id=roteiro_id,
                        role='RELIA',
                        content=resposta_text
                    )
                    # Exibe a resposta da LLM no chat dentro de um container com bordas
                    with st.container():
                        st.markdown('<div class="chat-message-relia">', unsafe_allow_html=True)
                        st.markdown(f"**🤖 RELIA:** {resposta_text}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.rerun()
            
                    
            # Botão de Checkpoint dentro de um container com borda e design melhorado
            # Botões de ação
                                    
            col1, col2,col3 = st.columns([1, 5, 1]) # Cria colunas para o botão dentro do container
            
            with col1:
                col11, col21,col31 = st.columns([1, 3, 1]) # Cria colunas para o botão dentro do container
                with col21:                    
                    if st.button(" ⬅️ Gerar Relatório "):
                        st.session_state["tela"] = "area_leitor"
                        st.session_state['etapa_atual'] = 0
                        st.rerun()
                    
            
            with col2:
                
                  # CSS personalizado para estilizar e posicionar o botão do Streamlit
                    button_css = """
                        <style>
                        /* Estilização e posicionamento do botão padrão do Streamlit */
                        div.stButton > button:first-child {
                            position: fixed;               /* Fixa o botão na tela */
                            top: 10%;                      /* Posiciona no meio verticalmente */
                                                /* Posiciona no meio horizontalmente */
                            transform: translate(-15%, -15%); /* Centraliza exatamente */
                            background-color: #00edfb; /* Cor de fundo */
                            color: white;                  /* Cor do texto */
                            padding: 5px 5px;            /* Padding interno */
                            font-size: 8px;               /* Tamanho da fonte */
                            border: none;                  /* Sem borda */
                            border-radius: 8px;            /* Bordas arredondadas */
                            cursor: pointer;               /* Cursor de pointer ao passar o mouse */
                            transition: background-color 0.3s, transform 0.3s; /* Transições suaves */
                            z-index: 9999;                 /* Garante que o botão fique acima de outros elementos */
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Sombra para dar profundidade */
                                                    
                        }
                        
                        /* Estilo base para todos os botões */
                        div.stButton > button:first-child {
                            min-width: 120px;
                            height: 40px;
                            background-color: #00edfb;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            font-size: 14px;
                            padding: 8px 16px;
                            cursor: pointer;
                            transition: all 0.3s ease;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            text-align: center;
                            margin: 0 5px;
                        }
                        
                        /* Botão de navegação esquerdo */
                        .nav-button-left {
                            position: fixed;
                            top: 50%;
                            left: 20px;
                            transform: translateY(-50%);
                            z-index: 1000;
                        }
                        
                        /* Botão de navegação direito */
                        .nav-button-right {
                            position: fixed;
                            top: 50%;
                            right: 20px;
                            transform: translateY(-50%);
                            z-index: 1000;
                        }
                        div.stButton > button:first-child:hover {
                            background-color: #e67e22;     /* Cor ao passar o mouse */
                            transform: translate(-65%, -50%) scale(1.05); /* Aumenta ligeiramente o botão */
                            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                        }
                        /* Estilo responsivo para telas menores */
                        @media (max-width: 768px) {
                            div.stButton > button:first-child {
                                min-width: 100px;
                                font-size: 12px;
                                padding: 6px 12px;
                            }
                            
                            .fixed-bottom-buttons {
                                flex-wrap: wrap;
                                justify-content: center;
                            }
                        }
                        
                        </style>
                        """
                    st.markdown(button_css, unsafe_allow_html=True)

                    exibir_botoes_interesses_flotantes()

                    st.markdown('</div>', unsafe_allow_html=True)  # Fechando action-buttons-container
                           
            with col3:
                colr1, colr2,colr3 = st.columns([1, 2, 1]) # Cria colunas para o botão dentro do container
                with colr2: 
                    
                   
                    if st.button(" ▶️ Ponto de Reflexão "):
                        exibir_checkpoint()
                        st.session_state["tela"] = "checkpoint"
                        st.session_state['etapa_atual'] = 0
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)  # Fechando action-buttons-container
            
        # Rodapé
        # Footer minimalista com tooltip
        st.markdown("""
            <div class="footer" title="O RELIA utiliza IA generativa e pode conter imprecisões. Recomendamos verificar as informações em fontes acadêmicas confiáveis.">
                ⚠️ Conteúdo gerado por IA - Pode cometer erros. Considere verificar informações importantes. ⚠️ 
            </div>
        """, unsafe_allow_html=True) 
        st.markdown('</div>', unsafe_allow_html=True)
       

# Carregar o CSS personalizado
#local_css("style.css")

def exibir_botoes_interesses_flotantes():
    """Exibe os botões de interesse de forma aprimorada e flutuante junto com outros botões de ação."""
    # Definir os botões de interesse e suas descrições
    interesses = [
        ("Contexto Histórico", "Clique para saber mais sobre o contexto histórico da obra", "#f39c12"),
        ("Curiosidades", "Clique para descobrir curiosidades sobre a obra", "#e67e22"),
        ("Impacto Cultural", "Clique para entender o impacto cultural da obra", "#1abc9c"),
        ("Estilo", "Clique para saber sobre a linguagem e estilos desta obra", "#3498db"),
        ("Questões Intrigantes", "Clique para explorar questões instigantes sobre a obra", "#9b59b6"),
        ("Moral", "Clique para entender a moral da história da obra", "#e74c3c"),
        ("Personagens", "Clique para conhecer os personagens da obra", "#2ecc71")
    ]

       # Sempre manter os 7 botões principais visíveis
    botoes_visiveis = interesses.copy()
    
    # Exibir os botões dentro de uma barra fixa na parte inferior
    st.markdown('<div class="fixed-bottom-buttons">', unsafe_allow_html=True)
    
    cols = st.columns(len(interesses) + 3, vertical_alignment="center", gap="medium")  # Colunas para "Ponto de Reflexão", botões de interesse, "Mais", e "Gerar Relatório"
    
    with st.container():
        
        # Botões de interesses e ações
        for idx, (interesse, help_text, color) in enumerate(interesses):
            with cols[idx + 1]:
                icon = ICON_MAP.get(interesse, "🔹")
                if st.button(f"{icon} {interesse}"):
                    registrar_botao(interesse, TAXONOMY_MAP.get(interesse, ["Desconhecido", "Desconhecido"]))
                    gerar_resposta_interesse(interesse)
                    st.rerun()
        
        # Botão "Mais" para gerar ações adicionais
        with cols[-2]:
            if st.button(f"{ICON_MAP['Mais']} Mais"):
                # Gera 3 tópicos adicionais aleatórios da lista de ações ACOES
                acoes_disponiveis = [acao for acao in ACOES if acao not in [interesse[0] for interesse in botoes_visiveis]]
                acoes_selecionadas = random.sample(acoes_disponiveis, min(3, len(acoes_disponiveis)))
                # Adiciona os tópicos ao conteúdo para exibição
                for acao in acoes_selecionadas:
                    gerar_resposta_interesse(acao)
                    registrar_botao(acao, TAXONOMY_MAP.get(acao, ["Desconhecido", "Desconhecido"]))
                st.rerun()
            
                # CSS personalizado para estilizar o botão do Streamlit
            button_css = """
                <style>
                /* Estilização do botão padrão do Streamlit */
                
                </style>
                """
            st.markdown(button_css, unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
