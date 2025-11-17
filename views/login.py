import streamlit as st
from database import inserir_perfil_login, obter_perfil, check_password, atualizar_usuario_Perfil, perfil_completo
import re
import sqlitecloud  #type: ignore 


# Funções auxiliares
def validar_email(email):
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email)

def campo_obrigatorio(label):
    """Retorna o rótulo com um asterisco vermelho indicando que é obrigatório."""
    return f"{label} <span style='color:red;'>*</span>"

# Função para exibir a tela de login
def tela_login():
    """Exibe a tela de login com indicação de campos obrigatórios e feedback visual."""
    with st.container():
        
        # Cria tres colunas para centralizar o texto 
        col1, col2, col3, col4 = st.columns([1,1,2,1])
        
        with col2:
            with st.container(border=False):
                # Logo e Cabeçalho
                st.image('imagens/logo_relia-removebg.png', width=200)
        with col3:
            with st.container(border=False):        
                st.markdown(
                """
                <h1 style='text-align: center;'>Bem-vindo ao RELIA</h1>
                """, 
                unsafe_allow_html=True,
                help="""O RELIA é uma plataforma educacional que utiliza Inteligência Artificial para criar 
                roteiros de estudos literários personalizados. Aqui você encontrará análises, 
                interpretações e guias de leitura adaptados ao seu perfil."""
                )
                st.markdown(
                """
                <h3 style='text-align: center;'>Faça login ou crie seu Perfil:</h3>
                """, 
                unsafe_allow_html=True,
            help="""    - Login: Acesse sua conta existente para continuar seus estudos
            - Criar Perfil: Crie uma Perfil para começar sua jornada literária
                """
                    )

        # Cria duas colunas para exibir o texto e o vídeo lado a lado
        col1, col2 = st.columns([1, 1])

        # Coluna 1: Conteúdo Explicativo
        with col1:
            with st.expander("Saiba mais sobre o RELIA", expanded=True):
                st.container(border=True)
                st.markdown("""
            <iframe width="100%" height="480"  src="https://www.youtube.com/embed/7BogkB2UEPc?rel=0&controls=1&showinfo=0&autoplay=0" 
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen></iframe>
            """, unsafe_allow_html=True)
                
                st.markdown("""
                <div class="expander-content">
                Ao utilizar técnicas avançadas de processamento de linguagem natural, o RELIA auxilia leitores de todas as idades e níveis de conhecimento a explorar obras literárias com profundidade e clareza.
                
                Com o RELIA, você pode:

                - **Analisar Textos Complexos**: A IA identifica conceitos-chave, relações entre ideias e diferentes níveis de significado, facilitando a interpretação de textos complexos.
                - **Participar de Diálogos Interativos**: O sistema promove a interação entre o leitor e a IA, respondendo a perguntas, oferecendo diferentes perspectivas de análise e incentivando a reflexão crítica.
               
                Nosso objetivo não é apenas facilitar a leitura e interpretação de textos, mas também promover a empatia, a responsabilidade individual e a construção de um futuro mais ético e interseccional. Junte-se a nós nesta jornada de leitura assistida por IA e descubra novas maneiras de se conectar com a literatura e com outros leitores ao redor do mundo.
                </div>
                """, unsafe_allow_html=True)

        # Coluna 2: Vídeo Explicativo
        with col2:
             # Define as abas de Login e Cadastro
            tab_login, tab_cadastro = st.tabs(["Login", "Criar Perfil"])

            # Aba de Login
            with tab_login:
                with st.container():
                    # Centraliza o formulário de login
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col2:
                        # Título da seção de login
                        st.markdown("<h3 style='text-align: center;'>Faça Login</h3>", unsafe_allow_html=True , help="Insira seu email cadastrado e senha, para entrar no RELIA"  )
                        
                        # Campo de Email com indicação de obrigatoriedade
                        st.markdown(f"<h6>{'Email'}</h6>", unsafe_allow_html=True)
                        email = st.text_input("Email", placeholder="Digite seu email aqui", key="Email",label_visibility="collapsed")
                       
                        # Campo de Senha com indicação de obrigatoriedade
                        st.markdown(f"<h6>{'Senha'}</h6>", unsafe_allow_html=True)
                        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha aqui", key="Senha",label_visibility="collapsed")
                       
                        # Botão de Login com chave única para evitar conflitos
                        if st.button("Entrar", disabled=not (email and senha), key="login_button"):
                            perfil = obter_perfil(email)
                            if perfil and check_password(perfil["senha"], senha):
                                # Define as variáveis de sessão para o usuário logado
                                st.session_state["usuario_id"] = perfil["id"]
                                st.session_state["usuario"] = {
                                    'id': perfil["id"],
                                    'nome': perfil["nome"],
                                    'email': perfil["email"], 
                                    'idade': perfil["idade"],
                                    'cidade': perfil["cidade"],
                                    'interesses': perfil["interesses"],
                                    'nivel_educacional': perfil["nivel_educacional"],
                                    'habito_leitura': perfil["habito_leitura"],
                                    'opcao_compartilhar': perfil["opcao_compartilhar"]
                                }
                                st.session_state["tela"] = "pesquisa_obra"
                                
                                # Verifica se o perfil está completo
                                if not perfil_completo(st.session_state["usuario"]):
                                    st.session_state["perfil_completo"] = False
                                else:
                                    st.session_state["perfil_completo"] = True
                                
                                st.toast("Login realizado com sucesso! Redirecionando...")
                                st.rerun()
                            else:
                                st.error("Email ou senha incorretos.", icon="🚨")
                    

            # Aba de Cadastro
            with tab_cadastro:
                tela_cadastro()
            

       
