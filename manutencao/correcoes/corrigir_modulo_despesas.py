"""
Script para verificar e corrigir a estrutura do banco de dados para o módulo de despesas.
"""
import os
import sys
import sqlite3
from pathlib import Path
import platform

# Adiciona o diretório raiz ao path para importar a classe Database
sys.path.append(str(Path(__file__).parent.parent.parent))
from database.database import Database

def verificar_tabelas():
    print("\n=== VERIFICANDO ESTRUTURA DO BANCO DE DADOS PARA MÓDULO DE DESPESAS ===")
    
    # Inicializa o banco de dados
    db = Database()
    
    try:
        cursor = db.conn.cursor()
        
        # Verificar se a tabela de categorias de despesa existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_despesa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabela 'categorias_despesa' verificada/criada com sucesso!")
        
        # Inserir categorias padrão se a tabela estiver vazia
        cursor.execute("SELECT COUNT(*) as total FROM categorias_despesa")
        if cursor.fetchone()['total'] == 0:
            categorias_padrao = [
                ("Aluguel", "Pagamento de aluguel do imóvel"),
                ("Água", "Conta de água"),
                ("Luz", "Conta de energia elétrica"),
                ("Internet", "Serviço de internet"),
                ("Salários", "Pagamento de funcionários"),
                ("Manutenção", "Manutenção de equipamentos"),
                ("Outros", "Outras despesas diversas")
            ]
            cursor.executemany(
                "INSERT INTO categorias_despesa (nome, descricao) VALUES (?, ?)",
                categorias_padrao
            )
            print(f"✅ Inseridas {len(categorias_padrao)} categorias padrão")
        
        # Verificar se a tabela de despesas recorrentes existe
        cursor.execute("""
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
        print("✅ Tabela 'despesas_recorrentes' verificada/criada com sucesso!")
        
        # Verificar se a coluna 'status' existe e removê-la se necessário
        cursor.execute("PRAGMA table_info(despesas_recorrentes)")
        colunas = cursor.fetchall()
        tem_status = any(col[1] == 'status' for col in colunas)
        
        if tem_status:
            print("⚠️  Coluna 'status' encontrada na tabela despesas_recorrentes. Removendo...")
            
            # Criar uma nova tabela sem a coluna status
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS despesas_recorrentes_nova (
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
            
            # Copiar dados para a nova tabela (exceto a coluna status)
            cursor.execute("""
                INSERT INTO despesas_recorrentes_nova 
                (id, tipo, categoria, descricao, valor, data_vencimento, data_cadastro, usuario_id)
                SELECT id, tipo, categoria, descricao, valor, data_vencimento, data_cadastro, usuario_id
                FROM despesas_recorrentes
            """)
            
            # Remover a tabela antiga e renomear a nova
            cursor.execute("DROP TABLE despesas_recorrentes")
            cursor.execute("ALTER TABLE despesas_recorrentes_nova RENAME TO despesas_recorrentes")
            
            print("✅ Coluna 'status' removida com sucesso!")
        
        db.conn.commit()
        print("\n✅ Verificação e correção concluídas com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar/corrigir banco de dados: {e}")
        db.conn.rollback()
        return False
    finally:
        db.conn.close()

if __name__ == "__main__":
    print("=== CORRIGIR MÓDULO DE DESPESAS ===")
    print("Este script irá verificar e corrigir a estrutura do banco de dados para o módulo de despesas.")
    
    input("Pressione Enter para continuar ou Ctrl+C para cancelar...")
    
    if verificar_tabelas():
        print("\n✅ O módulo de despesas está pronto para uso!")
    else:
        print("\n❌ Ocorreram erros durante a verificação/correção. Consulte as mensagens acima.")
    
    input("\nPressione Enter para sair...")
