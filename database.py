import sqlite3
import bcrypt
import os
import streamlit as st
from datetime import datetime
import time
import json
import sqlitecloud #type: ignore
from sqlitecloud import IntegrityError, OperationalError #type: ignore
import pandas as pd  # Adicionar este import
import numpy as np   # Também útil para operações com dados

# Obtenha o diretório do script atual
#current_dir = os.path.dirname(os.path.abspath(__file__))

# Defina o caminho do banco de dados
#DB_PATH = os.path.join(current_dir, 'relia.db')
#print(f"Banco de dados localizado em: {DB_PATH}")  # Log para depuração

#SQLITE_CLOUD_CONNECTION_STRING = "sqlitecloud://cajmhcgwhz.sqlite.cloud:8860?apikey=pVKmEORux6vXehMrvbGCzUog5UHsQTDw5EjB9esWfOo"
# Configuração básica

# Configuração do SQLite Cloud
SQLITE_CLOUD_CONNECTION_STRING = st.secrets["SQLITE_CLOUD"]["CONNECTION_STRING"]
DATABASE_NAME = "relia.db" # Nome do banco no SQLite Cloud


def get_db_connection():
    """Estabelece conexão com o SQLite Cloud."""
    try:
        conn = sqlitecloud.connect(SQLITE_CLOUD_CONNECTION_STRING)
        conn.execute(f"USE DATABASE {DATABASE_NAME}")
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        raise

"""def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn"""

def setup_database():
    conn = get_db_connection()
    """ with conn:
         # Use a base de dados correta
        #db_name = "relia.db"  # Substituir pelo nome do banco que está na conexão
        #conn.execute(f"USE DATABASE {db_name}")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                idade INTEGER,
                cidade TEXT,
                interesses TEXT, 
                nivel_educacional TEXT,
                habito_leitura TEXT,
                opcao_compartilhar INTEGER,
                criado_em TEXT DEFAULT (DATETIME('now', 'localtime')),
                ultima_atualizacao TEXT DEFAULT (DATETIME('now', 'localtime'))
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS obras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                ano_publicacao INTEGER,
                genero TEXT
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roteiro_id INTEGER NOT NULL,
                acao_id INTEGER NOT NULL,
                nivel_taxonomia TEXT,
                pergunta TEXT NOT NULL,
                resposta TEXT NOT NULL,
                nota_llm INTEGER,
                feedback_llm TEXT,
                data_hora TEXT DEFAULT (DATETIME('now', 'localtime')),
                FOREIGN KEY (roteiro_id) REFERENCES roteiros(id)
            );
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS roteiros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            obra_id INTEGER NOT NULL,
            usuario_id INTEGER,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'ativo',
            FOREIGN KEY (obra_id) REFERENCES obras(id)
        );
    ''')
    
        conn.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roteiro_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (roteiro_id) REFERENCES roteiros(id)
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS logs_uso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER, 
                acao TEXT NOT NULL,
                data_hora TEXT DEFAULT (DATETIME('now', 'localtime')),
                detalhes TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS acoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nomes_acao TEXT NOT NULL,
                nivel_bloom TEXT NOT NULL,
                pontos INTEGER NOT NULL,
                tipo_resposta TEXT NOT NULL,
                template_pergunta TEXT NOT NULL,
                respostas_esperadas TEXT
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback_automatizado (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roteiro_id INTEGER NOT NULL,
                resumo_checkpoints TEXT,
                feedback_motivacional TEXT,
                recomendacoes TEXT,
                insights TEXT,
                data_geracao TEXT DEFAULT (DATETIME('now', 'localtime')),
                FOREIGN KEY (roteiro_id) REFERENCES roteiros(id)
            );
        ''')
        
        conn.commit()"""
        
    print("Banco de dados configurado com sucesso.")
        
    
def hash_password(password: str)-> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed


def check_password(hashed_password, password):
    #return password
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


# Decorador para garantir o fechamento da conexão e tratamento de erros
def db_operation(func):
    def wrapper(*args, **kwargs):
        conn = get_db_connection()
        try:
            return func(conn, *args, **kwargs)
        except IntegrityError as e:
            print(st.error(f"Erro de integridade no banco de dados: {e}", disabled=True))
        except OperationalError as e:
            print(st.error(f"Erro operacional ao executar a operação no banco de dados: {e}", disabled=True))
        finally:
            conn.close()
    return wrapper


