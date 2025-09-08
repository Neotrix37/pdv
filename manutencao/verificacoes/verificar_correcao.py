#!/usr/bin/env python3
"""
Script para verificar se as correções foram aplicadas corretamente
"""

import sys
import os
import sqlite3
from pathlib import Path

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

def verificar_banco():
    """Verifica se o banco de dados tem a estrutura correta"""
    print("=== VERIFICAÇÃO DO BANCO DE DADOS ===")
    
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
        else:
            print("✅ Tabela 'vendas' encontrada.")
        
        # 2. Verificar se a coluna 'total' existe na tabela vendas
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'total' not in colunas:
            print("❌ Coluna 'total' não encontrada na tabela vendas!")
            return False
        else:
            print("✅ Coluna 'total' encontrada na tabela vendas.")
        
        # 3. Verificar se a tabela retiradas_caixa existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='retiradas_caixa'")
        if not cursor.fetchone():
            print("❌ Tabela 'retiradas_caixa' não encontrada!")
            return False
        else:
            print("✅ Tabela 'retiradas_caixa' encontrada.")
        
        # 4. Verificar se os índices existem
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_vendas_total'")
        if not cursor.fetchone():
            print("⚠️ Índice 'idx_vendas_total' não encontrado.")
        else:
            print("✅ Índice 'idx_vendas_total' encontrado.")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_vendas_data'")
        if not cursor.fetchone():
            print("⚠️ Índice 'idx_vendas_data' não encontrado.")
        else:
            print("✅ Índice 'idx_vendas_data' encontrado.")
        
        # 5. Testar consulta de relatório financeiro
        print("\nTestando consulta de relatório financeiro...")
        try:
            cursor.execute("""
                SELECT 
                    SUM(v.total) as total_vendas
                FROM vendas v
                WHERE v.status != 'Anulada' OR v.status IS NULL
                AND DATE(v.data_venda) = DATE('now')
            """)
            resultado = cursor.fetchone()
            print(f"✅ Consulta de relatório financeiro funcionou: {resultado}")
        except Exception as e:
            print(f"❌ Erro na consulta de relatório financeiro: {e}")
            return False
        
        print("\n✅ Banco de dados verificado com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar banco de dados: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verificar_backups():
    """Verifica se os backups têm a estrutura correta"""
    print("\n=== VERIFICAÇÃO DOS BACKUPS ===")
    
    # Verificar se o diretório de backups existe
    backup_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "backups"
    if not backup_dir.exists():
        print("❌ Diretório de backups não encontrado!")
        return False
    
    # Listar todos os backups
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    
    if not backups:
        print("✅ Nenhum backup encontrado para verificar.")
        return True
    
    print(f"Encontrados {len(backups)} backups para verificar.")
    
    # Verificar cada backup
    sucessos = 0
    falhas = 0
    
    for backup_file in backups:
        backup_path = backup_dir / backup_file
        print(f"\nVerificando backup: {backup_file}")
        
        try:
            # Conectar ao backup
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            
            # 1. Verificar se a coluna 'total' existe na tabela vendas
            cursor.execute("PRAGMA table_info(vendas)")
            colunas = [coluna[1] for coluna in cursor.fetchall()]
            
            if 'total' not in colunas:
                print(f"  ❌ Coluna 'total' não encontrada em {backup_file}!")
                falhas += 1
                continue
            else:
                print(f"  ✅ Coluna 'total' encontrada em {backup_file}.")
            
            # 2. Verificar se a tabela retiradas_caixa existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='retiradas_caixa'")
            if not cursor.fetchone():
                print(f"  ❌ Tabela 'retiradas_caixa' não encontrada em {backup_file}!")
                falhas += 1
                continue
            else:
                print(f"  ✅ Tabela 'retiradas_caixa' encontrada em {backup_file}.")
            
            conn.close()
            print(f"  ✅ Backup {backup_file} verificado com sucesso!")
            sucessos += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao verificar backup {backup_file}: {e}")
            falhas += 1
    
    # Resumo
    print("\n=== RESUMO DA VERIFICAÇÃO DE BACKUPS ===")
    print(f"✅ Backups verificados com sucesso: {sucessos}")
    print(f"❌ Backups com problemas: {falhas}")
    
    if falhas == 0:
        print("\n🎉 Todos os backups estão corretos!")
        return True
    else:
        print(f"\n⚠️  {falhas} backup(s) têm problemas. Execute o script 'corrigir_problemas_sistema.py' para corrigi-los.")
        return False

def main():
    print("=== VERIFICAÇÃO DE CORREÇÕES DO SISTEMA PDV ===")
    print("Este script irá verificar se as correções foram aplicadas corretamente.")
    print("\nIniciando verificações...")
    
    # Verificar banco de dados
    banco_ok = verificar_banco()
    
    # Verificar backups
    backups_ok = verificar_backups()
    
    # Resumo final
    print("\n=== RESUMO FINAL ===")
    print(f"1. Banco de dados: {'✅ OK' if banco_ok else '❌ Problemas encontrados'}")
    print(f"2. Backups: {'✅ OK' if backups_ok else '❌ Problemas encontrados'}")
    
    if banco_ok and backups_ok:
        print("\n🎉 O sistema está corretamente configurado!")
    else:
        print("\n⚠️  Foram encontrados problemas. Execute o script 'corrigir_problemas_sistema.py' para corrigi-los.")

if __name__ == "__main__":
    main()
    input("\nPressione Enter para sair...")