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

def verificar_funcoes():
    db_path = get_database_path()
    if not db_path:
        print("Não foi possível encontrar o banco de dados.")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== VERIFICANDO FUNÇÕES CORRIGIDAS ===")
        
        # Verificar funções na tabela config_funcoes
        cursor.execute("SELECT nome_funcao, data_atualizacao FROM config_funcoes")
        print("\nFunções disponíveis na tabela config_funcoes:")
        for row in cursor.fetchall():
            print(f"- {row['nome_funcao']} (última atualização: {row['data_atualizacao']})")
        
        # Verificar estrutura da tabela retiradas_caixa
        print("\nVerificando estrutura da tabela retiradas_caixa:")
        cursor.execute("PRAGMA table_info(retiradas_caixa)")
        colunas = [col[1] for col in cursor.fetchall()]
        print(f"Colunas encontradas: {', '.join(colunas) if colunas else 'Tabela não encontrada'}")
        
        # Verificar dados de exemplo
        mes_atual = datetime.now().strftime('%Y-%m')
        
        # Verificar vendas do mês
        print("\n=== DADOS DO MÊS ATUAL ===")
        print(f"Mês de referência: {mes_atual}")
        
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
        total_vendas = float(result['total_vendas']) if result and 'total_vendas' in result and result['total_vendas'] is not None else 0.0
        print(f"\nTotal de vendas do mês: MT {total_vendas:.2f}")
        
        # Lucro bruto do mês
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE
                    WHEN v.status = 'Anulada' THEN 0
                    ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                END
            ), 0) as lucro_bruto
            FROM vendas v
            JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE strftime('%Y-%m', v.data_venda) = ?
        """, (mes_atual,))
        
        result = cursor.fetchone()
        lucro_bruto = float(result['lucro_bruto']) if result and 'lucro_bruto' in result and result['lucro_bruto'] is not None else 0.0
        print(f"Lucro bruto do mês: MT {lucro_bruto:.2f}")
        
        # Verificar saques do mês
        print("\n=== SAQUES DO MÊS ===")
        
        # Verificar se a tabela retiradas_caixa existe e tem dados
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='retiradas_caixa'")
        if cursor.fetchone():
            # Verificar colunas disponíveis
            cursor.execute("PRAGMA table_info(retiradas_caixa)")
            colunas = [col[1] for col in cursor.fetchall()]
            
            # Verificar saques de vendas
            if 'origem' in colunas and 'status' in colunas:
                cursor.execute("""
                    SELECT COALESCE(SUM(valor), 0) as total_saques
                    FROM retiradas_caixa
                    WHERE origem = 'vendas'
                    AND strftime('%Y-%m', data_retirada) = ?
                    AND (status IS NULL OR status = 'Completo' OR status = 'Aprovado')
                """, (mes_atual,))
                
                result = cursor.fetchone()
                saques_vendas = float(result['total_saques']) if result and 'total_saques' in result and result['total_saques'] is not None else 0.0
                print(f"Saques de vendas do mês: MT {saques_vendas:.2f}")
                
                # Calcular vendas disponíveis
                vendas_disponiveis = max(0, total_vendas - saques_vendas)
                print(f"Vendas disponíveis: MT {vendas_disponiveis:.2f}")
                
                # Verificar saques de lucro
                cursor.execute("""
                    SELECT COALESCE(SUM(valor), 0) as total_saques
                    FROM retiradas_caixa
                    WHERE (origem = 'lucro' OR tipo = 'Saque de Lucro')
                    AND strftime('%Y-%m', data_retirada) = ?
                    AND (status IS NULL OR status = 'Completo' OR status = 'Aprovado')
                """, (mes_atual,))
                
                result = cursor.fetchone()
                saques_lucro = float(result['total_saques']) if result and 'total_saques' in result and result['total_saques'] is not None else 0.0
                print(f"Saques de lucro do mês: MT {saques_lucro:.2f}")
                
                # Calcular lucro disponível
                lucro_disponivel = max(0, lucro_bruto - saques_lucro)
                print(f"Lucro disponível: MT {lucro_disponivel:.2f}")
            else:
                print("\n[AVISO] A tabela retiradas_caixa não tem todas as colunas necessárias.")
                print(f"Colunas necessárias: 'origem', 'status'")
                print(f"Colunas encontradas: {', '.join(colunas) if colunas else 'Nenhuma coluna'}")
        else:
            print("\n[AVISO] A tabela 'retiradas_caixa' não foi encontrada no banco de dados.")
            print("As funções de vendas disponíveis e lucro disponível podem não funcionar corretamente.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nErro ao verificar as funções: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== VERIFICAÇÃO DAS FUNÇÕES CORRIGIDAS ===")
    print("Este script verifica se as funções de cálculo de vendas e lucro estão funcionando corretamente.")
    
    try:
        verificar_funcoes()
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Ocorreu um erro durante a verificação: {e}")
    
    input("\nPressione Enter para sair...")
