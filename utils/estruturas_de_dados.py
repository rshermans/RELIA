import streamlit as st
import openai
import tiktoken # type: ignore
from utils.api import get_openai_response
import re
import sqlite3
from database import carregar_dados_banco, obter_nome_acao_por_id
import random
import streamlit.components.v1 as components


#  Estrutura de dados para representar os níveis de Bloom e as ações

#------------------ Revisão de incosistencias e adaptação para tabela acoes-----------------------------

# Estabelecer a conexão com o banco de dados
conn = sqlite3.connect('relia.db') 

@st.cache_data
def get_dados_banco():
    return carregar_dados_banco(conn)


def encontrar_acao_checkpoint(nivel_bloom, pontuacao_total, acoes_niveis):
    # Filtrar ações pelo nível de Bloom
    acoes_do_nivel = [
        acao_id for acao_id, dados in acoes_niveis.items() 
        if dados.get('nivel_bloom') == nivel_bloom
    ]
    
    if not acoes_do_nivel:
        return None
    
    # Debug: Mostrar ações disponíveis para o nível atual
    #st.write(f"Ações disponíveis para o nível '{nivel_bloom}': {acoes_do_nivel}")
    
    
    # Randomizar uma ação do nível
    acao_id = random.choice(acoes_do_nivel)
    pontos_acao = acoes_niveis[acao_id].get('pontos', 1)  # Exemplo de pontos
    tipo_resposta = acoes_niveis[acao_id].get('tipo_resposta', 'texto')  # Exemplo de tipo
    nomes_acao = acoes_niveis[acao_id].get('nomes_acao', 'Ação Desconhecida')
    
    return acao_id, pontos_acao, tipo_resposta, nomes_acao


# Função para limitar a quantidade de tokens
def limitar_tokens(texto, max_tokens=1000):
    enc = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens = enc.encode(texto)

    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    
    return enc.decode(tokens)

# Função para resumir o histórico de mensagens
def resumir_historico_mensagens(mensagens, max_tokens=600):
    texto_completo = " ".join([msg['content'] for msg in mensagens])
    texto_resumido = limitar_tokens(texto_completo, max_tokens)
    
    resumo_final = [{"role": "system", "content": "Resumo do histórico anterior:"},
                    {"role": "user", "content": texto_resumido}]
    
    return resumo_final


def gerar_resposta_chatgpt(prompt, historico_mensagens=None, max_tokens=1500):
    """
    Gera uma resposta utilizando o ChatGPT, com a adaptação para limitar tokens e resumir o histórico de mensagens.
    """
    try:
        # Verifica se há histórico de mensagens a ser resumido
        if historico_mensagens:
            # Resumir o histórico de mensagens se existir
            mensagens_resumidas = resumir_historico_mensagens(historico_mensagens, max_tokens)
        else:
            mensagens_resumidas = []

        # Adiciona o prompt atual à lista de mensagens
        mensagens_resumidas.append({"role": "user", "content": prompt})

        # Chamada para a API da LLM
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=mensagens_resumidas,
            max_tokens=3000,  # Ajuste do limite de tokens para a resposta
            temperature=0.7
        )

        # Extrair e retornar a resposta
        resposta = response.choices[0]['message']['content'].strip()
        return resposta
    
    except Exception as e:
        print(f"Erro ao se comunicar com a LLM: {e}")
        return None
    

def obter_resposta_texto(acao_id):
    key = f"resposta_texto_{acao_id}"
    valor_inicial = st.session_state.get(key, "")
    cole, colR,cole2 = st.columns([1, 4, 1])
    with colR:  resposta = st.text_area(f"Resposta para a ação {obter_nome_acao_por_id(acao_id)}:", value=valor_inicial, height=100, key=key)
        # Atualizar o session_state após a resposta ser modificada
    if resposta:
        st.session_state[key] = resposta
    # Injetar CSS para destacar o campo de texto
    st.markdown(f"""
        <style>
            /* Estilizando o textarea do Streamlit */
            textarea[data-testid="stTextArea"][aria-describedby*="{key}"] {{
                background-color: #f0f9ff;  /* Cor de fundo azul claro suave */
                box-shadow: 0 0 10px rgba(0, 123, 255, 0.3);  /* Sombra azul suave ao redor do campo */
                border-radius: 10px;  /* Bordas arredondadas para um visual amigável */
                transition: background-color 0.3s ease-in-out, box-shadow 0.3s ease-in-out;  /* Suavização das mudanças */
            }}

            /* Destaque ao focar no campo de texto */
            textarea[data-testid="stTextArea"][aria-describedby*="{key}"]:focus {{
                background-color: #e6f7ff;  /* Cor de fundo mais intensa quando em foco */
                box-shadow: 0 0 15px rgba(0, 123, 255, 0.5);  /* Sombra mais intensa para indicar foco */
                outline: none;  /* Remover outline padrão do navegador */
            }}
        </style>
    """, unsafe_allow_html=True)

    print("Resposta na função resposta texto: ",resposta)
    return resposta


