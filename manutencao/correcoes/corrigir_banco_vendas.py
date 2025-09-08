"""
Script para corrigir problemas na tabela de vendas:
1. Adiciona a coluna 'total' se não existir
2. Atualiza os totais das vendas existentes
3. Otimiza a estrutura do banco de dados
"""

import sqlite3
import os
from pathlib import Path

def corrigir_banco():
    print("=== CORREÇÃO DO BANCO DE DADOS ===\n")
    
    # Localização do banco de dados
    db_path = Path(os.environ.get('APPDATA', '')) / 'SistemaGestao' / 'database' / 'sistema.db'
    if not db_path.exists():
        db_path = Path("database/sistema.db")
    
    print(f"Conectando ao banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. Verificar e adicionar a coluna 'total' se não existir
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'total' not in colunas:
            print("Adicionando coluna 'total' a tabela vendas...")
            cursor.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0")
            print("[OK] Coluna 'total' adicionada com sucesso!")
        
        # 2. Atualizar totais das vendas existentes
        print("\nAtualizando totais das vendas...")
        cursor.execute("""
            UPDATE vendas 
            SET total = (
                SELECT COALESCE(SUM(vi.quantidade * vi.preco_unitario), 0)
                FROM itens_venda vi
                WHERE vi.venda_id = vendas.id
            )
            WHERE total IS NULL OR total = 0
        """)
        print(f"[OK] {cursor.rowcount} vendas atualizadas")
        
        # 3. Criar índices para melhorar desempenho
        print("\nOtimizando índices...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data_venda)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_venda_itens_venda_id ON itens_venda(venda_id)")
            print("[OK] Indices otimizados")
        except Exception as e:
            print(f"⚠️  Aviso ao criar índices: {e}")
        
        conn.commit()
        print("\n[SUCESSO] Banco de dados otimizado com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n[ERRO] Erro ao atualizar o banco de dados: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if corrigir_banco():
        print("\nPor favor, reinicie o sistema para aplicar as alterações.")
    else:
        print("\n[ERRO] Falha ao atualizar o banco de dados.")
    
    input("\nPressione Enter para sair...")
