import sqlite3
from datetime import datetime

def verificar_vendas_hoje():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database/sistema.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Consulta para verificar vendas de hoje
        query = """
        SELECT 
            COUNT(*) as total_vendas,
            COALESCE(SUM(total), 0) as valor_total,
            SUM(CASE WHEN status = 'Anulada' THEN 1 ELSE 0 END) as total_anuladas
        FROM vendas 
        WHERE DATE(data_venda) = DATE('now')
        """
        
        cursor.execute(query)
        resultado = cursor.fetchone()
        
        if resultado:
            print("\n=== VENDAS DE HOJE ===")
            print(f"Total de vendas: {resultado['total_vendas']}")
            print(f"Valor total: MT {resultado['valor_total']:.2f}")
            print(f"Vendas anuladas: {resultado['total_anuladas']}")
        else:
            print("Nenhuma venda encontrada para hoje.")
            
        # Verificar itens de venda de hoje
        query_itens = """
        SELECT 
            v.id as venda_id,
            v.data_venda,
            v.total as total_venda,
            v.status,
            COUNT(iv.id) as total_itens,
            SUM(iv.subtotal) as subtotal_itens,
            SUM(iv.preco_custo_unitario * iv.quantidade) as custo_total,
            SUM(iv.subtotal - (iv.preco_custo_unitario * iv.quantidade)) as lucro_venda
        FROM vendas v
        LEFT JOIN itens_venda iv ON v.id = iv.venda_id
        WHERE DATE(v.data_venda) = DATE('now')
        GROUP BY v.id
        ORDER BY v.data_venda DESC
        """
        
        cursor.execute(query_itens)
        vendas = cursor.fetchall()
        
        if vendas:
            print("\n=== DETALHES DAS VENDAS ===")
            for i, venda in enumerate(vendas[:5]):  # Mostrar apenas as 5 primeiras para não poluir
                print(f"\nVenda {i+1}:")
                print(f"  ID: {venda['venda_id']}")
                print(f"  Data: {venda['data_venda']}")
                print(f"  Status: {venda['status']}")
                print(f"  Total: MT {venda['total_venda']:.2f}")
                print(f"  Itens: {venda['total_itens']}")
                print(f"  Subtotal: MT {venda['subtotal_itens']:.2f}" if venda['subtotal_itens'] else "  Subtotal: N/A")
                print(f"  Custo total: MT {venda['custo_total']:.2f}" if venda['custo_total'] is not None else "  Custo total: N/A")
                print(f"  Lucro: MT {venda['lucro_venda']:.2f}" if venda['lucro_venda'] is not None else "  Lucro: N/A")
        else:
            print("\nNenhum item de venda encontrado para hoje.")
        
        # Calcular lucro total do dia
        query_lucro = """
        SELECT 
            COALESCE(SUM(
                CASE 
                    WHEN v.status = 'Anulada' THEN 0 
                    ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                END
            ), 0) as lucro_dia
        FROM vendas v
        JOIN itens_venda iv ON v.id = iv.venda_id
        WHERE DATE(v.data_venda) = DATE('now')
        """
        
        cursor.execute(query_lucro)
        lucro_dia = cursor.fetchone()['lucro_dia']
        print(f"\n=== LUCRO DO DIA ===")
        print(f"Lucro total: MT {lucro_dia:.2f}")
        
    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    verificar_vendas_hoje()
