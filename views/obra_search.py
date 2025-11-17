import streamlit as st
from database import inserir_obra, criar_roteiro, obter_obra_por_titulo_autor,perfil_completo
import re
import json
import openai
import time


# Defina a chave da API
openai.api_key = st.secrets["OPENAI"]["OPENAI_API_KEY"]

# Inicializa chaves necessárias no estado da sessão
for key in ['sugestoes', 'titulo', 'autor', 'obra', 'obra_id', 'usuario_id']:
    if key not in st.session_state:
        if key == 'sugestoes':
            st.session_state[key] = []
        elif key == 'obra':
            st.session_state[key] = {"titulo": "", "autor": "", "ano_publicacao": "", "genero": ""}
        else:
            st.session_state[key] = None
    
    
def sanitize_input(text):
    """
    Sanitiza a entrada removendo caracteres especiais indesejados.
    
    Args:
        text (str): Texto de entrada do usuário.
        
    Returns:
        str: Texto sanitizado.
    """
    return re.sub(r'[^\w\s]', '', text).strip()


@st.cache_data(show_spinner=False, ttl=3600)
def gerar_sugestoes_obras(titulo, autor):
    """
    Gera sugestões de obras a partir de um título e autor usando a API do OpenAI.
    """
    
    prompt = f"""
    Sugira a obra original e real com o título '{titulo}' e autor '{autor}'. Não Alucine com os resultados,  explore apenas obras que realmente existam.
    Forneça as sugestões no seguinte formato JSON:
    [
        {{
            "titulo": "Nome do Livro",
            "autor": "Nome do Autor",
            "ano_publicacao": 1234,
            "genero": "Gênero do Livro"
        }},
        ...
    ]
    """
    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "Você é um assistente útil para sugestões de livros."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500
        )

        # Verifique o conteúdo da resposta para depuração
        resposta_texto = resposta.choices[0].message.content.strip()
        print("Resposta da API:", resposta_texto)  # Debug: Imprime a resposta da API

        # Tente encontrar e extrair o JSON da resposta
        json_start = resposta_texto.find('[')
        json_end = resposta_texto.rfind(']') + 1
        if json_start != -1 and json_end != -1:
            json_str = resposta_texto[json_start:json_end]
            sugestoes = json.loads(json_str)
        else:
            raise ValueError("Não foi possível encontrar uma resposta válida")

          # Validar e filtrar as sugestões
        sugestoes_validas = []
        for sugestao in sugestoes:
            if all(key in sugestao for key in ['titulo', 'autor', 'ano_publicacao', 'genero']):
                sugestoes_validas.append(sugestao)

        return sugestoes_validas

    except json.JSONDecodeError as e:
        st.error(f"Erro ao converter a resposta para JSON: {e}")
        st.warning("Por favor, verifique as informações da obra e do autor e tente novamente.")
        st.error(f"Resposta da API não está no formato esperado: {resposta_texto}")
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Erro ao obter sugestões: {e}")
    
    return []


def f_sugere_obras(titulo, autor):
    """
    Gera e armazena sugestões de obras no estado da sessão.
    
    Args:
        titulo (str): Título da obra.
        autor (str): Nome do autor.
    """
    sugestoes = gerar_sugestoes_obras(titulo, autor)
    st.session_state['sugestoes'] = sugestoes  # Armazenar como lista de dicionários
    

def f_escolher_obra(obra_selecionada):
    """
    Processa a obra selecionada pelo usuário, verificando sua existência no banco de dados
    e criando um roteiro associado.
    
    Args:
        obra_selecionada (str): String formatada da obra selecionada.
    """
    if obra_selecionada:
        # Separar os detalhes da obra selecionada
        partes_obra = [parte.strip() for parte in obra_selecionada.split(" | ")]
        if len(partes_obra) == 4:
            titulo, autor, ano_publicacao, genero = partes_obra

            # Verificar se a obra já existe na base de dados
            obra_existente = obter_obra_por_titulo_autor(titulo, autor)

            if obra_existente:
                # Carregar os dados da obra existente para a sessão
                st.session_state['obra_id'] = obra_existente['id']
                st.session_state['roteiro_id'] = criar_roteiro(st.session_state['obra_id'], st.session_state['usuario_id'])
                st.toast(f"Obra '{titulo}' já existe. Dados carregados com sucesso!")
            else:
                # Inserir nova obra no banco de dados
                try:
                    insert_id = inserir_obra(titulo=titulo, autor=autor, ano_publicacao=int(ano_publicacao), genero=genero)
                    st.toast(f"Obra '{titulo}' inserida com sucesso!")

                    if insert_id:
                        st.session_state['obra_id'] = insert_id
                        st.session_state['roteiro_id'] = criar_roteiro(st.session_state['obra_id'], st.session_state['usuario_id'])
                        st.toast("Roteiro criado com sucesso!")
                        time.sleep(1)
                except Exception as e:
                    st.error("Erro na gravação no banco")
                    st.write(str(e))
                    print(f"Exception ao inserir obra ou criar roteiro: {e}")  # Log adicional
        else:
            st.error("Formato inválido da obra selecionada.")
    else:
        st.warning("Por favor, selecione uma obra.")


