# corrigir_valor_total.py
import sqlite3
import os
from pathlib import Path

def corrigir_coluna_valor_total():
    print("=== CORREÇÃO DA COLUNA VALOR_TOTAL ===\n")
    
    # Caminho para o banco de dados
    db_path = Path(os.environ.get('APPDATA', '')) / 'SistemaGestao' / 'database' / 'sistema.db'
    if not db_path.exists():
        db_path = Path("database/sistema.db")
    
    print(f"Conectando ao banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. Fazer backup da tabela atual
        print("\n1. Fazendo backup da tabela 'vendas'...")
        cursor.execute("SELECT * FROM vendas")
        vendas_data = cursor.fetchall()
        
        # Obter os nomes das colunas
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        # 2. Criar uma nova tabela com a estrutura correta
        print("2. Criando nova tabela com estrutura corrigida...")
        
        # Desativar chaves estrangeiras temporariamente
        cursor.execute("PRAGMA foreign_keys=off")
        
        # Renomear tabela atual para backup
        cursor.execute("ALTER TABLE vendas RENAME TO vendas_old")
        
        # Criar nova tabela com valor_total permitindo NULL
        cursor.execute('''
        CREATE TABLE vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valor_total REAL,  -- Agora permite NULL
            desconto REAL DEFAULT 0,
            valor_recebido REAL,
            troco REAL DEFAULT 0,
            forma_pagamento TEXT,
            status TEXT DEFAULT 'Finalizada',
            usuario_id INTEGER,
            cliente_id INTEGER DEFAULT 0,
            observacoes TEXT DEFAULT '',
            motivo_alteracao TEXT DEFAULT '',
            alterado_por INTEGER DEFAULT 0,
            data_alteracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            origem TEXT DEFAULT 'venda_direta',
            valor_original_divida REAL DEFAULT 0,
            desconto_aplicado_divida REAL DEFAULT 0,
            total REAL DEFAULT 0
        )
        ''')
        
        # 3. Copiar os dados da tabela antiga para a nova
        print("3. Restaurando dados...")
        
        # Criar a string de colunas para o INSERT
        colunas_str = ', '.join(colunas)
        placeholders = ', '.join(['?'] * len(colunas))
        
        # Inserir os dados na nova tabela
        cursor.executemany(
            f"INSERT INTO vendas ({colunas_str}) VALUES ({placeholders})",
            vendas_data
        )
        
        # 4. Verificar se todos os registros foram migrados
        cursor.execute("SELECT COUNT(*) FROM vendas")
        count_novo = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vendas_old")
        count_antigo = cursor.fetchone()[0]
        
        if count_novo == count_antigo:
            # Remover a tabela antiga
            cursor.execute("DROP TABLE vendas_old")
            print(f"   [OK] {count_novo} registros migrados com sucesso!")
        else:
            print(f"   [AVISO] Número de registros diferentes: antigo={count_antigo}, novo={count_novo}")
            print("   A tabela antiga foi mantida como 'vendas_old' para segurança")
        
        # Reativar chaves estrangeiras
        cursor.execute("PRAGMA foreign_keys=on")
        
        conn.commit()
        print("\n✅ Correção concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante a correção: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== CORREÇÃO DA COLUNA VALOR_TOTAL ===\n")
    print("Este script irá modificar a tabela 'vendas' para permitir valores nulos na coluna 'valor_total'.")
    print("Por favor, faça um backup do banco de dados antes de continuar.\n")
    
    input("Pressione Enter para continuar ou Ctrl+C para cancelar...")
    
    if corrigir_coluna_valor_total():
        print("\n✅ Processo concluído com sucesso!")
        print("Por favor, REINICIE o sistema para aplicar as alterações.")
    else:
        print("\n❌ Ocorreu um erro durante a correção.")
    
    input("\nPressione Enter para sair...")
