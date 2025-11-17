import streamlit as st
import sqlitecloud #type: ignore
from database import (
    inserir_checkpoint,   
    obter_roteiro_id_inicial, 
    carregar_dados_banco, 
    get_db_connection,  criar_ou_obter_roteiro, obter_roteiro
)
import json
from utils.estruturas_de_dados import (
    obter_nivel_atual_usuario, 
    encontrar_acao_checkpoint, 
    exibir_campo_resposta, 
    gerar_pergunta_com_llm, 
    avaliar_resposta_com_llm, 
    validar_pontuacao
)
import openai
from functools import lru_cache
from threading import Lock
from streamlit_extras.colored_header import colored_header # type: ignore
from views.area_do_leitor import determinar_nivel_e_progresso
from utils.bloom_level_info import show_level_header, show_feedback_reflection, show_progress_bar

# Configuração da API do ChatGPT
openai.api_key = st.secrets["OPENAI"]["OPENAI_API_KEY"]

# Estabelecer a conexão com o banco de dados
conn = get_db_connection 


# Lock para evitar condições de corrida
pontuacao_lock = Lock()
session_state_lock = Lock()

# Inicialização das variáveis de estado
def inicializar_estado_session():
    if 'etapas_completas' not in st.session_state:
        st.session_state['etapas_completas'] = [False] * 6  # Para os 6 níveis de Bloom
    if 'nivel_atual' not in st.session_state:
        st.session_state['nivel_atual'] = 0  # Começa no nível 0 (Lembrar)
    if 'pontuacao_total' not in st.session_state:
        st.session_state['pontuacao_total'] = 0
    if 'respostas_usuario' not in st.session_state:
        st.session_state['respostas_usuario'] = {}
    if 'etapa_atual' not in st.session_state:
        st.session_state['etapa_atual'] = 0
    if 'tela' not in st.session_state:
        st.session_state['tela'] = 'checkpoint'  # Tela inicial
    if 'roteiro_id' not in st.session_state:
        if 'usuario' in st.session_state and 'id' in st.session_state['usuario']:
            usuario_id = st.session_state['usuario']['id']
            #st.session_state['roteiro_id'] = obter_roteiro_id_inicial(usuario_id)
            st.session_state['roteiro_id'] = criar_ou_obter_roteiro(st.session_state['obra_id'], usuario_id)
            print("Na inicializacao: ",  st.session_state['roteiro_id'])
            st.stop()
    if 'pergunta_atual' not in st.session_state:
        st.session_state['pergunta_atual'] = None
    if 'acao_id_atual' not in st.session_state:
        st.session_state['acao_id_atual'] = None    
  

#------------------ Revisão de incosistencias e adaptação para tabela acoes-----------------------------

# Função para preparar o contexto para o checkpoint
def preparar_contexto(nivel_bloom, pontos_acao):
    contexto = {
        'obra': st.session_state.get('obra', 'Título Não Disponível'),
        'autor': st.session_state.get('autor', 'Autor Não Disponível'),
        'nivel_bloom': nivel_bloom,
        'perfil_usuario': (
            f"Nome: {st.session_state['usuario'].get('nome', 'Nome Não Disponível')}, "
            f"Idade: {st.session_state['usuario'].get('idade', 'Idade Não Disponível')}, "
            f"Interesses: {st.session_state['usuario'].get('interesses', 'Interesses Não Disponíveis')}"
        ),
        'pontos_maximos': pontos_acao,
    }
    return contexto


# Função para verificar se todas as chaves necessárias estão presentes em acao_data
def verificar_chaves_acao(acao_data):
    required_keys = ['template_pergunta', 'nomes_acao']
    missing_keys = [key for key in required_keys if key not in acao_data]
    if missing_keys:
        st.error(f"As chaves {missing_keys} estão faltando em 'acao_data'.")
        return False
    return True


