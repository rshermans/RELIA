import streamlit as st
import openai
from database import (inserir_checkpoint, obter_checkpoints, atualizar_checkpoint,  inserir_checkpoint,
                      criar_ou_obter_roteiro, 
                      inserir_log_uso, registrar_log_uso, obter_obra_por_id)  # Importe as funções necessárias do banco de dados
import time



# Configuração da API do ChatGPT
openai.api_key = st.secrets["OPENAI"]["OPENAI_API_KEY"]

# Níveis da Taxonomia de Bloom
bloom_niveis = ["Lembrar", "Entender", "Aplicar", "Analisar", "Avaliar", "Criar"]


def gerar_perguntas_para_obra(obra_id):
    # Obter a obra do banco de dados com o ID
    obra = obter_obra_por_id(obra_id)
    if obra:
        texto = obra["texto"]  # Substitua por como você armazena o texto da obra
        perguntas = []

        # Perguntas de Conhecimento
        with st.expander("Conhecimento"):
            # Perguntas que exigem que o usuário recupere informações diretas do texto
            for pergunta_conhecimento in criar_perguntas(texto, "Conhecimento"):
                st.write(pergunta_conhecimento)
                #  Campo de resposta: st.text_input, st.text_area
                resposta_usuario = st.text_input("Sua resposta:")
                # Botão para avaliar a resposta
                if st.button("Avaliar"):
                    # Chamar função avaliar_resposta e exibir feedback
                    pontuacao, feedback = avaliar_resposta(pergunta_conhecimento, resposta_usuario, "Conhecimento")
                    st.write(f"Feedback: {feedback}")
                    st.write(f"Pontuação: {pontuacao}")
                    # Salvar no banco de dados: registrar_checkpoint


        # ... (continue com as demais categorias da Taxonomia de Bloom, utilizando expander para cada nível) 
        return perguntas
    else:
        st.error("Obra não encontrada.")
        return []
    
    
def criar_perguntas(texto, nivel_bloom):
    if nivel_bloom == "Conhecimento":
        #  Extrair informações do texto (nomes de personagens, locais, etc.) 
        doc = nlp(texto)  # Use a biblioteca spaCy para análise do texto
        entidades = [entidade.text for entidade in doc.ents if entidade.label_ == "PER"]  # Ex: Extraia nomes de personagens
        
        # Criar perguntas sobre essas informações:
        perguntas = []
        for entidade in entidades:
            perguntas.append(f"Qual o nome do personagem?") 
            perguntas.append(f"Qual o nome do local?")
        
        return perguntas   


def avaliar_resposta(pergunta, resposta_usuario, nivel_bloom):
    # ... (Lógica para verificar a resposta com base no gabarito)

    # ... (Lógica para chamar a LLM para avaliar a resposta, se necessário)
    
    feedback = "Feedback..." #  Feedback gerado automaticamente pela LLM
    pontuacao = 7 # Pontuação atribuída automaticamente pela LLM
    
    st.write(f"Feedback: {feedback}")
    st.write(f"Pontuação: {pontuacao}")
    return pontuacao, feedback
    
    