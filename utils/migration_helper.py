"""
Helper para migração automática de esquemas de banco após restauração de backup.
Adiciona colunas necessárias para sincronização quando não existem.
"""
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
import os
import platform

class MigrationHelper:
    def __init__(self):
        self.db_path = self._get_database_path()
    
    def _get_database_path(self) -> Path:
        """Obtém o caminho do banco de dados baseado no sistema operacional."""
        sistema = platform.system().lower()
        if sistema == 'windows' and 'APPDATA' in os.environ:
            app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
        else:
            app_data_db_dir = Path(os.path.expanduser('~')) / '.sistemagestao' / 'database'
        
        app_data_db_dir.mkdir(parents=True, exist_ok=True)
        return app_data_db_dir / 'sistema.db'
    
    def migrate_all_tables(self):
        """Executa migração completa de todas as tabelas."""
        print("[MIGRATION] Verificando e migrando esquemas de sincronização...")
        
        try:
            self.migrate_usuarios_table()
            self.migrate_produtos_table()
            self.migrate_clientes_table()
            self.migrate_vendas_table()
            self.create_change_log_table()
            print("[MIGRATION] Migração completa realizada com sucesso!")
        except Exception as e:
            print(f"[MIGRATION] Erro durante migração: {e}")
    
    def migrate_usuarios_table(self):
        """Adiciona colunas de sincronização na tabela usuarios se não existirem."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Verificar colunas existentes
            cursor.execute("PRAGMA table_info(usuarios)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Adicionar coluna uuid se não existir
            if 'uuid' not in columns:
                print("[MIGRATION] Adicionando coluna 'uuid' na tabela usuarios")
                cursor.execute("ALTER TABLE usuarios ADD COLUMN uuid TEXT")
                
                # Gerar UUIDs para registros existentes
                cursor.execute("SELECT id FROM usuarios")
                user_ids = cursor.fetchall()
                for (user_id,) in user_ids:
                    new_uuid = str(uuid.uuid4())
                    cursor.execute("UPDATE usuarios SET uuid = ? WHERE id = ?", (new_uuid, user_id))
                
                print(f"[MIGRATION] UUIDs gerados para {len(user_ids)} usuários existentes")
            
            # Adicionar coluna synced se não existir
            if 'synced' not in columns:
                print("[MIGRATION] Adicionando coluna 'synced' na tabela usuarios")
                cursor.execute("ALTER TABLE usuarios ADD COLUMN synced INTEGER DEFAULT 0")
            
            conn.commit()
    
    def migrate_produtos_table(self):
        """Adiciona colunas de sincronização na tabela produtos se não existirem."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Verificar colunas existentes
            cursor.execute("PRAGMA table_info(produtos)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Adicionar coluna uuid se não existir
            if 'uuid' not in columns:
                print("[MIGRATION] Adicionando coluna 'uuid' na tabela produtos")
                cursor.execute("ALTER TABLE produtos ADD COLUMN uuid TEXT")
                
                # Gerar UUIDs para registros existentes
                cursor.execute("SELECT id FROM produtos")
                product_ids = cursor.fetchall()
                for (product_id,) in product_ids:
                    new_uuid = str(uuid.uuid4())
                    cursor.execute("UPDATE produtos SET uuid = ? WHERE id = ?", (new_uuid, product_id))
                
                print(f"[MIGRATION] UUIDs gerados para {len(product_ids)} produtos existentes")
            
            # Adicionar coluna synced se não existir
            if 'synced' not in columns:
                print("[MIGRATION] Adicionando coluna 'synced' na tabela produtos")
                cursor.execute("ALTER TABLE produtos ADD COLUMN synced INTEGER DEFAULT 0")
            
            conn.commit()
    
    def migrate_clientes_table(self):
        """Adiciona colunas de sincronização na tabela clientes se não existirem."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
            if not cursor.fetchone():
                print("[MIGRATION] Tabela 'clientes' não encontrada, pulando migração")
                return
            
            # Verificar colunas existentes
            cursor.execute("PRAGMA table_info(clientes)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Adicionar coluna uuid se não existir
            if 'uuid' not in columns:
                print("[MIGRATION] Adicionando coluna 'uuid' na tabela clientes")
                cursor.execute("ALTER TABLE clientes ADD COLUMN uuid TEXT")
                
                # Gerar UUIDs para registros existentes
                cursor.execute("SELECT id FROM clientes")
                client_ids = cursor.fetchall()
                for (client_id,) in client_ids:
                    new_uuid = str(uuid.uuid4())
                    cursor.execute("UPDATE clientes SET uuid = ? WHERE id = ?", (new_uuid, client_id))
                
                print(f"[MIGRATION] UUIDs gerados para {len(client_ids)} clientes existentes")
            
            # Adicionar coluna synced se não existir
            if 'synced' not in columns:
                print("[MIGRATION] Adicionando coluna 'synced' na tabela clientes")
                cursor.execute("ALTER TABLE clientes ADD COLUMN synced INTEGER DEFAULT 0")
            
            conn.commit()
    
    def migrate_vendas_table(self):
        """Adiciona colunas de sincronização na tabela vendas se não existirem."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vendas'")
            if not cursor.fetchone():
                print("[MIGRATION] Tabela 'vendas' não encontrada, pulando migração")
                return
            
            # Verificar colunas existentes
            cursor.execute("PRAGMA table_info(vendas)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Adicionar coluna uuid se não existir
            if 'uuid' not in columns:
                print("[MIGRATION] Adicionando coluna 'uuid' na tabela vendas")
                cursor.execute("ALTER TABLE vendas ADD COLUMN uuid TEXT")
                
                # Gerar UUIDs para registros existentes
                cursor.execute("SELECT id FROM vendas")
                sale_ids = cursor.fetchall()
                for (sale_id,) in sale_ids:
                    new_uuid = str(uuid.uuid4())
                    cursor.execute("UPDATE vendas SET uuid = ? WHERE id = ?", (new_uuid, sale_id))
                
                print(f"[MIGRATION] UUIDs gerados para {len(sale_ids)} vendas existentes")
            
            # Adicionar coluna synced se não existir
            if 'synced' not in columns:
                print("[MIGRATION] Adicionando coluna 'synced' na tabela vendas")
                cursor.execute("ALTER TABLE vendas ADD COLUMN synced INTEGER DEFAULT 0")
            
            conn.commit()
    
    def create_change_log_table(self):
        """Cria a tabela change_log se não existir."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='change_log'")
            if not cursor.fetchone():
                print("[MIGRATION] Criando tabela 'change_log'")
                cursor.execute("""
                    CREATE TABLE change_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_type TEXT NOT NULL,
                        entity_uuid TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        data TEXT,
                        timestamp TEXT NOT NULL,
                        status TEXT DEFAULT 'pending'
                    )
                """)
                
                # Criar índices para performance
                cursor.execute("CREATE INDEX idx_change_log_entity ON change_log(entity_type, entity_uuid)")
                cursor.execute("CREATE INDEX idx_change_log_status ON change_log(status)")
                
                conn.commit()
                print("[MIGRATION] Tabela 'change_log' criada com sucesso")
    
    def check_migration_needed(self) -> bool:
        """Verifica se alguma migração é necessária."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Verificar tabelas principais
                tables_to_check = ['usuarios', 'produtos', 'clientes', 'vendas']
                
                for table in tables_to_check:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    if cursor.fetchone():
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        if 'uuid' not in columns or 'synced' not in columns:
                            return True
                
                # Verificar se change_log existe
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='change_log'")
                if not cursor.fetchone():
                    return True
                
                return False
        except Exception as e:
            print(f"[MIGRATION] Erro ao verificar necessidade de migração: {e}")
            return True