# Função para criar um checkpoint no banco de dados
def criar_checkpoint(roteiro, acao_id, nivel_bloom, pergunta, resposta, pontuacao, feedback):
    try:
        inserir_checkpoint(
            roteiro_id=roteiro,
            acao_id=acao_id,
            nivel_taxonomia=nivel_bloom,
            pergunta=pergunta,
            resposta=resposta,
            nota_llm=pontuacao,
            feedback_llm=feedback
        )
        st.toast("Ponto de Reflexão registrado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao criar checkpoint: {e}")
        

# Função para processar a resposta do usuário
def processar_resposta(acao_id, pergunta, resposta_usuario, contexto, pontos_acao):
    """
    Processa a resposta do usuário, gera feedback e valida a pontuação.
    
    Args:
        acao_id (int): Identificador da ação.
        pergunta (str): Pergunta apresentada ao usuário.
        resposta_usuario (str): Resposta fornecida pelo usuário.
        contexto (dict): Contexto para a avaliação.
        pontos_acao (int): Pontuação atribuída à ação.
    
    Returns:
        Tuple[str, int, int]: Feedback, pontuação validada, pontuação da LLM.
    """
    feedback, pontuacao_llm = avaliar_resposta_com_llm(pergunta, resposta_usuario, contexto)
    pontuacao_validada = validar_pontuacao(pontuacao_llm, pontos_acao)
    roteiro = st.session_state['roteiro_id']
    #criar_checkpoint(roteiro, acao_id, contexto['nivel_bloom'], pergunta, resposta_usuario, pontuacao_validada, feedback)
    # Atualizar progresso do usuário
    atualizar_progresso_usuario(contexto['nivel_bloom'], pontuacao_validada)
    #mostrar_feedback(pontuacao_validada, feedback)
    return feedback, pontuacao_validada,pontuacao_llm
            

# Função para atualizar o progresso do usuário após a submissão da resposta
def atualizar_progresso_usuario(nivel_bloom, pontuacao_validada):
    if pontuacao_validada > 0:
        with pontuacao_lock:
            st.session_state['pontuacao_total'] += pontuacao_validada
    novo_nivel_bloom, _ = obter_nivel_atual_usuario()
    if novo_nivel_bloom != nivel_bloom:
        st.toast("Você avançou para o próximo nível!")
        st.session_state['nivel_atual'] = novo_nivel_bloom
        st.session_state['tela'] = "checkpoint"
    
    else:
        st.toast("Resposta registrada! Continue para a próxima pergunta.")
        st.session_state['pergunta_atual'] = None
        st.session_state['acao_id_atual'] = None
        
        
        
# Função para exibir o feedback
def mostrar_feedback(pontuacao, feedback_final):
    if pontuacao >= 8:
        tipo_alerta = "success"
    elif pontuacao >= 5:
        tipo_alerta = "info"
    else:
        tipo_alerta = "warning"

    if tipo_alerta == "success":
        st.success(f"**Pontuação:** {pontuacao}\n\n**Feedback:** {feedback_final}")
    elif tipo_alerta == "info":
        st.info(f"**Pontuação:** {pontuacao}\n\n**Feedback:** {feedback_final}")
    else:
        st.warning(f"**Pontuação:** {pontuacao}\n\n**Feedback:** {feedback_final}")
        
        
# Função para gerar pergunta com cache
@lru_cache(maxsize=32)
def gerar_pergunta_com_llm_cached(acao_data_tuple, contexto_tuple):
    acao_data = dict(acao_data_tuple)  # Converter de volta para dicionário
    contexto = dict(contexto_tuple)    # Converter de volta para dicionário
    return gerar_pergunta_com_llm(acao_data, contexto)


