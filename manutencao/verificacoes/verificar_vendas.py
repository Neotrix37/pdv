# verificar_vendas.py
import sqlite3
import os
from pathlib import Path

def verificar_tabela_vendas():
    print("=== VERIFICAÇÃO DA TABELA VENDAS ===\n")
    
    # Caminho para o banco de dados
    db_path = Path(os.environ.get('APPDATA', '')) / 'SistemaGestao' / 'database' / 'sistema.db'
    if not db_path.exists():
        db_path = Path("database/sistema.db")
    
    print(f"Conectando ao banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. Verificar se a tabela vendas existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vendas'")
        if not cursor.fetchone():
            print("[ERRO] A tabela 'vendas' não existe!")
            return False
        
        # 2. Verificar colunas da tabela
        print("\n1. ESTRUTURA DA TABELA VENDAS:")
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = cursor.fetchall()
        
        print("{:<3} {:<20} {:<10} {:<5} {:<5} {:<5}".format(
            "ID", "NOME", "TIPO", "NOT NULL", "DEFAULT", "PK"))
        print("-" * 60)
        
        for col in colunas:
            print("{:<3} {:<20} {:<10} {:<8} {:<8} {:<5}".format(
                col[0], col[1], col[2], 
                "NÃO" if col[3] else "SIM",
                str(col[4]) if col[4] else "-",
                "SIM" if col[5] == 1 else ""
            ))
        
        # 3. Verificar se a coluna valor_total existe
        colunas_nomes = [col[1] for col in colunas]
        print("\n2. VERIFICAÇÃO DA COLUNA 'valor_total':")
        
        if 'valor_total' not in colunas_nomes:
            print("   [ERRO] A coluna 'valor_total' não foi encontrada!")
            print("   Ação necessária: Adicionar a coluna 'valor_total'")
            return False
        
        # 4. Verificar se a coluna permite NULL
        cursor.execute("""
            SELECT "notnull" FROM pragma_table_info('vendas') 
            WHERE name = 'valor_total'
        """)
        resultado = cursor.fetchone()
        
        if not resultado:
            print("   [ERRO] Não foi possível verificar as restrições da coluna 'valor_total'")
            return False
            
        permite_null = resultado[0] == 0
        
        if not permite_null:
            print("   [AVISO] A coluna 'valor_total' não permite valores nulos")
            print("   Ação necessária: Alterar a coluna para permitir NULL")
        else:
            print("   [OK] A coluna 'valor_total' está configurada corretamente")
        
        # 5. Verificar se existem registros com valor_total nulo
        cursor.execute("SELECT COUNT(*) FROM vendas WHERE valor_total IS NULL")
        nulos = cursor.fetchone()[0]
        
        print(f"\n3. REGISTROS COM VALOR_TOTAL NULO: {nulos}")
        
        if nulos > 0:
            print(f"   [AVISO] Existem {nulos} registros com valor_total nulo")
            print("   Ação necessária: Atualizar registros com valor_total nulo para 0")
        
        return True
        
    except Exception as e:
        print(f"\n[ERRO] Falha ao verificar a tabela: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== VERIFICADOR DE ESTRUTURA DA TABELA VENDAS ===\n")
    print("Este script irá verificar se a tabela 'vendas' está correta.")
    print("Por favor, aguarde...\n")
    
    if verificar_tabela_vendas():
        print("\n✅ Verificação concluída com sucesso!")
    else:
        print("\n❌ Foram encontrados problemas que precisam ser corrigidos.")
    
    input("\nPressione Enter para sair...")
