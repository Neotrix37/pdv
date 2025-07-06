#!/usr/bin/env python3
"""
Script de teste para debugar o fluxo de dívidas, estoque e valores
"""

from database.database import Database
import sqlite3

def testar_fluxo_dividas():
    """Testa o fluxo completo de dívidas"""
    print("=== TESTE DE FLUXO DE DÍVIDAS ===")
    
    db = Database()
    
    # 1. Verificar valores iniciais
    print("\n1. VALORES INICIAIS:")
    valor_estoque_inicial = db.get_valor_estoque()
    valor_potencial_inicial = db.get_valor_venda_estoque()
    print(f"Valor em estoque: MT {valor_estoque_inicial:.2f}")
    print(f"Valor potencial: MT {valor_potencial_inicial:.2f}")
    
    # 2. Verificar produtos disponíveis
    print("\n2. PRODUTOS DISPONÍVEIS:")
    produtos = db.fetchall("""
        SELECT id, nome, estoque, preco_custo, preco_venda 
        FROM produtos 
        WHERE ativo = 1 
        ORDER BY estoque DESC 
        LIMIT 5
    """)
    
    for p in produtos:
        print(f"ID {p['id']}: {p['nome']} - Estoque: {p['estoque']} - Custo: MT {p['preco_custo']:.2f} - Venda: MT {p['preco_venda']:.2f}")
    
    # 3. Verificar clientes
    print("\n3. CLIENTES DISPONÍVEIS:")
    clientes = db.fetchall("SELECT id, nome, especial, desconto_divida FROM clientes LIMIT 3")
    for c in clientes:
        print(f"ID {c['id']}: {c['nome']} - Especial: {c['especial']} - Desconto: {c['desconto_divida']*100:.1f}%")
    
    # 4. Verificar dívidas existentes
    print("\n4. DÍVIDAS EXISTENTES:")
    dividas = db.fetchall("""
        SELECT id, cliente_id, valor_total, valor_pago, status 
        FROM dividas 
        ORDER BY id DESC 
        LIMIT 5
    """)
    
    for d in dividas:
        print(f"Dívida {d['id']}: Cliente {d['cliente_id']} - Total: MT {d['valor_total']:.2f} - Pago: MT {d['valor_pago']:.2f} - Status: {d['status']}")
    
    # 5. Verificar vendas de dívidas quitadas
    print("\n5. VENDAS DE DÍVIDAS QUITADAS:")
    vendas_dividas = db.fetchall("""
        SELECT id, total, status, origem 
        FROM vendas 
        WHERE origem = 'divida_quitada' 
        ORDER BY id DESC 
        LIMIT 5
    """)
    
    for v in vendas_dividas:
        print(f"Venda {v['id']}: Total MT {v['total']:.2f} - Status: {v['status']} - Origem: {v['origem']}")
    
    # 6. Verificar itens de dívidas
    print("\n6. ITENS DE DÍVIDAS:")
    itens_dividas = db.fetchall("""
        SELECT id.divida_id, id.produto_id, id.quantidade, p.nome as produto_nome
        FROM itens_divida id
        JOIN produtos p ON p.id = id.produto_id
        ORDER BY id.divida_id DESC
        LIMIT 10
    """)
    
    for i in itens_dividas:
        print(f"Dívida {i['divida_id']}: {i['produto_nome']} - Qtd: {i['quantidade']}")
    
    print("\n=== FIM DO TESTE ===")

def testar_estoque_produto(produto_id):
    """Testa o estoque de um produto específico"""
    print(f"\n=== TESTE DE ESTOQUE DO PRODUTO {produto_id} ===")
    
    db = Database()
    
    # Buscar informações do produto
    produto = db.fetchone("""
        SELECT id, nome, estoque, preco_custo, preco_venda 
        FROM produtos 
        WHERE id = ?
    """, (produto_id,))
    
    if not produto:
        print(f"Produto {produto_id} não encontrado!")
        return
    
    print(f"Produto: {produto['nome']}")
    print(f"Estoque atual: {produto['estoque']}")
    print(f"Preço de custo: MT {produto['preco_custo']:.2f}")
    print(f"Preço de venda: MT {produto['preco_venda']:.2f}")
    print(f"Valor em estoque: MT {produto['estoque'] * produto['preco_custo']:.2f}")
    print(f"Valor potencial: MT {produto['estoque'] * produto['preco_venda']:.2f}")
    
    # Verificar itens de dívidas deste produto
    itens_dividas = db.fetchall("""
        SELECT id.divida_id, id.quantidade, d.status, d.valor_total, d.valor_pago
        FROM itens_divida id
        JOIN dividas d ON d.id = id.divida_id
        WHERE id.produto_id = ?
        ORDER BY id.divida_id DESC
    """, (produto_id,))
    
    print(f"\nItens em dívidas: {len(itens_dividas)}")
    for item in itens_dividas:
        print(f"Dívida {item['divida_id']}: {item['quantidade']} unidades - Status: {item['status']} - Total: MT {item['valor_total']:.2f} - Pago: MT {item['valor_pago']:.2f}")

if __name__ == "__main__":
    testar_fluxo_dividas()
    
    # Testar estoque de um produto específico (substitua pelo ID desejado)
    # testar_estoque_produto(1) 