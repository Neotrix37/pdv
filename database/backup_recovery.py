import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class BackupRecoveryManager:
    """Gerenciador de recuperação pós-backup para todas as entidades híbridas."""
    
    def __init__(self):
        self.db_path = self._get_database_path()
        
        # Tabelas que precisam de colunas de sincronização
        self.hybrid_tables = {
            'produtos': ['uuid', 'synced', 'created_at', 'updated_at'],
            'usuarios': ['uuid', 'synced'],
            'clientes': ['uuid', 'synced'], 
            'vendas': ['uuid', 'synced']
        }
    
    def _get_database_path(self) -> Path:
        """Obtém o caminho REAL do banco de dados ativo (APPDATA)."""
        try:
            # Usar o singleton Database para obter o caminho correto (APPDATA)
            from .database import Database
            db = Database()
            return Path(str(db.db_path))
        except Exception:
            # Fallback: antigo (não recomendado)
            return Path(__file__).parent / 'sistema.db'
    
    def detect_backup_restoration(self) -> Dict[str, Any]:
        """Detecta se o banco foi restaurado de backup verificando inconsistências."""
        print("=== DETECTANDO RESTAURAÇÃO DE BACKUP ===")
        
        issues = {
            'missing_columns': {},
            'missing_uuids': {},
            'unsynced_records': {},
            'missing_change_log': False,
            'needs_recovery': False
        }
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Verificar se change_log existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='change_log'
            """)
            if not cursor.fetchone():
                issues['missing_change_log'] = True
                issues['needs_recovery'] = True
                print("ERRO: Tabela change_log nao encontrada")
            
            # Verificar cada tabela híbrida
            for table, required_columns in self.hybrid_tables.items():
                print(f"\nVerificando tabela: {table}")
                
                # Verificar se a tabela existe
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
                
                if not cursor.fetchone():
                    print(f"AVISO: Tabela {table} nao encontrada")
                    # Considerar ausência de tabela como necessitando recuperação
                    issues['missing_columns'][table] = required_columns
                    issues['needs_recovery'] = True
                    continue
                
                # Verificar colunas existentes
                cursor.execute(f"PRAGMA table_info({table})")
                existing_columns = [col[1] for col in cursor.fetchall()]
                
                missing_cols = []
                for col in required_columns:
                    if col not in existing_columns:
                        missing_cols.append(col)
                
                if missing_cols:
                    issues['missing_columns'][table] = missing_cols
                    issues['needs_recovery'] = True
                    print(f"ERRO: Colunas ausentes em {table}: {missing_cols}")
                
                # Verificar registros sem UUID
                if 'uuid' in existing_columns:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE uuid IS NULL OR uuid = ''
                    """)
                    missing_uuid_count = cursor.fetchone()[0]
                    
                    if missing_uuid_count > 0:
                        issues['missing_uuids'][table] = missing_uuid_count
                        issues['needs_recovery'] = True
                        print(f"ERRO: {missing_uuid_count} registros sem UUID em {table}")
                
                # Verificar registros não sincronizados
                if 'synced' in existing_columns:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE synced IS NULL OR synced = 0
                    """)
                    unsynced_count = cursor.fetchone()[0]
                    
                    if unsynced_count > 0:
                        issues['unsynced_records'][table] = unsynced_count
                        print(f"AVISO: {unsynced_count} registros nao sincronizados em {table}")
        
        if issues['needs_recovery']:
            print("\nRECUPERACAO NECESSARIA - Backup detectado")
        else:
            print("\nBanco de dados integro - Nenhuma recuperacao necessaria")
        
        return issues
    
    def perform_full_recovery(self) -> Dict[str, Any]:
        """Executa recuperação completa pós-backup."""
        print("\n=== INICIANDO RECUPERAÇÃO COMPLETA ===")
        
        recovery_results = {
            'tables_fixed': [],
            'columns_added': {},
            'uuids_generated': {},
            'change_log_created': False,
            'success': True,
            'errors': []
        }
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # 1. Criar tabela change_log se não existir
                self._ensure_change_log_table(cursor, recovery_results)
                
                # 2. Processar cada tabela híbrida
                for table, required_columns in self.hybrid_tables.items():
                    try:
                        print(f"\n--- Processando {table} ---")
                        
                        # Verificar se tabela existe
                        cursor.execute("""
                            SELECT name FROM sqlite_master 
                            WHERE type='table' AND name=?
                        """, (table,))
                        
                        if not cursor.fetchone():
                            print(f"⚠️  Tabela {table} não encontrada, pulando...")
                            continue
                        
                        # Adicionar colunas ausentes
                        self._add_missing_columns(cursor, table, required_columns, recovery_results)
                        
                        # Gerar UUIDs ausentes
                        self._generate_missing_uuids(cursor, table, recovery_results)
                        
                        # Atualizar timestamps se necessário
                        self._update_timestamps(cursor, table, recovery_results)
                        
                        recovery_results['tables_fixed'].append(table)
                        print(f"OK: {table} processada com sucesso")
                        
                    except Exception as e:
                        error_msg = f"Erro ao processar {table}: {str(e)}"
                        print(f"ERRO: {error_msg}")
                        recovery_results['errors'].append(error_msg)
                
                conn.commit()
                
        except Exception as e:
            recovery_results['success'] = False
            recovery_results['errors'].append(f"Erro geral na recuperação: {str(e)}")
            print(f"ERRO geral: {str(e)}")
        
        # Resumo final
        print(f"\n=== RECUPERAÇÃO CONCLUÍDA ===")
        print(f"Tabelas processadas: {len(recovery_results['tables_fixed'])}")
        print(f"Colunas adicionadas: {sum(len(cols) for cols in recovery_results['columns_added'].values())}")
        print(f"UUIDs gerados: {sum(recovery_results['uuids_generated'].values())}")
        print(f"Erros: {len(recovery_results['errors'])}")
        
        if recovery_results['errors']:
            print("AVISO: Erros encontrados:")
            for error in recovery_results['errors']:
                print(f"  - {error}")
        
        return recovery_results
    
    def _ensure_change_log_table(self, cursor, results):
        """Garante que a tabela change_log existe."""
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='change_log'
        """)
        
        if not cursor.fetchone():
            print("Criando tabela change_log...")
            cursor.execute("""
                CREATE TABLE change_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    data_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    status TEXT DEFAULT 'pending'
                )
            """)
            results['change_log_created'] = True
            print("OK: Tabela change_log criada")
    
    def _add_missing_columns(self, cursor, table, required_columns, results):
        """Adiciona colunas ausentes na tabela."""
        # Verificar colunas existentes
        cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        added_columns = []
        
        for column in required_columns:
            if column not in existing_columns:
                try:
                    if column == 'uuid':
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN uuid TEXT")
                    elif column == 'synced':
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN synced INTEGER DEFAULT 0")
                    elif column in ['created_at', 'updated_at']:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
                    
                    added_columns.append(column)
                    print(f"OK: Coluna {column} adicionada em {table}")
                    
                except Exception as e:
                    print(f"ERRO: Erro ao adicionar coluna {column} em {table}: {e}")
        
        if added_columns:
            results['columns_added'][table] = added_columns
    
    def _generate_missing_uuids(self, cursor, table, results):
        """Gera UUIDs para registros que não possuem."""
        # Verificar se coluna uuid existe
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'uuid' not in columns:
            return
        
        # Buscar registros sem UUID
        cursor.execute(f"""
            SELECT id FROM {table} 
            WHERE uuid IS NULL OR uuid = ''
        """)
        records_without_uuid = cursor.fetchall()
        
        if records_without_uuid:
            print(f"Gerando UUIDs para {len(records_without_uuid)} registros em {table}...")
            
            for record in records_without_uuid:
                new_uuid = str(uuid.uuid4())
                cursor.execute(f"""
                    UPDATE {table} SET uuid = ? WHERE id = ?
                """, (new_uuid, record[0]))
            
            results['uuids_generated'][table] = len(records_without_uuid)
            print(f"OK: {len(records_without_uuid)} UUIDs gerados em {table}")
    
    def _update_timestamps(self, cursor, table, results):
        """Atualiza timestamps ausentes."""
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        current_time = datetime.now().isoformat()
        
        # Atualizar created_at se existir e estiver vazio
        if 'created_at' in columns:
            cursor.execute(f"""
                UPDATE {table} 
                SET created_at = ? 
                WHERE created_at IS NULL OR created_at = ''
            """, (current_time,))
        
        # Atualizar updated_at se existir e estiver vazio
        if 'updated_at' in columns:
            cursor.execute(f"""
                UPDATE {table} 
                SET updated_at = ? 
                WHERE updated_at IS NULL OR updated_at = ''
            """, (current_time,))
    
    def quick_check_and_fix(self) -> bool:
        """Verificação rápida e correção automática se necessário."""
        print("=== VERIFICAÇÃO RÁPIDA PÓS-BACKUP ===")
        
        issues = self.detect_backup_restoration()
        
        if issues['needs_recovery']:
            print("Iniciando correcao automatica...")
            recovery_result = self.perform_full_recovery()
            return recovery_result['success']
        else:
            print("OK: Nenhuma correcao necessaria")
            return True
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Obtém status atual de todas as tabelas híbridas."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'tables': {},
            'overall_health': 'healthy'
        }
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            for table in self.hybrid_tables.keys():
                try:
                    # Verificar se tabela existe
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, (table,))
                    
                    if not cursor.fetchone():
                        status['tables'][table] = {'exists': False}
                        status['overall_health'] = 'needs_attention'
                        continue
                    
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    total_records = cursor.fetchone()[0]
                    
                    # Contar registros com UUID
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE uuid IS NOT NULL AND uuid != ''
                    """)
                    records_with_uuid = cursor.fetchone()[0]
                    
                    # Contar registros sincronizados
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE synced = 1
                    """)
                    synced_records = cursor.fetchone()[0]
                    
                    status['tables'][table] = {
                        'exists': True,
                        'total_records': total_records,
                        'records_with_uuid': records_with_uuid,
                        'synced_records': synced_records,
                        'uuid_coverage': (records_with_uuid / total_records * 100) if total_records > 0 else 100,
                        'sync_coverage': (synced_records / total_records * 100) if total_records > 0 else 0
                    }
                    
                    # Verificar saúde da tabela
                    if records_with_uuid < total_records:
                        status['overall_health'] = 'needs_attention'
                
                except Exception as e:
                    status['tables'][table] = {'error': str(e)}
                    status['overall_health'] = 'error'
        
        return status


