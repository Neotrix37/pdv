import sqlite3
import os
from pathlib import Path
from werkzeug.security import generate_password_hash


def corrigir_reset_database():
    print("Corrigindo método reset_database para incluir tabela de fornecedores...")
    
    # Caminho para o banco de dados
    db_dir = Path(os.path.dirname(__file__)) / 'database'
    db_path = db_dir / 'sistema.db'
    
    print(f"Caminho do banco de dados: {db_path}")
    
    # Verificar se o diretório e o arquivo existem
    if not db_dir.exists():
        print(f"Diretório não encontrado: {db_dir}")
        return False
        
    if not db_path.exists():
        print(f"Arquivo de banco de dados não encontrado: {db_path}")
        return False
    
    # Conectar ao banco de dados
    conn = sqlite3.connect(str(db_path.absolute()))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Verificar se a tabela de fornecedores existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fornecedores'")
        if not cursor.fetchone():
            print("Criando tabela de fornecedores...")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                email TEXT,
                endereco TEXT,
                cnpj TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Inserir fornecedor padrão
            cursor.execute('''
                INSERT OR IGNORE INTO fornecedores (id, nome, ativo)
                VALUES (1, 'Fornecedor Padrão', 1)
            ''')
            
            conn.commit()
            print("Tabela de fornecedores criada com sucesso!")
        else:
            print("Tabela de fornecedores já existe.")
            
            # Verificar se o fornecedor padrão existe
            cursor.execute("SELECT * FROM fornecedores WHERE id = 1")
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT OR IGNORE INTO fornecedores (id, nome, ativo)
                    VALUES (1, 'Fornecedor Padrão', 1)
                ''')
                conn.commit()
                print("Fornecedor padrão criado com sucesso!")
        
        # Verificar se a coluna nivel existe na tabela usuarios
        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = cursor.fetchall()
        colunas_nomes = [coluna[1] for coluna in colunas]
        
        if 'nivel' not in colunas_nomes:
            print("Adicionando coluna 'nivel' à tabela usuarios...")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN nivel INTEGER DEFAULT 1")
            conn.commit()
            print("Coluna 'nivel' adicionada com sucesso!")
        
        # Atualizar o usuário admin para garantir que tenha nivel = 2
        cursor.execute("UPDATE usuarios SET nivel = 2, is_admin = 1, ativo = 1 WHERE usuario = 'admin'")
        conn.commit()
        print("Usuário admin atualizado com sucesso!")
        
        # Verificar se o usuário admin existe
        cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
        admin = cursor.fetchone()
        if not admin:
            print("Criando usuário admin...")
            senha_hash = generate_password_hash("842384")
            cursor.execute('''
                INSERT INTO usuarios (nome, usuario, senha, is_admin, ativo, nivel)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'Administrador',
                'admin',
                senha_hash,
                1,  # is_admin = True
                1,  # ativo = True
                2   # nivel = 2 (admin)
            ))
            conn.commit()
            print("Usuário admin criado com sucesso!")
        
        print("Correções aplicadas com sucesso!")
        return True
    
    except Exception as e:
        print(f"Erro ao corrigir reset_database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    corrigir_reset_database()