#!/usr/bin/env python3
"""
Script para diagnosticar e corrigir problemas de estoque após restauração de backup
"""

import sys
import os
import sqlite3

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database

def diagnosticar_estoque():
    """Diagnostica problemas de estoque no banco de dados"""
    print("=== DIAGNÓSTICO DE ESTOQUE ===\n")
    
    try:
        db = Database()
        cursor = db.conn.cursor()
        
        # 1. Verificar estrutura da tabela produtos
        print("1. Verificando estrutura da tabela produtos...")
        cursor.execute("PRAGMA table_info(produtos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("Colunas da tabela produtos:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # 2. Verificar se as colunas de estoque existem
        if 'estoque' not in column_names:
            print("❌ ERRO: Coluna 'estoque' não existe na tabela produtos!")
            return False
        
        if 'estoque_minimo' not in column_names:
            print("❌ ERRO: Coluna 'estoque_minimo' não existe na tabela produtos!")
            return False
        
        # 3. Verificar tipos de dados das colunas de estoque
        print("\n2. Verificando tipos de dados das colunas de estoque...")
        for col in columns:
            if col[1] in ['estoque', 'estoque_minimo']:
                print(f"  - {col[1]}: {col[2]} (deve ser REAL)")
                if col[2].upper() != 'REAL':
                    print(f"    ⚠️  AVISO: {col[1]} deveria ser REAL, mas é {col[2]}")
        
        # 4. Contar produtos com estoque zero
        print("\n3. Analisando produtos com estoque zero...")
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque = 0 OR estoque IS NULL")
        total_zero = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM produtos")
        total_produtos = cursor.fetchone()[0]
        
        print(f"  - Total de produtos: {total_produtos}")
        print(f"  - Produtos com estoque zero: {total_zero}")
        print(f"  - Percentual com estoque zero: {(total_zero/total_produtos*100):.1f}%")
        
        # 5. Verificar produtos com estoque NULL
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque IS NULL")
        total_null = cursor.fetchone()[0]
        print(f"  - Produtos com estoque NULL: {total_null}")
        
        # 6. Mostrar alguns exemplos de produtos com estoque zero
        print("\n4. Exemplos de produtos com estoque zero:")
        cursor.execute("""
            SELECT id, codigo, nome, estoque, estoque_minimo 
            FROM produtos 
            WHERE estoque = 0 OR estoque IS NULL 
            LIMIT 5
        """)
        
        produtos_zero = cursor.fetchall()
        for produto in produtos_zero:
            print(f"  - ID {produto[0]}: {produto[2]} (Código: {produto[1]}) - Estoque: {produto[3]} - Mínimo: {produto[4]}")
        
        # 7. Verificar se há produtos com estoque negativo
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque < 0")
        total_negativo = cursor.fetchone()[0]
        print(f"\n5. Produtos com estoque negativo: {total_negativo}")
        
        if total_negativo > 0:
            cursor.execute("""
                SELECT id, codigo, nome, estoque 
                FROM produtos 
                WHERE estoque < 0 
                LIMIT 3
            """)
            for produto in cursor.fetchall():
                print(f"  - ID {produto[0]}: {produto[2]} - Estoque: {produto[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao diagnosticar estoque: {e}")
        return False

def corrigir_estoque():
    """Corrige problemas de estoque no banco de dados"""
    print("\n=== CORREÇÃO DE ESTOQUE ===\n")
    
    try:
        db = Database()
        cursor = db.conn.cursor()
        
        # 1. Corrigir estoque NULL para 0
        print("1. Corrigindo estoque NULL para 0...")
        cursor.execute("UPDATE produtos SET estoque = 0 WHERE estoque IS NULL")
        produtos_corrigidos = cursor.rowcount
        print(f"  ✅ {produtos_corrigidos} produtos corrigidos")
        
        # 2. Corrigir estoque_minimo NULL para 0
        print("2. Corrigindo estoque_minimo NULL para 0...")
        cursor.execute("UPDATE produtos SET estoque_minimo = 0 WHERE estoque_minimo IS NULL")
        minimo_corrigidos = cursor.rowcount
        print(f"  ✅ {minimo_corrigidos} produtos corrigidos")
        
        # 3. Corrigir estoque negativo para 0
        print("3. Corrigindo estoque negativo para 0...")
        cursor.execute("UPDATE produtos SET estoque = 0 WHERE estoque < 0")
        negativo_corrigidos = cursor.rowcount
        print(f"  ✅ {negativo_corrigidos} produtos corrigidos")
        
        # 4. Verificar se as colunas são do tipo REAL
        print("4. Verificando tipos de dados...")
        cursor.execute("PRAGMA table_info(produtos)")
        columns = cursor.fetchall()
        
        for col in columns:
            if col[1] in ['estoque', 'estoque_minimo'] and col[2].upper() != 'REAL':
                print(f"  ⚠️  Convertendo {col[1]} de {col[2]} para REAL...")
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
                    
                    print(f"    ✅ {col[1]} convertido para REAL com sucesso!")
                    
                except Exception as e:
                    print(f"    ❌ Erro ao converter {col[1]}: {e}")
        
        db.conn.commit()
        
        # 5. Verificar resultado final
        print("\n5. Verificando resultado final...")
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque = 0 OR estoque IS NULL")
        total_zero_final = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM produtos")
        total_produtos_final = cursor.fetchone()[0]
        
        print(f"  - Total de produtos: {total_produtos_final}")
        print(f"  - Produtos com estoque zero: {total_zero_final}")
        print(f"  - Percentual com estoque zero: {(total_zero_final/total_produtos_final*100):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir estoque: {e}")
        return False

def verificar_backup_estoque(backup_path):
    """Verifica o estoque em um backup específico"""
    print(f"\n=== VERIFICANDO BACKUP: {os.path.basename(backup_path)} ===\n")
    
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # Verificar estrutura
        cursor.execute("PRAGMA table_info(produtos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'estoque' not in column_names:
            print("❌ ERRO: Tabela produtos não tem coluna 'estoque'!")
            return False
        
        # Contar produtos
        cursor.execute("SELECT COUNT(*) as total FROM produtos")
        total_produtos = cursor.fetchone()[0]
        
        # Contar produtos com estoque zero
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque = 0 OR estoque IS NULL")
        total_zero = cursor.fetchone()[0]
        
        # Contar produtos com estoque
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque > 0")
        total_com_estoque = cursor.fetchone()[0]
        
        print(f"Total de produtos: {total_produtos}")
        print(f"Produtos com estoque > 0: {total_com_estoque}")
        print(f"Produtos com estoque zero: {total_zero}")
        print(f"Percentual com estoque: {(total_com_estoque/total_produtos*100):.1f}%")
        
        # Mostrar alguns produtos com estoque
        cursor.execute("""
            SELECT id, codigo, nome, estoque 
            FROM produtos 
            WHERE estoque > 0 
            ORDER BY estoque DESC 
            LIMIT 5
        """)
        
        print("\nProdutos com estoque (top 5):")
        for produto in cursor.fetchall():
            print(f"  - {produto[2]} (ID: {produto[0]}) - Estoque: {produto[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar backup: {e}")
        return False

def main():
    print("=== DIAGNÓSTICO E CORREÇÃO DE ESTOQUE ===\n")
    
    # 1. Diagnosticar o banco atual
    if not diagnosticar_estoque():
        print("❌ Falha no diagnóstico!")
        return
    
    # 2. Perguntar se quer corrigir
    print("\n" + "="*50)
    resposta = input("Deseja corrigir os problemas de estoque? (s/n): ").lower().strip()
    
    if resposta in ['s', 'sim', 'y', 'yes']:
        if corrigir_estoque():
            print("\n✅ Correção concluída com sucesso!")
        else:
            print("\n❌ Falha na correção!")
    
    # 3. Verificar backups se existirem
    backup_dir = os.path.join(os.path.dirname(__file__), "backups")
    if os.path.exists(backup_dir):
        backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        
        if backups:
            print(f"\nEncontrados {len(backups)} backups.")
            resposta = input("Deseja verificar o estoque nos backups? (s/n): ").lower().strip()
            
            if resposta in ['s', 'sim', 'y', 'yes']:
                print("\nVerificando backups...")
                for backup_file in backups[:3]:  # Verificar apenas os 3 primeiros
                    backup_path = os.path.join(backup_dir, backup_file)
                    verificar_backup_estoque(backup_path)
    
    print("\n🎉 Diagnóstico concluído!")

if __name__ == "__main__":
    main()
