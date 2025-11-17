import streamlit as st
st.set_page_config(
    page_title="RELIA - Roteiro de Leitura Empática",
    page_icon="📚",
    layout="wide",  # Deixa o layout mais espaçoso, ideal para visualizar o conteúdo
    initial_sidebar_state="expanded",  # A barra lateral estará expandida ao abrir
    menu_items={
        'Get Help': 'https://www.reliaapp.com/help',  # Link para ajuda
        'Report a bug': "https://www.reliaapp.com/bug",  # Link para reporte de bugs
        'About': "# RELIA\nBem-vindo ao app de Roteiro de Leitura Empática!\n**RELIA** é uma plataforma para ajudar na leitura e compreensão profunda de obras literárias.",  # Informações sobre o app
    }
)

from views.sidebar import tela_sidebar
from views.home import tela_principal
from views.login import tela_login # type: ignore
from views.profile import tela_perfil
from views.password_recovery import tela_recuperar_senha, tela_nova_senha # type: ignore
from views.obra_search import tela_selecionar_obra # type: ignore
from views.chat import tela_chat # type: ignore
from database import setup_database #inserir_obra, criar_roteiro, obter_obra_por_id
from views.admin import tela_admin  # Importa a nova tela de administração
from views.checkpoint import tela_checkpoint
from views.area_do_leitor import tela_area_leitor  # type: ignore Importa a tela da "Área do Leitor"
 

# Configuração da página - esta linha deve ser a primeira do seu script
#st.set_page_config(page_title="RELIA", page_icon="📚")


def local_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Carregar o CSS personalizado
local_css("style.css")


# Inicializa todas as chaves necessárias no início
def inicializar_session_state():
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
        "llm_response": None,
        "messages": [],
        "chat_iniciado": False,
        "obra_atual": None,
        "sugestoes":[],
        "resumo_exibido":[],
        "resumo":[],
        "botoes_pressionados":[] ,
        "pontuacao_total": 0 ,
        "language": [] ,
        "popup_shown": None
        
    }

    for chave, valor in chaves_necessarias.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor

# Inicializa todas as chaves necessárias
inicializar_session_state()

def main():
    #st.set_page_config(page_title="RELIA", page_icon="📚")

  # Configuração inicial do banco de dados
    #setup_database()
    
    if "database_setup" not in st.session_state:
        setup_database()
        st.session_state["database_setup"] = True

      # Verifica se o usuário está logado
    if st.session_state["usuario_id"] is None:
        st.session_state["tela"] = "login"
        tela_login()
        return

    # Inicializa o estado da tela
    if "tela" not in st.session_state:
        st.session_state["tela"] = "login"  # Começa na tela de login


    # Renderiza a barra lateral
    tela_sidebar()

    # Controle de navegação entre as telas
    if st.session_state["tela"] == "login":
        tela_login()
    elif st.session_state["tela"] == "inicial":
        tela_principal()
    elif st.session_state["tela"] == "perfil":
        tela_perfil()
    elif st.session_state["tela"] == "recuperar_senha":
        tela_recuperar_senha()
    elif st.session_state["tela"] == "nova_senha":
        tela_nova_senha()
    elif st.session_state["tela"] == "pesquisa_obra":
        tela_selecionar_obra()
    elif st.session_state["tela"] == "chat":
        if st.session_state.get("iniciar_roteiro", False) or (st.session_state.get("obra_id") and st.session_state.get("usuario_id")):
            st.session_state["iniciar_roteiro"] = False  # Reset para garantir que não seja usado incorretamente
            tela_chat()
        else:
            st.warning("Por favor, selecione uma obra primeiro.")
            st.session_state["tela"] = "pesquisa_obra"
            st.rerun()
    elif st.session_state["tela"] == "admin":  
        tela_admin()  # Chama a função que renderiza a tela de administração
    elif st.session_state["tela"] == "checkpoint":
        tela_checkpoint()
        #from views.checkpoint import exibir_checkpoint  # Importa a função
        #exibir_checkpoint(etapa=1, pergunta="Pergunta do Checkpoint")  # Substitua pela lógica de etapa e pergunta 
    elif st.session_state["tela"] == "area_leitor":  
        tela_area_leitor()
    else:
        st.error("Tela não encontrada!")
                

if __name__ == "__main__":
    main()
    