#!/usr/bin/env python3
"""
Script para corrigir o índice corrompido da coluna estoque
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def corrigir_indice_estoque():
    """Corrige o índice corrompido da coluna estoque"""
    print("=== CORREÇÃO DO ÍNDICE DE ESTOQUE ===\n")
    
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
        
        # Verificar índices existentes
        print("\n2. Verificando índices existentes:")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
        indices = cursor.fetchall()
        
        for idx in indices:
            print(f"  - {idx[0]}: {idx[1]}")
        
        # Verificar se existe o índice problemático
        idx_problema = None
        for idx in indices:
            if 'idx_produtos_estoque' in idx[0]:
                idx_problema = idx
                break
        
        if idx_problema:
            print(f"\n3. Encontrado índice problemático: {idx_problema[0]}")
            print(f"   SQL: {idx_problema[1]}")
            
            # Remover o índice problemático
            try:
                cursor.execute(f"DROP INDEX {idx_problema[0]}")
                print(f"  [OK] Índice {idx_problema[0]} removido com sucesso!")
            except Exception as e:
                print(f"  ❌ Erro ao remover índice: {e}")
                return False
        else:
            print("\n3. Nenhum índice problemático encontrado")
        
        # Verificar estrutura da tabela produtos
        print("\n4. Verificando estrutura da tabela produtos:")
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
        temp_cols = [col for col in colunas if col[1].startswith('temp_')]
        if temp_cols:
            print(f"\n5. Encontradas {len(temp_cols)} colunas temporárias:")
            for col in temp_cols:
                print(f"  - {col[1]} ({col[2]})")
            
            # Remover colunas temporárias
            print("\n6. Removendo colunas temporárias:")
            for col in temp_cols:
                try:
                    cursor.execute(f"ALTER TABLE produtos DROP COLUMN {col[1]}")
                    print(f"  [OK] Coluna {col[1]} removida")
                except Exception as e:
                    print(f"  ❌ Erro ao remover {col[1]}: {e}")
        
        # Verificar se estoque precisa ser convertido
        print("\n7. Verificando conversão de estoque:")
        
        if estoque_col and estoque_col[2].upper() == 'INTEGER':
            print("  - Convertendo estoque de INTEGER para REAL")
            
            try:
                # Fazer backup dos valores
                cursor.execute("SELECT id, estoque FROM produtos")
                produtos_estoque = cursor.fetchall()
                print(f"  - Backup de {len(produtos_estoque)} produtos")
                
                # Criar nova coluna REAL
                cursor.execute("ALTER TABLE produtos ADD COLUMN estoque_real REAL DEFAULT 0")
                print("  [OK] Nova coluna estoque_real criada")
                
                # Copiar valores
                for produto in produtos_estoque:
                    valor = float(produto[1]) if produto[1] is not None else 0.0
                    cursor.execute("UPDATE produtos SET estoque_real = ? WHERE id = ?", (valor, produto[0]))
                
                # Remover coluna antiga
                cursor.execute("ALTER TABLE produtos DROP COLUMN estoque")
                print("  [OK] Coluna estoque antiga removida")
                
                # Renomear nova coluna
                cursor.execute("ALTER TABLE produtos RENAME COLUMN estoque_real TO estoque")
                print("  [OK] Coluna renomeada para estoque")
                
            except Exception as e:
                conn.rollback()
                print(f"  ❌ Erro na conversão: {e}")
                return False
        else:
            print("  [OK] Coluna estoque já é REAL")
        
        # Verificar estoque_minimo
        if estoque_minimo_col and estoque_minimo_col[2].upper() == 'INTEGER':
            print("  - Convertendo estoque_minimo de INTEGER para REAL")
            
            try:
                cursor.execute("ALTER TABLE produtos ADD COLUMN estoque_minimo_real REAL DEFAULT 0")
                cursor.execute("UPDATE produtos SET estoque_minimo_real = CAST(estoque_minimo AS REAL)")
                cursor.execute("ALTER TABLE produtos DROP COLUMN estoque_minimo")
                cursor.execute("ALTER TABLE produtos RENAME COLUMN estoque_minimo_real TO estoque_minimo")
                print("  [OK] Conversão de estoque_minimo concluída")
            except Exception as e:
                conn.rollback()
                print(f"  ❌ Erro na conversão de estoque_minimo: {e}")
                return False
        else:
            print("  [OK] Coluna estoque_minimo já é REAL")
        
        # Recriar índice se necessário
        print("\n8. Recriando índice de estoque:")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_produtos_estoque 
                ON produtos(estoque)
            """)
            print("  [OK] Índice de estoque recriado com sucesso!")
        except Exception as e:
            print(f"  ❌ Erro ao recriar índice: {e}")
        
        # Commit das alterações
        conn.commit()
        print("\n9. Alteracoes confirmadas no banco")
        
        # Verificar resultado final
        print("\n10. Verificando resultado final:")
        cursor.execute("PRAGMA table_info(produtos)")
        colunas_finais = cursor.fetchall()
        
        for col in colunas_finais:
            if col[1] in ['estoque', 'estoque_minimo']:
                print(f"  - {col[1]}: {col[2]}")
        
        # Verificar produtos com estoque
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque > 0")
        produtos_com_estoque = cursor.fetchone()[0]
        print(f"\n11. Produtos com estoque: {produtos_com_estoque}")
        
        if produtos_com_estoque > 0:
            cursor.execute("SELECT SUM(estoque * preco_custo) FROM produtos WHERE ativo = 1")
            valor_estoque = cursor.fetchone()[0] or 0
            print(f"  - Valor total em estoque: MT {valor_estoque:.2f}")
        
        conn.close()
        
        print("\n[SUCESSO] Correcao do indice concluida com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na correção: {e}")
        return False

def main():
    print("=== CORREÇÃO DO ÍNDICE DE ESTOQUE ===\n")
    
    if corrigir_indice_estoque():
        print("\n[SUCESSO] Problema do indice corrigido! Agora o estoque deve persistir entre execucoes.")
        print("\nPROXIMOS PASSOS:")
        print("1. Execute o sistema: python main.py")
        print("2. Restaure o backup com produtos: backup_20250820_170858.db")
        print("3. Feche e reabra o sistema para verificar se o estoque persiste")
    else:
        print("\n[ERRO] Falha na correcao. Verifique os erros acima.")

if __name__ == "__main__":
    main()