def tela_checkpoint():
    
    # Inicialização do estado da sessão
    inicializar_estado_session()
    
    # Estilo CSS personalizado
    st.markdown("""
        <style>
            [data-testid="stVerticalBlock"] {
                background-color: #fafafa;
                padding: 0.2rem;
                border-radius: 5px;
                
                margin: 0.2rem 0;
               
            }
            
            </style>
        """, unsafe_allow_html=True)
    
    
    if 'checkpoint_state' not in st.session_state:
        st.session_state.checkpoint_state = {
            'etapa': 'iniciar',
            'roteiro_id': None,
            'acao_id': None,
            'nivel_bloom': None,
            'pergunta': None,
            'pontuacao_llm': None,
            'porcentagem_acerto': None,
            'resposta': None,
            'feedback': None,
            'pontuacao': 0,
            'obra_id': st.session_state.get('obra_id'),
            'checkpoint_criado': False
        }
    
    state = st.session_state.checkpoint_state

    # Conectar ao banco de dados
    conn = get_db_connection()
    if not conn:
        st.error("Falha na conexão com o banco de dados.")
        return
    
      # Carregar ações e determinar nível do usuário
    acoes_niveis = carregar_dados_banco(conn)
    nivel_bloom, pontuacao_total = obter_nivel_atual_usuario()
    nivel_bloom = nivel_bloom.strip().capitalize()
    
    
    col1,col2, col3 = st.columns([3,1,3])
    
    with col1:    
        # Header animado
        colored_header(
            label=f"Ponto de Reflexão RELIA - Obra: {st.session_state.get('obra', 'Título Não Disponível')} ",
            description="Avalie seu conhecimento e compreensão",
            color_name="blue-100"
        )
    
    with col3:
        # ou qualquer outro nível
        show_level_header(nivel_bloom)
    
    
      # Container principal com fundo branco
    with st.container(border=False):
    # Barra de progresso estilizada
        show_progress_bar(pontuacao_total)
    
    
    # Obter ou criar o roteiro correto
    if not state['roteiro_id']:
        usuario_id = st.session_state['usuario']['id']
        obra_id = st.session_state['obra_id']
        state['roteiro_id'] = criar_ou_obter_roteiro(obra_id, usuario_id)
        if not state['roteiro_id']:
            st.error("Não foi possível criar ou obter o roteiro.")
            return
    
        
    # Container principal
    with st.container(border=False):
        if state['etapa'] == 'iniciar':
            st.markdown("## Bem-vindo ao Ponto de Reflexão RELIA!")
            st.write("Prepare-se para testar seu conhecimento e avançar na sua jornada de aprendizado.")
            if st.button("Começar", key="start_button"):
                state['etapa'] = 'gerar_pergunta'
                st.rerun()

        elif state['etapa'] == 'gerar_pergunta':
            acao_info = encontrar_acao_checkpoint(nivel_bloom, pontuacao_total, acoes_niveis)
            if not acao_info:
                st.error(f"Não foi possível encontrar a ação para o nível de Bloom {nivel_bloom}")
                return

            acao_id, pontos_acao, tipo_resposta, nomes_acao = acao_info
            acao_data = acoes_niveis.get(acao_id)
            
            if not acao_data:
                st.error(f"Dados da ação inválidos para o ID {acao_id}")
                return

            contexto = preparar_contexto(nivel_bloom, pontos_acao)
            
            with st.spinner("Gerando pergunta..."):
                pergunta = gerar_pergunta_com_llm_cached(tuple(sorted(acao_data.items())),  tuple(sorted(contexto.items())))
                if pergunta:
                    state.update({
                        'pergunta': pergunta,
                        'acao_id': acao_id,
                        'tipo_resposta': tipo_resposta,
                        'nivel_bloom': nivel_bloom,
                        'etapa': 'responder',
                        'checkpoint_criado': False  # Resetar a flag
                    })
                    st.rerun()
                else:
                    st.error("Erro ao gerar pergunta. Tente novamente.")

        elif state['etapa'] == 'responder':
            st.markdown(f"## Pergunta:\n\n{state['pergunta']}  | ( **Vale: {acoes_niveis[state['acao_id']]['pontos']} pontos** )  ")
            
            resposta_usuario = exibir_campo_resposta(state['tipo_resposta'], state['acao_id'])
            
            Enviar_resposta, Concluir_Checkpoint = st.columns(2)

            with Enviar_resposta:
                if st.button("Enviar Resposta", key="enviar_resposta", type='primary'):
                    if resposta_usuario:
                        state['resposta'] = resposta_usuario
                        state['etapa'] = 'avaliar'
                        st.rerun()
                    else:
                        st.warning("Por favor, insira uma resposta antes de enviar.")

            with Concluir_Checkpoint:
                if st.button("Concluir Ponto de Reflexão", key="finish_checkpoint"):
                    state['etapa'] = 'conclusao'
                    st.rerun()
            
            
        elif state['etapa'] == 'avaliar':
            if not state['checkpoint_criado']:
                with st.spinner("Avaliando resposta..."):
                    contexto = preparar_contexto(state['nivel_bloom'], acoes_niveis[state['acao_id']]['pontos'])
                    feedback, pontuacao,pontuacao_llm = processar_resposta(
                        state['acao_id'],
                        state['pergunta'],
                        state['resposta'],
                        contexto,
                        acoes_niveis[state['acao_id']]['pontos']
                    )
                    
                     # Calcular a porcentagem de acerto
                    porcentagem_acerto = (pontuacao_llm / 10) * 100  # Assumindo que a LLM pontua de 0 a 10
                    
                    print(state['roteiro_id'])
                    #st.stop()
                    criar_checkpoint(
                        state['roteiro_id'], 
                        state['acao_id'], 
                        state['nivel_bloom'], 
                        state['pergunta'], 
                        state['resposta'], 
                        pontuacao, 
                        feedback
                    )
                    state.update({
                        'feedback': feedback,
                        'pontuacao': pontuacao,
                        'pontuacao_llm': pontuacao_llm,
                        'porcentagem_acerto': porcentagem_acerto,
                        'etapa': 'feedback',
                        'checkpoint_criado': True
                    })
                    state['etapa'] = 'feedback'
                    st.rerun()
                
                
        elif state['etapa'] == 'feedback':
            show_feedback_reflection(state, acoes_niveis)
            
            
            col1, Proxima_Pergunta, Concluir_Checkpoint2, col4 = st.columns([1,2,2,1])
            
            with Proxima_Pergunta:
                if st.button("Próxima Pergunta", key="next_step", type='primary'):
                    state['etapa'] = 'gerar_pergunta'
                    st.rerun()
            
            with Concluir_Checkpoint2:    
                if st.button("Concluir Ponto de Reflexão", key="finish_checkpoint"):
                    state['etapa'] = 'conclusao'
                    st.rerun()

        elif state['etapa'] == 'conclusao':
            st.markdown("## Ponto de Reflexão Concluído!")
            st.balloons()
            st.success(f"Parabéns! Você completou o Ponto de Reflexão com {st.session_state.get('pontuacao_total', 0)} pontos.")
            
            if st.button("Voltar para o Roteiro de Leitura", key="back_to_reading"):
                st.session_state['tela'] = 'chat'
                state['etapa'] = 'iniciar'
                st.rerun()

