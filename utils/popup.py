import streamlit as st

# Inicializar o estado de sessão para verificar se o popup já foi mostrado
if "popup_shown" not in st.session_state:
    st.session_state["popup_shown"] = False

def show_welcome_popup():
    # Criar duas colunas
    col1, col2 = st.columns([1, 1])  # O argumento [1, 1] define que ambas as colunas terão o mesmo tamanho
    
    # Colocar o conteúdo na primeira coluna
    with col1:
        with st.container(border=False):
            st.markdown(
                """
                <div style='background-color:#f0f0f0; padding:20px; border-radius:10px;'>
                    <h2>Guia de boas-vindas para o RELIA!</h2>
                    <p>RELIA é uma plataforma que vai transformar sua experiência de leitura com roteiros empáticos e análise detalhada de obras literárias.</p>
                    <p>Aqui está como você pode começar:</p>
                    <ul>
                        <li><strong>Selecione uma obra literária</strong> e explore nossos roteiros.</li>
                        <li>Responda a perguntas interativas para aprofundar sua compreensão.</li>
                        <li>Receba feedback personalizado com base nas suas respostas.</li>
                    </ul>
                    <p>Estamos aqui para ajudar a enriquecer sua jornada de leitura. Aproveite!</p>
                </div>
                """, unsafe_allow_html=True
            )
    
    # Colocar o vídeo na segunda coluna
    with col2:
        with st.container(border=True):
            st.video("https://www.youtube.com/embed/7BogkB2UEPc?rel=0&controls=0&showinfo=0", start_time=0,autoplay=True,loop=True)
        

# Mostrar o popup de boas-vindas apenas na primeira vez
if not st.session_state["popup_shown"]:
    show_welcome_popup()
    # Botão para fechar o popup e registrar que ele foi mostrado
    if st.button("Fechar"):
        st.session_state["popup_shown"] = True

# Seu código da aplicação RELIA pode seguir abaixo
#st.write("Aqui está o restante da aplicação RELIA...")