def obter_resposta_quizz(acao_id):
    options = ["Opção 1", "Opção 2", "Opção 3", "Opção 4"]
    key = f"resposta_quizz_{acao_id}"
    valor_inicial = st.session_state.get(key, options[0])
    resposta = st.radio(f"Selecione a resposta correta para a ação {acao_id}:", options, index=options.index(valor_inicial), key=key)
    return resposta


def obter_resposta_input(acao_id):
    key = f"resposta_input_{acao_id}"
    valor_inicial = st.session_state.get(key, "")
    resposta = st.text_input(f"Resposta para a ação {acao_id}:", value=valor_inicial, key=key)
    return resposta


def obter_resposta_checkbox(acao_id, opcoes=None):
    if opcoes is None:
        opcoes = ["Item 1", "Item 2", "Item 3"]
    key = f"resposta_checkbox_{acao_id}"
    valor_inicial = st.session_state.get(key, [])
    resposta = st.multiselect(f"Selecione as opções para a ação {acao_id}:", opcoes, default=valor_inicial, key=key)
    return resposta


def obter_resposta_slider(acao_id, min_val=0, max_val=1000):
    key = f"resposta_slider_{acao_id}"
    valor_inicial = st.session_state.get(key, min_val)
    resposta = st.slider(f"Resposta para a ação {acao_id}:", min_value=min_val, max_value=max_val, value=valor_inicial, key=key)
    return resposta


def exibir_campo_resposta_OLD(tipo_resposta, acao_id):
    """
    Exibe o campo de resposta apropriado com base no tipo de resposta.

    Parâmetros:
    - tipo_resposta (str): O tipo de resposta esperado (e.g., 'texto', 'quizz', 'input', 'checkbox', 'slider').
    - acao_id (int): O ID da ação atual.

    Retorna:
    - resposta_usuario (str): A resposta fornecida pelo usuário.
    """
    tipo_resposta = tipo_resposta.lower()
    
    mapeamento_widgets = {
        'texto': obter_resposta_texto,
        'textarea': obter_resposta_texto,
        'quizz': obter_resposta_quizz,
        'input': obter_resposta_input,
        'checkbox': obter_resposta_checkbox,
        'slider': obter_resposta_slider
    }
    
    if tipo_resposta in mapeamento_widgets:
        resposta = mapeamento_widgets[tipo_resposta](acao_id)
        print("Resposta na função exibir campo: ",resposta)
        st.session_state['resposta'] = resposta
    else:
        st.error(f"Tipo de resposta '{tipo_resposta}' desconhecido.")
        resposta = None  
    return resposta



def exibir_campo_resposta(tipo_resposta, acao_id):
    """
    Exibe o campo de resposta baseado no tipo de resposta.
    Atualiza o st.session_state com a resposta do usuário.
    """
    resposta_key = f'resposta_{acao_id}'
    
    if tipo_resposta == 'texto' or 'textarea':
        resposta = st.text_area("Sua Resposta:",value="", key=resposta_key)
        st.session_state['resposta'] = resposta
        #print("Sesion State na função exibir campo: ",{st.session_state['resposta']})
        print("Resposta na função exibir campo: ",resposta)
        return resposta
    elif tipo_resposta == 'multiple_choice':
        # Exemplo de campo de múltipla escolha
        opcoes = ['Opção 1', 'Opção 2', 'Opção 3']
        resposta = st.radio("Escolha uma opção:", opcoes, key=resposta_key)
        return resposta
    # Adicione outros tipos de resposta conforme necessário
    else:
        st.error("Tipo de resposta desconhecido.")
        return ""



# Funções revisadas pelo GPT o1-Preview


