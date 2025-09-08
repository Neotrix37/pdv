"""
Script para criar a tabela de despesas_recorrentes se ela não existir.
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar a classe Database
sys.path.append(str(Path(__file__).parent.parent.parent))
from database.database import Database

def criar_tabela_despesas():
    print("\n=== CRIANDO TABELA DE DESPESAS ===")
    
    # Inicializa o banco de dados
    db = Database()
    
    try:
        # Criar a tabela despesas_recorrentes se não existir
        db.execute("""
            CREATE TABLE IF NOT EXISTS despesas_recorrentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descricao TEXT,
                valor REAL NOT NULL,
                data_vencimento DATE NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        print("✅ Tabela 'despesas_recorrentes' criada com sucesso!")
        
        # Verificar se a tabela foi criada
        tabela_existe = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='despesas_recorrentes'"
        )
        
        if tabela_existe:
            print("✅ Verificação: A tabela 'despesas_recorrentes' existe no banco de dados")
            return True
        else:
            print("❌ Erro: A tabela 'despesas_recorrentes' não foi criada corretamente")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar a tabela: {e}")
        return False

if __name__ == "__main__":
    print("=== CRIAR TABELA DE DESPESAS ===")
    print("Este script irá criar a tabela 'despesas_recorrentes' se ela não existir.")
    
    input("Pressione Enter para continuar ou Ctrl+C para cancelar...")
    
    if criar_tabela_despesas():
        print("\n✅ Tabela de despesas verificada/criada com sucesso!")
    else:
        print("\n❌ Ocorreram erros durante a criação da tabela.")
    
    input("\nPressione Enter para sair...")
