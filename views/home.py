import streamlit as st

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

    st.markdown('<div class="sub-header"><strong>RELIA</strong> - Roteiro Empático de Leitura e Interpretação por Inteligência Artificial - é uma ferramenta inovadora projetada para ampliar a compreensão textual e o acesso à leitura através da inteligência artificial.</div>', unsafe_allow_html=True)

    with st.expander("Saiba mais sobre o RELIA"):
        st.markdown("""
        <div class="expander-content">
        Ao utilizar técnicas avançadas de processamento de linguagem natural, o RELIA auxilia leitores de todas as idades e níveis de conhecimento a explorar obras literárias com profundidade e clareza.
        
        Com o RELIA, você pode:

        - **Analisar Textos Complexos**: A IA identifica conceitos-chave, relações entre ideias e diferentes níveis de significado, facilitando a interpretação de textos complexos.
        - **Participar de Diálogos Interativos**: O sistema promove a interação entre o leitor e a IA, respondendo a perguntas, oferecendo diferentes perspectivas de análise e incentivando a reflexão crítica.
        
        Nosso objetivo não é apenas facilitar a leitura e interpretação de textos, mas também promover a empatia, a responsabilidade individual e a construção de um futuro mais ético e interseccional. Junte-se a nós nesta jornada de leitura assistida por IA e descubra novas maneiras de se conectar com a literatura e com outros leitores ao redor do mundo.
        </div>
        """, unsafe_allow_html=True)