def gerar_pergunta_com_llm(acao_data, contexto):
    """
    Gera uma pergunta personalizada usando a LLM, com base em uma ação e no contexto da obra.
    """
    try:
        prompt = (
            f"Crie uma pergunta de {contexto['nivel_bloom']} sobre a obra '{contexto['obra']}' de {contexto['autor']} "
            f"focalizada na ação de '{acao_data['nomes_acao']}'.  O leitor é {contexto['perfil_usuario']}. "
            f"A pergunta deve ser concisa e clara e objetiva para o contexto apresentado e não conter links ou outros elementos formatados.  "
            f"Exemplo de pergunta: '{acao_data['template_pergunta'].format(obra=contexto['obra'])}'"
        )

        pergunta = get_openai_response(prompt)  # Retorna a pergunta obtida da LLM.

        if pergunta is None or not pergunta:  # Lida com resposta nula ou vazia da LLM.
           return st.error("Erro ao gerar pergunta. Tente novamente.")
        
        return pergunta  
    except Exception as e:
        return st.error(f"Erro ao gerar pergunta: {e}")



def avaliar_resposta_com_llm(pergunta, resposta_usuario, contexto):
    """
    Avalia a resposta do usuário usando a LLM e retorna o feedback e a pontuação.
    
    Parâmetros:
    - pergunta (str): A pergunta feita ao usuário.
    - resposta_usuario (str): A resposta fornecida pelo usuário.
    - contexto (dict): Dicionário contendo informações contextuais como obra, autor, nível de Bloom, etc.
    
    Retorna:
    - feedback_final (str): Feedback detalhado sobre a resposta do usuário.
    - pontuacao (int): Pontuação obtida pelo usuário.
    """
    prompt = gerar_prompt_avaliacao(pergunta, resposta_usuario, contexto)
    
    try:
        # Obter a resposta do LLM
        resposta_avaliacao = get_openai_response(prompt)

        if not resposta_avaliacao:
            st.error("Erro ao avaliar a resposta com a LLM. A resposta não foi recuperada.")
            return "Erro na avaliação da resposta.", 0

        # Processar a resposta da LLM
        feedback_final, pontuacao = processar_resposta_llm(resposta_avaliacao)

        # Atualizar a pontuação total do usuário
        #st.session_state['pontuacao_total'] += pontuacao

        return feedback_final, pontuacao

    except Exception as e:
        st.error(f"Erro inesperado ao avaliar a resposta da LLM: {e}")
        return "Erro na avaliação da resposta.", 0


def obter_acao_por_nivel_e_pontuacao(nivel_bloom, pontuacao):
    # Conectar ao banco de dados
    conn = sqlite3.connect('relia.db')
    cursor = conn.cursor()

    # Consultar a ação pelo nível de Bloom e pela pontuação
    cursor.execute("SELECT * FROM acoes WHERE nivel_bloom = ? AND pontos = ?", (nivel_bloom, pontuacao))
    acao = cursor.fetchone()

    # Fechar a conexão com o banco de dados
    conn.close()

    # Se a ação for encontrada, retornar um dicionário com os dados
    if acao:
        return {
            "id": acao[0],
            "nome": acao[1],
            "nivel_bloom": acao[2],
            "pontos": acao[3],
            "tipo_resposta": acao[4],
            "template_pergunta": acao[5],
            "respostas_esperadas": acao[6]
        }
    else:
        return None

# Dicionário com a estrutura da rubrica de avaliação
# Perguntas para cada nível


def obter_nivel_atual_usuario():
    """
    Obtém o nível atual do usuário com base na pontuação total.
    """
    pontuacao_total = st.session_state.get('pontuacao_total', 0)
    nivel_bloom = determinar_nivel_bloom(pontuacao_total)
    return nivel_bloom, pontuacao_total


def determinar_nivel_bloom(pontuacao):
    """
    Determina o nível de proficiência com base na pontuação.
    """
    if pontuacao <= 15:
        return "Lembrar"
    elif pontuacao <= 45:
        return "Compreender"
    elif pontuacao <= 91:
        return "Aplicar"
    elif pontuacao <= 153:
        return "Analisar"
    elif pontuacao <= 190:
        return "Avaliar"
    else:
        return "Criar"


