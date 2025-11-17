import streamlit as st
from streamlit_extras.colored_header import colored_header # type: ignore
from views.area_do_leitor import determinar_nivel_e_progresso

def show_bloom_level_info(nivel_bloom):
    """
    Mostra informações sobre o nível da Taxonomia de Bloom em um pop-up estilizado.
    
    Args:
        nivel_bloom (str): O nível atual da Taxonomia de Bloom
    """
    # Informações sobre os níveis de Bloom
    bloom_info = {
        'Lembrar': {
            'cor': '#A2D9CE',
            'descricao': 'Neste nível, o foco está em recordar e reconhecer informações e conceitos básicos.',
            'verbos': ['Definir', 'Listar', 'Reconhecer', 'Identificar', 'Recuperar'],
            'icon': '🤔'
        },
        'Compreender': {
            'cor': '#A9DFBF',
            'descricao': 'Demonstrar entendimento através da interpretação e explicação de conceitos.',
            'verbos': ['Explicar', 'Classificar', 'Descrever', 'Discutir', 'Localizar'],
            'icon': '💡'
        },
        'Aplicar': {
            'cor': '#5499C7',
            'descricao': 'Usar o conhecimento adquirido em novas situações para resolver problemas.',
            'verbos': ['Implementar', 'Executar', 'Usar', 'Demonstrar', 'Interpretar'],
            'icon': '⚙️'
        },
        'Analisar': {
            'cor': '#F5B041',
            'descricao': 'Dividir informação em partes e entender relações entre elas.',
            'verbos': ['Comparar', 'Organizar', 'Desconstruir', 'Atribuir', 'Estruturar'],
            'icon': '🔍'
        },
        'Avaliar': {
            'cor': '#EC7063',
            'descricao': 'Fazer julgamentos baseados em critérios e padrões.',
            'verbos': ['Checar', 'Criticar', 'Julgar', 'Justificar', 'Argumentar'],
            'icon': '⭐'
        },
        'Criar': {
            'cor': '#AF7AC5',
            'descricao': 'Reunir elementos para formar algo novo ou fazer julgamentos sobre valores.',
            'verbos': ['Gerar', 'Planejar', 'Produzir', 'Desenhar', 'Construir'],
            'icon': '✨'
        }
    }
    
    # Obter informações do nível atual
    nivel_info = bloom_info.get(nivel_bloom, st.session_state['nivel_atual'])
    if not nivel_info:
        return
    
    # Criar o container expansível com estilo personalizado
    with st.expander(f"{nivel_info['icon']} Saiba mais: Nível: {nivel_bloom}", expanded=False):
        # Usar HTML/CSS para estilização avançada
        st.markdown(f"""
            <div style="
                padding: 15px;
                border-radius: 10px;
                background-color: {nivel_info['cor']}22;
                border-left: 5px solid {nivel_info['cor']};
            ">
                <h4 style="color: {nivel_info['cor']}; margin-bottom: 10px;">
                    {nivel_bloom}
                </h4>
                <p style="margin-bottom: 15px;">
                    {nivel_info['descricao']}
                </p>
                <div>
                    <strong>Verbos comuns:</strong><br>
                    {'  •  '.join(nivel_info['verbos'])}
                </div>
            </div>
        """, unsafe_allow_html=True)

# Exemplo de uso
def show_level_header(nivel_bloom):
    """
    Mostra o cabeçalho com o nível atual e o pop-up de informações.
    
    Args:
        nivel_bloom (str): O nível atual da Taxonomia de Bloom
    """
    
    nivel_info = {
        'Lembrar': {
            'cor': '#A2D9CE',
            'icone': '🤔'
        },
        'Compreender': {
            'cor': '#A9DFBF',
            'icone': '💡'
        },
        'Aplicar': {
            'cor': '#5499C7',
            'icone': '⚙️'
        },
        'Analisar': {
            'cor': '#F5B041',
            'icone': '🔍'
        },
        'Avaliar': {
            'cor': '#EC7063',
            'icone': '⭐'
        },
        'Criar': {
            'cor': '#AF7AC5',
            'icone': '✨'
        }
    }
    
    col1, col2 = st.columns([2,2])
    with col1:
        #st.header(f"Nível Atual: {nivel_bloom}")
        info = nivel_info.get(nivel_bloom, {'cor': '#000000', 'icone': '📚'})
        st.markdown(f"""
                    <div style='
                        padding: 10px; 
                        border-radius: 5px; 
                        s
                        margin-bottom: 20px;
                    '>
                        <h1 style='
                            margin: 0;
                            color: #333;
                            font-size: 24px;
                        '>
                            Nível Atual: {info['icone']} 
                            <span style='
                                color: {info['cor']};
                                font-weight: bold;
                            '>
                                {nivel_bloom}
                            </span>
                        </h1>
                    </div>
                """, unsafe_allow_html=True)
          
    with col2:
        show_bloom_level_info(nivel_bloom)
        
        
