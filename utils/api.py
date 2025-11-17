import requests
import streamlit as st
import openai
import google.generativeai as genai #type: ignore
from typing import Optional


# Configurações das APIs

# Configurações das APIs
API_KEY_ANTHROPIC = st.secrets["ANTHROPIC"]["ANTHROPIC_API_KEY"]
API_URL_ANTHROPIC = "https://api.anthropic.com/v1/messages"

API_KEY_GEMINI = st.secrets["GOOGLE"]["GOOGLE_API_KEY"]  # Insira sua chave de API aqui

API_KEY_OPENAI = st.secrets["OPENAI"]["OPENAI_API_KEY"]
openai.api_key = API_KEY_OPENAI

#Chamadas:
#get_openai_response(prompt, model="gpt-4o-mini", max_tokens=1500, retries=3, delay=2, idioma="pt")
#get_anthropic_response(prompt, idioma="pt", max_tokens=2000)

# Função para obter resposta da Anthropic
def get_openai_response(prompt, model="gpt-4o-mini", max_tokens=1500, retries=3, delay=2, idioma="pt-pt"):
    import time

    # Mensagem de sistema que indica qual idioma usar
    system_message = f"Use este idioma para responder: {idioma}"

    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "system", "content": "Você é um assistente útil que cria perguntas educacionais."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                n=1,
                stop=None,
                temperature=0.7,
            )
            try:
                return response.choices[0].message.content.strip()
            except AttributeError:
                return None  # Ou qualquer outro valor adequado para lidar com erros na estrutura da resposta.
        except openai.error.OpenAIError as e:
            print(f"Erro na chamada à API do OpenAI: {e}. Tentativa {attempt + 1} de {retries}.")
            time.sleep(delay)
    print("Falha ao se comunicar com a API do OpenAI após várias tentativas.")
    return None


# Função para obter resposta da OpenAI
def get_openai_response_antiga(prompt, max_tokens=2000):
    if not API_KEY_OPENAI:
        return "A API Key para a OpenAI não está configurada. Não é possível gerar uma resposta."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "Você é RELIA, um assistente útil para sugestões de livros."},  # Identificação como RELIA
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].message['content']
    except openai.error.OpenAIError as e:
        print(f"Erro ao obter resposta da API OpenAI: {e}")
        return None


def get_anthropic_response(prompt, idioma="pt-pt", max_tokens=2000):
    if not API_KEY_ANTHROPIC:
        return "A API Key para a Anthropic não está configurada. Não é possível gerar uma resposta."

    try:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY_ANTHROPIC,
            "anthropic-version": "2023-06-01"
        }
        
        # Incluir o idioma na mensagem
        user_message = f"[{idioma}] RELIA: {prompt}"  # Prefixo indicando o idioma

        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": user_message}]
        }

        # Enviar a requisição
        response = requests.post(API_URL_ANTHROPIC, json=data, headers=headers)
        response.raise_for_status()

        return response.json()['content'][0]['text']
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter resposta da API Anthropic: {e}")
        return None


# Mecanismo de retentativa simples
def retry_request(func, *args, retries=3, **kwargs):
    for attempt in range(retries):
        result = func(*args, **kwargs)
        if result:
            return result
        print(f"Tentativa {attempt + 1} falhou. Tentando novamente...")
    return "Erro: todas as tentativas de requisição falharam."



def get_gemini_response(prompt: str, idioma: str = "pt-pt", max_tokens: int = 2000) -> Optional[str]:
    if not API_KEY_GEMINI:
        return "A API Key para o Google Gemini não está configurada. Não é possível gerar uma resposta."
    
    try:
        genai.configure(api_key=API_KEY_GEMINI)
        model = genai.GenerativeModel('gemini-pro')
        user_message = f"[{idioma}] {prompt}"
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40
        }
        response = model.generate_content(user_message, generation_config=generation_config)
        return response.text
        
    except Exception as e:
        print(f"Erro ao obter resposta da API Gemini: {e}")
        return None
    
