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

def corrigir_funcao_vendas_disponiveis():
    db_path = get_database_path()
    if not db_path:
        print("Não foi possível encontrar o banco de dados.")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== CORRIGINDO FUNÇÃO DE VENDAS DISPONÍVEIS ===")
        
        # Código da função corrigida
        funcao_corrigida = """
def get_vendas_disponiveis_mes(self):
    \"\"\"Retorna o total de vendas do mês atual MENOS os saques realizados\"\"\"
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
        
        result_vendas = self.fetchone(query_vendas)
        total_vendas = float(result_vendas['total']) if result_vendas and 'total' in result_vendas and result_vendas['total'] is not None else 0.0
        
        # Total de saques de vendas do mês
        query_saques = \"\"\"
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'vendas'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND (status IS NULL OR status = 'Completo' OR status = 'Aprovado')
        \"\"\"
        
        result_saques = self.fetchone(query_saques)
        total_saques = float(result_saques['total_saques']) if result_saques and 'total_saques' in result_saques and result_saques['total_saques'] is not None else 0.0
        
        # Debug: imprimir valores para verificação
        print(f"[DEBUG] Vendas brutas do mês: MT {total_vendas:.2f}")
        print(f"[DEBUG] Saques de vendas do mês: MT {total_saques:.2f}")
        print(f"[DEBUG] Vendas disponíveis: MT {max(0, total_vendas - total_saques):.2f}")
        
        # Retorna vendas menos saques, garantindo que não seja negativo
        return max(0, total_vendas - total_saques)
    except Exception as e:
        print(f"Erro ao calcular vendas disponíveis do mês: {e}")
        import traceback
        traceback.print_exc()
        return 0.0
"""
        
        # Atualizar ou inserir a função na tabela config_funcoes
        cursor.execute("""
        INSERT OR REPLACE INTO config_funcoes (nome_funcao, codigo_fonte)
        VALUES (?, ?)
        """, ('get_vendas_disponiveis_mes', funcao_corrigida))
        
        conn.commit()
        print("Função get_vendas_disponiveis_mes corrigida com sucesso!")
        
        # Verificar a tabela retiradas_caixa
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='retiradas_caixa'
            """)
            
            if not cursor.fetchone():
                print("\n[AVISO] A tabela 'retiradas_caixa' não existe no banco de dados.")
            else:
                # Verificar as colunas existentes
                cursor.execute("PRAGMA table_info(retiradas_caixa)")
                colunas = [col[1] for col in cursor.fetchall()]
                
                # Verificar colunas necessárias
                colunas_necessarias = ['data_retirada', 'valor', 'origem', 'status']
                colunas_faltando = [col for col in colunas_necessarias if col not in colunas]
                
                if colunas_faltando:
                    print(f"\n[AVISO] A tabela retiradas_caixa não tem todas as colunas necessárias. Faltando: {', '.join(colunas_faltando)}")
                
                # Verificar dados existentes
                cursor.execute("SELECT COUNT(*) as total FROM retiradas_caixa")
                total_retiradas = cursor.fetchone()['total']
                print(f"\nTotal de registros na tabela retiradas_caixa: {total_retiradas}")
                
                # Estatísticas do mês atual
                mes_atual = datetime.now().strftime('%Y-%m')
                
                # Total de saques de vendas no mês
                cursor.execute("""
                    SELECT COALESCE(SUM(valor), 0) as total_saques
                    FROM retiradas_caixa
                    WHERE origem = 'vendas'
                    AND strftime('%Y-%m', data_retirada) = ?
                    AND (status IS NULL OR status = 'Completo' OR status = 'Aprovado')
                """, (mes_atual,))
                
                result = cursor.fetchone()
                saques_mes = float(result['total_saques']) if result and 'total_saques' in result and result['total_saques'] is not None else 0.0
                print(f"Total de saques de vendas no mês atual: MT {saques_mes:.2f}")
                
                # Total de vendas do mês
                cursor.execute("""
                    SELECT COALESCE(SUM(
                        CASE 
                            WHEN status = 'Anulada' THEN 0 
                            ELSE total 
                        END
                    ), 0) as total_vendas
                    FROM vendas
                    WHERE strftime('%Y-%m', data_venda) = ?
                """, (mes_atual,))
                
                result = cursor.fetchone()
                vendas_mes = float(result['total_vendas']) if result and 'total_vendas' in result and result['total_vendas'] is not None else 0.0
                print(f"Total de vendas no mês atual: MT {vendas_mes:.2f}")
                
                # Vendas disponíveis
                print(f"\nVendas disponíveis (vendas - saques): MT {max(0, vendas_mes - saques_mes):.2f}")
                
        except Exception as e:
            print(f"\n[AVISO] Erro ao verificar a tabela retiradas_caixa: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nErro ao corrigir a função de vendas disponíveis: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    print("=== CORRIGIR FUNÇÃO DE VENDAS DISPONÍVEIS ===")
    print("Este script irá corrigir a função que calcula as vendas disponíveis do mês.")
    
    try:
        corrigir_funcao_vendas_disponiveis()
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Ocorreu um erro durante a execução: {e}")
    
    input("\nPressione Enter para sair...")
