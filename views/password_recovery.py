import streamlit as st
from user_crud import obter_perfil, atualizar_perfil
from utils.email_utils import send_recovery_email  # type: ignore # Supondo que exista uma função para envio de email

def tela_recuperar_senha():
    st.header("Recuperar Senha")
    email = st.text_input("Digite seu email")

    if st.button("Enviar"):
        perfil = obter_perfil(email)
        if perfil:
            # Gerar um token de recuperação de senha e enviar por email
            recovery_token = "token_de_recuperacao"  # Aqui você pode gerar um token real
            send_recovery_email(email, recovery_token)
            st.success("Email de recuperação enviado. Por favor, verifique sua caixa de entrada.")
        else:
            st.error("Email não encontrado.")
            
def tela_nova_senha():
    st.header("Nova Senha")
    token = st.text_input("Digite o token de recuperação")
    nova_senha = st.text_input("Digite a nova senha", type="password")

    if st.button("Enviar"):
        # Verificar se o token é válido
        if token == "token_de_recuperacao":  # Validação real do token
            email = "email_associado_ao_token"  # Obter o email associado ao token
            perfil = obter_perfil(email)
            if perfil:
                atualizar_perfil(perfil["uid"], senha=nova_senha)
                st.success("Senha alterada com sucesso.")
            else:
                st.error("Perfil não encontrado.")
        else:
            st.error("Token inválido.")
