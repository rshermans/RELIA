import streamlit as st


def limpar_contexto_chat():
    """
    Limpa o contexto de chat para iniciar uma nova conversa com a obra selecionada.
    """
    chaves_necessarias = {
        "usuario_id": None,
        "usuario": {
            "id": None,
            "nome": "",
            "idade": 0,
            "cidade": "",
            "interesses": ""
        },
        "tela": "login",  # Começa na tela de login
        "titulo": "",
        "autor": "",
        "obra": {
            "titulo": "",
            "autor": ""
        },
        "obra_id": None,
        "roteiro_id": None,
        #"llm_response": None,
        #"messages": [],
        "chat_iniciado": False,
        "obra_atual": None,
        "resumo_exibido": False
        
    }

    for chave, valor in chaves_necessarias.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor
            
    st.session_state.messages = []
    st.session_state.llm_response = None  # Limpa a resposta da LLM se necessário
    

def tela_sidebar():
    with st.sidebar:
        #st.header("RELIA")
        st.image("assets/logo_relia.png", width=150) # , use_column_width="auto")
        
        
        
        # Cumprimento ao usuário logado
        if st.session_state.get("usuario"):
            usuario_nome = st.session_state["usuario"]["nome"]
            st.write(f"👋 Olá, {usuario_nome}!")
            #st.sidebar.write(f"Nível: {st.session_state.get('nivel_atual', 'Iniciante')}")
            #st.sidebar.progress(st.session_state.get('progresso', 0.0))
            if st.session_state.get("tela")in ["chat", "checkpoint"]:
                st.sidebar.write(f"Pontuação: {st.session_state.get('pontuacao_total', 0)} pts")
                 
        if st.button("🏠 Voltar ao Início", help="Retorna à página inicial"):
            st.session_state.clear()
            st.rerun()

        if st.button("📂 Atualizar Perfil", help="Atualize suas informações pessoais"):
            st.session_state["tela"] = "perfil"
            st.rerun()

        if st.session_state.get("botao_recuperar_senha", False):
                if st.button("🔑 Recuperar Senha", help="Redefina sua senha pela recuperação por email"):
                    st.session_state["tela"] = "recuperar_senha"
                    st.rerun()
            
         # Botão para área do leitor, visível apenas se o usuário estiver logado
        if st.session_state.get("usuario"):
            if st.session_state.get("botao_ativo", True):
                if st.session_state.get("tela") in ["pesquisa_obra","chat", "area_leitor","checkpoint"]:
                    if st.button("📚 Área do Leitor",help= "Acesse seus roteiros de leitura e relatórios."):
                        st.session_state["tela"] = "area_leitor"
                        st.rerun()
                
        # Verifica se a tela atual é "chat" ou "area_leitor"
        if st.session_state.get("tela") in ["chat","checkpoint","perfil","admin", "area_leitor"]:
            # Botão para voltar e escolher outra obra
            if st.button("🔙 Escolher Outra Obra", help="Retorne à seleção de obras para um novo roteiro"):
                limpar_contexto_chat()  # Limpa o contexto de mensagens do chat
                st.session_state["tela"] = "pesquisa_obra"
                st.rerun()
                
        
        # Verifica se o usuário é administrador para exibir o botão de administração
        if st.session_state.get("usuario") and st.session_state["usuario"]["email"] == "rshermans@sapo.pt":
            if st.button("⚙️ Administração", help="Acesse as ferramentas de administração do sistema RELIA"):
                st.session_state["tela"] = "admin"
                st.rerun()
                
    #Implementação de botão e estilos do botão para o inquerito:
    # Adiciona os estilos CSS personalizados
        st.markdown("""
            <style>
            /* Container para o botão */
            .relia-button-container {
                text-align: left;
                margin: 2rem 0;
                
            }
            
            /* Estilo base do botão */
            .relia-button {
               
                background: linear-gradient(45deg, #acc9e2, #64B5F6);  /* Tons de azul do RELIA */
                border: none;
                border-radius: 10px;
                color: white;
                padding: 15px 20px;
                font-size: 0.8rem;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                box-shadow: 0 5px 15px rgba(255, 75, 43, 0.4);
                
            }
            
            /* Efeito de hover */
            .relia-button:hover {
                transform: translateY(-3px);
                background: linear-gradient(45deg, #FF9800, #FFB74D);  /* Tons de laranja */
                box-shadow: 0 8px 20px rgba(255, 75, 43, 0.6);
            }
            
            /* Animação de brilho cintilante */
            .relia-button::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: rgba(255, 255, 255, 0.3);
                transform: rotate(45deg);
                animation: shine 3s infinite;
            }
            
            /* Animação de pulso com verde */
            .relia-button::after {
                content: '';
                position: absolute;
                width: 100%;
                height: 100%;
                top: 0;
                left: 0;
                background: rgba(76, 175, 80, 0.1);  /* Tom de verde */
                border-radius: 15px;
                animation: pulse 2s infinite;
            }
            
            /* Ícone de estrela */
            .star-icon {
                display: inline-block;
                margin-right: 8px;
                animation: rotate 4s linear infinite;
                color: #FFD700;  /* Dourado para estrela */
            }
            
            /* Notificação de agradecimento */
            .thank-you-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(45deg, #4CAF50, #81C784);  /* Tons de verde */
                color: white;
                padding: 15px 25px;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
                animation: slideIn 0.5s ease-out;
                z-index: 1000;
                display: none;
            }
            
            /* Keyframes para as animações */
            @keyframes shine {
                0% {
                    transform: rotate(45deg) translateY(-100%);
                }
                100% {
                    transform: rotate(45deg) translateY(100%);
                }
            }
            
            @keyframes pulse {
                0% {
                    transform: scale(1);
                    opacity: 0.7;
                }
                50% {
                    transform: scale(1.05);
                    opacity: 0.3;
                }
                100% {
                    transform: scale(1);
                    opacity: 0.7;
                }
            }
            
            @keyframes rotate {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(360deg);
                }
            }
            
            /* Notificação flutuante */
            .floating-notification {
                position: fixed;
                top: 10px;
                left: 10px;
                background: #4CAF50;
                color: white;
                padding: 15px;
                border-radius: 10px;
                animation: slideIn 0.5s ease-out;
                z-index: 1000;
            }
            
            @keyframes slideIn {
                0% {
                    transform: translateX(100%);
                }
                100% {
                    transform: translateX(0);
                }
            }
            </style>
        """, unsafe_allow_html=True)

        # Verifica se a tela atual é uma das telas permitidas
        if st.session_state.get("tela") in ["chat", "checkpoint", "perfil", "area_leitor"]:
            
            # Container para centralizar o botão
            st.markdown('<div class="relia-button-container">', unsafe_allow_html=True)
            
            # Container para centralizar o botão com link direto
            st.markdown("""
                <div class="relia-button-container">
                    <a href="https://bit.ly/Zoho-RELIA" color= white class="relia-button" target="_blank">
                        <span class="star-icon">⭐</span>
                        Inquérito  sobre o RELIA
                    </a>
                </div>
            """, unsafe_allow_html=True)