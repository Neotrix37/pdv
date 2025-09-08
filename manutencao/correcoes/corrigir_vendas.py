# corrigir_vendas.py
import sqlite3
import os
from pathlib import Path
from datetime import datetime

def corrigir_tabela_vendas():
    print("=== CORREÇÃO DA TABELA VENDAS ===\n")
    
    # Caminho para o banco de dados
    db_path = Path(os.environ.get('APPDATA', '')) / 'SistemaGestao' / 'database' / 'sistema.db'
    if not db_path.exists():
        db_path = Path("database/sistema.db")
    
    print(f"Conectando ao banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. Adicionar coluna valor_total se não existir
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'valor_total' not in colunas:
            print("1. Adicionando coluna 'valor_total'...")
            cursor.execute("ALTER TABLE vendas ADD COLUMN valor_total REAL DEFAULT 0")
            print("   [OK] Coluna 'valor_total' adicionada")
            
            # Atualizar valores existentes
            print("   Atualizando valores existentes...")
            cursor.execute("""
                UPDATE vendas 
                SET valor_total = COALESCE((
                    SELECT SUM(quantidade * preco_unitario)
                    FROM itens_venda
                    WHERE venda_id = vendas.id
                ), 0)
                WHERE valor_total IS NULL
            """)
            print(f"   [OK] {cursor.rowcount} registros atualizados")
        
        # 2. Verificar outras colunas obrigatórias
        print("\n2. Verificando colunas obrigatórias...")
        colunas_obrigatorias = {
            'cliente_id': 'INTEGER DEFAULT 1',
            'usuario_id': 'INTEGER NOT NULL DEFAULT 1',
            'data_venda': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'status': 'TEXT DEFAULT "Pendente"'
        }
        
        for coluna, tipo in colunas_obrigatorias.items():
            if coluna not in colunas:
                print(f"   Adicionando coluna '{coluna}'...")
                cursor.execute(f"ALTER TABLE vendas ADD COLUMN {coluna} {tipo}")
                print(f"   [OK] Coluna '{coluna}' adicionada")
                
                # Se for data_venda, atualizar registros antigos
                if coluna == 'data_venda':
                    cursor.execute("""
                        UPDATE vendas 
                        SET data_venda = datetime('now')
                        WHERE data_venda IS NULL
                    """)
        
        conn.commit()
        print("\n[SUCESSO] Tabela 'vendas' corrigida com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n[ERRO] Falha ao corrigir a tabela: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== CORRETOR DE BANCO DE DADOS ===\n")
    print("Este script irá corrigir a estrutura da tabela de vendas.")
    print("Por favor, certifique-se de fazer backup do banco de dados antes de continuar.\n")
    
    input("Pressione Enter para continuar ou Ctrl+C para cancelar...")
    
    if corrigir_tabela_vendas():
        print("\n✅ Processo concluído com sucesso!")
        print("Por favor, REINICIE o sistema para aplicar as alterações.")
    else:
        print("\n❌ Ocorreu um erro durante a correção.")
        print("Verifique as mensagens de erro acima e tente novamente.")
    
    input("\nPressione Enter para sair...")
