import streamlit as st
from database import inserir_perfil,obter_perfil,check_password, atualizar_usuario_Perfil,perfil_completo
import re
import time
#from streamlit import tooltip
import sqlitecloud #type: ignore


def validar_email(email):
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email)


def campo_obrigatorio(label):
    """Retorna o rótulo com um asterisco vermelho indicando que é obrigatório."""
    return f"{label} <span style='color:red;'>*</span>"


def tela_perfil():
    
    # Inicializa o estado dos campos
    if "usuario" not in st.session_state:
        st.error("Usuário não está logado. Redirecionando para o login...")
        st.session_state["tela"] = "login"
        st.rerun()
    
    # Carrega o perfil do usuário logado
    usuario = st.session_state["usuario"]
    perfil = obter_perfil(usuario["email"])
    
    with st.container():
        col1, col2 = st.columns([1,2])
        with col1:
                st.image("imagens/RELIA_index_perfil.jpg", width=150)
                 
        with col2:
                st.header("Atualiza seu Perfil") 
    with st.container():
        col1, col2 = st.columns([1,2])
        with col1:
            with st.container():
                #st.image("imagens/RELIA_index_perfil.jpg", width=200)
                with st.expander("Por que pedimos seu perfil?" ,True):
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
            with st.container(border=True):
                 # Campos de Atualização de Perfil com Asteriscos Vermelhos e Feedback
                st.markdown(f"<h5>{campo_obrigatorio('Nome')}</h5>", unsafe_allow_html=True)
                nome = st.text_input("nome", value=perfil["nome"], label_visibility="collapsed")
                if not nome:
                    st.markdown("<span style='color:red;'>* Nome é obrigatório.</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:green;'>✔️</span>", unsafe_allow_html=True)
                
                st.markdown(f"<h5>{campo_obrigatorio('Email')}</h5>", unsafe_allow_html=True)
                email = perfil["email"]  # Email não pode ser alterado
                st.text_input("email", value=email, disabled=True,label_visibility="collapsed")
                
                st.markdown(f"<h5>{campo_obrigatorio('Senha')}</h5>", unsafe_allow_html=True)
                senha = st.text_input("senha", type="password", placeholder="Digite sua senha aqui",label_visibility="collapsed")
                if not senha:
                    st.markdown("<span style='color:red;'>* Senha é obrigatória.</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:green;'>✔️</span>", unsafe_allow_html=True)
                
                st.markdown("<h5>Idade</h5>", unsafe_allow_html=True)
                idade = st.number_input("Idade", min_value=14, max_value=100, value=perfil["idade"] if perfil["idade"] else 14)
                
                st.markdown("<h5>Cidade</h5>", unsafe_allow_html=True)
                cidade = st.text_input("cidade", value=perfil["cidade"] if perfil["cidade"] else "",label_visibility="collapsed")
                
                st.markdown("<h5>Interesses</h5>", unsafe_allow_html=True)
                interesses = st.text_area("area", value=perfil["interesses"] if perfil["interesses"] else "",label_visibility="collapsed")
                
                # Nível Educacional
                st.markdown("<h5>Nível Educacional</h5>", unsafe_allow_html=True)
                opcoes_nivel_educacional = ["Nível Educacional", "Fundamental", "Secundário", "Superior"]
                nivel_educacional_index = opcoes_nivel_educacional.index(perfil["nivel_educacional"]) if perfil["nivel_educacional"] in opcoes_nivel_educacional else 0
                nivel_educacional = st.selectbox("Nível Educacional", opcoes_nivel_educacional, index=nivel_educacional_index)
                
                # Hábito de Leitura
                st.markdown("<h5>Hábito de Leitura</h5>", unsafe_allow_html=True)
                opcoes_habito_leitura = ["Hábito de Leitura", "Não gosto", "Casual", "Frequente"]
                habito_leitura_index = opcoes_habito_leitura.index(perfil["habito_leitura"]) if perfil["habito_leitura"] in opcoes_habito_leitura else 0
                habito_leitura = st.selectbox("Hábito de Leitura", opcoes_habito_leitura, index=habito_leitura_index)
                
                # Opção de Compartilhamento
                opcao_compartilhar = st.checkbox("Aceito compartilhar meus dados", value=bool(perfil["opcao_compartilhar"]))
                
                if opcao_compartilhar:
                    st.info("Você aceitou compartilhar seus dados.")
                else:
                    st.warning("Você não aceitou compartilhar seus dados. Recomendamos que o faça para uma melhor experiência.")
                
                # Disclaimer sobre os termos
                st.markdown("""
                <style>
                .disclaimer {
                    color: #555555;
                    font-size: 12px;
                    margin-top: 10px;
                    margin-bottom: 15px;
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
                
                # Botão de Atualização
                if st.button("Atualizar Perfil"):
                    # Validações
                    errors = []
                    if not validar_email(email):
                        errors.append("Por favor, insira um email válido.")
                    if not nome:
                        errors.append("Nome é obrigatório.")
                    if not senha:
                        errors.append("Senha é obrigatória.")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        # Atualiza o perfil no banco de dados
                        try:
                            atualizar_usuario_Perfil(
                                usuario_id=perfil['id'],
                                nome=nome,
                                email=email,
                                idade=idade,
                                cidade=cidade,
                                interesses=interesses,
                                nivel_educacional=nivel_educacional,
                                habito_leitura=habito_leitura,
                                opcao_compartilhar=1 if opcao_compartilhar else 0
                            )
                            
                            # Atualiza o perfil na sessão
                            usuario_atualizado = obter_perfil(email)
                            st.session_state["usuario"] = {
                                'id': usuario_atualizado["id"],
                                'nome': usuario_atualizado["nome"],
                                'email': usuario_atualizado["email"], 
                                'idade': usuario_atualizado["idade"],
                                'cidade': usuario_atualizado["cidade"],
                                'interesses': usuario_atualizado["interesses"]
                            }
                            
                            # Atualiza o estado de perfil completo
                            if perfil_completo(st.session_state["usuario"]):
                                st.session_state["perfil_completo"] = True
                            else:
                                st.session_state["perfil_completo"] = False
                            
                            # Mensagem de sucesso
                            st.success("Perfil atualizado com sucesso! Redirecionando para a escolha da obra...")
                            
                            # Define a próxima tela
                            st.session_state["tela"] = "pesquisa_obra"
                            
                            # Redireciona para a próxima tela sem usar time.sleep()
                            st.rerun()
                        
                        except sqlitecloud.IntegrityError:
                            st.error("O email fornecido já está em uso.")
                        except Exception as e:
                            st.toast(f"Ocorreu um erro ao tentar atualizar o perfil: {e}")
                                
                        st.rerun()  # Utilizar mudar pagina
                
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

# No seu código principal, atualizar os links:
        st.markdown("""
            <div class="disclaimer">
                Ao atualizar seu perfil, você concorda com os 
                <a href="/termos" target="_self">Termos e Condições</a> e a 
                <a href="/privacidade" target="_self">Política de Privacidade</a>, 
                de acordo com as legislações européias mais recentes.
            </div>
        """, unsafe_allow_html=True)
                            
                    