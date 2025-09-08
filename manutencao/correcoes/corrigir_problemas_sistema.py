#!/usr/bin/env python3
"""
Script para corrigir problemas no sistema PDV:
1. Erro 'no such column named total' ao finalizar vendas
2. Erro ao gerar relatório financeiro
3. Valores incorretos após restauração de backup
"""

import sys
import os
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def localizar_banco():
    """Localiza o arquivo do banco de dados"""
    # Verificar no APPDATA (Windows)
    db_path = Path(os.environ.get('APPDATA', '')) / 'SistemaGestao' / 'database' / 'sistema.db'
    if db_path.exists():
        return db_path
    
    # Verificar no diretório local
    db_path = Path(os.path.dirname(os.path.abspath(__file__))) / 'database' / 'sistema.db'
    if db_path.exists():
        return db_path
    
    # Verificar no diretório raiz
    db_path = Path(os.path.dirname(os.path.abspath(__file__))) / 'sistema.db'
    if db_path.exists():
        return db_path
    
    return None

def corrigir_coluna_total():
    """Corrige o problema da coluna 'total' na tabela de vendas"""
    print("\n=== CORRIGINDO COLUNA 'TOTAL' NA TABELA DE VENDAS ===")
    
    db_path = localizar_banco()
    if not db_path:
        print("❌ Banco de dados não encontrado!")
        return False
    
    print(f"Conectando ao banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. Verificar se a tabela vendas existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vendas'")
        if not cursor.fetchone():
            print("❌ Tabela 'vendas' não encontrada!")
            return False
        
        # 2. Verificar e adicionar a coluna 'total' se não existir
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'total' not in colunas:
            print("Adicionando coluna 'total' à tabela vendas...")
            cursor.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0")
            print("✅ Coluna 'total' adicionada com sucesso!")
        else:
            print("✅ Coluna 'total' já existe na tabela vendas.")
        
        # 3. Atualizar totais das vendas existentes
        print("\nAtualizando totais das vendas...")
        cursor.execute("""
            UPDATE vendas 
            SET total = (
                SELECT COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0)
                FROM itens_venda iv
                WHERE iv.venda_id = vendas.id
                AND (iv.status IS NULL OR iv.status != 'Removido')
            )
            WHERE total IS NULL OR total = 0
        """)
        print(f"✅ {cursor.rowcount} vendas atualizadas")
        
        # 4. Criar índices para melhorar desempenho
        print("\nOtimizando índices...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data_venda)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_total ON vendas(total)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_venda_itens_venda_id ON itens_venda(venda_id)")
            print("✅ Índices otimizados")
        except Exception as e:
            print(f"⚠️  Aviso ao criar índices: {e}")
        
        conn.commit()
        print("\n✅ Coluna 'total' corrigida com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao corrigir coluna 'total': {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def corrigir_relatorio_financeiro():
    """Corrige problemas no relatório financeiro"""
    print("\n=== CORRIGINDO RELATÓRIO FINANCEIRO ===")
    
    db_path = localizar_banco()
    if not db_path:
        print("❌ Banco de dados não encontrado!")
        return False
    
    print(f"Conectando ao banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar se as consultas do relatório financeiro funcionam
        print("Testando consulta de vendas...")
        try:
            cursor.execute("""
                SELECT 
                    SUM(v.total) as total_vendas
                FROM vendas v
                WHERE v.status != 'Anulada' OR v.status IS NULL
                AND DATE(v.data_venda) = DATE('now')
            """)
            resultado = cursor.fetchone()
            print(f"✅ Consulta de vendas funcionou: {resultado}")
        except Exception as e:
            print(f"❌ Erro na consulta de vendas: {e}")
            
            # Tentar corrigir a consulta
            print("Tentando corrigir a consulta...")
            try:
                # Verificar se a coluna total existe
                cursor.execute("PRAGMA table_info(vendas)")
                colunas = [coluna[1] for coluna in cursor.fetchall()]
                
                if 'total' not in colunas:
                    print("A coluna 'total' não existe na tabela vendas. Adicionando...")
                    cursor.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0")
                    
                    # Atualizar os valores da coluna total
                    cursor.execute("""
                        UPDATE vendas 
                        SET total = (
                            SELECT COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0)
                            FROM itens_venda iv
                            WHERE iv.venda_id = vendas.id
                            AND (iv.status IS NULL OR iv.status != 'Removido')
                        )
                    """)
                    conn.commit()
                    print("✅ Coluna 'total' adicionada e valores atualizados")
                    
                # Testar a consulta novamente
                cursor.execute("""
                    SELECT 
                        SUM(v.total) as total_vendas
                    FROM vendas v
                    WHERE v.status != 'Anulada' OR v.status IS NULL
                    AND DATE(v.data_venda) = DATE('now')
                """)
                resultado = cursor.fetchone()
                print(f"✅ Consulta de vendas corrigida: {resultado}")
            except Exception as e2:
                print(f"❌ Não foi possível corrigir a consulta: {e2}")
                return False
        
        print("\n✅ Relatório financeiro corrigido com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao corrigir relatório financeiro: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def corrigir_backups():
    """Corrige problemas nos backups"""
    print("\n=== CORRIGINDO BACKUPS ===")
    
    # Verificar se o diretório de backups existe
    backup_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "backups"
    if not backup_dir.exists():
        print("❌ Diretório de backups não encontrado!")
        return False
    
    # Listar todos os backups
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    
    if not backups:
        print("✅ Nenhum backup encontrado para corrigir.")
        return True
    
    print(f"Encontrados {len(backups)} backups para corrigir.")
    
    # Fazer backup dos backups originais
    backup_original_dir = backup_dir / f"original_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_original_dir.mkdir(exist_ok=True)
    
    print("Fazendo backup dos arquivos originais...")
    for backup_file in backups:
        original_path = backup_dir / backup_file
        backup_path = backup_original_dir / backup_file
        shutil.copy2(str(original_path), str(backup_path))
        print(f"  - {backup_file} -> backup salvo")
    
    print(f"\nBackup dos originais salvo em: {backup_original_dir}")
    
    # Corrigir cada backup
    sucessos = 0
    falhas = 0
    
    for backup_file in backups:
        backup_path = backup_dir / backup_file
        print(f"\nCorrigindo backup: {backup_file}")
        
        try:
            # Conectar ao backup
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            
            # 1. Verificar e adicionar a coluna 'total' se não existir
            cursor.execute("PRAGMA table_info(vendas)")
            colunas = [coluna[1] for coluna in cursor.fetchall()]
            
            if 'total' not in colunas:
                print("  - Adicionando coluna 'total' à tabela vendas...")
                cursor.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0")
                print("    ✅ Coluna 'total' adicionada com sucesso!")
            else:
                print("  ✅ Coluna 'total' já existe na tabela vendas.")
            
            # 2. Atualizar totais das vendas existentes
            print("  - Atualizando totais das vendas...")
            cursor.execute("""
                UPDATE vendas 
                SET total = (
                    SELECT COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0)
                    FROM itens_venda iv
                    WHERE iv.venda_id = vendas.id
                    AND (iv.status IS NULL OR iv.status != 'Removido')
                )
                WHERE total IS NULL OR total = 0
            """)
            print(f"    ✅ {cursor.rowcount} vendas atualizadas")
            
            # 3. Verificar se a tabela retiradas_caixa existe
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
                
                print("    ✅ Tabela criada com sucesso!")
            else:
                print("  ✅ Tabela retiradas_caixa já existe!")
                
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
                        print(f"    - Adicionando coluna '{coluna}'...")
                        try:
                            cursor.execute(f"""
                                ALTER TABLE retiradas_caixa
                                ADD COLUMN {coluna} {definicao}
                            """)
                            print(f"      ✅ Coluna '{coluna}' adicionada!")
                        except Exception as e:
                            print(f"      ❌ Erro ao adicionar coluna '{coluna}': {e}")
            
            # 4. Criar índices para melhorar desempenho
            print("  - Otimizando índices...")
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data_venda)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_total ON vendas(total)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_venda_itens_venda_id ON itens_venda(venda_id)")
                print("    ✅ Índices otimizados")
            except Exception as e:
                print(f"    ⚠️  Aviso ao criar índices: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"  ✅ Backup {backup_file} corrigido com sucesso!")
            sucessos += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao corrigir backup {backup_file}: {e}")
            falhas += 1
    
    # Resumo
    print("\n=== RESUMO DA CORREÇÃO DE BACKUPS ===")
    print(f"✅ Backups corrigidos com sucesso: {sucessos}")
    print(f"❌ Backups com falha: {falhas}")
    print(f"📁 Backup dos originais: {backup_original_dir}")
    
    if falhas == 0:
        print("\n🎉 Todos os backups foram corrigidos com sucesso!")
        return True
    else:
        print(f"\n⚠️  {falhas} backup(s) falharam. Verifique os logs acima.")
        return False

def main():
    print("=== CORREÇÃO DE PROBLEMAS DO SISTEMA PDV ===")
    print("Este script irá corrigir os seguintes problemas:")
    print("1. Erro 'no such column named total' ao finalizar vendas")
    print("2. Erro ao gerar relatório financeiro")
    print("3. Valores incorretos após restauração de backup")
    print("\nIniciando correções...")
    
    # Corrigir coluna total na tabela vendas
    coluna_total_ok = corrigir_coluna_total()
    
    # Corrigir relatório financeiro
    relatorio_ok = corrigir_relatorio_financeiro()
    
    # Corrigir backups
    backups_ok = corrigir_backups()
    
    # Resumo final
    print("\n=== RESUMO FINAL ===")
    print(f"1. Coluna 'total' na tabela vendas: {'✅ Corrigido' if coluna_total_ok else '❌ Falha'}")
    print(f"2. Relatório financeiro: {'✅ Corrigido' if relatorio_ok else '❌ Falha'}")
    print(f"3. Backups: {'✅ Corrigido' if backups_ok else '❌ Falha'}")
    
    if coluna_total_ok and relatorio_ok and backups_ok:
        print("\n🎉 Todos os problemas foram corrigidos com sucesso!")
        print("Por favor, reinicie o sistema para aplicar todas as alterações.")
    else:
        print("\n⚠️  Alguns problemas não puderam ser corrigidos. Verifique os logs acima.")

if __name__ == "__main__":
    main()
    input("\nPressione Enter para sair...")