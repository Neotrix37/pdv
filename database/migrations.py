import sqlite3
import os
import uuid
from pathlib import Path
import platform

def get_database_path():
    """Obtém o caminho do banco de dados baseado no sistema operacional."""
    sistema = platform.system().lower()
    if sistema == 'windows' and 'APPDATA' in os.environ:
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
    else:
        app_data_db_dir = Path(os.path.expanduser('~')) / '.sistemagestao' / 'database'
    
    app_data_db_dir.mkdir(parents=True, exist_ok=True)
    return app_data_db_dir / 'sistema.db'

def create_change_log_table():
    """Cria a tabela change_log para rastrear mudanças offline."""
    db_path = get_database_path()
    
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='change_log'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Verificar estrutura da tabela existente
            cursor.execute("PRAGMA table_info(change_log)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'entity_type' not in columns:
                print("Tabela change_log existe mas está incompleta. Recriando...")
                cursor.execute("DROP TABLE change_log")
                table_exists = False
            else:
                print("Tabela change_log já existe com estrutura correta")
                return
        
        if not table_exists:
            # Criar tabela change_log
            cursor.execute("""
            CREATE TABLE change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                operation TEXT NOT NULL CHECK (operation IN ('CREATE', 'UPDATE', 'DELETE')),
                data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_at TIMESTAMP NULL,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'synced', 'error')),
                error_message TEXT NULL,
                retry_count INTEGER DEFAULT 0
            )
            """)
        
        # Criar índices para performance
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_change_log_status 
        ON change_log(status)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_change_log_entity 
        ON change_log(entity_type, entity_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_change_log_created 
        ON change_log(created_at)
        """)
        
        conn.commit()
        print("Tabela change_log criada com sucesso!")

def add_sync_columns_to_table(table_name):
    """Adiciona colunas de sincronização a uma tabela específica."""
    db_path = get_database_path()
    
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"Tabela '{table_name}' não existe, pulando...")
            return
        
        # Verificar se as colunas já existem
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Adicionar colunas se não existirem
        if 'uuid' not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN uuid TEXT")
            print(f"Coluna 'uuid' adicionada à tabela {table_name}")
            
            # Gerar UUIDs para registros existentes
            cursor.execute(f"SELECT id FROM {table_name} WHERE uuid IS NULL")
            rows = cursor.fetchall()
            for row in rows:
                new_uuid = str(uuid.uuid4())
                cursor.execute(f"UPDATE {table_name} SET uuid = ? WHERE id = ?", (new_uuid, row[0]))
            print(f"UUIDs gerados para {len(rows)} registros existentes em {table_name}")
        
        if 'created_at' not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN created_at TIMESTAMP")
            # Atualizar registros existentes com timestamp atual
            cursor.execute(f"UPDATE {table_name} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            print(f"Coluna 'created_at' adicionada à tabela {table_name}")
        
        if 'updated_at' not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN updated_at TIMESTAMP")
            # Atualizar registros existentes com timestamp atual
            cursor.execute(f"UPDATE {table_name} SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
            print(f"Coluna 'updated_at' adicionada à tabela {table_name}")
        
        if 'synced' not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN synced INTEGER DEFAULT 0")
            print(f"Coluna 'synced' adicionada à tabela {table_name}")
        
        # Criar trigger para atualizar updated_at
        cursor.execute(f"""
        CREATE TRIGGER IF NOT EXISTS {table_name}_updated_at 
        AFTER UPDATE ON {table_name}
        BEGIN
            UPDATE {table_name} SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """)
        
        conn.commit()
        print(f"Colunas de sincronização adicionadas à tabela {table_name}!")

def add_sync_columns_to_all_tables():
    """Adiciona colunas de sincronização a todas as tabelas principais."""
    tables = ['produtos', 'usuarios', 'clientes', 'vendas']
    
    for table in tables:
        try:
            add_sync_columns_to_table(table)
        except Exception as e:
            print(f"Erro ao migrar tabela {table}: {e}")

def run_migrations():
    """Executa todas as migrações necessárias."""
    print("Executando migrações do banco de dados...")
    
    try:
        create_change_log_table()
        add_sync_columns_to_all_tables()
        print("Todas as migrações foram executadas com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao executar migrações: {e}")
        return False

if __name__ == "__main__":
    run_migrations()