@db_operation
def inserir_perfil_login(conn, nome, email, senha, idade, cidade, interesses, nivel_educacional, habito_leitura, opcao_compartilhar):
    """
    Insere um novo perfil de usuário na base de dados.
    """
    cursor = conn.cursor()
    # Hash da senha
    senha_hash = hash_password(senha)

    # Log temporário (REMOVER EM PRODUÇÃO)
    #print(f"Hash da senha para {email}: {senha_hash}")
    
    try:
        cursor.execute('''
            INSERT INTO usuarios (
                nome, email, senha, idade, cidade, interesses, nivel_educacional, habito_leitura, opcao_compartilhar
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            nome,
            email,
            senha_hash,  # Armazena o hash da senha
            idade,
            cidade,
            interesses,
            nivel_educacional,
            habito_leitura,
            opcao_compartilhar
        ))
        conn.commit()
    except sqlitecloud.IntegrityError as e:
        print(f"Erro ao inserir perfil: {e}")
    finally:
        conn.close()


@db_operation
def inserir_perfil(conn, nome, email, senha, idade, cidade, interesses, opcao_compartilhar):
    """
    Insere um novo perfil de usuário na base de dados.
    """
    cursor = conn.cursor()
    # Hash da senha
    hashed = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
    hashed_string = hashed.decode('utf-8')  # Converte de bytes para string
    
    cursor.execute('''
        INSERT INTO usuarios (nome, email, senha, idade, cidade, interesses, opcao_compartilhar)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (nome, email, senha, idade, cidade, interesses, opcao_compartilhar))
    conn.commit()
    return cursor.lastrowid  # Retorna o ID do perfil inserido


