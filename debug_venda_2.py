#!/usr/bin/env python3
"""
Script para debugar a venda ID 2 que está dando erro 500.
"""

import sqlite3
import os
import json

def main():
    db_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "SistemaGestao", "database", "sistema.db")
    
    print("=== DEBUG VENDA ID 2 ===")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Buscar venda ID 2
    cursor.execute("""
        SELECT * FROM vendas WHERE id = 2
    """)
    venda = cursor.fetchone()
    
    if venda:
        print("=== DADOS DA VENDA ===")
        for key in venda.keys():
            print(f"{key}: {venda[key]}")
        
        # Buscar itens da venda
        print("\n=== ITENS DA VENDA ===")
        cursor.execute("""
            SELECT iv.*, p.codigo, p.nome, p.uuid as produto_uuid
            FROM itens_venda iv
            LEFT JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = 2
        """)
        itens = cursor.fetchall()
        
        for item in itens:
            print("--- Item ---")
            for key in item.keys():
                print(f"  {key}: {item[key]}")
        
        # Mostrar como seria o JSON enviado
        print("\n=== JSON QUE SERIA ENVIADO ===")
        itens_data = []
        for item in itens:
            if item['produto_uuid']:
                qtd_raw = float(item['quantidade'])
                qtd_int = int(qtd_raw)
                peso_kg = 0.0
                if qtd_raw != qtd_int:
                    peso_kg = qtd_raw - qtd_int
                
                itens_data.append({
                    "produto_id": item['produto_uuid'],
                    "quantidade": qtd_int,
                    "peso_kg": peso_kg,
                    "preco_unitario": float(item['preco_unitario']),
                    "subtotal": float(item['subtotal'])
                })
        
        venda_data = {
            "uuid": venda['uuid'],
            "data_venda": venda['data_venda'],
            "total": float(venda['total']),
            "desconto": float(venda['desconto_aplicado_divida']) if venda['desconto_aplicado_divida'] else 0.0,
            "forma_pagamento": venda['forma_pagamento'] or "Dinheiro",
            "status": venda['status'],
            "itens": itens_data
        }
        
        print(json.dumps(venda_data, indent=2, ensure_ascii=False))
        
    else:
        print("Venda ID 2 não encontrada!")
    
    conn.close()

if __name__ == "__main__":
    main()
