import yaml
import streamlit_authenticator as stauth # type: ignore

def load_config():
    config = {
        'credentials': {
            'usernames': {
                'user1': {
                    'name': 'John Doe',
                    'password': stauth.Hasher(['password']).generate()[0]  # Altere 'password' para a senha desejada
                },
                'user2': {
                    'name': 'Jane Doe',
                    'password': stauth.Hasher(['password']).generate()[0]
                }
            }
        },
        'cookie': {
            'expiry_days': 30,
            'key': 'abcdef',
            'name': 'streamlit_auth'
        },
        'preauthorized': {
            'emails': [
                'user1@example.com',
                'user2@example.com'
            ]
        }
    }
    return config

def add_user(username, name, password):
    config = load_config()
    config['credentials']['usernames'][username] = {
        'name': name,
        'password': stauth.Hasher([password]).generate()[0]
    }
    # Salvar config atualizado em um arquivo YAML ou banco de dados

def remove_user(username):
    config = load_config()
    if username in config['credentials']['usernames']:
        del config['credentials']['usernames'][username]
    # Salvar config atualizado em um arquivo YAML ou banco de dados
