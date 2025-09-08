#!/usr/bin/env python3
"""
Script para corrigir o problema de conversão da coluna estoque
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def corrigir_conversao_estoque():
    """Corrige o problema de conversão da coluna estoque"""
    print("=== CORREÇÃO DA CONVERSÃO DE ESTOQUE ===\n")
    
    try:
        # Caminho do banco APPDATA
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
        appdata_db = app_data_db_dir / 'sistema.db'
        
        print(f"1. Conectando ao banco: {appdata_db}")
        
        if not appdata_db.exists():
            print("❌ Banco APPDATA não existe!")
            return False
        
        # Conectar ao banco
        conn = sqlite3.connect(str(appdata_db))
        cursor = conn.cursor()
        
        # Verificar estrutura atual da tabela produtos
        print("\n2. Verificando estrutura da tabela produtos:")
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = cursor.fetchall()
        
        estoque_col = None
        estoque_minimo_col = None
        
        for col in colunas:
            print(f"  - {col[1]} ({col[2]})")
            if col[1] == 'estoque':
                estoque_col = col
            elif col[1] == 'estoque_minimo':
                estoque_minimo_col = col
        
        # Verificar se há colunas temporárias
        print("\n3. Verificando colunas temporárias:")
        temp_cols = [col for col in colunas if col[1].startswith('temp_')]
        if temp_cols:
            print("  ❌ Encontradas colunas temporárias que precisam ser limpas:")
            for col in temp_cols:
                print(f"    - {col[1]} ({col[2]})")
            
            # Limpar colunas temporárias
            print("\n4. Limpando colunas temporárias:")
            for col in temp_cols:
                try:
                    cursor.execute(f"ALTER TABLE produtos DROP COLUMN {col[1]}")
                    print(f"  ✅ Coluna {col[1]} removida")
                except Exception as e:
                    print(f"  ❌ Erro ao remover {col[1]}: {e}")
        
        # Verificar se estoque precisa ser convertido
        print("\n5. Verificando necessidade de conversão:")
        
        if estoque_col and estoque_col[2].upper() == 'INTEGER':
            print(f"  - Coluna estoque é INTEGER, precisa ser convertida para REAL")
            
            # Fazer backup dos valores atuais
            cursor.execute("SELECT id, estoque FROM produtos")
            produtos_estoque = cursor.fetchall()
            print(f"  - Backup de {len(produtos_estoque)} produtos com estoque")
            
            # Converter estoque para REAL
            try:
                # Criar nova coluna REAL
                cursor.execute("ALTER TABLE produtos ADD COLUMN estoque_real REAL DEFAULT 0")
                print("  ✅ Nova coluna estoque_real criada")
                
                # Copiar valores
                for produto in produtos_estoque:
                    cursor.execute("UPDATE produtos SET estoque_real = ? WHERE id = ?", 
                                 (float(produto[1]) if produto[1] is not None else 0.0, produto[0]))
                
                # Remover coluna antiga
                cursor.execute("ALTER TABLE produtos DROP COLUMN estoque")
                print("  ✅ Coluna estoque antiga removida")
                
                # Renomear nova coluna
                cursor.execute("ALTER TABLE produtos RENAME COLUMN estoque_real TO estoque")
                print("  ✅ Coluna renomeada para estoque")
                
                conn.commit()
                print("  ✅ Conversão de estoque concluída com sucesso!")
                
            except Exception as e:
                conn.rollback()
                print(f"  ❌ Erro na conversão de estoque: {e}")
                return False
        else:
            print("  ✅ Coluna estoque já é REAL ou não existe")
        
        # Verificar estoque_minimo
        if estoque_minimo_col and estoque_minimo_col[2].upper() == 'INTEGER':
            print(f"  - Coluna estoque_minimo é INTEGER, precisa ser convertida para REAL")
            
            try:
                # Criar nova coluna REAL
                cursor.execute("ALTER TABLE produtos ADD COLUMN estoque_minimo_real REAL DEFAULT 0")
                print("  ✅ Nova coluna estoque_minimo_real criada")
                
                # Copiar valores
                cursor.execute("UPDATE produtos SET estoque_minimo_real = CAST(estoque_minimo AS REAL)")
                
                # Remover coluna antiga
                cursor.execute("ALTER TABLE produtos DROP COLUMN estoque_minimo")
                print("  ✅ Coluna estoque_minimo antiga removida")
                
                # Renomear nova coluna
                cursor.execute("ALTER TABLE produtos RENAME COLUMN estoque_minimo_real TO estoque_minimo")
                print("  ✅ Coluna renomeada para estoque_minimo")
                
                conn.commit()
                print("  ✅ Conversão de estoque_minimo concluída com sucesso!")
                
            except Exception as e:
                conn.rollback()
                print(f"  ❌ Erro na conversão de estoque_minimo: {e}")
                return False
        else:
            print("  ✅ Coluna estoque_minimo já é REAL ou não existe")
        
        # Verificar resultado final
        print("\n6. Verificando resultado final:")
        cursor.execute("PRAGMA table_info(produtos)")
        colunas_finais = cursor.fetchall()
        
        for col in colunas_finais:
            if col[1] in ['estoque', 'estoque_minimo']:
                print(f"  - {col[1]}: {col[2]}")
        
        # Verificar se há produtos com estoque
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque > 0")
        produtos_com_estoque = cursor.fetchone()[0]
        print(f"\n7. Produtos com estoque: {produtos_com_estoque}")
        
        if produtos_com_estoque > 0:
            cursor.execute("SELECT SUM(estoque * preco_custo) FROM produtos WHERE ativo = 1")
            valor_estoque = cursor.fetchone()[0] or 0
            print(f"  - Valor total em estoque: MT {valor_estoque:.2f}")
        
        conn.close()
        
        print("\n🎉 Correção concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na correção: {e}")
        return False

def main():
    print("=== CORREÇÃO DO PROBLEMA DE ESTOQUE ===\n")
    
    if corrigir_conversao_estoque():
        print("\n✅ Problema corrigido! Agora o estoque deve persistir entre execuções.")
        print("\n📋 Próximos passos:")
        print("1. Execute o sistema: python main.py")
        print("2. Restaure o backup com produtos: backup_20250820_170858.db")
        print("3. Feche e reabra o sistema para verificar se o estoque persiste")
    else:
        print("\n❌ Falha na correção. Verifique os erros acima.")

if __name__ == "__main__":
    main()