def obter_perfil(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
    row = cursor.fetchone()
    
    if row:
        columns = [column[0] for column in cursor.description]
        perfil = dict(zip(columns, row))  # Converte o resultado da consulta em um dicionário
        return perfil
    return None

def obter_perfil_por_id(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (id,))
        row = cursor.fetchone()

        if row:
            columns = [column[0] for column in cursor.description]
            perfil = dict(zip(columns, row))  # Converte o resultado da consulta em um dicionário
            return perfil
    except Exception as e:
        print(f"Erro ao obter perfil por ID: {e}")
    finally:
        if conn:
            conn.close()
    return None


def atualizar_perfil(uid, nome=None, email=None, senha=None, idade=None, cidade=None, interesses=None, nivel_educacional=None, habito_leitura=None, opcao_compartilhar=None):
    conn = get_db_connection()
    campos = []
    valores = []
    if nome:
        campos.append("nome = ?")
        valores.append(nome)
    if email:
        campos.append("email = ?")
        valores.append(email)
    if senha:
        campos.append("senha = ?")
        valores.append(hash_password(senha))
    if idade:
        campos.append("idade = ?")
        valores.append(idade)
    if cidade:
        campos.append("cidade = ?")
        valores.append(cidade)
    if interesses:
        campos.append("interesses = ?")
        valores.append(interesses)
    if nivel_educacional:
        campos.append("nivel_educacional = ?")
        valores.append(nivel_educacional)
    if habito_leitura:
        campos.append("habito_leitura = ?")
        valores.append(habito_leitura)
    if opcao_compartilhar is not None:
        campos.append("opcao_compartilhar = ?")
        valores.append(opcao_compartilhar)
    
    valores.append(uid)
    sql = f"UPDATE usuarios SET {', '.join(campos)}, ultima_atualizacao = DATETIME('now', 'localtime') WHERE uid = ?"
    
    try:
        conn.execute(sql, valores)
        conn.commit()
    except sqlitecloud.IntegrityError as e:
        print(f"Erro ao atualizar perfil: {e}")
    finally:
        conn.close()

def excluir_perfil(uid):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM usuarios WHERE uid = ?', (uid,))
        conn.commit()
    except sqlitecloud.IntegrityError as e:
        print(f"Erro ao excluir perfil: {e}")
    finally:
        conn.close()
        

#CRUD Usuarios:

@db_operation
def obter_usuarios(conn):
    obras = conn.execute('SELECT * FROM usuarios').fetchall()
    return obras


def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios')
    colunas = [description[0] for description in cursor.description]
    usuarios = cursor.fetchall()
    conn.close()
    return colunas, usuarios


def listar_usuarios_indice():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios')
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios


def atualizar_usuario_4itens(id, nome, idade, cidade):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE usuarios SET nome=?, idade=?, cidade=? WHERE id=?', (nome, idade, cidade, id))
    conn.commit()
    conn.close()


@db_operation
def deletar_usuario(conn, id):
    try:
        # Buscar o nome do usuário pelo ID antes de excluir
        cursor = conn.cursor()
        cursor.execute('SELECT nome FROM usuarios WHERE id=?', (id,))
        usuario = cursor.fetchone()

        if usuario:
            nome_usuario = usuario[0]

            # Excluir o usuário
            cursor.execute('DELETE FROM usuarios WHERE id=?', (id,))
            conn.commit()

            # Mensagem de sucesso com o nome do usuário
            st.success(f"Usuário '{nome_usuario}' excluído com sucesso!")
        else:
            st.warning("Usuário não encontrado.")

    except sqlitecloud.Error as e:
        st.error(f"Erro ao excluir usuário: {e}")


@db_operation
def atualizar_usuario(conn, usuario_id, nome=None, email=None, idade=None, cidade=None, interesses=None):
    """
    Atualiza as informações de um usuário existente.
    """
    campos = []
    valores = []
    if nome:
        campos.append("nome = ?")
        valores.append(nome)
    if email:
        campos.append("email = ?")
        valores.append(email)
    if idade:
        campos.append("idade = ?")
        valores.append(idade)
    if cidade:
        campos.append("cidade = ?")
        valores.append(cidade)
    if interesses:
        campos.append("interesses = ?")
        valores.append(interesses)
    
    valores.append(usuario_id)
    sql = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"
    conn.execute(sql, valores)
    conn.commit()
 
    
@db_operation
def atualizar_usuario_Perfil(conn, usuario_id, nome=None, email=None, idade=None, cidade=None, interesses=None, nivel_educacional=None, habito_leitura=None, opcao_compartilhar=None):
    """
    Atualiza as informações de um usuário existente.
    """
    campos = []
    valores = []
    if nome:
        campos.append("nome = ?")
        valores.append(nome)
    if email:
        campos.append("email = ?")
        valores.append(email)
    if idade:
        campos.append("idade = ?")
        valores.append(idade)
    if cidade:
        campos.append("cidade = ?")
        valores.append(cidade)
    if interesses:
        campos.append("interesses = ?")
        valores.append(interesses)
    if nivel_educacional:
        campos.append("nivel_educacional = ?")
        valores.append(nivel_educacional)
    if habito_leitura:
        campos.append("habito_leitura = ?")
        valores.append(habito_leitura)
    if opcao_compartilhar is not None:
        campos.append("opcao_compartilhar = ?")
        valores.append(int(opcao_compartilhar))  # Converte para int (0 ou 1)

    valores.append(usuario_id)
    sql = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"
    conn.execute(sql, valores)
    conn.commit()
    
    
#CRUD OBRAS

@db_operation
def inserir_obra(conn, titulo, autor, ano_publicacao, genero):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO obras (titulo, autor, ano_publicacao, genero)
        VALUES (?, ?, ?, ?)
    ''', (titulo, autor, ano_publicacao, genero))
    conn.commit()
    return cursor.lastrowid  # Retorna o ID da obra inserida

@db_operation
def obter_obras(conn):
    obras = conn.execute('SELECT * FROM obras').fetchall()
    return obras

@db_operation
def obter_obra_por_id(conn, obra_id):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM obras WHERE id = ?', (obra_id,))
    row = cursor.fetchone()

    if row:
        columns = [column[0] for column in cursor.description]
        obra = dict(zip(columns, row))
        return obra
    return None

@db_operation
def atualizar_obra(conn, obra_id, titulo=None, autor=None, ano_publicacao=None, genero=None):
    campos = []
    valores = []
    if titulo:
        campos.append("titulo = ?")
        valores.append(titulo)
    if autor:
        campos.append("autor = ?")
        valores.append(autor)
    if ano_publicacao:
        campos.append("ano_publicacao = ?")
        valores.append(ano_publicacao)
    if genero:
        campos.append("genero = ?")
        valores.append(genero)
    
    valores.append(obra_id)
    sql = f"UPDATE obras SET {', '.join(campos)} WHERE id = ?"
    conn.execute(sql, valores)
    conn.commit()

@db_operation
def excluir_obra(conn, obra_id):
    conn.execute('DELETE FROM obras WHERE id = ?', (obra_id,))
    conn.commit()


@db_operation
def listar_obras(conn):
    """
    Lista todas as obras presentes na base de dados.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM obras')
    rows = cursor.fetchall()
    
    if rows:
        colunas = [description[0] for description in cursor.description]
        columns = [column[0] for column in cursor.description]
        obras = [dict(zip(columns, row)) for row in rows]
        return colunas,obras
    
    return[]


@db_operation
def listar_obras_indice(conn):
    """
    Lista todas as obras presentes na base de dados.
    """
    obras = conn.execute('SELECT * FROM obras').fetchall()
    return obras


@db_operation
def atualizar_obra(conn, obra_id, titulo=None, autor=None, ano_publicacao=None, genero=None):
    """
    Atualiza as informações de uma obra existente.
    """
    campos = []
    valores = []
    if titulo:
        campos.append("titulo = ?")
        valores.append(titulo)
    if autor:
        campos.append("autor = ?")
        valores.append(autor)
    if ano_publicacao:
        campos.append("ano_publicacao = ?")
        valores.append(ano_publicacao)
    if genero:
        campos.append("genero = ?")
        valores.append(genero)
    
    valores.append(obra_id)
    sql = f"UPDATE obras SET {', '.join(campos)} WHERE id = ?"
    
    conn.execute(sql, valores)
    conn.commit()


@db_operation
def deletar_obra(conn, obra_id):
    """
    Deleta uma obra da base de dados.
    """
    conn.execute('DELETE FROM obras WHERE id = ?', (obra_id,))
    conn.commit()


#CRUD LOGS USUARIO


@db_operation
def inserir_log_uso(conn, usuario_id, acao, detalhes=None):
    """
    Insere um log de uso no banco de dados.
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs_uso (usuario_id, acao, detalhes)
        VALUES (?, ?, ?)
    ''', (usuario_id, acao, detalhes))
    conn.commit()
    log_id = cursor.lastrowid  # Obtém o ID do log inserido
    return log_id


