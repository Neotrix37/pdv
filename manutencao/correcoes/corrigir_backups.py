#!/usr/bin/env python3
"""
Script para corrigir todos os backups existentes adicionando a tabela retiradas_caixa
"""

import sys
import os
import sqlite3
import shutil
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def corrigir_backup(backup_path):
    """Corrige um backup específico adicionando a tabela retiradas_caixa"""
    try:
        print(f"Corrigindo backup: {os.path.basename(backup_path)}")
        
        # Conectar ao backup
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela retiradas_caixa existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='retiradas_caixa'
        """)
        
        if not cursor.fetchone():
            print("  - Criando tabela retiradas_caixa...")
            
            # Criar a tabela
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
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (aprovador_id) REFERENCES usuarios(id)
                )
            ''')
            
            # Criar trigger
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS retiradas_caixa_updated_at 
                AFTER UPDATE ON retiradas_caixa
                BEGIN
                    UPDATE retiradas_caixa 
                    SET updated_at = datetime('now', 'localtime') 
                    WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
            print("  ✅ Tabela criada com sucesso!")
        else:
            print("  ✅ Tabela já existe!")
            
            # Verificar estrutura da tabela
            cursor.execute("PRAGMA table_info(retiradas_caixa)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Verificar e adicionar colunas ausentes
            colunas_necessarias = {
                'origem': "TEXT NOT NULL DEFAULT 'vendas'",
                'status': "TEXT NOT NULL DEFAULT 'pendente'",
                'aprovador_id': "INTEGER REFERENCES usuarios(id)",
                'data_aprovacao': "TIMESTAMP",
                'motivo': "TEXT NOT NULL DEFAULT 'Retirada de caixa'",
                'observacao': "TEXT",
                'created_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                'updated_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            
            for coluna, definicao in colunas_necessarias.items():
                if coluna not in column_names:
                    print(f"  - Adicionando coluna '{coluna}'...")
                    try:
                        cursor.execute(f"""
                            ALTER TABLE retiradas_caixa
                            ADD COLUMN {coluna} {definicao}
                        """)
                        conn.commit()
                        print(f"    ✅ Coluna '{coluna}' adicionada!")
                    except Exception as e:
                        print(f"    ❌ Erro ao adicionar coluna '{coluna}': {e}")
            
            # Verificar trigger
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='trigger' AND name='retiradas_caixa_updated_at'
            """)
            
            if not cursor.fetchone():
                print("  - Criando trigger...")
                try:
                    cursor.execute("""
                        CREATE TRIGGER IF NOT EXISTS retiradas_caixa_updated_at 
                        AFTER UPDATE ON retiradas_caixa
                        BEGIN
                            UPDATE retiradas_caixa 
                            SET updated_at = datetime('now', 'localtime') 
                            WHERE id = NEW.id;
                        END
                    """)
                    conn.commit()
                    print("    ✅ Trigger criado!")
                except Exception as e:
                    print(f"    ❌ Erro ao criar trigger: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao corrigir backup: {e}")
        return False

def main():
    print("=== Script de Correção de Backups ===\n")
    
    # Verificar se o diretório de backups existe
    backup_dir = os.path.join(os.path.dirname(__file__), "backups")
    if not os.path.exists(backup_dir):
        print("❌ Diretório de backups não encontrado!")
        return
    
    # Listar todos os backups
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    
    if not backups:
        print("✅ Nenhum backup encontrado para corrigir.")
        return
    
    print(f"Encontrados {len(backups)} backups para corrigir:\n")
    
    # Fazer backup dos backups originais
    backup_original_dir = os.path.join(backup_dir, "original_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(backup_original_dir, exist_ok=True)
    
    print("Fazendo backup dos arquivos originais...")
    for backup_file in backups:
        original_path = os.path.join(backup_dir, backup_file)
        backup_path = os.path.join(backup_original_dir, backup_file)
        shutil.copy2(original_path, backup_path)
        print(f"  - {backup_file} -> backup salvo")
    
    print(f"\nBackup dos originais salvo em: {backup_original_dir}\n")
    
    # Corrigir cada backup
    sucessos = 0
    falhas = 0
    
    for backup_file in backups:
        backup_path = os.path.join(backup_dir, backup_file)
        
        if corrigir_backup(backup_path):
            sucessos += 1
        else:
            falhas += 1
        
        print()  # Linha em branco entre backups
    
    # Resumo
    print("=== RESUMO ===")
    print(f"✅ Backups corrigidos com sucesso: {sucessos}")
    print(f"❌ Backups com falha: {falhas}")
    print(f"📁 Backup dos originais: {backup_original_dir}")
    
    if falhas == 0:
        print("\n🎉 Todos os backups foram corrigidos com sucesso!")
    else:
        print(f"\n⚠️  {falhas} backup(s) falharam. Verifique os logs acima.")

if __name__ == "__main__":
    main()
