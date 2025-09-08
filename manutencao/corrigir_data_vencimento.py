"""
Script para tornar o campo data_vencimento opcional na tabela despesas_recorrentes.
"""
import sqlite3
import os
from pathlib import Path

def corrigir_data_vencimento():
    print("\n=== CORRIGINDO CAMPO DATA_VENCIMENTO ===")
    
    # Caminho para o banco de dados
    db_path = os.path.join(os.getenv('APPDATA'), 'SistemaGestao', 'database', 'sistema.db')
    
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='despesas_recorrentes'")
        if not cursor.fetchone():
            print("[ERRO] A tabela 'despesas_recorrentes' não existe no banco de dados.")
            return False
        
        # Verificar a estrutura atual da tabela
        cursor.execute('PRAGMA table_info(despesas_recorrentes)')
        colunas = cursor.fetchall()
        
        # Encontrar a definição da coluna data_vencimento
        data_vencimento_col = next((col for col in colunas if col[1] == 'data_vencimento'), None)
        
        if not data_vencimento_col:
            print("[ERRO] A coluna 'data_vencimento' não foi encontrada na tabela.")
            return False
            
        # Se a coluna já não for NOT NULL, não é necessário fazer nada
        if not data_vencimento_col[3]:  # O índice 3 é o flag NOT NULL
            print("[INFO] A coluna 'data_vencimento' já é opcional. Nenhuma alteração necessária.")
            return True
            
        print("Modificando a coluna 'data_vencimento' para ser opcional...")
        
        # 1. Criar tabela temporária com a mesma estrutura, mas com data_vencimento opcional
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS despesas_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                data_vencimento DATE,
                data_pagamento DATE,
                status TEXT NOT NULL,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # 2. Copiar dados da tabela antiga para a nova
        cursor.execute("""
            INSERT INTO despesas_temp 
            (id, tipo, categoria, descricao, valor, data_vencimento, data_pagamento, status, created_at, updated_at)
            SELECT id, tipo, categoria, descricao, valor, data_vencimento, data_pagamento, status, created_at, updated_at
            FROM despesas_recorrentes
        """)
        
        # 3. Remover a tabela antiga
        cursor.execute("DROP TABLE despesas_recorrentes")
        
        # 4. Renomear a tabela temporária para o nome original
        cursor.execute("ALTER TABLE despesas_temp RENAME TO despesas_recorrentes")
        
        print("[SUCESSO] Tabela 'despesas_recorrentes' modificada com sucesso!")
        print("[SUCESSO] O campo 'data_vencimento' agora é opcional.")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao modificar a tabela: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== CORRIGIR CAMPO DATA_VENCIMENTO ===")
    print("Este script irá modificar a tabela 'despesas_recorrentes' para tornar o campo 'data_vencimento' opcional.")
    print("\n[INFO] Executando correção...")
    
    if corrigir_data_vencimento():
        print("\n[SUCESSO] Correção concluída com sucesso!")
    else:
        print("\n[ERRO] Ocorreram erros durante a correção da tabela.")
