import streamlit as st
import sqlite3 
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
#from print_color import print
import os
import requests
#from dotenv import load_dotenv


# Tenta obter a chave API dos segredos do Streamlit ou de variáveis de ambiente
API_KEY = st.secrets["ANTHROPIC_API_KEY"]

# Carregar variáveis de ambiente do arquivo .env
#load_dotenv()

# Obter a chave API das variáveis de ambiente
#API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not API_KEY:
    st.error("API Key não encontrada. Por favor, configure a chave API.")
    st.stop()

API_URL = "https://api.anthropic.com/v1/messages"

# Banco de dados
conn = sqlite3.connect('relia.db')

# Funções de banco de dados

def setup():  
    os.system('clear')
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS perfis (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, idade INTEGER, cidade TEXT, gostos TEXT, opcao_compartilhar INTEGER)')
        #print("Tabela PERFIS criada", tag='success', tag_color='green', color='white')
        conn.execute('CREATE TABLE IF NOT EXISTS obras (id INTEGER PRIMARY KEY AUTOINCREMENT, obra TEXT, autor INTEGER, profile_id INTEGER)')
        #print("Tabela OBRAS criada", tag='success', tag_color='green', color='white')
        conn.execute('CREATE TABLE IF NOT EXISTS prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, prompt TEXT)')
        #print("Tabela PROMPTS criada", tag='success', tag_color='green', color='white')
        return 1
    except Exception as e:
        #print(f"Erro na criação de tabelas: {e}", tag='failure', tag_color='red', color='magenta')
        return 0

def perfil_insert(nome, idade, cidade, gostos):
    sql_str = "INSERT INTO perfis (nome, idade, cidade, gostos, opcao_compartilhar ) VALUES (?, ?, ?, ?, ?)"
    try:
        conn.execute(sql_str, (nome, idade, cidade, gostos, 1))
        conn.commit()
        #print("Novo perfil inserido", tag='success', tag_color='green', color='white')
    except Exception as e:
        #print(f"Erro na inserção do perfil: {e}", tag='failure', tag_color='red', color='magenta')
        print(e)

def obra_insert(obra, autor):
    sql_str = "INSERT INTO obras (obra, autor, profile_id) VALUES (?, ?, ?)"
    try:
        conn.execute(sql_str, (obra, autor, 1))
        conn.commit()
        #print("Nova obra inserida", tag='success', tag_color='green', color='white')
    except Exception as e:
        #print(f"Erro na inserção da obra: {e}", tag='failure', tag_color='red', color='magenta')
        print(e)

# Função get_anthropic_response atualizada
def get_anthropic_response(prompt, max_tokens=1000):
    try:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": "claude-2.1",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(API_URL, json=data, headers=headers)
        response.raise_for_status()
        return response.json()['content'][0]['text']
    except requests.exceptions.RequestException as e:
        #print(f"Erro ao obter resposta da API Anthropic: {e}")
        if e.response is not None:
            #print(f"Detalhes do erro: {e.response.text}")
            print(e)
        return None
    
    
# Telas da aplicação


# Sidebar
def tela_sidebar():
    with st.sidebar:
        st.header("RELIA")
        st.image("imagens/logo_relia-removebg.png", width=None, use_column_width="auto")  # Substitua pelo caminho do logo

        # Botões de Controle
        if st.button("🏠 Voltar ao Início"):
            # Limpar a sessão e voltar ao início
            st.session_state.clear()
            st.rerun()


def tela_principal():
    st.title("RELIA")
    st.markdown("""
    <style>
    .main-header {
        font-size: 2em;
        margin-bottom: 0.5em;
    }
    .sub-header {
        font-size: 1.5em;
        margin-bottom: 1em;
    }
    .expander-content {
        font-size: 1.2em;
    }
    </style>
    """, unsafe_allow_html=True)

    #st.markdown('<div class="main-header">RELIA</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header"><strong>RELIA</strong> - Roteiro Empático de Leitura e Interpretação por Inteligência Artificial - é uma ferramenta inovadora projetada para ampliar a compreensão textual e o acesso à leitura através da inteligência artificial.</div>', unsafe_allow_html=True)

    with st.expander("Saiba mais sobre o RELIA"):
        st.markdown("""
        <div class="expander-content">
        Ao utilizar técnicas avançadas de processamento de linguagem natural, o RELIA auxilia leitores de todas as idades e níveis de conhecimento a explorar obras literárias com profundidade e clareza.
        
        Com o RELIA, você pode:

        - **Analisar Textos Complexos**: A IA identifica conceitos-chave, relações entre ideias e diferentes níveis de significado, facilitando a interpretação de textos complexos.
        - **Participar de Diálogos Interativos**: O sistema promove a interação entre o leitor e a IA, respondendo a perguntas, oferecendo diferentes perspectivas de análise e incentivando a reflexão crítica.
        - **Compartilhar e Colaborar**: Conecte-se com outros leitores, possibilitando debates enriquecedores e a construção conjunta de conhecimento a partir da leitura dos textos.

        Nosso objetivo não é apenas facilitar a leitura e interpretação de textos, mas também promover a empatia, a responsabilidade individual e a construção de um futuro mais ético e interseccional. Junte-se a nós nesta jornada de leitura assistida por IA e descubra novas maneiras de se conectar com a literatura e com outros leitores ao redor do mundo.
        </div>
        """, unsafe_allow_html=True)