# Função para exibir a tela de cadastro
def tela_cadastro():
    """Exibe a tela de cadastro com todos os campos do perfil, indicando obrigatoriedade e fornecendo feedback visual."""
    with st.container():
                # Agrupando campos em duas colunas para compactar
                col_a, col_b = st.columns(2)
                # Coluna A: Nome, Senha, Confirmar Senha
                with col_a:
                    with st.container(border=True):
                        # Campo de Nome com indicação de obrigatoriedade
                        st.markdown(f"<h6>{campo_obrigatorio('Nome')}</h6>", unsafe_allow_html=True)
                        nome = st.text_input("", placeholder="Digite o seu nome aqui", key="Nome")
                        
                        # Campo de Senha com indicação de obrigatoriedade
                        st.markdown(f"<h6>{campo_obrigatorio('Senha Inicial')}</h6>", unsafe_allow_html=True)
                        nova_senha = st.text_input("", type="password", placeholder="Digite sua senha aqui", key="Senha Inicial")
                        
                        # Campo de Confirmar Senha com indicação de obrigatoriedade
                        st.markdown(f"<h6>{campo_obrigatorio('Confirmar Senha')}</h6>", unsafe_allow_html=True)
                        confirmar_senha = st.text_input("", type="password", placeholder="Confirme sua senha aqui", key="Confirmar Senha")
                        if not confirmar_senha:
                            st.markdown("<span style='color:red; font-size: 12px;'>* Confirmação de senha é obrigatória.</span>", unsafe_allow_html=True)
                        elif nova_senha and (nova_senha != confirmar_senha):
                            st.markdown("<span style='color:red; font-size: 12px;'>* As senhas não coincidem.</span>", unsafe_allow_html=True)

                # Coluna B: Email, Nível Educacional, Hábito de Leitura
                with col_b:
                    with st.container(border=True):
                        # Campo de Email com indicação de obrigatoriedade
                        st.markdown(f"<h6>{campo_obrigatorio('Email')}</h6>", unsafe_allow_html=True)
                        novo_email = st.text_input("", placeholder="Digite seu email aqui", key="Email_2")
                        if not novo_email:
                            st.markdown("<span style='color:red; font-size: 12px;'>* Email é obrigatório.</span>", unsafe_allow_html=True)
                        elif not validar_email(novo_email):
                            st.markdown("<span style='color:red; font-size: 12px;'>* Formato de email inválido.</span>", unsafe_allow_html=True)

                        # Campo de Nível Educacional
                        st.markdown(f"<h6>{campo_obrigatorio('Nível Educacional')}</h6>", unsafe_allow_html=True)
                        opcoes_nivel_educacional = ["Nível Educacional", "Fundamental", "Secundário", "Superior"]
                        nivel_educacional = st.selectbox("", opcoes_nivel_educacional, index=0, key="Nível Educacional")
                        
                        # Campo de Hábito de Leitura
                        st.markdown(f"<h6>{campo_obrigatorio('Hábito de Leitura')}</h6>", unsafe_allow_html=True)
                        opcoes_habito_leitura = ["Hábito de Leitura", "Não gosto", "Casual", "Frequente"]
                        habito_leitura = st.selectbox("", opcoes_habito_leitura, index=0, key="Hábito de Leitura")
                
                if not nome or novo_email or nova_senha or nivel_educacional or habito_leitura:
                            st.markdown("<span style='color:red; font-size: 12px;'>* Dados obrigatórios.</span>", unsafe_allow_html=True)
                    
                # Campo de Idade e Cidade (em uma única linha para compactação)
                st.markdown("<h6>Idade e Cidade</h6>", unsafe_allow_html=True)
                col_c, col_d = st.columns([1, 2])
                with st.container(border=True):
                    with col_c:
                        idade = st.number_input("Idade", min_value=14, max_value=100, value=14, key="cadastro_idade", label_visibility="collapsed")
                    with col_d:
                        cidade = st.text_input("Cidade", placeholder="Digite sua cidade aqui", key="Cidade", label_visibility="collapsed")

                with st.container(border=True):
                    # Campo de Interesses
                    st.markdown("<h6>Interesses</h6>", unsafe_allow_html=True)
                    interesses = st.text_area("", placeholder="Descreva seus interesses aqui", key="Interesses", height=70)

                   
                # Disclaimer sobre os termos
                st.markdown("""
                <style>
                .disclaimer {
                    color: #555555;
                    font-size: 12px;
                    margin-top: 5px;
                    margin-bottom: 10px;
                }
                .disclaimer a {
                    color: #1E90FF;
                    text-decoration: none;
                }
                .disclaimer a:hover {
                    text-decoration: underline;
                }
                </style>
                <div class="disclaimer">
                    Ao atualizar seu perfil, você concorda com os <a href="https://www.notion.so/Termos-e-Condi-es-134eca455c7080a69d32df81b1c04438?pvs=4" target="blank">Termos e Condições</a> e a 
                    <a href="https://www.notion.so/Politica-de-Privacidade-131eca455c708051bb21c71e8af45219?pvs=4" target="blank">
                    Política de Privacidade</a>, de acordo com as legislações europeias mais recentes.
                </div>
                """, unsafe_allow_html=True)

                # Inicializando o valor do consentimento no session_state, se não existir
                if "compartilhar_perfil" not in st.session_state:
                    st.session_state["compartilhar_perfil"] = "Não compartilhar"

                # Campo de Seleção com `st.selectbox` para consentimento
                opcao_compartilhar = st.selectbox(
                    "Selecione sua opção de consentimento:",
                    options=["Compartilhar meu perfil", "Não compartilhar"],
                    index=1 if st.session_state["compartilhar_perfil"] == "Não compartilhar" else 0,
                    key="cadastro_opcao_compartilhar"
                )

                # Atualizando o valor no session_state
                st.session_state["compartilhar_perfil"] = opcao_compartilhar

                # Mensagens de feedback ao usuário
                if opcao_compartilhar == "Compartilhar meu perfil":
                    st.markdown(
                        "<div style='color: green; font-weight: bold;'>✔️ Você optou por compartilhar seus dados.</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<div style='color: red; font-weight: bold;'>❌ Você optou por NÃO compartilhar seus dados.</div>",
                        unsafe_allow_html=True
                    )
                
                # Botão de Cadastro com chave única
                if st.button("Registar", disabled=not (
                    nome and 
                    validar_email(novo_email) and 
                    nova_senha and 
                    confirmar_senha and 
                    nova_senha == confirmar_senha and
                    nivel_educacional and
                    habito_leitura
                ), key="cadastro_button"):
                    # Validações adicionais
                    erros = []
                    if not validar_email(novo_email):
                        erros.append("Por favor, insira um email válido.")
                    if not nome:
                        erros.append("Nome é obrigatório.")
                    if not nova_senha:
                        erros.append("Senha é obrigatória.")
                    if nova_senha != confirmar_senha:
                        erros.append("As senhas não coincidem.")
                    if not nivel_educacional:
                        erros.append("Nível Educacional é obrigatório.")
                    if not habito_leitura:
                        erros.append("Hábito de Leitura é obrigatório.")

                    if erros:
                        for erro in erros:
                            st.error(erro)
                    else:
                        # Cria um novo perfil no banco de dados
                        try:
                            inserir_perfil_login(
                                nome=nome,
                                email=novo_email,
                                senha=nova_senha,
                                idade=idade,
                                cidade=cidade,
                                interesses=interesses,
                                nivel_educacional=nivel_educacional,
                                habito_leitura=habito_leitura,
                                opcao_compartilhar=1 if opcao_compartilhar else 0 
                            )
                            st.toast("Perfil cadastrado com sucesso!")
                            st.info("Agora você pode fazer o login.")
                            #st.rerun()
                        except sqlitecloud.IntegrityError:
                            st.toast("O email fornecido já está em uso.")
                        except Exception as e:
                            st.toast(f"Ocorreu um erro ao registar usuário: {e}")
            