def confirmar_selecao():
    if st.session_state.obra_selecionada_temp:
        # Recupera os dados da obra selecionada
        obra_selecionada = st.session_state.obra_selecionada_temp
        partes_obra = obra_selecionada.split(" | ")

        if len(partes_obra) == 4:
            titulo, autor, ano_publicacao, genero = partes_obra

            try:
                # Inserir a obra na base de dados
                obra_id = inserir_obra(
                    titulo=titulo.strip(),
                    autor=autor.strip(),
                    ano_publicacao=int(ano_publicacao.strip()),
                    genero=genero.strip()
                )

                if obra_id:
                    st.success(f"Obra '{titulo}' inserida com sucesso!")

                    # Guardar obra e usuário no estado da sessão
                    st.session_state['obra'] = {
                        'titulo': titulo, 
                        'autor': autor, 
                        'ano_publicacao': ano_publicacao, 
                        'genero': genero
                    }
                    st.session_state['obra_id'] = obra_id

                    # Utilize o ID do usuário logado do session_state
                    usuario_id = st.session_state.get('usuario_id')
                    if usuario_id:
                        # Criar o roteiro
                        roteiro_id = criar_roteiro(obra_id, usuario_id)
                        st.session_state['roteiro_id'] = roteiro_id
                        st.toast("Roteiro criado com sucesso!")
                        time.sleep(3)
                        st.success("Roteiro criado com sucesso!")
                        
                       
                    else:
                        st.error("Usuário não está logado.")
            except Exception as e:
                st.error(f"Erro ao inserir obra ou criar roteiro: {e}")
        else:
            st.error("Formato inválido da obra selecionada.")
    else:
        st.warning("Por favor, selecione uma obra antes de confirmar.")

      
# Função para limpar os campos
def limpar_campos():
    """
    Limpa os campos de entrada e reseta o estado da sessão.
    """
    st.session_state['titulo'] = ""
    st.session_state['autor'] = ""
    st.session_state['sugestoes'] = []
    st.session_state['obra_selecionada_temp'] = None
    st.session_state['obra'] = {"titulo": "", "autor": "", "ano_publicacao": "", "genero": ""}
    st.session_state['obra_id'] = None
    st.session_state['usuario_id'] = None
    st.rerun()
    
    