def registrar_log_uso(acao, usuario_id, detalhes=""):
    """
    Função para registrar logs de uso na tabela de logs.
    """
    try:
        inserir_log_uso(usuario_id, acao, detalhes)
    except Exception as e:
        st.error(f"Erro ao registrar log de uso: {e}")
        print(f"Exception ao registrar log de uso: {e}")
        

@db_operation
def obter_logs_uso(conn, usuario_id=None):
    """
    Obtém todos os logs de uso do banco de dados, filtrando pelo ID do usuário se fornecido.
    """
    if usuario_id:
        cursor = conn.execute('SELECT * FROM logs_uso WHERE usuario_id = ?', (usuario_id,))
    else:
        cursor = conn.execute('SELECT * FROM logs_uso')
    logs = cursor.fetchall()
    return logs

@db_operation
def excluir_log_uso(conn, log_id):
    """
    Exclui um log de uso do banco de dados pelo ID do log.
    """
    conn.execute('DELETE FROM logs_uso WHERE id = ?', (log_id,))
    conn.commit()


def iniciar_timer(acao):
    """
    Inicia o timer para registrar o tempo de uso em uma tela específica.
    """
    if "tempo_inicio" not in st.session_state:
        st.session_state["tempo_inicio"] = datetime.now()
    st.session_state["acao"] = acao
    

def finalizar_timer():
    """
    Finaliza o timer e registra o log de uso no banco de dados.
    """
    if "tempo_inicio" in st.session_state:
        tempo_fim = datetime.now()
        tempo_uso = (tempo_fim - st.session_state["tempo_inicio"]).total_seconds()
        usuario_id = st.session_state.get("usuario_id", None)
        acao = st.session_state.get("acao", "Ação desconhecida")

        # Registrar log de uso com detalhes
        detalhes = f"Tempo de uso: {tempo_uso} segundos"
        if usuario_id:
            inserir_log_uso(usuario_id, acao, detalhes)
        else:
            st.warning("Não foi possível registrar o log de uso: usuário não logado.")

        # Limpar estado do timer
        del st.session_state["tempo_inicio"]
        del st.session_state["acao"]
        

#CRUD CHECKPOINT

@db_operation
def inserir_checkpoint(conn, roteiro_id, acao_id, nivel_taxonomia, pergunta, resposta, nota_llm=None, feedback_llm=None):
    """
    Insere um novo checkpoint na tabela 'checkpoints'.

    Args:
        conn (sqlitecloud.Connection): Conexão com o banco de dados.
        roteiro_id (int): ID do roteiro.
        acao_id (int): ID da ação.
        nivel_taxonomia (str): Nível da Taxonomia de Bloom.
        pergunta (str): Pergunta gerada.
        resposta (str): Resposta do usuário.
        nota_llm (int): Pontuação atribuída pela LLM.
        feedback_llm (str): Feedback gerado pela LLM.

    Returns:
        None
    """
    try:
        conn.execute('''
            INSERT INTO checkpoints (roteiro_id, acao_id, nivel_taxonomia, pergunta, resposta, nota_llm, feedback_llm)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (roteiro_id, acao_id, nivel_taxonomia, pergunta, resposta, nota_llm, feedback_llm))
        conn.commit()
    except Exception as e:
        st.error(f"Erro ao inserir checkpoint: {e}")

@db_operation
def obter_checkpoints(conn, roteiro_id):
    """
    Obtém todos os checkpoints associados a um roteiro específico.
    
    Args:
        conn: Conexão com o banco de dados
        roteiro_id: ID do roteiro
        
    Returns:
        list: Lista de dicionários com os dados dos checkpoints
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.roteiro_id, c.acao_id, c.nivel_taxonomia, 
                   c.pergunta, c.resposta, c.nota_llm, c.feedback_llm, 
                   c.data_hora
            FROM checkpoints c 
            WHERE c.roteiro_id = ?
        ''', (roteiro_id,))
        
        # Obter os nomes das colunas
        columns = [description[0] for description in cursor.description]
        
        # Converter os resultados em lista de dicionários
        checkpoints = []
        rows = cursor.fetchall()
        
        if not rows:
            return []  # Retorna lista vazia se não houver resultados
            
        for row in rows:
            checkpoint = dict(zip(columns, row))
            # Converter None para 0 na nota_llm para evitar problemas com sum()
            checkpoint['nota_llm'] = checkpoint.get('nota_llm', 0) or 0
            checkpoints.append(checkpoint)
            
        return checkpoints
        
    except Exception as e:
        st.error(f"Erro ao obter checkpoints: {e}")
        return []  # Retorna lista vazia em caso de erro


@db_operation
def atualizar_checkpoint(conn, checkpoint_id, nota_llm=None, feedback_llm=None):
    """
    Atualiza um checkpoint existente na base de dados.
    """
    try:
        conn.execute('''
            UPDATE checkpoints 
            SET nota_llm = ?, feedback_llm = ?
            WHERE id = ?
        ''', (nota_llm, feedback_llm, checkpoint_id))
        conn.commit()
    except Exception as e:
        st.error(f"Erro ao atualizar checkpoint: {e}")

