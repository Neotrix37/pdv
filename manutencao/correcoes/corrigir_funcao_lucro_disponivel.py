import sqlite3
import os
from datetime import datetime

def get_database_path():
    # Try to locate the database in different locations
    possible_paths = [
        os.path.join(os.getenv('APPDATA'), 'SistemaGestao', 'database', 'sistema.db'),
        'database/sistema.db',
        'sistema.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Database found at: {path}")
            return path
    
    print("Error: Database not found.")
    return None

def corrigir_funcao_lucro_disponivel():
    db_path = get_database_path()
    if not db_path:
        print("Unable to locate the database.")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== FIXING get_lucro_disponivel_mes FUNCTION ===")
        
        # Check if the function has already been fixed
        cursor.execute("SELECT * FROM config_funcoes WHERE nome_funcao = 'get_lucro_disponivel_mes'")
        if cursor.fetchone():
            print("The function has already been fixed previously.")
            return
        
        # Define the corrected function
        funcao_corrigida = """
def get_lucro_disponivel_mes(self):
    \"\"\"Returns the current month's profit MINUS the profit withdrawals made\"\"\"
    try:
        # Calculate gross profit for the month
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
        
        # Get withdrawals for the current month
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
        
        # Calculate available profit
        lucro_disponivel = max(0, lucro_bruto - total_saques)
        
        # Debug: print values for verification
        print(f"[DEBUG] Gross profit this month: MT {lucro_bruto:.2f}")
        print(f"[DEBUG] Profit withdrawals this month: MT {total_saques:.2f}")
        print(f"[DEBUG] Available profit: MT {lucro_disponivel:.2f}")
        
        return lucro_disponivel
    except Exception as e:
        print(f"Error calculating available profit for the month: {e}")
        import traceback
        traceback.print_exc()
        return 0.0
"""
        
        # Create the config_funcoes table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_funcoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_funcao TEXT UNIQUE,
            codigo_fonte TEXT,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Insert the corrected function into the configuration table
        cursor.execute("""
        INSERT OR REPLACE INTO config_funcoes (nome_funcao, codigo_fonte)
        VALUES (?, ?)
        """, ('get_lucro_disponivel_mes', funcao_corrigida))
        
        conn.commit()
        print("Function get_lucro_disponivel_mes fixed successfully!")
        
        # Check the retiradas_caixa table and provide statistics
        try:
            # Check if the table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='retiradas_caixa'
            """)
            
            if not cursor.fetchone():
                print("\n[WARNING] The 'retiradas_caixa' table does not exist in the database.")
                print("The function has been fixed but may not work correctly without this table.")
            else:
                # Check the columns
                cursor.execute("PRAGMA table_info(retiradas_caixa)")
                colunas = [col[1] for col in cursor.fetchall()]
                
                # Check for required columns
                colunas_necessarias = ['data_retirada', 'valor', 'tipo', 'status', 'origem']
                colunas_faltando = [col for col in colunas_necessarias if col not in colunas]
                
                if colunas_faltando:
                    print(f"\n[WARNING] The retiradas_caixa table is missing required columns: {', '.join(colunas_faltando)}")
                    print("The function has been fixed but may not work correctly until the table is updated.")
                
                # Check if there's data in the table
                cursor.execute("SELECT COUNT(*) as total FROM retiradas_caixa")
                total_retiradas = cursor.fetchone()['total']
                print(f"\nTotal records in retiradas_caixa table: {total_retiradas}")
                
                # Show some statistics
                if total_retiradas > 0:
                    # Total profit withdrawals this month
                    mes_atual = datetime.now().strftime('%Y-%m')
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor), 0) as total_saques
                        FROM retiradas_caixa
                        WHERE strftime('%Y-%m', data_retirada) = ?
                        AND (tipo = 'Saque de Lucro' OR origem = 'lucro')
                        AND (status IS NULL OR status = 'Completo' OR status = 'Aprovado')
                    """, (mes_atual,))
                    
                    result = cursor.fetchone()
                    saques_mes = float(result['total_saques']) if result and 'total_saques' in result and result['total_saques'] is not None else 0.0
                    print(f"Total profit withdrawals this month: MT {saques_mes:.2f}")
                    
                    # Total profit for the month
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
                    print(f"Total profit this month: MT {lucro_mes:.2f}")
                    
                    # Available profit
                    print(f"\nAvailable profit (profit - withdrawals): MT {max(0, lucro_mes - saques_mes):.2f}")
                
        except Exception as e:
            print(f"\n[WARNING] Error checking retiradas_caixa table: {e}")
            print("The function has been fixed but there might be issues with the database structure.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nError fixing the available profit function: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    print("=== FIX AVAILABLE PROFIT FUNCTION ===")
    print("This script will fix the function that calculates the available profit for the month.")
    
    # Add global error handling
    try:
        corrigir_funcao_lucro_disponivel()
    except Exception as e:
        print(f"\n[CRITICAL ERROR] An error occurred during execution: {e}")
        print("Please check database permissions and try again.")
    
    input("\nPress Enter to exit...")