def tela_selecionar_obra():
   
    if "usuario" not in st.session_state:
            st.warning("Você não está logado. Por favor, faça o login.")
            return
        
        # Verifica se o perfil está completo
    if not st.session_state.get("perfil_completo", True):
            st.warning("Seu perfil está incompleto. Por favor, click em atualizar  perfil na barra lateral para continuar.")
            return
    
    # Inicializar 'sugestoes' se não existir
    if 'sugestoes' not in st.session_state:
        st.session_state['sugestoes'] = []
        obra_selecionada = []
        primeira_obra = []
            
    # Resto da lógica da tela principal
    #st.header("Busque uma obra literária:")
    
    # Título estilizado
      
    with st.container(border=True):
        """
        Define a interface principal onde o usuário insere o título e autor,
        busca sugestões, seleciona uma obra e confirma a criação do roteiro.
        """
        # Sanitizar as entradas do usuário
        # Título da seção
        st.markdown('<p class="titulo-destaque"> 🎯 Pesquise uma obra</p>', unsafe_allow_html=True, 
                    help="Bem-vindo ao RELIA! Aqui você pode iniciar seu roteiro de leitura personalizado, pesquisando por obras literárias de seu interesse.")
      
        # Campo do título da obra
        st.markdown(
            f"<h6>{'Obra'}</h6>", 
            unsafe_allow_html=True, 
            help="Insira o título da obra que deseja estudar. Pode ser um livro, poema, conto ou qualquer obra literária disponível no RELIA."
        )
        titulo_input = st.text_input(
            "titulo_input",
            placeholder="Digite o nome da obra", 
            key="titulo_input",
            label_visibility="collapsed",
            help="Dica: Digite o título completo ou parcial da obra. Por exemplo: 'Dom Casmurro' ou 'Memórias Póstumas'"
        )

        # Campo do autor
        st.markdown(
            f"<h6>{'Autor'}</h6>", 
            unsafe_allow_html=True, 
            help="Insira o nome do autor da obra. Pode ser o nome completo ou como o autor é mais conhecido."
        )
        autor_input = st.text_input(
            "autor_input",
            placeholder="Digite o nome do autor", 
            key="autor_input",
            label_visibility="collapsed",
            help="Dica: Digite o nome do autor como ele é mais conhecido. Por exemplo: 'Machado de Assis' ou apenas 'Machado'"
        )

        # Processamento dos inputs
        st.session_state['titulo'] = sanitize_input(titulo_input)
        st.session_state['autor'] = sanitize_input(autor_input)

        # Botão para buscar sugestões de obras
        button_busca_obra = st.button("Buscar", disabled=not (st.session_state['titulo'] and st.session_state['autor']),help="Para buscar uma obra preencha o nome da Obra e Autor.")
      
        
        # Ação: buscar sugestões de obras
        if button_busca_obra:
            with st.spinner('Gerando sugestões...'):
                f_sugere_obras(st.session_state['titulo'], st.session_state['autor'])

        # Escolha da obra
        if st.session_state['sugestoes']:
            primeira_obra = st.session_state['sugestoes'][0]
            obra_selecionada = f"{primeira_obra['titulo']} | {primeira_obra['autor']} | {primeira_obra['ano_publicacao']} | {primeira_obra['genero']}"
            
            # CSS personalizado para estilização
            st.markdown("""
                <style>
                .titulo-destaque {
                    color: #1E88E5;
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    padding: 10px;
                }
                .obra-container {
                    background-color: #f0f8ff;
                    border-left: 5px solid #1E88E5;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                .emoji-texto {
                    font-size: 20px;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Container com a obra
            with st.container():
                st.markdown('<p class="titulo-destaque">📚 Sugestão do RELIA</p>', unsafe_allow_html=True)
                st.markdown('<div class="obra-container">', unsafe_allow_html=True)
                
                # Separando as informações da obra para melhor apresentação
                titulo, autor, ano, genero = obra_selecionada.split(" | ")
                
                st.markdown(f"""
                    ### {titulo}
                    **Autor:** {autor}  
                    **Ano:** {ano}  
                    **Gênero:** {genero}
                """)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Mensagem de ajuda estilizada
                st.info("💡 Esta é a obra sugerida especialmente para o seu roteiro de leitura no RELIA!", icon="✨")
                
                st.session_state['obra_selecionada_temp'] = obra_selecionada
                
                # Botão de ação (opcional)
                if st.button("📖 Começar o Roteiro de Leitura", disabled=not (
                                st.session_state.get('obra_selecionada_temp') and
                                titulo_input and
                                autor_input
                            ), type="primary"):
                    
                    f_escolher_obra(obra_selecionada)
                    st.session_state['resumo_exibido'] = False 
                    st.session_state['tela'] = 'chat'
                    for key in st.session_state.keys():
                        print(key,":",st.session_state[key])
                        st.session_state['sugestoes'] = []
                        st.rerun()
                    
                    st.success("Ótima escolha! Vamos começar esta jornada literária! 🚀")

        else:
            obra_selecionada = None
            st.warning("Você ainda não buscou uma obra. 😕")
                
        st.divider()

        #Footer com botão de informações
        footer_container = st.container()
        with footer_container:
            col1, col2, col3 = st.columns([1,3,1])
            with col2:
                st.warning("⚠️ RELIA é baseado em IA. Por favor, verifique as informações críticas em fontes confiáveis.")
                if st.button("ℹ️ Mais informações sobre o uso de IA"):
                    st.info("""
                        O RELIA utiliza tecnologia de Inteligência Artificial para:
                        - Gerar sugestões de roteiros de leitura
                        - Criar análises literárias
                        - Oferecer interpretações de textos
                        
                        Como toda IA generativa, pode:
                        - Cometer erros factuais
                        - Fazer interpretações imprecisas
                        - Gerar conteúdo inconsistente
                        
                        Recomendamos sempre:
                        - Verificar informações em fontes acadêmicas
                        - Consultar a obra original
                        - Comparar com análises de especialistas
                        """)
               
        # CSS personalizado para o footer
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

           

         # Rodapé
        # Footer minimalista com tooltip
        st.markdown("""
            <div class="footer" title="O RELIA utiliza IA generativa e pode conter imprecisões. Recomendamos verificar as informações em fontes acadêmicas confiáveis.">
                ⚠️ Conteúdo gerado por IA - Pode cometer erros. Considere verificar informações importantes. ⚠️ 
            </div>
        """, unsafe_allow_html=True) 
        st.markdown('</div>', unsafe_allow_html=True)