# Footer
    st.markdown("---")
    st.markdown("RELIA - Roteiro Empático de Leitura com Inteligência Artificial")   
    st.markdown("""
            <style>
            .footer {
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                background-color: #f8f9fa;
                color: #6c757d;
                text-align: center;
                padding: 10px;
                font-size: 14px;
                border-top: 1px solid #dee2e6;
            }
            
            .footer-content {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 5px;
            }
            
            .footer-warning {
                color: #856404;
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                border-radius: 4px;
                padding: 8px 12px;
                margin: 0 auto;
                max-width: 800px;
                font-size: 13px;
            }
            </style>
        """, unsafe_allow_html=True)

    # Footer minimalista com tooltip
    st.markdown("""
        <div class="footer" title="O RELIA utiliza IA generativa e pode conter imprecisões. Recomendamos verificar as informações em fontes acadêmicas confiáveis.">
            ⚠️ Conteúdo gerado por IA - Verificar informações importantes
        </div>
    """, unsafe_allow_html=True)  


#--------- Nova Proposta ------------




# ---- Fim dos dados da proposta ----

       
            
#------------------------------- Tipos de Checkpoints --------------


#---------------- IMPORTANTE NA TELA CHKPOINT --------------------------------


# ----- Modularizando o tela ---------------------


