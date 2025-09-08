import sqlite3
import os
from datetime import datetime

def get_database_path():
    # Tenta localizar o banco de dados em diferentes locais
    possible_paths = [
        os.path.join(os.getenv('APPDATA'), 'SistemaGestao', 'database', 'sistema.db'),
        'database/sistema.db',
        'sistema.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Banco de dados encontrado em: {path}")
            return path
    
    print("Erro: Banco de dados não encontrado.")
    return None

def atualizar_estrutura_banco():
    db_path = get_database_path()
    if not db_path:
        print("Não foi possível encontrar o banco de dados.")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== ATUALIZANDO ESTRUTURA DO BANCO DE DADOS ===")
        
        # Verificar e adicionar colunas ausentes na tabela retiradas_caixa
        cursor.execute("PRAGMA table_info(retiradas_caixa)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        # Colunas a serem adicionadas, se não existirem
        colunas_para_adicionar = [
            ('origem', 'TEXT', 'vendas'),
            ('tipo', 'TEXT', 'Saque de Caixa'),
            ('status', 'TEXT', 'Completo')
        ]
        
        for coluna, tipo, valor_padrao in colunas_para_adicionar:
            if coluna not in colunas:
                print(f"Adicionando coluna '{coluna}' na tabela retiradas_caixa...")
                cursor.execute(f"ALTER TABLE retiradas_caixa ADD COLUMN {coluna} {tipo} DEFAULT '{valor_padrao}'")
                print(f"Coluna '{coluna}' adicionada com sucesso!")
            else:
                print(f"Coluna '{coluna}' já existe na tabela retiradas_caixa.")
        
        # Atualizar registros existentes para definir valores padrão
        for coluna, _, valor_padrao in colunas_para_adicionar:
            if coluna in colunas:
                print(f"Atualizando registros existentes na coluna '{coluna}'...")
                cursor.execute(f"UPDATE retiradas_caixa SET {coluna} = ? WHERE {coluna} IS NULL", (valor_padrao,))
        
        # Verificar se a tabela de configuração de funções existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config_funcoes'")
        if not cursor.fetchone():
            print("\nCriando tabela config_funcoes...")
            cursor.execute("""
            CREATE TABLE config_funcoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_funcao TEXT UNIQUE,
                codigo_fonte TEXT,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("Tabela config_funcoes criada com sucesso!")
        
        conn.commit()
        print("\nEstrutura do banco de dados atualizada com sucesso!")
        
        # Verificar se as funções de cálculo estão corretas
        print("\n=== VERIFICANDO FUNÇÕES DE CÁLCULO ===")
        
        # Verificar função get_vendas_disponiveis_mes
        cursor.execute("SELECT * FROM config_funcoes WHERE nome_funcao = 'get_vendas_disponiveis_mes'")
        if cursor.fetchone():
            print("Função get_vendas_disponiveis_mes encontrada e configurada.")
        else:
            print("[AVISO] Função get_vendas_disponiveis_mes não encontrada na tabela config_funcoes.")
        
        # Verificar função get_lucro_disponivel_mes
        cursor.execute("SELECT * FROM config_funcoes WHERE nome_funcao = 'get_lucro_disponivel_mes'")
        if cursor.fetchone():
            print("Função get_lucro_disponivel_mes encontrada e configurada.")
        else:
            print("[AVISO] Função get_lucro_disponivel_mes não encontrada na tabela config_funcoes.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nErro ao atualizar a estrutura do banco de dados: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    print("=== ATUALIZAÇÃO DA ESTRUTURA DO BANCO DE DADOS ===")
    print("Este script atualiza a estrutura do banco de dados para suportar as funções de cálculo de vendas e lucro.")
    
    try:
        atualizar_estrutura_banco()
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Ocorreu um erro durante a execução: {e}")
    
    input("\nPressione Enter para sair...")