def run_backup_recovery_check():
    """Função utilitária para executar verificação de recuperação."""
    recovery_manager = BackupRecoveryManager()
    return recovery_manager.quick_check_and_fix()


if __name__ == "__main__":
    # Executar verificação se chamado diretamente
    recovery_manager = BackupRecoveryManager()
    
    print("=== SISTEMA DE RECUPERAÇÃO PÓS-BACKUP ===")
    
    # Detectar problemas
    issues = recovery_manager.detect_backup_restoration()
    
    if issues['needs_recovery']:
        print("\n🔧 Problemas detectados. Executar recuperação? (s/n): ", end="")
        response = input().lower().strip()
        
        if response in ['s', 'sim', 'y', 'yes']:
            recovery_manager.perform_full_recovery()
        else:
            print("Recuperação cancelada pelo usuário.")
    
    # Mostrar status final
    print("\n=== STATUS FINAL ===")
    status = recovery_manager.get_recovery_status()
    print(f"Saúde geral: {status['overall_health']}")
    
    for table, info in status['tables'].items():
        if info.get('exists', False):
            uuid_cov = info.get('uuid_coverage', 0)
            sync_cov = info.get('sync_coverage', 0)
            print(f"{table}: {info['total_records']} registros, {uuid_cov:.1f}% UUID, {sync_cov:.1f}% sync")
        else:
            print(f"{table}: não encontrada")
