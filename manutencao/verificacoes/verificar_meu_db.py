#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar os dados reais do backup meu.db
"""

import sqlite3
import os
from datetime import datetime

def verificar_meu_db():
    """Verifica os dados reais do backup meu.db"""
    backup_path = "backups/meu.db"
    
    if not os.path.exists(backup_path):
        print(f"Backup nao encontrado: {backup_path}")
        return
    
    print("VERIFICACAO DETALHADA DO BACKUP meu.db")
    print("=" * 50)
    
    try:
        # Conectar ao backup
        conn = sqlite3.connect(backup_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar vendas por período
        print("\n1. VENDAS POR PERIODO:")
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', data_venda) as mes,
                COUNT(*) as total_vendas,
                COALESCE(SUM(total), 0) as valor_total
            FROM vendas 
            GROUP BY strftime('%Y-%m', data_venda)
            ORDER BY mes DESC
        """)
        vendas_por_mes = cursor.fetchall()
        
        if vendas_por_mes:
            for row in vendas_por_mes:
                print(f"  {row['mes']}: {row['total_vendas']} vendas - MT {row['valor_total']:.2f}")
        else:
            print("  Nenhuma venda encontrada")
        
        # Verificar vendas totais
        print("\n2. RESUMO GERAL:")
        cursor.execute("SELECT COUNT(*) as total FROM vendas")
        total_vendas = cursor.fetchone()['total']
        print(f"  Total de vendas: {total_vendas}")
        
        if total_vendas > 0:
            cursor.execute("SELECT COALESCE(SUM(total), 0) as soma FROM vendas WHERE status != 'Anulada' OR status IS NULL")
            soma_vendas = cursor.fetchone()['soma']
            print(f"  Valor total das vendas: MT {soma_vendas:.2f}")
            
            # Primeira e última venda
            cursor.execute("SELECT MIN(data_venda) as primeira, MAX(data_venda) as ultima FROM vendas")
            periodo = cursor.fetchone()
            print(f"  Periodo: {periodo['primeira']} ate {periodo['ultima']}")
        
        # Verificar produtos e estoque
        print("\n3. PRODUTOS E ESTOQUE:")
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE ativo = 1 OR ativo IS NULL")
        total_produtos = cursor.fetchone()['total']
        print(f"  Produtos ativos: {total_produtos}")
        
        if total_produtos > 0:
            cursor.execute("SELECT COALESCE(SUM(preco_custo * estoque), 0) as valor_estoque FROM produtos WHERE ativo = 1 OR ativo IS NULL")
            valor_estoque = cursor.fetchone()['valor_estoque']
            print(f"  Valor em estoque: MT {valor_estoque:.2f}")
            
            cursor.execute("SELECT COALESCE(SUM(preco_venda * estoque), 0) as valor_venda FROM produtos WHERE ativo = 1 OR ativo IS NULL")
            valor_venda = cursor.fetchone()['valor_venda']
            print(f"  Valor potencial: MT {valor_venda:.2f}")
        
        # Verificar vendas do mês atual (agosto 2025)
        print("\n4. VENDAS DO MES ATUAL (AGOSTO 2025):")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_vendas,
                COALESCE(SUM(total), 0) as valor_total
            FROM vendas 
            WHERE strftime('%Y-%m', data_venda) = '2025-08'
        """)
        vendas_agosto = cursor.fetchone()
        print(f"  Vendas em agosto 2025: {vendas_agosto['total_vendas']} vendas - MT {vendas_agosto['valor_total']:.2f}")
        
        # Verificar vendas de hoje
        print("\n5. VENDAS DE HOJE (23/08/2025):")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_vendas,
                COALESCE(SUM(total), 0) as valor_total
            FROM vendas 
            WHERE DATE(data_venda) = '2025-08-23'
        """)
        vendas_hoje = cursor.fetchone()
        print(f"  Vendas hoje: {vendas_hoje['total_vendas']} vendas - MT {vendas_hoje['valor_total']:.2f}")
        
        # Verificar estrutura da tabela vendas
        print("\n6. ESTRUTURA DA TABELA VENDAS:")
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = cursor.fetchall()
        colunas_nomes = [col[1] for col in colunas]
        print(f"  Colunas: {', '.join(colunas_nomes)}")
        
        tem_total = 'total' in colunas_nomes
        print(f"  Tem coluna 'total': {'SIM' if tem_total else 'NAO'}")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("CONCLUSAO:")
        print("Se as vendas aparecem como MT 100.00 no dashboard mas o backup")
        print("tem mais dados, provavelmente as vendas sao de periodos anteriores")
        print("e o dashboard so mostra vendas do mes/dia atual.")
        
    except Exception as e:
        print(f"Erro ao verificar backup: {e}")

if __name__ == "__main__":
    verificar_meu_db()
