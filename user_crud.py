from database import get_db_connection, hash_password
import sqlite3

def inserir_perfil(nome, email, senha, idade, cidade, interesses, nivel_educacional, habito_leitura, opcao_compartilhar):
    conn = get_db_connection()
    senha_hash = hash_password(senha)
    try:
        conn.execute('''
            INSERT INTO usuarios (nome, email, senha, idade, cidade, interesses, nivel_educacional, habito_leitura,  opcao_compartilhar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome, email, senha_hash, idade, cidade, interesses, nivel_educacional, habito_leitura, opcao_compartilhar))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Erro ao inserir perfil: {e}")
    finally:
        conn.close()

def obter_perfil(email):
    conn = get_db_connection()
    perfil = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
    conn.close()
    return perfil

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
    except sqlite3.IntegrityError as e:
        print(f"Erro ao atualizar perfil: {e}")
    finally:
        conn.close()

def excluir_perfil(uid):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM usuarios WHERE uid = ?', (uid,))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Erro ao excluir perfil: {e}")
    finally:
        conn.close()


# CRUD DA OBRAS

def inserir_obra(titulo, autor, ano_publicacao, genero, sinopse, capa, isbn, url_google):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO obras (titulo, autor, ano_publicacao, genero, sinopse, capa, isbn, url_google)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (titulo, autor, ano_publicacao, genero, sinopse, capa, isbn, url_google))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Erro ao inserir obra: {e}")
    finally:
        conn.close()

def obter_obras():
    conn = get_db_connection()
    obras = conn.execute('SELECT * FROM obras').fetchall()
    conn.close()
    return obras

def obter_obra_por_id(obra_id):
    conn = get_db_connection()
    obra = conn.execute('SELECT * FROM obras WHERE id = ?', (obra_id,)).fetchone()
    conn.close()
    return obra

def associar_obra_usuario(obra_id, usuario_id):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO roteiros (obra_id, usuario_id)
            VALUES (?, ?)
        ''', (obra_id, usuario_id))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Erro ao associar obra ao usuário: {e}")
    finally:
        conn.close()