# Uma divisão na tela
    st.divider()  # Isso cria uma linha divisória

    st.subheader("Por que pedimos seu perfil?")
    st.markdown("""
        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
        Para oferecer uma experiência de leitura personalizada e relevante, o RELIA solicita algumas informações do seu perfil. Aqui estão os motivos:

        - **Personalização da Experiência de Leitura**: Adaptamos a análise e interpretação das obras de acordo com suas preferências e contexto individual, tornando a leitura mais envolvente e significativa.
        - **Relevância dos Conteúdos**: Selecionamos e destacamos informações que são mais significativas para você, aumentando sua satisfação com a leitura.
        - **Melhoria da Interação com a IA**: Ajustamos a complexidade das respostas e a forma de comunicação para melhor atender às suas necessidades individuais.
        - **Construção de um Futuro Mais Ético e Interseccional**: Promovemos um ambiente de leitura inclusivo e diversificado, refletindo a diversidade dos leitores e promovendo a empatia.

        Acreditamos que esses aspectos não só melhoram sua experiência de leitura, mas também contribuem para uma compreensão mais profunda e enriquecedora das obras literárias.
        </div>
        """, unsafe_allow_html=True)
    
def show_terms():
    st.title("Termos e Condições de Uso")
    # Carregar conteúdo do arquivo markdown
    with open("assets/termos.md", "r", encoding="utf-8") as file:
        terms_content = file.read()
    st.markdown(terms_content)

# pages/privacidade.py
def show_privacy():
    st.title("Política de Privacidade")
    with open("assets/privacidade.md", "r", encoding="utf-8") as file:
        privacy_content = file.read()
    st.markdown(privacy_content)

