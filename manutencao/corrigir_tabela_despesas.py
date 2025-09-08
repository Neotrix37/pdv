"""
Script para corrigir a estrutura da tabela despesas_recorrentes, tornando data_vencimento opcional.
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar a classe Database
sys.path.append(str(Path(__file__).parent.parent))
from database.database import Database

def corrigir_tabela_despesas():
    print("\n=== CORRIGINDO TABELA DE DESPESAS ===")
    
    # Inicializa o banco de dados
    db = Database()
    
    try:
        # Verificar se a tabela existe
        tabela_existe = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='despesas_recorrentes'"
        )
        
        if not tabela_existe:
            print("[ERRO] A tabela 'despesas_recorrentes' não existe no banco de dados.")
            return False
            
        # Criar uma nova tabela com a estrutura correta
        print("Criando nova estrutura da tabela...")
        
        # 1. Criar tabela temporária com a estrutura correta
        db.execute("""
            CREATE TABLE IF NOT EXISTS despesas_recorrentes_temp (
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
        db.execute("""
            INSERT INTO despesas_recorrentes_temp 
            (id, tipo, categoria, descricao, valor, data_vencimento, data_pagamento, status, created_at, updated_at)
            SELECT id, tipo, categoria, descricao, valor, data_vencimento, data_pagamento, status, created_at, updated_at
            FROM despesas_recorrentes
        """)
        
        # 3. Remover a tabela antiga
        db.execute("DROP TABLE despesas_recorrentes")
        
        # 4. Renomear a tabela temporária para o nome original
        db.execute("ALTER TABLE despesas_recorrentes_temp RENAME TO despesas_recorrentes")
        
        print("[SUCESSO] Tabela 'despesas_recorrentes' corrigida com sucesso!")
        print("[SUCESSO] O campo 'data_vencimento' agora é opcional.")
        
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao corrigir a tabela: {e}")
        return False

if __name__ == "__main__":
    print("=== CORRIGIR TABELA DE DESPESAS ===")
    print("Este script irá corrigir a tabela 'despesas_recorrentes' para tornar o campo 'data_vencimento' opcional.")
    print("\n[INFO] Executando correção...")
    
    if corrigir_tabela_despesas():
        print("\n[SUCESSO] Correção concluída com sucesso!")
    else:
        print("\n[ERRO] Ocorreram erros durante a correção da tabela.")
