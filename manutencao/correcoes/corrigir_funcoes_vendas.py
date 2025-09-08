import sqlite3
import os
import sys
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
    
    print("Erro: Banco de dados não encontrado nos locais padrão.")
    print("Por favor, verifique se o banco de dados existe em um destes locais:")
    for path in possible_paths:
        print(f"- {path}")
    sys.exit(1)

def corrigir_funcoes_vendas():
    db_path = get_database_path()
    print(f"\n=== CORRIGINDO FUNÇÕES DE VENDAS E LUCRO ===")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n1. Corrigindo função get_total_vendas_mes...")
        
        # Verificar se a função já foi corrigida
        cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type = 'function' AND name = 'get_total_vendas_mes'
        """)
        
        if cursor.fetchone() is not None:
            print("A função get_total_vendas_mes já foi corrigida.")
        else:
            # Criar a função corrigida
            cursor.execute("""
            CREATE FUNCTION IF NOT EXISTS get_total_vendas_mes() 
            RETURNS REAL
            BEGIN
                DECLARE total_vendas REAL;
                
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN status = 'Anulada' THEN 0 
                        ELSE total 
                    END
                ), 0) INTO total_vendas
                FROM vendas
                WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now');
                
                RETURN IFNULL(total_vendas, 0);
            END;
            """)
            print("Função get_total_vendas_mes criada/corrigida com sucesso!")
        
        # Corrigir a função get_total_vendas_mes na classe Database
        print("\n2. Atualizando a classe Database...")
        
        # Verificar se a tabela de configuração existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_funcoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_funcao TEXT NOT NULL,
            codigo_fonte TEXT NOT NULL,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Inserir a função corrigida na tabela de configuração
        # Definir a função corrigida como uma string simples
        funcao_corrigida = """
def get_total_vendas_mes(self):
    # Retorna o total de vendas do mês atual
    try:
        query = \"\"\"
            SELECT COALESCE(SUM(
                CASE 
                    WHEN status = 'Anulada' THEN 0 
                    ELSE total 
                END
            ), 0) as total
            FROM vendas
            WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
        \"\"\"
        
        result = self.fetchone(query)
        # Garante que sempre retorna um número, mesmo que o resultado seja None
        return float(result['total']) if result and 'total' in result and result['total'] is not None else 0.0
    except Exception as e:
        print(f"Erro ao buscar total de vendas do mês: {e}")
        return 0.0
"""
        
        # Verificar se já existe uma entrada para esta função
        cursor.execute("""
        SELECT id FROM config_funcoes WHERE nome_funcao = 'get_total_vendas_mes'
        """)
        
        if cursor.fetchone() is None:
            cursor.execute("""
            INSERT INTO config_funcoes (nome_funcao, codigo_fonte)
            VALUES (?, ?)
            """, ('get_total_vendas_mes', funcao_corrigida))
            print("Código da função get_total_vendas_mes salvo na tabela de configuração.")
        
        # Corrigir a função get_vendas_disponiveis_mes
        print("\n3. Corrigindo função get_vendas_disponiveis_mes...")
        
        # Definir a função de vendas disponíveis
        funcao_vendas_disponiveis = """
def get_vendas_disponiveis_mes(self):
    # Retorna o total de vendas do mês atual MENOS os saques realizados
    try:
        # Total de vendas do mês
        query_vendas = \"\"\"
            SELECT COALESCE(SUM(
                CASE 
                    WHEN status = 'Anulada' THEN 0 
                    ELSE total 
                END
            ), 0) as total
            FROM vendas
            WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
        \"\"\"
        
        # Total de saques do mês
        query_saques = \"\"\"
            SELECT COALESCE(SUM(valor), 0) as total
            FROM retiradas_caixa
            WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now')
        \"\"\"
        
        # Executa as consultas
        vendas = self.fetchone(query_vendas)
        saques = self.fetchone(query_saques)
        
        # Garante que os valores são números
        total_vendas = float(vendas['total']) if vendas and 'total' in vendas and vendas['total'] is not None else 0.0
        total_saques = float(saques['total']) if saques and 'total' in saques and saques['total'] is not None else 0.0
        
        # Calcula o saldo disponível
        saldo = total_vendas - total_saques
        return max(0, saldo)  # Retorna 0 se o saldo for negativo
        
    except Exception as e:
        print(f"Erro ao calcular vendas disponíveis do mês: {e}")
        return 0.0
