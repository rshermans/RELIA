import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit as st
from email.mime.image import MIMEImage

# Obter as configurações de email dos segredos do Streamlit
EMAIL_HOST = st.secrets["EMAIL"]["EMAIL_HOST"]
EMAIL_PORT = st.secrets["EMAIL"]["EMAIL_PORT"]
EMAIL_HOST_USER = st.secrets["EMAIL"]["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = st.secrets["EMAIL"]["EMAIL_HOST_PASSWORD"]  # Use a senha de aplicativo aqui
EMAIL_USE_TLS = st.secrets["EMAIL"].get("EMAIL_USE_TLS", True)

def send_recovery_email(to_email, token):
    try:
        # Configurar o servidor de email
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        if EMAIL_USE_TLS:
            server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

        # Criar a mensagem
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = to_email
        msg['Subject'] = "Recuperação de Senha - RELIA"

        # Corpo do email
        body = f"""
        Olá,

        Você solicitou a recuperação da sua senha. Por favor, use o seguinte token para redefinir sua senha:

        Token: {token}

        Se você não solicitou a recuperação de senha, por favor, ignore este email.

        Obrigado,
        Equipe RELIA
        """
        msg.attach(MIMEText(body, 'plain'))

        # Enviar o email
        server.send_message(msg)
        server.quit()

        print(f"Email de recuperação enviado para {to_email}")
    except Exception as e:
        print(f"Erro ao enviar email de recuperação: {e}")
        st.error(f"Erro ao enviar email de recuperação: {e}")



def send_report_email(to_email, subject, html_content, image_attachments=None):
    try:
        # Configurar o servidor de email
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        if EMAIL_USE_TLS:
            server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

        # Criar a mensagem do email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        # Anexar o conteúdo HTML ao email
        msg.attach(MIMEText(html_content, 'html'))

        # Anexar as imagens ao email, se houver
        if image_attachments:
            for attachment in image_attachments:
                with open(attachment["path"], 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', f'<{attachment["cid"]}>')
                    msg.attach(img)

        # Enviar o email
        server.send_message(msg)
        server.quit()

        print(f"Email de relatório enviado para {to_email}")
        #st.success("Relatório enviado para seu email com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar email de relatório: {e}")
        st.error(f"Erro ao enviar email de relatório: {e}")
        
        