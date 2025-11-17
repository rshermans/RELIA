import sqlite3
import json
from database import get_db_connection, db_operation

# Carregue o JSON fora da função
with open('bloom_taxonomia.json', 'r', encoding='utf-8') as f:
    bloom_taxonomia = json.load(f)
    
@db_operation
def inserir_acoes_no_banco(conn):
    """Insere as ações da Taxonomia de Bloom na tabela 'acoes' do banco de dados."""
    
    for nivel_nome, nivel_data in bloom_taxonomia.items():
        nivel_bloom = nivel_data["nivel"]
        for acao, dados_acao in nivel_data["acoes"].items():
            conn.execute(
                '''
                INSERT OR REPLACE INTO acoes (id, nome_acoes, nivel_bloom, pontos, tipo_resposta, template_pergunta, descricao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    dados_acao["id"],
                    acao,
                    nivel_bloom,
                    dados_acao["pontos"],
                    dados_acao["tipo_resposta"],
                    dados_acao["template_pergunta"],
                    dados_acao["descricao"]
                )
            )
    
    conn.commit()

if __name__ == "__main__":
    inserir_acoes_no_banco()