# Funções de checkpoint específicas (lista e quizz)
def checkpoint_list(pergunta, contexto, acao_data):
    with st.container():
        st.write(pergunta)
        
        # Campo de resposta
        resposta_usuario = st.text_area("Digite sua resposta aqui (liste as informações solicitadas):", key=f"text_area_{acao_data['id']}")
        
        if st.button("Enviar Resposta List", key=f"enviar_resposta_list_{acao_data['id']}"):
            if resposta_usuario.strip():
                feedback, pontuacao = avaliar_resposta_com_llm(pergunta, resposta_usuario, contexto)
                st.write(f"**Feedback:** {feedback}")
                st.write(f"**Pontuação:** {pontuacao}")
                
                # Registrar o checkpoint no banco de dados
                criar_checkpoint(
                    st.session_state['roteiro_id'],
                    acao_data['id'],
                    contexto['nivel_bloom'],
                    pergunta,
                    resposta_usuario,
                    pontuacao,
                    feedback
                )
                
                # Atualizar a pontuação total do usuário
                with pontuacao_lock:
                    st.session_state['pontuacao_total'] += pontuacao
                
                # Verificar se o usuário completou o nível
                novo_nivel_bloom, _ = obter_nivel_atual_usuario()
                if novo_nivel_bloom != contexto['nivel_bloom']:
                    st.success("Você avançou para o próximo nível!")
                    st.session_state['tela'] = "checkpoint"
                    st.session_state['nivel_atual'] = novo_nivel_bloom
                    st.rerun()
                else:
                    if st.button("Continuar no Nível Atual", key="continuar_nivel_atual"):
                        st.session_state['tela'] = "checkpoint"
                        st.rerun()
            else:
                st.error("Por favor, insira sua resposta antes de enviar.")

def checkpoint_quizz(pergunta, contexto, acao_data):
    with st.container():
        st.write(pergunta)
        
        # Campo de resposta
        resposta_usuario = st.radio("Selecione a resposta correta:", options=acao_data['opcoes'], key=f"radio_{acao_data['id']}")
        
        if st.button("Enviar Resposta Quizz", key=f"enviar_resposta_quizz_{acao_data['id']}"):
            if resposta_usuario:
                feedback, pontuacao = avaliar_resposta_com_llm(pergunta, resposta_usuario, contexto)
                st.write(f"**Feedback:** {feedback}")
                st.write(f"**Pontuação:** {pontuacao}")
                
                # Registrar o checkpoint no banco de dados
                criar_checkpoint(
                    st.session_state['roteiro_id'],
                    acao_data['id'],
                    contexto['nivel_bloom'],
                    pergunta,
                    resposta_usuario,
                    pontuacao,
                    feedback
                )
                
                # Atualizar a pontuação total do usuário
                with pontuacao_lock:
                    st.session_state['pontuacao_total'] += pontuacao
                
                # Verificar se o usuário completou o nível
                novo_nivel_bloom, _ = obter_nivel_atual_usuario()
                if novo_nivel_bloom != contexto['nivel_bloom']:
                    st.success("Você avançou para o próximo nível!")
                    st.session_state['tela'] = "checkpoint"
                    st.session_state['nivel_atual'] = novo_nivel_bloom
                    st.rerun()
                else:
                    if st.button("Continuar no Nível Atual", key="continuar_nivel_atual_quizz"):
                        st.session_state['tela'] = "checkpoint"
                        st.rerun()
            else:
                st.error("Por favor, selecione uma resposta antes de enviar.")

# Função auxiliar para debug (opcional)
def mostrar_estado_atual(acao_id):
    st.write("Estado atual das respostas:")
    for key in st.session_state:
        if key.startswith(f"resposta_") and key.endswith(f"_{acao_id}"):
            st.write(f"{key}: {st.session_state[key]}")

 
