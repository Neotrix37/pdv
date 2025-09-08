import sqlite3
import os

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

def corrigir_funcoes():
    db_path = get_database_path()
    if not db_path:
        print("Não foi possível encontrar o banco de dados.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n=== CORRIGINDO FUNÇÕES DE VENDAS ===")
        
        # Criar tabela de configuração se não existir
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_funcoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_funcao TEXT NOT NULL,
            codigo_fonte TEXT NOT NULL,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 1. Função get_total_vendas_mes
        print("1. Corrigindo get_total_vendas_mes...")
        cursor.execute("DELETE FROM config_funcoes WHERE nome_funcao = 'get_total_vendas_mes'")
        
        cursor.execute('''
        INSERT INTO config_funcoes (nome_funcao, codigo_fonte)
        VALUES (?, ?)
        ''', ('get_total_vendas_mes', 
              'def get_total_vendas_mes(self):\n    try:\n        query = """SELECT COALESCE(SUM(CASE WHEN status = \'Anulada\' THEN 0 ELSE total END), 0) as total \n                 FROM vendas WHERE strftime(\'%Y-%m\', data_venda) = strftime(\'%Y-%m\', \'now\')"""\n        result = self.fetchone(query)\n        return float(result[\'total\']) if result and result[\'total\'] is not None else 0.0\n    except Exception as e:\n        print(f"Erro em get_total_vendas_mes: {e}")\n        return 0.0'))
        
        # 2. Função get_vendas_disponiveis_mes
        print("2. Corrigindo get_vendas_disponiveis_mes...")
        cursor.execute("DELETE FROM config_funcoes WHERE nome_funcao = 'get_vendas_disponiveis_mes'")
        
        cursor.execute('''
        INSERT INTO config_funcoes (nome_funcao, codigo_fonte)
        VALUES (?, ?)
        ''', ('get_vendas_disponiveis_mes',
              'def get_vendas_disponiveis_mes(self):\n    try:\n        # Total de vendas do mês\n        query_vendas = """SELECT COALESCE(SUM(CASE WHEN status = \'Anulada\' THEN 0 ELSE total END), 0) as total \n                        FROM vendas WHERE strftime(\'%Y-%m\', data_venda) = strftime(\'%Y-%m\', \'now\')"""\n        vendas = self.fetchone(query_vendas)\n        total_vendas = float(vendas[\'total\']) if vendas and vendas[\'total\'] is not None else 0.0\n        \n        # Total de saques do mês\n        query_saques = """SELECT COALESCE(SUM(valor), 0) as total FROM retiradas_caixa \n                         WHERE strftime(\'%Y-%m\', data) = strftime(\'%Y-%m\', \'now\')"""\n        saques = self.fetchone(query_saques)\n        total_saques = float(saques[\'total\']) if saques and saques[\'total\'] is not None else 0.0\n        \n        return max(0, total_vendas - total_saques)\n    except Exception as e:\n        print(f"Erro em get_vendas_disponiveis_mes: {e}")\n        return 0.0'))
        
        # 3. Função get_lucro_disponivel_mes
        print("3. Corrigindo get_lucro_disponivel_mes...")
        cursor.execute("DELETE FROM config_funcoes WHERE nome_funcao = 'get_lucro_disponivel_mes'")
        
        cursor.execute('''
        INSERT INTO config_funcoes (nome_funcao, codigo_fonte)
        VALUES (?, ?)
        ''', ('get_lucro_disponivel_mes',
              'def get_lucro_disponivel_mes(self):\n    try:\n        # Lucro bruto do mês\n        lucro_bruto = self.get_lucro_mes() or 0.0\n        \n        # Total de saques de lucro do mês\n        query_saques = """SELECT COALESCE(SUM(valor), 0) as total FROM retiradas_caixa \n                         WHERE strftime(\'%Y-%m\', data) = strftime(\'%Y-%m\', \'now\') \n                         AND tipo = \'lucro\'"""\n        saques = self.fetchone(query_saques)\n        total_saques = float(saques[\'total\']) if saques and saques[\'total\'] is not None else 0.0\n        \n        return max(0, lucro_bruto - total_saques)\n    except Exception as e:\n        print(f"Erro em get_lucro_disponivel_mes: {e}")\n        return 0.0'))
        
        # Criar views para otimização
        print("\nCriando views de otimização...")
        
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS vw_resumo_vendas_dia AS
        SELECT 
            DATE(data_venda) as data,
            COUNT(*) as total_vendas,
            SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END) as valor_total,
            COUNT(CASE WHEN status = 'Anulada' THEN 1 END) as total_anuladas
        FROM vendas
        GROUP BY DATE(data_venda)
        ORDER BY data DESC''')
        
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS vw_resumo_vendas_mes AS
        SELECT 
            strftime('%Y-%m', data_venda) as mes,
            COUNT(*) as total_vendas,
            SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END) as valor_total,
            COUNT(CASE WHEN status = 'Anulada' THEN 1 END) as total_anuladas
        FROM vendas
        GROUP BY strftime('%Y-%m', data_venda)
        ORDER BY mes DESC''')
        
        # Confirmar as alterações
        conn.commit()
        
        print("\n=== CORREÇÕES APLICADAS COM SUCESSO! ===")
        print("As seguintes melhorias foram realizadas:")
        print("1. Função get_total_vendas_mes corrigida")
        print("2. Função get_vendas_disponiveis_mes corrigida")
        print("3. Função get_lucro_disponivel_mes corrigida")
        print("4. Views de otimização criadas")
        
        # Mostrar estatísticas atuais
        print("\n=== ESTATÍSTICAS ATUAIS ===")
        
        # Total de vendas do mês
        cursor.execute("""
        SELECT 
            strftime('%Y-%m', 'now') as mes_atual,
            COUNT(*) as total_vendas,
            SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END) as valor_total,
            COUNT(CASE WHEN status = 'Anulada' THEN 1 END) as total_anuladas
        FROM vendas
        WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')""")
        
        stats = cursor.fetchone()
        if stats:
            print(f"Mês atual: {stats[0] or 'N/A'}")
            print(f"Total de vendas: {stats[1] or 0}")
            print(f"Valor total: MT {float(stats[2] or 0):.2f}")
            print(f"Vendas anuladas: {stats[3] or 0}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nErro ao executar as correções: {e}")
        if 'conn' in locals():
            conn.rollback()
        return

if __name__ == "__main__":
    print("=== CORRIGINDO FUNÇÕES DE VENDAS ===")
    print("Este script irá corrigir as funções de cálculo de vendas e lucro")
    corrigir_funcoes()
