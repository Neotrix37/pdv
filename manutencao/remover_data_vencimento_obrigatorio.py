"""
Script para modificar a tabela despesas_recorrentes, tornando data_vencimento opcional.
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar a classe Database
sys.path.append(str(Path(__file__).parent.parent))
from database.database import Database

def modificar_tabela_despesas():
    print("\n=== MODIFICANDO TABELA DE DESPESAS ===")
    
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
            
        # Criar uma nova tabela sem a restrição NOT NULL em data_vencimento
        print("Criando nova estrutura da tabela...")
        
        # 1. Criar tabela temporária
        db.execute("""
            CREATE TABLE IF NOT EXISTS despesas_recorrentes_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descricao TEXT,
                valor REAL NOT NULL,
                data_vencimento DATE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER NOT NULL,
                data_pagamento DATE,
                status TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # 2. Copiar dados da tabela antiga para a nova
        db.execute("""
            INSERT INTO despesas_recorrentes_temp 
            (id, tipo, categoria, descricao, valor, data_vencimento, data_cadastro, usuario_id, data_pagamento, status)
            SELECT id, tipo, categoria, descricao, valor, data_vencimento, data_cadastro, usuario_id, data_pagamento, status
            FROM despesas_recorrentes
        """)
        
        # 3. Remover a tabela antiga
        db.execute("DROP TABLE despesas_recorrentes")
        
        # 4. Renomear a tabela temporária para o nome original
        db.execute("ALTER TABLE despesas_recorrentes_temp RENAME TO despesas_recorrentes")
        
        print("[SUCESSO] Tabela 'despesas_recorrentes' modificada com sucesso!")
        print("[SUCESSO] O campo 'data_vencimento' agora é opcional.")
        
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao modificar a tabela: {e}")
        return False

if __name__ == "__main__":
    print("=== REMOVER OBRIGATORIEDADE DE DATA DE VENCIMENTO ===")
    print("Este script irá modificar a tabela 'despesas_recorrentes' para tornar o campo 'data_vencimento' opcional.")
    print("\n[INFO] Executando modificação...")
    
    if modificar_tabela_despesas():
        print("\n[SUCESSO] Modificação concluída com sucesso!")
    else:
        print("\n[ERRO] Ocorreram erros durante a modificação da tabela.")