def gerar_prompt_avaliacao(pergunta, resposta_usuario, contexto):
    """
    Gera o prompt para avaliação da resposta do Leitor pela LLM.
    
    Parâmetros:
    - pergunta (str): A pergunta feita ao Leitor.
    - resposta_usuario (str): A resposta fornecida pelo Leitor.
    - contexto (dict): Dicionário contendo informações contextuais como obra, autor, nível de Bloom, etc.
    
    Retorna:
    - prompt (str): O prompt formatado para enviar à LLM.
    """
    prompt = f"""
    Avalie a resposta a esta pergunta, considerando a obra '{contexto['obra']}', o nível da Taxonomia de Bloom {contexto['nivel_bloom']} e o contexto fornecido.
    
    **Pergunta:** {pergunta}

    **Resposta do Usuário:** {resposta_usuario}

    **Avaliação (Se válida ou não a pontuação e Feedback):**

    Por favor, forneça uma avaliação construtiva seguindo este formato:

    Pontuação: [0-10]
    Feedback: [feedback detalhado sobre a resposta do Leitor, explicando as razões para a pontuação]

    Exemplo de resposta: 
    Pontuação: 8
    Feedback: 💫 Pontos Fortes:
    - Excelente identificação do conflito interno do protagonista
    - Análise perspicaz da simbologia presente no capítulo 3
    
    📈 Oportunidades de Desenvolvimento:
    - Explore mais a fundo a relação entre o contexto histórico e as escolhas do autor
    - Considere como os elementos narrativos contribuem para o tema central

    🔍 Feedback Personalizado:
    Sua interpretação demonstra sensibilidade e compreensão profunda da obra. Você captou muito bem as nuances do personagem principal e trouxe observações valiosas sobre a narrativa. Para enriquecer ainda mais sua análise, sugiro explorar como o contexto social da época influenciou a escrita do autor.

    📖 Sugestão de Leitura Complementar:
    Recomendo a leitura de "Título Relacionado" de Autor Complementar, que aborda temas similares e pode oferecer novas perspectivas para sua análise.

    - Se tiver dúvida que a obra exista em portugês pode mostrar em inglês. Não alucine e nem crie sugestões que não existam. Se não tiver certeza do que sugerir, sugira trechos da obra, ou temas. 
        Avise se houver imprecisões ou duvidas nas sugestões. Seja cauteloso e responsável pelas informações prestadas sobre o feedback e sobre a obra. Mas seja sempre inovador e disrruptivo. 
    """
    return prompt


def processar_resposta_llm(resposta_avaliacao):
    """
    Processa a resposta da LLM para extrair a pontuação e o feedback.
    
    Parâmetros:
    - resposta_avaliacao (str): A resposta recebida da LLM.
    
    Retorna:
    - feedback_final (str): Feedback detalhado sobre a resposta do usuário.
    - pontuacao (int): Pontuação obtida pelo usuário.
    """
    pontuacao = extrair_pontuacao(resposta_avaliacao)
    feedback_final = extrair_feedback(resposta_avaliacao)
    return feedback_final, pontuacao


def validar_pontuacao(pontuacao_llm, pontos_acao):
    """
    Valida a pontuação da ação com base na pontuação da LLM.
    
    Args:
        pontuacao_llm (int): Pontuação recebida da LLM (0 a 10).
        pontos_acao (int): Pontuação atribuída à ação.
    
    Returns:
        int: Pontuação validada (pontos_acao ou 0).
    """
    if pontuacao_llm < 0 or pontuacao_llm > 10:
        st.error("Pontuação da LLM inválida. Deve estar entre 0 e 10.")
        return 0
    if pontuacao_llm >= 5:
        return pontos_acao
    else:
        return 0
    
    
def extrair_pontuacao(resposta_avaliacao):
    # Função para extrair a pontuação da resposta da LLM
    pontuacao_match = re.search(r"Pontuação:\s*(\d+)", resposta_avaliacao, re.IGNORECASE)
    if pontuacao_match:
        try:
            pontuacao = int(pontuacao_match.group(1))
            if pontuacao < 0 or pontuacao > 10:
                st.error(f"Pontuação inválida recebida: {pontuacao}. Deve estar entre 0 e 10.")
                return 0
            return pontuacao
        except ValueError:
            st.error(f"Erro ao converter pontuação para inteiro: {pontuacao_match.group(1)}")
            return 0
    else:
        st.error("Pontuação não encontrada na resposta da LLM.")
        return 0

def extrair_feedback(resposta_avaliacao):
    # Função para extrair o feedback da resposta da LLM
    feedback_match = re.search(r"Feedback:\s*(.*)", resposta_avaliacao, re.IGNORECASE | re.DOTALL)
    return feedback_match.group(1).strip() if feedback_match else "Feedback não fornecido."
    
        
