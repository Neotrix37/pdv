import os
import sqlite3
from database.database import Database

def atualizar_esquema_banco():
    """
    Atualiza o esquema do banco de dados para garantir que todas as tabelas e colunas necessárias existam.
    """
    print("Iniciando atualização do esquema do banco de dados...")
    
    try:
        # Conectar ao banco de dados
        db = Database()
        cursor = db.conn.cursor()
        
        print("Verificando a tabela retiradas_caixa...")
        
        # Verificar se a tabela existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='retiradas_caixa'
        """)
        
        if not cursor.fetchone():
            print("Criando tabela retiradas_cica...")
            cursor.execute('''
                CREATE TABLE retiradas_caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    aprovador_id INTEGER,
                    valor REAL NOT NULL,
                    motivo TEXT NOT NULL,
                    observacao TEXT,
                    origem TEXT NOT NULL DEFAULT 'vendas',
                    status TEXT NOT NULL DEFAULT 'pendente',
                    data_retirada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_aprovacao TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                    FOREIGN KEY (aprovador_id) REFERENCES usuarios (id)
                )
            ''')
            print("Tabela retiradas_caixa criada com sucesso!")
        
        # Verificar se a coluna 'origem' existe
        cursor.execute("PRAGMA table_info(retiradas_caixa)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'origem' not in columns:
            print("Adicionando coluna 'origem' à tabela retiradas_caixa...")
            try:
                cursor.execute('''
                    ALTER TABLE retiradas_caixa
                    ADD COLUMN origem TEXT NOT NULL DEFAULT 'vendas';
                ''')
                print("Coluna 'origem' adicionada com sucesso!")
            except sqlite3.OperationalError as e:
                if "duplicate column name: origem" in str(e):
                    print("A coluna 'origem' já existe na tabela.")
                else:
                    print(f"Erro ao adicionar coluna: {str(e)}")
                    raise
        else:
            print("A coluna 'origem' já existe na tabela retiradas_caixa.")
        
        # Criar trigger para updated_at se não existir
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='trigger' AND name='retiradas_caixa_updated_at'
        """)
        
        if not cursor.fetchone():
            print("Criando trigger para updated_at...")
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS retiradas_caixa_updated_at 
                AFTER UPDATE ON retiradas_caixa
                BEGIN
                    UPDATE retiradas_caixa 
                    SET updated_at = datetime('now', 'localtime') 
                    WHERE id = NEW.id;
                END
            ''')
            print("Trigger criada com sucesso!")
        
        # Confirmar as alterações
        db.conn.commit()
        print("Atualização do esquema concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro ao atualizar o esquema do banco de dados: {str(e)}")
        if 'db' in locals() and hasattr(db, 'conn'):
            db.conn.rollback()
        raise
    finally:
        if 'db' in locals() and hasattr(db, 'conn'):
            db.conn.close()

if __name__ == "__main__":
    print("=== ATUALIZAÇÃO DO ESQUEMA DO BANCO DE DADOS ===")
    print("Este script irá verificar e atualizar o esquema do banco de dados.")
    print("Por favor, certifique-se de fazer backup do banco de dados antes de continuar.")
    input("Pressione Enter para continuar ou Ctrl+C para cancelar...")
    
    try:
        atualizar_esquema_banco()
        print("\nAtualização concluída com sucesso!")
    except Exception as e:
        print(f"\nErro durante a atualização: {str(e)}")
        print("Por favor, verifique o erro e tente novamente.")
        exit(1)