def tela_perfil():
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.image("imagens/logo_relia-removebg.png")
        with st.expander("Por que pedimos seu perfil?"):
            st.markdown("""
            <div class="expander-content">
            Para oferecer uma experiência de leitura personalizada e relevante, o RELIA solicita algumas informações do seu perfil. Aqui estão os motivos:

            - **Personalização da Experiência de Leitura**: Adaptamos a análise e interpretação das obras de acordo com suas preferências e contexto individual, tornando a leitura mais envolvente e significativa.
            - **Relevância dos Conteúdos**: Selecionamos e destacamos informações que são mais significativas para você, aumentando sua satisfação com a leitura.
            - **Melhoria da Interação com a IA**: Ajustamos a complexidade das respostas e a forma de comunicação para melhor atender às suas necessidades individuais.
            - **Construção de um Futuro Mais Ético e Interseccional**: Promovemos um ambiente de leitura inclusivo e diversificado, refletindo a diversidade dos leitores e promovendo a empatia.

            Acreditamos que esses aspectos não só melhoram sua experiência de leitura, mas também contribuem para uma compreensão mais profunda e enriquecedora das obras literárias.
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.header("Monte seu perfil")
            nome = st.text_input("Nome", placeholder="Digite o seu nome aqui")
            idade = st.number_input("Idade", min_value=10, max_value=100, placeholder="Digite sua idade em anos")
            cidade = st.text_input("Cidade", placeholder="Digite cidade que você vive")
            gostos = st.text_area("Gostos & Hábitos", placeholder="Ex.: gosto de contos de terror")
            aceitar = st.checkbox("Aceito compartilhar meus dados")

            if st.button("Próximo"):
                if aceitar:
                    st.session_state["perfil"] = {
                        "nome": nome,
                        "idade": idade,
                        "cidade": cidade,
                        "gostos": gostos
                    }
                    try:
                        perfil_insert(nome, idade, cidade, gostos)
                        st.success("Perfil salvo com sucesso!")
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao tentar inserir um perfil: {e}")
                st.rerun()

def tela_obra():
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.image("imagens/obra.jpg")
        with col2:
            st.header("Escolha a Obra e Autor")
            obra = st.text_input("Obra")
            autor = st.text_input("Autor")

            if st.button("Próximo"):
                st.session_state["obra"] = {
                    "obra": obra,
                    "autor": autor
                }
                try:
                    obra_insert(obra, autor)
                    st.success("Obra e autor salvos com sucesso!")
                except Exception as e:
                    st.error(f"Ocorreu um erro ao tentar salvar a obra e o autor: {e}")
                st.rerun()

def tela_interesses():
    with st.container():
        #st.header("Obra e Autor")
        st.header(f"Obra {st.session_state['obra']['obra']} do autor {st.session_state['obra']['autor']}")
        prompt_resumo_obra = (f"Como um excelente professor em literatura, reflita bem e faça um resumo conciso da obra {st.session_state['obra']['obra']} "
                              f"e uma biografia mínima do autor {st.session_state['obra']['autor']}. Este resumo deve ter 300 tokens. Usar um texto adequado para um leitor "
                              f"com as seguintes características: Seu nome é {st.session_state['perfil']['nome']}, tem a idade de {st.session_state['perfil']['idade']} anos, "
                              f"vive na cidade de {st.session_state['perfil']['cidade']} e tem interesse em {st.session_state['perfil']['gostos']}. "
                              f"O resumo deve ser cativante e despertar a curiosidade do leitor. Utilize uma chamada para ação de escolher interesses sobre a obra dispostos no menu abaixo. "
                              f"Utilize formatação markdown no texto.")

        if "llm_response" not in st.session_state:
            response = get_anthropic_response(prompt_resumo_obra)
            if response:
                st.session_state["llm_response"] = response
            else:
                st.session_state["llm_response"] = "Erro ao gerar resposta do modelo."
    
        st.markdown(st.session_state["llm_response"])
        
       
        with st.container():
            st.write("Escolha um dos tópicos abaixo para explorar a obra:")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("Contexto Histórico", type="primary", help="Clique para saber mais sobre o contexto histórico da obra ", use_container_width=True):
                    prompt = (
                                f"Imagine que você é um excelente professor em literatura, especializado em estudos literários. "
                                f"Problema: A compreensão do contexto histórico e das influências do autor é muitas vezes subestimada, mas é crucial para entender profundamente a obra {st.session_state['obra']['obra']}. "
                                f"Importância: Conhecer o período histórico e as influências pode revelar motivações ocultas e temas centrais, enriquecendo a interpretação da obra. "
                                f"Complicação: O desafio está em conectar eventos históricos e influências de maneira relevante e interessante para o leitor. "
                                f"Ação: Forneça uma explicação detalhada sobre o contexto histórico da obra {st.session_state['obra']['obra']}, incluindo os eventos significativos que influenciaram a narrativa. "
                                f"Além disso, descreva brevemente as principais influências e temas nas obras do autor {st.session_state['obra']['autor']}. "
                                f"Adapte o texto para um leitor com as seguintes características: Seu nome é {st.session_state['perfil']['nome']}, tem a idade de {st.session_state['perfil']['idade']} anos, "
                                f"vive na cidade de {st.session_state['perfil']['cidade']} e tem interesse em {st.session_state['perfil']['gostos']}, (Completar...). "
                                f"Faça o contexto histórico e as influências do autor serem envolventes e educativos. E Utilize uma chamada para ação de escolher interesses sobre a obra dispostos no menu abaixo." 
                                f"Utilize formatação markdown no texto e limite-se a cerca de 300 TOKENS."
                            )
                    #lê com frequência {st.session_state['perfil']['leitura']}, com nível de educação {st.session_state['perfil']['nivel_educacao']}
                    handle_button_click(prompt)

            with col2:
                if st.button("Curiosidades", type="primary", use_container_width=True):
                    prompt = (f"Como um excelente professor em literatura, compartilhe algumas curiosidades fascinantes sobre a obra {st.session_state['obra']['obra']}. "
                            f"Inclua fatos interessantes sobre o processo de escrita, influências do autor, ou qualquer detalhe peculiar que possa atrair a atenção do leitor. "
                            f"Adapte o texto para um leitor com as seguintes características: Seu nome é {st.session_state['perfil']['nome']}, tem a idade de {st.session_state['perfil']['idade']} anos, "
                            f"vive na cidade de {st.session_state['perfil']['cidade']} e tem interesse em {st.session_state['perfil']['gostos']}. "
                            f"Faça as curiosidades serem cativantes e divertidas. Utilize formatação markdown no texto.")
                    handle_button_click(prompt)

                if st.button("Impacto Cultural", type="primary", use_container_width=True):
                    prompt = (f"Como um excelente professor em literatura, explique o impacto cultural da obra {st.session_state['obra']['obra']}. "
                            f"Discuta como a obra influenciou a sociedade, outras obras de literatura, e a cultura popular. "
                            f"Adapte o texto para um leitor com as seguintes características: Seu nome é {st.session_state['perfil']['nome']}, tem a idade de {st.session_state['perfil']['idade']} anos, "
                            f"vive na cidade de {st.session_state['perfil']['cidade']} e tem interesse em {st.session_state['perfil']['gostos']}. "
                            f"Faça o impacto cultural ser inspirador e informativo. Utilize formatação markdown no texto.")
                    handle_button_click(prompt)

            with col3:
                if st.button("Prêmios", type="primary", use_container_width=True):
                    prompt = (f"Como um excelente professor em literatura, descreva os prêmios que a obra {st.session_state['obra']['obra']} ganhou. "
                            f"Inclua informações sobre o significado desses prêmios e o reconhecimento crítico da obra. "
                            f"Adapte o texto para um leitor com as seguintes características: Seu nome é {st.session_state['perfil']['nome']}, tem a idade de {st.session_state['perfil']['idade']} anos, "
                            f"vive na cidade de {st.session_state['perfil']['cidade']} e tem interesse em {st.session_state['perfil']['gostos']}. "
                            f"Faça a descrição dos prêmios ser envolvente e educativa. Utilize formatação markdown no texto.")
                    handle_button_click(prompt)

                if st.button("Questões Intrigantes", type="primary", use_container_width=True):
                    prompt = (f"Como um excelente professor em literatura, levante algumas questões intrigantes sobre a obra {st.session_state['obra']['obra']}. "
                            f"Inclua perguntas que façam o leitor refletir sobre os temas e personagens da obra, promovendo uma análise mais profunda. "
                            f"Adapte o texto para um leitor com as seguintes características: Seu nome é {st.session_state['perfil']['nome']}, tem a idade de {st.session_state['perfil']['idade']} anos, "
                            f"vive na cidade de {st.session_state['perfil']['cidade']} e tem interesse em {st.session_state['perfil']['gostos']}. "
                            f"Faça as questões serem provocativas e reflexivas. Utilize formatação markdown no texto.")
                    handle_button_click(prompt)

            with col4:
                if st.button("Moral", type="primary", use_container_width=True):
                    prompt = (f"Como um excelente professor em literatura, explique qual é a moral da história da obra {st.session_state['obra']['obra']}. "
                            f"Inclua uma análise sobre as lições e mensagens que o autor pretende transmitir através da narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Seu nome é {st.session_state['perfil']['nome']}, tem a idade de {st.session_state['perfil']['idade']} anos, "
                            f"vive na cidade de {st.session_state['perfil']['cidade']} e tem interesse em {st.session_state['perfil']['gostos']}. "
                            f"Faça a moral da história ser clara e inspiradora. Utilize formatação markdown no texto.")
                    handle_button_click(prompt)

                if st.button("Personagens", type="primary", use_container_width=True):
                    prompt = (f"Como um excelente professor em literatura, forneça uma descrição detalhada dos personagens principais e secundários da obra {st.session_state['obra']['obra']}. "
                            f"Inclua informações sobre suas características, motivações e evolução ao longo da narrativa. "
                            f"Adapte o texto para um leitor com as seguintes características: Seu nome é {st.session_state['perfil']['nome']}, tem a idade de {st.session_state['perfil']['idade']} anos, "
                            f"vive na cidade de {st.session_state['perfil']['cidade']} e tem interesse em {st.session_state['perfil']['gostos']}. "
                            f"Faça a descrição dos personagens ser envolvente e informativa. Utilize formatação markdown no texto.")
                    handle_button_click(prompt)

    tela_chat()

# Função para lidar com cliques de botões e enviar prompts para a API
def handle_button_click(prompt):
    response = get_anthropic_response(prompt)
    response_text = response if response else "Erro ao gerar resposta do modelo."
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()

def tela_chat():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Faça alguma pergunta sobre a obra ou clique nos botões de interesses"):
        st.chat_message("user").markdown(prompt)        
        st.session_state.messages.append({"role": "user", "content": prompt})

        prompt_full = (f"Considere que a pergunta abaixo se refere a obra {st.session_state['obra']['obra']} e autor {st.session_state['obra']['autor']}. "
                       f"Considere que quem está questionando é um leitor com as seguintes características: Seu nome é {st.session_state['perfil']['nome']}, "
                       f"tem a idade de {st.session_state['perfil']['idade']} anos, vive na cidade de {st.session_state['perfil']['cidade']} e tem interesse em {st.session_state['perfil']['gostos']}. "
                       f"Considere o que já foi conversado. E a pergunta é essa: {prompt}")

        response = get_anthropic_response(prompt_full)
        response_text = response if response else "Erro ao gerar resposta do modelo."
        with st.chat_message("assistant"):
            st.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})

    col1, col2 = st.columns((4,1))
    with col2:
        st.button("✅ Checkpoint", help="Clique aqui para avaliar os seus conhecimentos sobre a obra")

# Função principal

def main():
    if "perfil" not in st.session_state:
        tela_perfil()
    elif "obra" not in st.session_state:
        tela_obra()
    elif "interesses" not in st.session_state:
        tela_interesses()   

# Inicia banco de dados
setup() 

# Inicia Barra Lateral
tela_sidebar() 

# Tela com informações iniciais
tela_principal()

# Executa o RELIA
main()
