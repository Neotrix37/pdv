import sqlite3

def verificar_estrutura():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database/sistema.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar estrutura da tabela vendas
        print("\n=== ESTRUTURA DA TABELA VENDAS ===")
        cursor.execute("PRAGMA table_info(vendas)")
        print("Colunas da tabela 'vendas':")
        for col in cursor.fetchall():
            print(f"- {col['name']} ({col['type']})")
        
        # Verificar estrutura da tabela itens_venda
        print("\n=== ESTRUTURA DA TABELA ITENS_VENDA ===")
        cursor.execute("PRAGMA table_info(itens_venda)")
        print("Colunas da tabela 'itens_venda':")
        for col in cursor.fetchall():
            print(f"- {col['name']} ({col['type']})")
        
        # Verificar se há registros nas tabelas
        cursor.execute("SELECT COUNT(*) as total FROM vendas WHERE DATE(data_venda) = DATE('now')")
        total_vendas = cursor.fetchone()['total']
        print(f"\nTotal de vendas hoje: {total_vendas}")
        
        cursor.execute("SELECT COUNT(*) as total FROM itens_venda")
        total_itens = cursor.fetchone()['total']
        print(f"Total de itens de venda: {total_itens}")
        
        # Verificar se há itens de venda para as vendas de hoje
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM itens_venda iv
            JOIN vendas v ON iv.venda_id = v.id
            WHERE DATE(v.data_venda) = DATE('now')
        """)
        itens_hoje = cursor.fetchone()['total']
        print(f"Itens de venda para vendas de hoje: {itens_hoje}")
        
        # Verificar dados de exemplo
        if total_vendas > 0:
            print("\n=== DADOS DE EXEMPLO ===")
            cursor.execute("""
                SELECT v.id, v.data_venda, v.total, v.status, 
                       COUNT(iv.id) as total_itens,
                       SUM(iv.quantidade) as total_quantidade,
                       SUM(iv.subtotal) as subtotal_total
                FROM vendas v
                LEFT JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE DATE(v.data_venda) = DATE('now')
                GROUP BY v.id
                ORDER BY v.data_venda DESC
                LIMIT 5
            """)
            
            print("\nVendas de hoje:")
            for venda in cursor.fetchall():
                print(f"\nID: {venda['id']}")
                print(f"Data: {venda['data_venda']}")
                print(f"Total: {venda['total']}")
                print(f"Status: {venda['status']}")
                print(f"Total itens: {venda['total_itens']}")
                print(f"Quantidade total: {venda['total_quantidade'] or 0}")
                print(f"Subtotal: {venda['subtotal_total'] or 0}")
                
                # Verificar itens desta venda
                cursor.execute("""
                    SELECT id, produto_id, quantidade, preco_unitario, subtotal, 
                           preco_custo_unitario, (preco_custo_unitario * quantidade) as custo_total,
                           (subtotal - (preco_custo_unitario * quantidade)) as lucro
                    FROM itens_venda 
                    WHERE venda_id = ?
                """, (venda['id'],))
                
                print("  Itens da venda:")
                for item in cursor.fetchall():
                    print(f"  - ID: {item['id']}, Produto: {item['produto_id']}, "
                          f"Qtd: {item['quantidade']}, Preço: {item['preco_unitario']}, "
                          f"Subtotal: {item['subtotal']}, Custo: {item['custo_total']}, "
                          f"Lucro: {item['lucro']}")
        
    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    verificar_estrutura()