def show_pontuacao():
    pontuacao_atual = st.session_state.get('pontuacao_total', 0)
    pontuacao_maxima = 253
    porcentagem = (pontuacao_atual / pontuacao_maxima) * 100
    
    st.markdown(f"""
        <div style='
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: inline-flex;
            align-items: center;
            gap: 10px;
        '>
            <div style='
                font-size: 18px;
                font-weight: bold;
                color: #1e88e5;
            '>
                Pontuação Total:
            </div>
            <div style='
                font-size: 24px;
                font-weight: bold;
                color: #2196f3;
            '>
                {pontuacao_atual}
            </div>
            <div style='
                font-size: 18px;
                color: #757575;
            '>
                /
            </div>
            <div style='
                font-size: 20px;
                font-weight: bold;
                color: #757575;
            '>
                {pontuacao_maxima}
            </div>
            <div style='
                background-color: #e3f2fd;
                padding: 4px 8px;
                border-radius: 20px;
                font-size: 14px;
                color: #1e88e5;
            '>
                {porcentagem:.1f}%
            </div>
        </div>
    """, unsafe_allow_html=True)


def show_feedback_reflection(state, acoes_niveis):
    """
    Mostra o feedback e resultados da reflexão de forma estilizada.
    """
    # Cores do RELIA
    cores = {
        'primaria': '#00edfb',      # Azul RELIA
        'secundaria': '#1e88e5',    # Azul mais escuro
        'sucesso': '#4cd964',       # Verde
        'alerta': '#ffd93d',        # Amarelo
        'info': '#63b3ed',          # Azul claro
    }

    # Container principal
    with st.container():
        # Título do Feedback
        st.markdown(f"""
            <h2 style='
                color: {cores['secundaria']};
                border-bottom: 2px solid {cores['primaria']};
                padding-bottom: 10px;
            '>
                📝 Feedback da Reflexão
            </h2>
        """, unsafe_allow_html=True)

        # Container para o feedback
        with st.container():
            # Cor do feedback baseada na pontuação
            feedback_color = cores['sucesso'] if state['pontuacao_llm'] >= 5 else cores['alerta']
            
            st.markdown(f"""
                <div style='
                    padding: 20px;
                    border-left: 5px solid {feedback_color};
                    background-color: {feedback_color}22;
                    border-radius: 5px;
                    margin: 10px 0;
                '>
                    {state['feedback']}
                </div>
            """, unsafe_allow_html=True)

        # Métricas em colunas
        col1, col2, col3= st.columns([1, 1,2])
        
        with col1:
            # Pontuação da atividade
            st.markdown(f"""
                <div style='
                    text-align: center;
                    padding: 15px;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                '>
                    <div style='color: {cores['secundaria']}; font-size: 14px;'>
                        Assertividade na atividade
                    </div>
                    <div style='
                        font-size: 24px;
                        font-weight: bold;
                        color: {cores['primaria']};
                    '>
                        {state['porcentagem_acerto']:.1f}%
                    </div>
                    <div style='font-size: 12px; color: #666;'>
                         a validar:  {acoes_niveis[state['acao_id']]['pontos']} pontos 
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
             show_pontuacao()
        
        with col3:
            # Status da validação
            status_color = cores['sucesso'] if state['pontuacao_llm'] >= 5 else cores['alerta']
            status_icon = "🎯" if state['pontuacao_llm'] >= 5 else "⚠️"
            status_text = "Pontuação da ação validada!" if state['pontuacao_llm'] >= 5 else "Pontuação da ação não validada."
            
            st.markdown(f"""
                <div style='
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 15px;
                    background-color: {status_color}22;
                    border-radius: 10px;
                '>
                    <span style='font-size: 24px;'>{status_icon}</span>
                    <span style='
                        color: {status_color};
                        font-weight: bold;
                    '>
                        {status_text}
                    </span>
                </div>
            """, unsafe_allow_html=True)

        # Mostrar pontuação total
        st.markdown("---")
       
        
def show_progress_bar(pontuacao_total):
    """
    Mostra uma barra de progresso estilizada que muda de cor conforme o nível.
    """
    # Cores para cada nível da taxonomia de Bloom
    cores_niveis = {
        'Lembrar': '#A2D9CE',      # Azul Claro
        'Compreender': '#A9DFBF',  # Verde Claro
        'Aplicar': '#5499C7',      # Azul
        'Analisar': '#F5B041',     # Laranja
        'Avaliar': '#EC7063',      # Vermelho
        'Criar': '#AF7AC5'         # Roxo
    }
    
    nivel_atual, progresso = determinar_nivel_e_progresso(pontuacao_total)
    cor_atual = cores_niveis.get(nivel_atual, '#A2D9CE')
    porcentagem = progresso * 100

    # Criar HTML personalizado para a barra de progresso
    st.markdown(f"""
        <div style="
            margin: 10px 0;
            padding: 10px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 5px;
            ">
                <div style="
                    font-size: 14px;
                    color: #666;
                ">
                    Progresso no Nível {nivel_atual}
                </div>
                <div style="
                    font-weight: bold;
                    color: {cor_atual};
                ">
                    {porcentagem:.0f}%
                </div>
            </div>
            <div style="
                background-color: #f0f0f0;
                border-radius: 10px;
                height: 10px;
                overflow: hidden;
            ">
                <div style="
                    width: {porcentagem}%;
                    height: 100%;
                    background-color: {cor_atual};
                    transition: width 0.5s ease;
                "></div>
            </div>
            <div style="
                display: flex;
                justify-content: flex-end;
                margin-top: 5px;
                font-size: 12px;
                color: #666;
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 5px;
                ">
                    <span style="
                        display: inline-block;
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background-color: {cor_atual};
                    "></span>
                    Nível {nivel_atual}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)        

        
