#!/usr/bin/env python3
"""Script para debugar problema das vendas no dashboard"""

import sqlite3
import os
from pathlib import Path

def debug_vendas():
    # Caminho do banco de dados
    db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    
    print(f"Conectando ao banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== ESTRUTURA DA TABELA VENDAS ===")
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = cursor.fetchall()
        for col in colunas:
            print(f"- {col[1]} ({col[2]}) - NOT NULL: {col[3]} - DEFAULT: {col[4]}")
        
        print("\n=== VENDAS DE HOJE ===")
        cursor.execute("""
            SELECT id, total, valor_total, data_venda, status, forma_pagamento
            FROM vendas 
            WHERE DATE(data_venda) = DATE('now')
            ORDER BY id DESC
        """)
        vendas = cursor.fetchall()
        
        print(f"Total de vendas hoje: {len(vendas)}")
        for venda in vendas:
            print(f"ID: {venda['id']}, total: {venda.get('total', 'N/A')}, valor_total: {venda.get('valor_total', 'N/A')}, status: {venda['status']}")
        
        print("\n=== TESTE DA QUERY DO DASHBOARD ===")
        cursor.execute("""
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN status = 'Anulada' THEN 0 
                        ELSE total 
                    END
                ), 0) as total_calculado,
                COUNT(*) as total_registros,
                SUM(CASE WHEN status = 'Anulada' THEN 1 ELSE 0 END) as total_anuladas
            FROM vendas
            WHERE DATE(data_venda) = DATE('now')
        """)
        resultado = cursor.fetchone()
        print(f"Total calculado: {resultado['total_calculado']}")
        print(f"Total registros: {resultado['total_registros']}")
        print(f"Total anuladas: {resultado['total_anuladas']}")
        
        print("\n=== VERIFICAR VALORES NULL ===")
        cursor.execute("""
            SELECT COUNT(*) as null_total, COUNT(*) as null_valor_total
            FROM vendas 
            WHERE DATE(data_venda) = DATE('now')
            AND (total IS NULL OR valor_total IS NULL)
        """)
        nulls = cursor.fetchone()
        print(f"Vendas com total NULL: {nulls['null_total']}")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_vendas()