@db_operation
def excluir_checkpoint(conn, checkpoint_id):
    """
    Exclui um checkpoint da base de dados.
    """
    try:
        conn.execute('DELETE FROM checkpoints WHERE id = ?', (checkpoint_id,))
        conn.commit()
    except Exception as e:
        st.error(f"Erro ao excluir checkpoint: {e}")

@db_operation
def inserir_checkpoint(conn, roteiro_id, acao_id, nivel_taxonomia, pergunta, resposta, nota_llm, feedback_llm):
    """Insere um checkpoint na base de dados."""
    conn.execute('''
        INSERT INTO checkpoints (roteiro_id, acao_id, nivel_taxonomia, pergunta, resposta, nota_llm, feedback_llm)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (roteiro_id, acao_id, nivel_taxonomia, pergunta, resposta, nota_llm, feedback_llm))
    conn.commit()


#Funções sobre roteiros:
    
@db_operation
def listar_roteiros(conn):
    query = """
    SELECT 
        r.id as roteiro_id,
        u.nome as usuario_nome,
        o.titulo as obra_titulo
    FROM 
        roteiros r
    JOIN 
        usuarios u ON r.usuario_id = u.id
    JOIN 
        obras o ON r.obra_id = o.id
    """
    cursor = conn.execute(query)
    rows = cursor.fetchall()

    # Converte cada linha em um dicionário
    columns = [column[0] for column in cursor.description]
    roteiros = [dict(zip(columns, row)) for row in rows]
    return roteiros


def listar_roteiros_indice():
    """
    Lista todos os roteiros presentes na base de dados.
    """
    conn = get_db_connection()
    roteiros = conn.execute('SELECT * FROM roteiros').fetchall()
    return roteiros


@db_operation
def listar_roteiros_G(conn):
    """
    Lista todos os roteiros, incluindo o nome do usuário e o título da obra.
    """
    cursor = conn.cursor()
    # Realiza um join entre as tabelas para obter o nome do usuário e o título da obra
    cursor.execute('''
        SELECT r.id AS roteiro_id, u.nome AS usuario_nome, o.titulo AS obra_titulo
        FROM roteiros r
        JOIN usuarios u ON r.usuario_id = u.id
        JOIN obras o ON r.obra_id = o.id
    ''')
    roteiros = cursor.fetchall()
    return roteiros

@db_operation
def atualizar_roteiro(conn, roteiro_id, obra_id=None, usuario_id=None):
    """
    Atualiza as informações de um roteiro existente.
    """
    campos = []
    valores = []
    if obra_id:
        campos.append("obra_id = ?")
        valores.append(obra_id)
    if usuario_id:
        campos.append("usuario_id = ?")
        valores.append(usuario_id)
    
    valores.append(roteiro_id)
    sql = f"UPDATE roteiros SET {', '.join(campos)} WHERE id = ?"
    
    conn.execute(sql, valores)
    conn.commit()


@db_operation
def deletar_roteiro(conn, roteiro_id):
    """
    Deleta um roteiro da base de dados.
    """
    conn.execute('DELETE FROM roteiros WHERE id = ?', (roteiro_id,))
    conn.commit()



@db_operation
def criar_roteiro(conn, obra_id, usuario_id):
    """
    Cria um roteiro associado à obra e ao usuário e retorna o ID do roteiro.
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO roteiros (obra_id, usuario_id)
        VALUES (?, ?)
    ''', (obra_id, usuario_id))
    conn.commit()
    roteiro_id = cursor.lastrowid  # Obtém o ID do roteiro inserido
    return roteiro_id


@db_operation
def obter_roteiro_por_usuario(conn, usuario_id):
    cursor = conn.execute('SELECT * FROM roteiros WHERE usuario_id = ?', (usuario_id,))
    rows = cursor.fetchall()

    # Converte cada linha em um dicionário
    columns = [column[0] for column in cursor.description]
    roteiros = [dict(zip(columns, row)) for row in rows]
    return roteiros


@db_operation
def excluir_roteiro(conn, roteiro_id):
    conn.execute('DELETE FROM roteiros WHERE id = ?', (roteiro_id,))
    conn.commit()


@db_operation
def obter_roteiros_por_usuario(conn, usuario_id):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM roteiros WHERE usuario_id = ?', (usuario_id,))
    rows = cursor.fetchall()

    if rows:
        columns = [column[0] for column in cursor.description]
        roteiros = [dict(zip(columns, row)) for row in rows]
        return roteiros
    return []

#CRUD'S Diversos