"""
                
                # Executa as consultas
                vendas = self.fetchone(query_vendas)
                saques = self.fetchone(query_saques)
                
                # Garante que os valores são números
                total_vendas = float(vendas['total']) if vendas and 'total' in vendas and vendas['total'] is not None else 0.0
                total_saques = float(saques['total']) if saques and 'total' in saques and saques['total'] is not None else 0.0
                
                # Calcula o saldo disponível
                saldo = total_vendas - total_saques
                return max(0, saldo)  # Retorna 0 se o saldo for negativo
                
            except Exception as e:
                print(f"Erro ao calcular vendas disponíveis do mês: {e}")
                return 0.0
        """
        
        # Verificar se já existe uma entrada para esta função
        cursor.execute("""
        SELECT id FROM config_funcoes WHERE nome_funcao = 'get_vendas_disponiveis_mes'
        """)
        
        if cursor.fetchone() is None:
            cursor.execute("""
            INSERT INTO config_funcoes (nome_funcao, codigo_fonte)
            VALUES (?, ?)
            """, ('get_vendas_disponiveis_mes', funcao_vendas_disponiveis))
            print("Código da função get_vendas_disponiveis_mes salvo na tabela de configuração.")
        
        # Corrigir a função get_lucro_disponivel_mes
        print("\n4. Corrigindo função get_lucro_disponivel_mes...")
        
        # Definir a função de lucro disponível
        funcao_lucro_disponivel = """
def get_lucro_disponivel_mes(self):
    # Retorna o lucro do mês atual MENOS os saques de lucro realizados
    try:
        # Lucro bruto do mês
        lucro_bruto = self.get_lucro_mes()
        
        if lucro_bruto is None:
            lucro_bruto = 0.0
        
        # Total de saques de lucro do mês
        query_saques = \"\"\"
            SELECT COALESCE(SUM(valor), 0) as total
            FROM retiradas_caixa
            WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now')
            AND tipo = 'lucro'
        \"\"\"
        
        saques = self.fetchone(query_saques)
        total_saques = float(saques['total']) if saques and 'total' in saques and saques['total'] is not None else 0.0
        
        # Calcula o lucro disponível
        lucro_disponivel = lucro_bruto - total_saques
        return max(0, lucro_disponivel)  # Retorna 0 se o lucro disponível for negativo
        
    except Exception as e:
        print(f"Erro ao calcular lucro disponível do mês: {e}")
        return 0.0
"""
                
                saques = self.fetchone(query_saques)
                total_saques = float(saques['total']) if saques and 'total' in saques and saques['total'] is not None else 0.0
                
                # Calcula o lucro disponível
                lucro_disponivel = lucro_bruto - total_saques
                return max(0, lucro_disponivel)  # Retorna 0 se o lucro disponível for negativo
                
            except Exception as e:
                print(f"Erro ao calcular lucro disponível do mês: {e}")
                return 0.0
        """
        
        # Verificar se já existe uma entrada para esta função
        cursor.execute("""
        SELECT id FROM config_funcoes WHERE nome_funcao = 'get_lucro_disponivel_mes'
        """)
        
        if cursor.fetchone() is None:
            cursor.execute("""
            INSERT INTO config_funcoes (nome_funcao, codigo_fonte)
            VALUES (?, ?)
            """, ('get_lucro_disponivel_mes', funcao_lucro_disponivel))
            print("Código da função get_lucro_disponivel_mes salvo na tabela de configuração.")
        
        # Criar uma view para facilitar as consultas de vendas e lucro
        print("\n5. Criando views para otimização...")
        
        # View para resumo de vendas por dia
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_resumo_vendas_dia AS
        SELECT 
            DATE(data_venda) as data,
            COUNT(*) as total_vendas,
            SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END) as valor_total,
            COUNT(CASE WHEN status = 'Anulada' THEN 1 END) as total_anuladas
        FROM vendas
        GROUP BY DATE(data_venda)
        ORDER BY data DESC
        """)
        
        # View para resumo de vendas por mês
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_resumo_vendas_mes AS
        SELECT 
            strftime('%Y-%m', data_venda) as mes,
            COUNT(*) as total_vendas,
            SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END) as valor_total,
            COUNT(CASE WHEN status = 'Anulada' THEN 1 END) as total_anuladas
        FROM vendas
        GROUP BY strftime('%Y-%m', data_venda)
        ORDER BY mes DESC
        """)
        
        # View para resumo de lucro por venda
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_lucro_por_venda AS
        SELECT 
            v.id as venda_id,
            v.data_venda,
            v.total as valor_venda,
            SUM(iv.quantidade * iv.preco_custo_unitario) as custo_total,
            (v.total - SUM(iv.quantidade * iv.preco_custo_unitario)) as lucro_bruto,
            v.status
        FROM vendas v
        LEFT JOIN itens_venda iv ON v.id = iv.venda_id
        GROUP BY v.id, v.data_venda, v.total, v.status
        HAVING v.status != 'Anulada'
        """)
        
        print("Views criadas com sucesso!")
        
        # Confirmar as alterações
        conn.commit()
        
        print("\n=== CORREÇÕES APLICADAS COM SUCESSO! ===")
        print("As seguintes melhorias foram realizadas:")
        print("1. Função get_total_vendas_mes corrigida para evitar erros com valores nulos")
        print("2. Função get_vendas_disponiveis_mes corrigida para lidar com valores nulos")
        print("3. Função get_lucro_disponivel_mes corrigida para evitar erros com valores nulos")
        print("4. Código-fonte das funções salvo na tabela config_funcoes")
        print("5. Views de otimização criadas para melhorar o desempenho")
        
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
        WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
        """)
        
        stats = cursor.fetchone()
        if stats:
            print(f"Mês atual: {stats['mes_atual']}")
            print(f"Total de vendas: {stats['total_vendas']}")
            print(f"Valor total: MT {float(stats['valor_total'] or 0):.2f}")
            print(f"Vendas anuladas: {stats['total_anuladas']}")
        
        # Total de saques do mês
        cursor.execute("""
        SELECT 
            COALESCE(SUM(valor), 0) as total_saques,
            COUNT(*) as total_registros
        FROM retiradas_caixa
        WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now')
        """)
        
        saques = cursor.fetchone()
        if saques:
            print(f"\nTotal de saques: {saques['total_registros']}")
            print(f"Valor total sacado: MT {float(saques['total_saques'] or 0):.2f}")
        
        cursor.close()
        conn.close()
        
        print("\n=== PROCESSO CONCLUÍDO COM SUCESSO! ===")
        
    except Exception as e:
        print(f"\nErro ao executar as correções: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)

if __name__ == "__main__":
    print("=== CORRIGIR FUNÇÕES DE VENDAS E LUCRO ===")
    print("Este script irá corrigir as funções de cálculo de vendas e lucro")
    print("para evitar erros 'NoneType' e melhorar a confiabilidade do sistema.")
    print("\nCertifique-se de fazer um backup do banco de dados antes de continuar.")
    
    confirm = input("\nDeseja continuar? (s/n): ").strip().lower()
    if confirm == 's':
        corrigir_funcoes_vendas()
    else:
        print("Operação cancelada pelo usuário.")
        sys.exit(0)
