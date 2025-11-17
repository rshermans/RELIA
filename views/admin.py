import streamlit as st
import pandas as pd
import plotly.express as px # type: ignore
from database import (listar_usuarios, atualizar_usuario, deletar_usuario, listar_obras, atualizar_obra, deletar_obra, listar_roteiros, atualizar_roteiro, deletar_roteiro, 
                      obter_perfil_por_id,listar_usuarios_indice,listar_roteiros_indice,listar_obras_indice,inserir_obra,obter_obra_por_id, listar_roteiros_G, listar_obras_com_roteiros,inserir_perfil
                      
)  
import time
import re
import matplotlib.pyplot as plt
import seaborn as sns


for key in st.session_state.keys():
        print(key,":",st.session_state[key])

def validar_email(email):
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email)


def tela_admin():
    st.title("Painel de Administração do RELIA")

    # Resumo Geral com Ícones
    st.header("Resumo Geral")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Usuários", len(listar_usuarios_indice()))
    with col2:
        st.metric("📚 Obras", len(listar_obras_indice()))
    with col3:
        st.metric("📜 Roteiros", len(listar_roteiros_indice()))

    # Gráficos de Resumo
    st.subheader("Visualização de Dados")
    tab1, tab2 = st.tabs(["Gráficos de Usuários", "Gráficos de Obras"])

    # Dados dos usuários
    colunas_usuarios, usuarios = listar_usuarios()
    df_usuarios = pd.DataFrame(usuarios, columns=colunas_usuarios)
    
    """ 
        # Dados dos roteiros
        colunas_roteiros, roteiros = listar_roteiros()
        #df_roteiros = pd.DataFrame(roteiros, columns=colunas_roteiros)
            
        # Caso esteja criando a partir de uma única linha (ou valores escalares)
        if isinstance(roteiros, dict):
            # Transformar em lista de dicionários
            df_roteiros = pd.DataFrame([roteiros])
        elif len(roteiros) > 0 and isinstance(roteiros[0], dict):
            # Se `roteiros` for uma lista de dicionários
            df_roteiros = pd.DataFrame(roteiros)
        else:
            # Caso contrário, passar um índice se os valores forem escalares
            df_roteiros = pd.DataFrame(roteiros, columns=colunas_roteiros, index=[0])
        """
    with tab1:
        st.subheader("Gráficos de Usuários")
        
        # Histograma da distribuição de idade dos usuários
        if not df_usuarios.empty and 'idade' in df_usuarios.columns:
            # Agrupando os dados para contagem
            grafico_dados = df_usuarios.groupby(['idade', 'nivel_educacional', 'habito_leitura']).size().reset_index(name='contagem')

            # Criando um gráfico de barras
            plt.figure(figsize=(12, 8))
            sns.barplot(data=grafico_dados, x='idade', y='contagem', hue='nivel_educacional', dodge=True) #style='habito_leitura',

            # Adicionando títulos e rótulos
            plt.title('Distribuição de Usuários por Idade, Nível Educacional e Hábito de Leitura')
            plt.xlabel('Idade')
            plt.ylabel('Contagem de Usuários')
            plt.xticks(rotation=45)

            # Exibindo o gráfico no Streamlit
            st.pyplot(plt)

            # Limpa a figura para evitar sobreposições em atualizações de Streamlit
            plt.clf()
        else:
            st.write("Dados de usuários não disponíveis ou coluna 'idade' não encontrada.")

    # Dados das obras
    colunas_obras,obras = listar_obras()
    df_obras = pd.DataFrame(obras, columns=colunas_obras)
    
    # Dados das obras com contagem de roteiros
    colunas_obras, obras = listar_obras_com_roteiros()
    df_obras_roteiros = pd.DataFrame(obras, columns=colunas_obras)

    with tab2:
        st.subheader("Gráfico de Obras e Roteiros")
        if not df_obras_roteiros.empty and 'obra_titulo' in df_obras_roteiros.columns and 'quantidade_roteiros' in df_obras_roteiros.columns:
            fig = px.scatter(
                df_obras_roteiros, 
                x='obra_titulo', 
                y='quantidade_roteiros',
                size='quantidade_roteiros',
                color='quantidade_roteiros',
                hover_name='obra_titulo',
                title='Quantidade de Roteiros por Obra'
            )
            fig.update_layout(xaxis_title='Obras', yaxis_title='Quantidade de Roteiros')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Dados de obras e roteiros não disponíveis ou colunas necessárias não encontradas.")

    # Tabelas Interativas
    st.header("Gerenciamento de Dados")
    tab_usuarios, tab_obras, tab_roteiros = st.tabs(["Usuários", "Obras", "Roteiros"])

    with tab_usuarios:
        st.subheader("Usuários")

        # Exibe o DataFrame de usuários para visualização
        df_usuarios = pd.DataFrame(usuarios, columns=['ID', 'Id Util','Nome', 'Email', 'Roteiros', 'Idade', 'Cidade', 'Interesses', 'Escolaridade','Habito de Leitura' ,'Compartilha dados', 'Criado','Atualizado'])
        if not df_usuarios.empty:
            st.write("Tabela de Usuários:")
            st.dataframe(df_usuarios)  # Mostra a tabela com os usuários antes dos botões

        # Inserir novo usuário
        with st.expander("Adicionar Novo Usuário"):
            st.write("Preencha os dados do novo usuário:")
            novo_nome = st.text_input("Nome")
            novo_email = st.text_input("Email")
            nova_senha = st.text_input("Senha", type="password")
            nova_idade = st.number_input("Idade", min_value=1, max_value=100)
            nova_cidade = st.text_input("Cidade")
            novos_interesses = st.text_area("Interesses")
            opcao_compartilhar = st.checkbox("Compartilhar dados?",value=False)

            if st.button("Salvar Novo Usuário"):
                if novo_nome and novo_email and nova_senha and nova_idade and nova_cidade and novos_interesses is not None:
                    if validar_email(novo_email):
                        try:
                            inserir_perfil(
                                novo_nome, novo_email, nova_senha, nova_idade, nova_cidade, novos_interesses, opcao_compartilhar
                            )
                            st.success(f"Usuário '{novo_nome}' adicionado com sucesso!")
                            #st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao adicionar o usuário: {e}")
                    else:
                         st.error(f"O email '{novo_email}' já está em uso. Por favor, use um email diferente.")
                       
                else:
                    st.warning("Todos os campos são obrigatórios para adicionar um novo usuário.")

        # Edição de usuário específico
        with st.expander("Editar Usuário"):
            st.write("Edite as informações do usuário ao inserir o ID ou nome abaixo:")

            # Campo para o ID ou nome do usuário a ser editado
            editar_id_usuario = st.text_input("Digite o ID ou Nome do Usuário que deseja editar:")

            # Filtra o usuário com base no ID ou Nome fornecido
            if editar_id_usuario:
                usuario = None
                try:
                    usuario_id = int(editar_id_usuario)
                    usuario = obter_perfil_por_id(usuario_id)
                except ValueError:
                    usuario = next((u for u in usuarios if u['nome'].lower() == editar_id_usuario.lower()), None)

                if usuario:
                    st.markdown(f"**Usuário Selecionado: {usuario['nome']} (ID: {usuario['id']})**")
                    novo_nome = st.text_input("Editar Nome do Usuário", value=usuario['nome'])
                    novo_email = st.text_input("Editar Email do Usuário", value=usuario['email'])
                    nova_idade = st.number_input("Editar Idade do Usuário", value=usuario['idade'], step=1)
                    nova_cidade = st.text_input("Editar Cidade do Usuário", value=usuario['cidade'])
                    novos_interesses = st.text_input("Editar Interesses do Usuário", value=usuario['interesses'])

                    if st.button(f"Atualizar Usuário ID {usuario['id']}"):
                        try:
                            atualizar_usuario(
                                usuario['id'],
                                novo_nome,
                                novo_email,
                                nova_idade,
                                nova_cidade,
                                novos_interesses
                            )
                            st.success(f"Usuário '{novo_nome}' atualizado com sucesso!")
                            #st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar o usuário: {e}")
                else:
                    st.warning("Usuário não encontrado. Verifique o ID ou Nome do usuário e tente novamente.")

        # Exclusão manual de usuários
        with st.expander("Excluir Usuário"):
            excluir_usuario_id = st.text_input("Digite o ID ou Nome do Usuário que deseja excluir:")

            if excluir_usuario_id:
                usuario = None
                try:
                    # Tenta obter o usuário pelo ID
                    usuario_id = int(excluir_usuario_id)
                    usuario = obter_perfil_por_id(usuario_id)
                except ValueError:
                    # Tenta obter o usuário pelo nome
                    usuario = next((u for u in usuarios if u['nome'].lower() == excluir_usuario_id.lower()), None)

                if usuario:
                    # Exibe o checkbox de confirmação
                    confirmar_exclusao = st.checkbox(f"Tem certeza que deseja excluir o usuário '{usuario['nome']}' (ID: {usuario['id']})?", key="confirmar_exclusao_usuario")

                    # Exibe o botão de exclusão se o checkbox for marcado
                    if confirmar_exclusao:
                        if st.button(f"Excluir Usuário '{usuario['nome']}' (ID: {usuario['id']})", key="botao_excluir_usuario"):
                            try:
                                deletar_usuario(usuario['id'])
                                st.success(f"Usuário '{usuario['nome']}' excluído com sucesso!")
                                #st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir o usuário: {e}")
                else:
                    st.error("Usuário não encontrado.")
            else:
                st.write("Insira o ID ou Nome do usuário que deseja excluir.")

    with tab_obras:
         # Dados das obras
        #colunas_obras, obras = listar_obras()
        #df_obras = pd.DataFrame(obras, columns=colunas_obras)

        st.subheader("Obras")

        # Exibe o DataFrame de obras para visualização
        if not df_obras.empty:
            # Conversão de ano_publicacao para numérico, tratando erros e substituindo valores inválidos por NaN
            df_obras['ano_publicacao'] = pd.to_numeric(df_obras['ano_publicacao'], errors='coerce') 

            # Preencher NaN com valor padrão para evitar erros de tipo (por exemplo, ano "0" ou qualquer outro valor padrão)
            df_obras['ano_publicacao'].fillna(0)

            st.write("Tabela de Obras:")
            st.dataframe(df_obras)  # Mostra a tabela com as obras antes dos botões

         # Inserir nova obra
        with st.expander("Adicionar Nova Obra"):
            st.write("Preencha os dados da nova obra:")
            novo_titulo = st.text_input("Título")
            novo_autor = st.text_input("Autor")
            novo_ano = st.number_input("Ano de Publicação", min_value=0000, max_value=2100, step=1, value=2024)
            novo_genero = st.text_input("Gênero")
            if st.button("Salvar Nova Obra"):
                if novo_titulo and novo_autor and novo_ano and novo_genero:
                    inserir_obra(novo_titulo, novo_autor, novo_ano, novo_genero)
                    st.success(f"Obra '{novo_titulo}' adicionada com sucesso!")
                    st.rerun()
                else:
                    st.warning("Todos os campos são obrigatórios para adicionar uma nova obra.")

        # Edição de obra específica
        with st.expander("Editar Obra"):
            st.write("Edite as informações da obra ao inserir o ID ou nome abaixo:")

            # Campo para o ID ou nome da obra a ser editada
            editar_id_obra = st.text_input("Digite o ID ou Nome da Obra que deseja editar:")

            # Filtra a obra com base no ID ou Nome fornecido
            if editar_id_obra:
                obra = None
                try:
                    obra_id = int(editar_id_obra)
                    obra = obter_obra_por_id(obra_id)
                except ValueError:
                    obra = next((o for o in obras if o[1].lower() == editar_id_obra.lower()), None)
                    
                if obra:
                    st.markdown(f"**Obra Selecionada: {obra[1]} (ID: {obra[0]})**")
                    novo_titulo = st.text_input("Editar Título da Obra", value=obra[1])
                    novo_autor = st.text_input("Editar Autor da Obra", value=obra[2])
                    novo_ano = st.number_input("Editar Ano de Publicação da Obra", value=int(obra[3]), step=1)
                    novo_genero = st.text_input("Editar Gênero da Obra", value=obra[4])

                    if st.button(f"Atualizar Obra ID {obra[0]}"):
                        try:
                            atualizar_obra(obra[0], novo_titulo, novo_autor, novo_ano, novo_genero)
                            st.success(f"Obra '{novo_titulo}' atualizada com sucesso!")
                            #st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar a obra: {e}")
                else:
                    st.warning("Obra não encontrada. Verifique o ID ou Nome da obra e tente novamente.")
                    

        # Exclusão manual de obras
        with st.expander("Excluir Obra"):
            excluir_obra_id = st.text_input("Digite o ID ou Nome da Obra que deseja excluir:")

            if excluir_obra_id:
                obra = None
                try:
                    # Tenta obter a obra pelo ID
                    obra_id = int(excluir_obra_id)
                    obra = obter_obra_por_id(obra_id)
                except ValueError:
                    # Tenta obter a obra pelo nome
                    obra = next((o for o in obras if o[1].lower() == excluir_obra_id.lower()), None)

                if obra:
                    # Exibe o checkbox de confirmação
                    confirmar_exclusao = st.checkbox(f"Tem certeza que deseja excluir a obra '{obra[1]}' (ID: {obra[0]})?", key="confirmar_exclusao")

                    # Exibe o botão de exclusão se o checkbox for marcado
                    if confirmar_exclusao:
                        if st.button(f"Excluir Obra '{obra[1]}' (ID: {obra[0]})", key="botao_excluir"):
                            try:
                                deletar_obra(obra[0])
                                st.success(f"Obra '{obra[1]}' excluída com sucesso!")
                                time.sleep(2)
                                #st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir a obra: {e}")
                else:
                    st.error("Obra não encontrada.")
            else:
                st.write("Insira o ID ou Nome da obra que deseja excluir.")


    with tab_roteiros:
        st.subheader("Roteiros")
        # Lista todos os roteiros com informações detalhadas
        roteiros = listar_roteiros_G()
        df_roteiros = pd.DataFrame(roteiros, columns=['Roteiro', 'Nome do Leitor', 'Título da Obra'])  # Defina as colunas

        if not df_roteiros.empty:
            # Exibe o dataframe editável
            st.dataframe(df_roteiros)

            # Exclusão manual de roteiros
            with st.expander("Excluir Roteiro"):
                excluir_roteiro_id = st.text_input("Digite o ID do Roteiro ou o Nome do Usuário ou Título da Obra para excluir:")

                if excluir_roteiro_id:
                    roteiro = None
                    try:
                        # Tenta obter o roteiro pelo ID
                        roteiro_id = int(excluir_roteiro_id)
                        roteiro = next((r for r in roteiros if r[0] == roteiro_id), None)
                    except ValueError:
                        # Tenta obter o roteiro pelo nome do usuário ou título da obra
                        roteiro = next((r for r in roteiros if r[1].lower() == excluir_roteiro_id.lower() or r[2].lower() == excluir_roteiro_id.lower()), None)

                    if roteiro:
                        # Exibe o checkbox de confirmação
                        confirmar_exclusao = st.checkbox(f"Tem certeza que deseja excluir o roteiro de '{roteiro[1]}' para a obra '{roteiro[2]}' (ID: {roteiro[0]})?", key="confirmar_exclusao_roteiro")

                        # Exibe o botão de exclusão se o checkbox for marcado
                        if confirmar_exclusao:
                            if st.button(f"Excluir Roteiro de '{roteiro[1]}' para a obra '{roteiro[2]}'", key="botao_excluir_roteiro"):
                                try:
                                    deletar_roteiro(roteiro[0])
                                    st.success(f"Roteiro de '{roteiro[1]}' para a obra '{roteiro[2]}' excluído com sucesso!")
                                    time.sleep(2)
                                    #st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir o roteiro: {e}")
                    else:
                        st.error("Roteiro não encontrado.")
                else:
                    st.write("Insira o ID do roteiro, Nome do Usuário, ou Título da Obra que deseja excluir.")
        else:
            st.write("Não há roteiros para exibir.")
            
