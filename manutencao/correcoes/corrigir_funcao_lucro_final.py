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

def corrigir_funcao_lucro_disponivel():
    db_path = get_database_path()
    if not db_path:
        print("Não foi possível encontrar o banco de dados.")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== CORRIGINDO FUNÇÃO DE LUCRO DISPONÍVEL ===")
        
        # Código da função corrigida
        funcao_corrigida = """
def get_lucro_disponivel_mes(self):
    \"\"\"Retorna o lucro do mês atual MENOS os saques de lucro realizados\"\"\"
    try:
        # Calcular lucro bruto do mês
        query_lucro = \"\"\"
            SELECT COALESCE(SUM(
                CASE
                    WHEN v.status = 'Anulada' THEN 0
                    ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                END
            ), 0) as lucro
            FROM vendas v
            JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE strftime('%Y-%m', v.data_venda) = strftime('%Y-%m', 'now')
        \"\"\"
        
        lucro_result = self.fetchone(query_lucro)
        lucro_bruto = float(lucro_result['lucro']) if lucro_result and 'lucro' in lucro_result and lucro_result['lucro'] is not None else 0.0
        
        # Buscar saques do mês
        mes_atual = datetime.now().strftime('%Y-%m')
        query_saques = \"\"\"
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE strftime('%Y-%m', data_retirada) = ?
            AND (tipo = 'Saque de Lucro' OR origem = 'lucro')
            AND (status IS NULL OR status = 'Completo' OR status = 'Aprovado')
        \"\"\"
        
        saques_result = self.fetchone(query_saques, (mes_atual,))
        total_saques = float(saques_result['total_saques']) if saques_result and 'total_saques' in saques_result and saques_result['total_saques'] is not None else 0.0
        
        # Calcular lucro disponível
        lucro_disponivel = max(0, lucro_bruto - total_saques)
        
        # Debug: imprimir valores para verificação
        print(f"[DEBUG] Lucro bruto do mês: MT {lucro_bruto:.2f}")
        print(f"[DEBUG] Saques de lucro do mês: MT {total_saques:.2f}")
        print(f"[DEBUG] Lucro disponível: MT {lucro_disponivel:.2f}")
        
        return lucro_disponivel
    except Exception as e:
        print(f"Erro ao calcular lucro disponível do mês: {e}")
        import traceback
        traceback.print_exc()
        return 0.0
"""
        
        # Atualizar ou inserir a função na tabela config_funcoes
        cursor.execute("""
        INSERT OR REPLACE INTO config_funcoes (nome_funcao, codigo_fonte)
        VALUES (?, ?)
        """, ('get_lucro_disponivel_mes', funcao_corrigida))
        
        conn.commit()
        print("Função get_lucro_disponivel_mes corrigida com sucesso!")
        
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
                colunas_necessarias = ['data_retirada', 'valor', 'tipo', 'status', 'origem']
                colunas_faltando = [col for col in colunas_necessarias if col not in colunas]
                
                if colunas_faltando:
                    print(f"\n[AVISO] A tabela retiradas_caixa não tem todas as colunas necessárias. Faltando: {', '.join(colunas_faltando)}")
                
                # Verificar dados existentes
                cursor.execute("SELECT COUNT(*) as total FROM retiradas_caixa")
                total_retiradas = cursor.fetchone()['total']
                print(f"\nTotal de registros na tabela retiradas_caixa: {total_retiradas}")
                
                # Estatísticas do mês atual
                mes_atual = datetime.now().strftime('%Y-%m')
                
                # Total de saques de lucro no mês
                cursor.execute("""
                    SELECT COALESCE(SUM(valor), 0) as total_saques
                    FROM retiradas_caixa
                    WHERE strftime('%Y-%m', data_retirada) = ?
                    AND (tipo = 'Saque de Lucro' OR origem = 'lucro')
                    AND (status IS NULL OR status = 'Completo' OR status = 'Aprovado')
                """, (mes_atual,))
                
                result = cursor.fetchone()
                saques_mes = float(result['total_saques']) if result and 'total_saques' in result and result['total_saques'] is not None else 0.0
                print(f"Total de saques de lucro no mês atual: MT {saques_mes:.2f}")
                
                # Total de lucro do mês
                cursor.execute("""
                    SELECT COALESCE(SUM(
                        CASE
                            WHEN v.status = 'Anulada' THEN 0
                            ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                        END
                    ), 0) as lucro_total
                    FROM vendas v
                    JOIN itens_venda iv ON v.id = iv.venda_id
                    WHERE strftime('%Y-%m', v.data_venda) = ?
                """, (mes_atual,))
                
                result = cursor.fetchone()
                lucro_mes = float(result['lucro_total']) if result and 'lucro_total' in result and result['lucro_total'] is not None else 0.0
                print(f"Total de lucro no mês atual: MT {lucro_mes:.2f}")
                
                # Lucro disponível
                print(f"\nLucro disponível (lucro - saques): MT {max(0, lucro_mes - saques_mes):.2f}")
                
        except Exception as e:
            print(f"\n[AVISO] Erro ao verificar a tabela retiradas_caixa: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nErro ao corrigir a função de lucro disponível: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    print("=== CORRIGIR FUNÇÃO DE LUCRO DISPONÍVEL ===")
    print("Este script irá corrigir a função que calcula o lucro disponível do mês.")
    
    try:
        corrigir_funcao_lucro_disponivel()
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Ocorreu um erro durante a execução: {e}")
    
    input("\nPressione Enter para sair...")