@db_operation
def obter_categorias_unicas(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT genero FROM obras WHERE genero IS NOT NULL AND genero != ""')
    categorias = [row[0] for row in cursor.fetchall()]
    return categorias


@db_operation
def obter_categorias_unicas(conn, usuario_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT obras.genero 
        FROM obras 
        INNER JOIN roteiros ON obras.id = roteiros.obra_id
        WHERE obras.genero IS NOT NULL 
          AND obras.genero != ''
          AND roteiros.usuario_id = ?
    ''', (usuario_id,))
    categorias = [row[0] for row in cursor.fetchall()]
    return categorias


@db_operation
def listar_obras_com_roteiros(conn):
    query = """
    SELECT 
        o.id as obra_id,
        o.titulo as obra_titulo,
        COUNT(r.id) as quantidade_roteiros
    FROM 
        obras o
    LEFT JOIN 
        roteiros r ON o.id = r.obra_id
    GROUP BY 
        o.id, o.titulo
    ORDER BY 
        quantidade_roteiros DESC
    """
    cursor = conn.execute(query)
    colunas = [description[0] for description in cursor.description]
    obras = cursor.fetchall()
    return colunas, obras


@db_operation
def obter_obra_por_titulo_autor(conn, titulo, autor):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM obras WHERE titulo = ? AND autor = ?', (titulo, autor))
    row = cursor.fetchone()

    if row:
        # Converte a tupla retornada em um dicionário, utilizando os nomes das colunas
        columns = [column[0] for column in cursor.description]
        obra = dict(zip(columns, row))
        return obra
    return None


def inserir_mensagem_chat(roteiro_id, role, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_messages (roteiro_id, role, content)
        VALUES (?, ?, ?)
    ''', (roteiro_id, role, content))
    conn.commit()
    conn.close()
    

@db_operation    
def obter_mensagens_chat_V1(conn,roteiro_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content, timestamp FROM chat_messages
        WHERE roteiro_id = ?
        ORDER BY timestamp ASC
    ''', (roteiro_id,))
    mensagens = cursor.fetchall()
    conn.close()
    return mensagens

def obter_mensagens_chat(roteiro_id):
    try:
        conn = get_db_connection()
        mensagens = conn.execute('SELECT role, content, timestamp FROM chat_messages WHERE roteiro_id = ?', (roteiro_id,)).fetchall()
        return mensagens
    except Exception as e:
        st.error(f"Erro ao recuperar mensagens de chat: {e}")
        return []

#@db_operation
def criar_novo_roteiro(obra_id, usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO roteiros (obra_id, usuario_id)
        VALUES (?, ?)
    ''', (obra_id, usuario_id))
    roteiro_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": roteiro_id, "obra_id": obra_id, "usuario_id": usuario_id}

#@db_operation
def obter_roteiro(obra_id, usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM roteiros
        WHERE obra_id = ? AND usuario_id = ?
    ''', (obra_id, usuario_id))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None


#@db_operation
def criar_ou_obter_roteiro(obra_id, usuario_id):
    roteiro_id = obter_roteiro(obra_id, usuario_id)
    if roteiro_id:
        return roteiro_id
    else:
        return criar_novo_roteiro(obra_id, usuario_id)
    
    
def perfil_completo(usuario):
    """Verifica se o perfil do usuário está completo."""
    campos_obrigatorios = ['idade', 'cidade', 'interesses']
    for campo in campos_obrigatorios:
        if not usuario.get(campo):
            return False
    return True


def exibir_alerta_perfil():
    st.warning("Seu perfil está incompleto. Por favor, atualize seu perfil na barra lateral para continuar.")
    st.session_state["tela"] = "perfil"

    # Contagem regressiva de 5 segundos
    countdown = 5
    for i in range(countdown, 0, -1):
        st.write(f"Redirecionando para a atualização do perfil em {i} segundos...")
        time.sleep(1)
        st.rerun()
    
    
@db_operation
def obter_acao_por_id(conn, acao_id):
    """
    Recupera os dados da ação com base no 'acao_id'.

    Args:
        conn (sqlitecloud.Connection): Conexão com o banco de dados.
        acao_id (int): ID da ação.

    Returns:
        dict: Dicionário contendo 'descricao' e 'nome' da ação, ou None se não encontrado.
    """
    cursor = conn.cursor()
    query = "SELECT descricao, nome FROM acoes WHERE id = ?"
    cursor.execute(query, (acao_id,))
    resultado = cursor.fetchone()
    if resultado:
        columns = [column[0] for column in cursor.description]
        acao = dict(zip(columns, resultado))
        return acao
        #return {"descricao": resultado[0], "nome": resultado[1]}
    else:
        st.error(f"Ação com ID {acao_id} não encontrada.")
        return None
    

@db_operation
def obter_nome_acao_por_id(conn, acao_id):
    """
    Recupera os nome da ação com base no 'acao_id'.

    Args:
        conn (sqlitecloud.Connection): Conexão com o banco de dados.
        acao_id (int): ID da ação.

    Returns:
        dict: Dicionário contendo 'nomes_acao' da ação, ou None se não encontrado.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT nomes_acao FROM acoes WHERE id = ?', (acao_id,))
    resultado = cursor.fetchone()
    return resultado[0] if resultado else "Ação Desconhecida"


@db_operation
def obter_acao_id_por_nome(conn, nome_acao):
    cursor = conn.cursor()
    query = "SELECT id FROM acoes WHERE nome = ?"
    cursor.execute(query, (nome_acao,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]  # Retorna o 'id' da ação
    else:
        st.error(f"Ação '{nome_acao}' não encontrada na tabela 'acoes'.")
        return None


def encontrar_acao_checkpoint(conn, nivel_bloom, pontuacao_total):
    """
    Consulta a tabela 'acoes' para encontrar a ação adequada com base no nível de Bloom e pontuação total.

    Args:
        conn (sqlitecloud.Connection): Conexão com o banco de dados.
        nivel_bloom (str): Nível atual da Taxonomia de Bloom.
        pontuacao_total (int): Pontuação total do usuário.

    Returns:
        tuple: (acao_id, pontos_acao, tipo_resposta) ou (None, None, None) se não encontrar.
    """
    cursor = conn.cursor()
    
    # Exemplo de lógica:
    # Seleciona a ação com o nível de Bloom correspondente e os pontos mais próximos ou necessários.
    # Ajuste a lógica conforme as necessidades do seu sistema.

    query = """
    SELECT id, pontos, tipo_resposta 
    FROM acoes 
    WHERE nivel_bloom = ? AND pontos > ? 
    ORDER BY pontos ASC
    LIMIT 1
    """
    cursor.execute(query, (nivel_bloom,))
    resultado = cursor.fetchone()

    if resultado:
        acao_id, pontos_acao, tipo_resposta = resultado
        return (acao_id, pontos_acao, tipo_resposta)
    else:
        st.error(f"Não foi encontrada uma ação para o nível de Bloom '{nivel_bloom}'.")
        return (None, None, None)
    
    
@db_operation
def obter_roteiro_id_inicial(conn, usuario_id):
    """
    Obtém o roteiro_id inicial para o usuário. Se não existir, cria um novo roteiro.

    Args:
        conn (sqlitecloud.Connection): Conexão com o banco de dados.
        usuario_id (int): ID único do usuário.

    Returns:
        int: ID do roteiro.
    """
    cursor = conn.cursor()

    # Verifica se já existe um roteiro ativo para o usuário
    cursor.execute("""
        SELECT id FROM roteiros
        WHERE usuario_id = ? AND status = 'ativo'
        LIMIT 1
    """, (usuario_id,))
    resultado = cursor.fetchone()

    if resultado:
        roteiro_id = resultado[0]
        st.write(f"Roteiro existente encontrado: ID {roteiro_id}")
    else:
        # Cria um novo roteiro
        cursor.execute("""
            INSERT INTO roteiros (usuario_id, status)
            VALUES (?, 'ativo')
        """, (usuario_id,))
        conn.commit()
        roteiro_id = cursor.lastrowid
        st.write(f"Novo roteiro criado: ID {roteiro_id}")

    return roteiro_id    


def carregar_dados_banco(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nomes_acao, nivel_bloom, pontos, tipo_resposta, template_pergunta, respostas_esperadas 
        FROM acoes
    """)
    acoes = cursor.fetchall()
    acoes_niveis = {
        acao[0]: {
            'nomes_acao': acao[1],
            'nivel_bloom': acao[2],
            'pontos': acao[3],
            'tipo_resposta': acao[4],
            'template_pergunta': acao[5],
            'respostas_esperadas': acao[6]
        }
        for acao in acoes
    }
    return acoes_niveis



def determinar_nivel_bloom(pontuacao):
    """
    Determina o nível de proficiência com base na pontuação.
    """
    if pontuacao <= 15:
        return "Lembrar"
    elif pontuacao <= 45:
        return "Compreender"
    elif pontuacao <= 91:
        return "Aplicar"
    elif pontuacao <= 153:
        return "Analisar"
    elif pontuacao <= 190:
        return "Avaliar"
    else:
        return "Criar"


# ------------------ Sobre Feedback ------------------------

# Função para salvar feedback automatizado
@db_operation
def salvar_feedback_automatizado(conn, roteiro_id, resumo_checkpoints, feedback_motivacional, recomendacoes, insights):
    try:
        # Converter variáveis para JSON (string), caso sejam listas ou dicionários
        if isinstance(resumo_checkpoints, (list, dict)):
            resumo_checkpoints = json.dumps(resumo_checkpoints, ensure_ascii=False)

        if isinstance(feedback_motivacional, (list, dict)):
            feedback_motivacional = json.dumps(feedback_motivacional, ensure_ascii=False)

        if isinstance(recomendacoes, (list, dict)):
            recomendacoes = json.dumps(recomendacoes, ensure_ascii=False)

        if isinstance(insights, (list, dict)):
            insights = json.dumps(insights, ensure_ascii=False)

        # Salvando os dados no banco de dados
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO feedback_automatizado (roteiro_id, resumo_checkpoints, feedback_motivacional, recomendacoes, insights)
            VALUES (?, ?, ?, ?, ?)
        ''', (roteiro_id, resumo_checkpoints, feedback_motivacional, recomendacoes, insights))
        conn.commit()
        
        print("Feedback automatizado salvo com sucesso")
    except Exception as e:
        print(f"Erro ao salvar feedback automatizado no banco de dados: {e}")

    
@db_operation
def log_erro(conn, usuario_id, detalhes):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs_uso (usuario_id, acao, detalhes)
        VALUES (?, ?, ?)
    ''', (usuario_id, 'erro', detalhes))
    conn.commit()
    

# Função para atualizar feedback automatizado   
@db_operation
def atualizar_feedback_automatizado(conn,roteiro_id, resumo_checkpoints, feedback_motivacional, recomendacoes, insights):
    try:
        cursor = conn.cursor()
        
        # Converter listas para JSON, se necessário
        if isinstance(recomendacoes, list):
            recomendacoes = json.dumps(recomendacoes)
        if isinstance(insights, list):
            insights = json.dumps(insights)
   
        cursor.execute('''
            UPDATE feedback_automatizado
            SET resumo_checkpoints = ?, feedback_motivacional = ?, recomendacoes = ?, insights = ?
            WHERE roteiro_id = ?
        ''', (resumo_checkpoints, feedback_motivacional, recomendacoes, insights, roteiro_id))
        conn.commit()
        
    except Exception as e:
        print(f"Erro ao atualizar feedback automatizado no banco de dados: {e}")
    

def convert_row_to_dict(cursor, row):
    """
    Converte uma linha de resultado do SQLite Cloud em um dicionário.
    
    Args:
        cursor: Cursor do banco de dados
        row: Linha de resultado
        
    Returns:
        dict: Dicionário com os dados da linha
    """
    if not row:
        return None
    return dict(zip([col[0] for col in cursor.description], row))

def convert_rows_to_dicts(cursor, rows):
    """
    Converte múltiplas linhas de resultado em lista de dicionários.
    
    Args:
        cursor: Cursor do banco de dados
        rows: Lista de linhas de resultado
        
    Returns:
        list: Lista de dicionários com os dados
    """
    if not rows:
        return []
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


# Exemplo de uso em uma função do banco de dados
"""@db_operation
def obter_dados_exemplo(conn, id):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tabela WHERE id = ?', (id,))
    row = cursor.fetchone()
    return convert_row_to_dict(cursor, row)"""


@db_operation
def carregar_usuarios_detalhados(conn):
    """
    Carrega dados detalhados dos usuários incluindo métricas de uso e progresso.
    
    Returns:
        pd.DataFrame: DataFrame com informações detalhadas dos usuários
    """
    try:
        cursor = conn.cursor()
        query = """
        SELECT 
            u.id,
            u.nome,
            u.email,
            u.idade,
            u.cidade,
            u.nivel_educacional,
            u.habito_leitura,
            u.opcao_compartilhar,
            u.criado_em,
            u.ultima_atualizacao,
            COUNT(DISTINCT r.id) as total_roteiros,
            COUNT(DISTINCT c.id) as total_checkpoints,
            COALESCE(AVG(c.nota_llm), 0) as media_notas,
            MAX(c.data_hora) as ultima_atividade
        FROM usuarios u
        LEFT JOIN roteiros r ON u.id = r.usuario_id
        LEFT JOIN checkpoints c ON r.id = c.roteiro_id
        GROUP BY u.id, u.nome, u.email, u.idade, u.cidade, 
                 u.nivel_educacional, u.habito_leitura, u.opcao_compartilhar,
                 u.criado_em, u.ultima_atualizacao
        ORDER BY u.ultima_atualizacao DESC
        """
        cursor.execute(query)
        
        # Obter nomes das colunas e dados
        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()
        
        # Se não houver resultados, retornar DataFrame vazio com as colunas corretas
        if not results:
            return pd.DataFrame(columns=columns)
        
        # Criar DataFrame
        df = pd.DataFrame(results, columns=columns)
        
        # Tratar valores nulos
        df['media_notas'] = df['media_notas'].fillna(0)
        df['ultima_atividade'] = df['ultima_atividade'].fillna(df['criado_em'])
        
        # Calcular status de atividade
        df['status'] = df['ultima_atividade'].apply(
            lambda x: 'Ativo' if (pd.Timestamp.now() - pd.Timestamp(x)).days < 30 else 'Inativo'
        )
        
        # Calcular nível baseado na média das notas
        df['nivel'] = df['media_notas'].apply(lambda x: calcular_nivel_usuario(x))
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar dados detalhados dos usuários: {e}")
        # Retornar DataFrame vazio com as colunas esperadas
        colunas_esperadas = [
            'id', 'nome', 'email', 'idade', 'cidade', 'nivel_educacional',
            'habito_leitura', 'opcao_compartilhar', 'criado_em', 'ultima_atualizacao',
            'total_roteiros', 'total_checkpoints', 'media_notas', 'ultima_atividade',
            'status', 'nivel'
        ]
        return pd.DataFrame(columns=colunas_esperadas)



@st.cache_data(ttl=300)  # Cache por 5 minutos
@db_operation
def calcular_nivel_usuario(media_notas):
    """
    Calcula o nível do usuário com base na média das notas.
    """
    try:
        media = float(media_notas)
        if pd.isna(media) or media == 0:
            return "Não Avaliado"
        elif media < 5:
            return "Iniciante"
        elif media < 8:
            return "Intermediário"
        else:
            return "Avançado"
    except (ValueError, TypeError):
        return "Não Avaliado"
    
    
def obter_feedbacks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM feedback_automatizado')
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    feedbacks = [dict(zip(columns, row)) for row in rows]
    return feedbacks

