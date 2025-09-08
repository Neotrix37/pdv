#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para análise completa de todas as vendas no banco de dados atual
Verifica integridade, consistência e estatísticas detalhadas
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

def analisar_todas_vendas():
    """Analisa todas as vendas no banco de dados atual"""
    
    print("ANÁLISE COMPLETA DE TODAS AS VENDAS")
    print("=" * 60)
    
    # Conectar ao banco de dados ativo (APPDATA)
    sistema = os.name
    if sistema == 'nt' and 'APPDATA' in os.environ:  # Windows
        db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    else:
        db_path = Path(os.path.expanduser('~')) / '.sistemagestao' / 'database' / 'sistema.db'
    
    print(f"[INFO] Analisando banco: {db_path}")
    
    if not db_path.exists():
        print(f"[ERRO] Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. ESTATÍSTICAS GERAIS
        print("\n1. ESTATÍSTICAS GERAIS")
        print("-" * 30)
        
        # Total de vendas
        cursor.execute("SELECT COUNT(*) FROM vendas")
        total_vendas = cursor.fetchone()[0]
        print(f"Total de vendas: {total_vendas}")
        
        # Vendas por status
        cursor.execute("""
            SELECT status, COUNT(*) as quantidade, 
                   COALESCE(SUM(total), 0) as valor_total
            FROM vendas 
            GROUP BY status
            ORDER BY quantidade DESC
        """)
        
        print("\nVendas por Status:")
        for row in cursor.fetchall():
            status, qtd, valor = row
            print(f"  {status}: {qtd} vendas, MT {valor:.2f}")
        
        # 2. ANÁLISE TEMPORAL
        print("\n2. ANÁLISE TEMPORAL")
        print("-" * 30)
        
        # Vendas por mês
        cursor.execute("""
            SELECT strftime('%Y-%m', data_venda) as mes,
                   COUNT(*) as quantidade,
                   COALESCE(SUM(CASE WHEN status != 'Anulada' THEN total ELSE 0 END), 0) as valor
            FROM vendas
            GROUP BY strftime('%Y-%m', data_venda)
            ORDER BY mes DESC
            LIMIT 12
        """)
        
        print("\nVendas por Mês (últimos 12 meses):")
        for row in cursor.fetchall():
            mes, qtd, valor = row
            print(f"  {mes}: {qtd} vendas, MT {valor:.2f}")
        
        # 3. ANÁLISE DE VALORES
        print("\n3. ANÁLISE DE VALORES")
        print("-" * 30)
        
        # Estatísticas de valores (excluindo anuladas)
        cursor.execute("""
            SELECT 
                COUNT(*) as vendas_validas,
                COALESCE(SUM(total), 0) as valor_total,
                COALESCE(AVG(total), 0) as valor_medio,
                COALESCE(MIN(total), 0) as valor_minimo,
                COALESCE(MAX(total), 0) as valor_maximo
            FROM vendas 
            WHERE status != 'Anulada'
        """)
        
        stats = cursor.fetchone()
        print(f"Vendas válidas: {stats[0]}")
        print(f"Valor total: MT {stats[1]:.2f}")
        print(f"Valor médio: MT {stats[2]:.2f}")
        print(f"Valor mínimo: MT {stats[3]:.2f}")
        print(f"Valor máximo: MT {stats[4]:.2f}")
        
        # 4. ANÁLISE DE INTEGRIDADE
        print("\n4. ANÁLISE DE INTEGRIDADE")
        print("-" * 30)
        
        # Verificar vendas sem itens
        cursor.execute("""
            SELECT COUNT(*) 
            FROM vendas v
            LEFT JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE iv.venda_id IS NULL
        """)
        vendas_sem_itens = cursor.fetchone()[0]
        print(f"Vendas sem itens: {vendas_sem_itens}")
        
        # Verificar inconsistências de total
        cursor.execute("""
            SELECT v.id, v.total as total_venda,
                   COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0) as total_calculado
            FROM vendas v
            LEFT JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE v.status != 'Anulada'
            GROUP BY v.id, v.total
            HAVING ABS(v.total - COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0)) > 0.01
            LIMIT 10
        """)
        
        inconsistencias = cursor.fetchall()
        print(f"Vendas com inconsistências de total: {len(inconsistencias)}")
        if inconsistencias:
            print("  Primeiras 10 inconsistências:")
            for venda_id, total_venda, total_calc in inconsistencias:
                print(f"    Venda {venda_id}: Registrado MT {total_venda:.2f}, Calculado MT {total_calc:.2f}")
        
        # 5. TOP VENDAS
        print("\n5. TOP 10 MAIORES VENDAS")
        print("-" * 30)
        
        cursor.execute("""
            SELECT id, data_venda, total, status, usuario_id
            FROM vendas
            WHERE status != 'Anulada'
            ORDER BY total DESC
            LIMIT 10
        """)
        
        for i, row in enumerate(cursor.fetchall(), 1):
            venda_id, data, total, status, usuario = row
            print(f"  {i}. Venda {venda_id}: MT {total:.2f} ({data}) - {status}")
        
        # 6. ANÁLISE DE PRODUTOS MAIS VENDIDOS
        print("\n6. TOP 10 PRODUTOS MAIS VENDIDOS")
        print("-" * 30)
        
        cursor.execute("""
            SELECT p.nome, 
                   SUM(iv.quantidade) as qtd_vendida,
                   COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0) as valor_total
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            JOIN vendas v ON iv.venda_id = v.id
            WHERE v.status != 'Anulada'
            GROUP BY p.id, p.nome
            ORDER BY qtd_vendida DESC
            LIMIT 10
        """)
        
        for i, row in enumerate(cursor.fetchall(), 1):
            nome, qtd, valor = row
            print(f"  {i}. {nome}: {qtd} unidades, MT {valor:.2f}")
        
        # 7. RESUMO FINAL
        print("\n7. RESUMO FINAL")
        print("-" * 30)
        
        # Calcular totais finais
        cursor.execute("""
            SELECT 
                COUNT(*) as total_registros,
                SUM(CASE WHEN status != 'Anulada' THEN 1 ELSE 0 END) as vendas_validas,
                SUM(CASE WHEN status = 'Anulada' THEN 1 ELSE 0 END) as vendas_anuladas,
                COALESCE(SUM(CASE WHEN status != 'Anulada' THEN total ELSE 0 END), 0) as receita_total
            FROM vendas
        """)
        
        resumo = cursor.fetchone()
        print(f"Total de registros: {resumo[0]}")
        print(f"Vendas válidas: {resumo[1]}")
        print(f"Vendas anuladas: {resumo[2]}")
        print(f"Receita total: MT {resumo[3]:.2f}")
        
        # Verificar data da primeira e última venda
        cursor.execute("""
            SELECT MIN(data_venda) as primeira, MAX(data_venda) as ultima
            FROM vendas
            WHERE status != 'Anulada'
        """)
        
        datas = cursor.fetchone()
        if datas[0]:
            print(f"Primeira venda: {datas[0]}")
            print(f"Última venda: {datas[1]}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("[CONCLUÍDO] Análise de vendas finalizada com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"[ERRO] Falha na análise: {e}")
        return False

if __name__ == "__main__":
    sucesso = analisar_todas_vendas()
    
    if sucesso:
        print("\n✅ Análise concluída com sucesso!")
    else:
        print("\n❌ Falha na análise dos dados.")
