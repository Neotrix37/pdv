#!/usr/bin/env python3
"""
Script para corrigir problemas de estoque em backups antigos
"""

import sys
import os
import sqlite3
import shutil
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def corrigir_estoque_backup(backup_path):
    """Corrige problemas de estoque em um backup específico"""
    try:
        print(f"Corrigindo estoque no backup: {os.path.basename(backup_path)}")
        
        # Conectar ao backup
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela produtos existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='produtos'
        """)
        
        if not cursor.fetchone():
            print("  ❌ Tabela produtos não existe neste backup!")
            conn.close()
            return False
        
        # Verificar estrutura da tabela produtos
        cursor.execute("PRAGMA table_info(produtos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'estoque' not in column_names:
            print("  ❌ Coluna 'estoque' não existe na tabela produtos!")
            conn.close()
            return False
        
        # Contar produtos antes da correção
        cursor.execute("SELECT COUNT(*) as total FROM produtos")
        total_produtos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque = 0 OR estoque IS NULL")
        total_zero_antes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque > 0")
        total_com_estoque_antes = cursor.fetchone()[0]
        
        print(f"  - Total de produtos: {total_produtos}")
        print(f"  - Com estoque antes: {total_com_estoque_antes}")
        print(f"  - Sem estoque antes: {total_zero_antes}")
        
        # Corrigir problemas de estoque
        correcoes_feitas = 0
        
        # 1. Corrigir estoque NULL para 0
        cursor.execute("UPDATE produtos SET estoque = 0 WHERE estoque IS NULL")
        null_corrigidos = cursor.rowcount
        if null_corrigidos > 0:
            print(f"  - Corrigidos {null_corrigidos} produtos com estoque NULL")
            correcoes_feitas += null_corrigidos
        
        # 2. Corrigir estoque_minimo NULL para 0 (se a coluna existir)
        if 'estoque_minimo' in column_names:
            cursor.execute("UPDATE produtos SET estoque_minimo = 0 WHERE estoque_minimo IS NULL")
            minimo_corrigidos = cursor.rowcount
            if minimo_corrigidos > 0:
                print(f"  - Corrigidos {minimo_corrigidos} produtos com estoque_minimo NULL")
                correcoes_feitas += minimo_corrigidos
        
        # 3. Corrigir estoque negativo para 0
        cursor.execute("UPDATE produtos SET estoque = 0 WHERE estoque < 0")
        negativo_corrigidos = cursor.rowcount
        if negativo_corrigidos > 0:
            print(f"  - Corrigidos {negativo_corrigidos} produtos com estoque negativo")
            correcoes_feitas += negativo_corrigidos
        
        # 4. Verificar se as colunas são do tipo REAL
        for col in columns:
            if col[1] in ['estoque', 'estoque_minimo'] and col[2].upper() != 'REAL':
                print(f"  - Convertendo {col[1]} de {col[2]} para REAL...")
                try:
                    # Criar coluna temporária
                    cursor.execute(f"""
                        ALTER TABLE produtos
                        ADD COLUMN temp_{col[1]} REAL DEFAULT 0
                    """)
                    
                    # Copiar dados
                    cursor.execute(f"""
                        UPDATE produtos 
                        SET temp_{col[1]} = CAST({col[1]} AS REAL)
                    """)
                    
                    # Remover coluna antiga
                    cursor.execute(f"""
                        ALTER TABLE produtos
                        DROP COLUMN {col[1]}
                    """)
                    
                    # Renomear coluna temporária
                    cursor.execute(f"""
                        ALTER TABLE produtos
                        RENAME COLUMN temp_{col[1]} TO {col[1]}
                    """)
                    
                    print(f"    ✅ {col[1]} convertido para REAL")
                    correcoes_feitas += 1
                    
                except Exception as e:
                    print(f"    ❌ Erro ao converter {col[1]}: {e}")
        
        conn.commit()
        
        # Verificar resultado após correção
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque > 0")
        total_com_estoque_depois = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque = 0 OR estoque IS NULL")
        total_zero_depois = cursor.fetchone()[0]
        
        print(f"  - Com estoque depois: {total_com_estoque_depois}")
        print(f"  - Sem estoque depois: {total_zero_depois}")
        
        if correcoes_feitas > 0:
            print(f"  ✅ {correcoes_feitas} correções realizadas")
        else:
            print(f"  ✅ Nenhuma correção necessária")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao corrigir backup: {e}")
        return False

def main():
    print("=== CORREÇÃO DE ESTOQUE EM BACKUPS ===\n")
    
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
    
    print(f"Encontrados {len(backups)} backups para verificar:\n")
    
    # Fazer backup dos backups originais
    backup_original_dir = os.path.join(backup_dir, "original_estoque_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(backup_original_dir, exist_ok=True)
    
    print("Fazendo backup dos arquivos originais...")
    for backup_file in backups:
        original_path = os.path.join(backup_dir, backup_file)
        backup_path = os.path.join(backup_original_dir, backup_file)
        shutil.copy2(original_path, backup_path)
        print(f"  - {backup_file} -> backup salvo")
    
    print(f"\nBackup dos originais salvo em: {backup_original_dir}\n")
    
    # Perguntar se quer corrigir
    resposta = input("Deseja corrigir os problemas de estoque nos backups? (s/n): ").lower().strip()
    
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("Operação cancelada.")
        return
    
    # Corrigir cada backup
    sucessos = 0
    falhas = 0
    
    for backup_file in backups:
        backup_path = os.path.join(backup_dir, backup_file)
        
        if corrigir_estoque_backup(backup_path):
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
        print("Agora quando você restaurar um backup, o estoque deve estar correto.")
    else:
        print(f"\n⚠️  {falhas} backup(s) falharam. Verifique os logs acima.")
    
    print("\n💡 Dica: Execute o script 'diagnosticar_estoque.py' para verificar o banco atual.")

if __name__ == "__main__":
    main()
