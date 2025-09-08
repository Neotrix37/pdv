#!/usr/bin/env python3
"""
Script para verificar detalhadamente o banco APPDATA
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verificar_banco_appdata():
    """Verifica detalhadamente o banco APPDATA"""
    print("=== VERIFICAÇÃO DETALHADA DO BANCO APPDATA ===\n")
    
    try:
        # Caminho do banco APPDATA
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
        appdata_db = app_data_db_dir / 'sistema.db'
        
        print(f"1. Caminho do banco: {appdata_db}")
        print(f"2. Banco existe: {appdata_db.exists()}")
        
        if not appdata_db.exists():
            print("❌ Banco APPDATA não existe!")
            return
        
        # Conectar ao banco
        conn = sqlite3.connect(str(appdata_db))
        cursor = conn.cursor()
        
        # Verificar tabelas
        print("\n3. Tabelas no banco:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        for tabela in tabelas:
            print(f"  - {tabela[0]}")
        
        # Verificar produtos
        print("\n4. Verificação da tabela produtos:")
        
        # Verificar se tabela existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='produtos'
        """)
        
        if not cursor.fetchone():
            print("  ❌ Tabela produtos não existe!")
            return
        
        # Contar produtos
        cursor.execute("SELECT COUNT(*) FROM produtos")
        total_produtos = cursor.fetchone()[0]
        print(f"  - Total de produtos: {total_produtos}")
        
        # Contar produtos ativos
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE ativo = 1")
        produtos_ativos = cursor.fetchone()[0]
        print(f"  - Produtos ativos: {produtos_ativos}")
        
        # Contar produtos com estoque
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque > 0")
        produtos_com_estoque = cursor.fetchone()[0]
        print(f"  - Produtos com estoque > 0: {produtos_com_estoque}")
        
        # Verificar estrutura da tabela
        print("\n5. Estrutura da tabela produtos:")
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = cursor.fetchall()
        for coluna in colunas:
            print(f"  - {coluna[1]} ({coluna[2]})")
        
        # Mostrar alguns produtos
        print("\n6. Primeiros 5 produtos:")
        cursor.execute("""
            SELECT id, codigo, nome, estoque, preco_custo, preco_venda, ativo
            FROM produtos 
            ORDER BY id 
            LIMIT 5
        """)
        
        produtos = cursor.fetchall()
        for produto in produtos:
            print(f"  - ID {produto[0]}: {produto[2]} (Código: {produto[1]})")
            print(f"    Estoque: {produto[3]} | Custo: MT {produto[4]:.2f} | Venda: MT {produto[5]:.2f}")
            print(f"    Ativo: {'Sim' if produto[6] else 'Não'}")
        
        # Calcular valores
        print("\n7. Cálculos de estoque:")
        
        # Valor total do estoque (ativo = 1)
        cursor.execute("""
            SELECT COALESCE(SUM(estoque * preco_custo), 0) as valor_total
            FROM produtos
            WHERE ativo = 1
        """)
        valor_estoque = cursor.fetchone()[0] or 0
        print(f"  - Valor total em estoque (ativo=1): MT {valor_estoque:.2f}")
        
        # Valor total do estoque (todos)
        cursor.execute("""
            SELECT COALESCE(SUM(estoque * preco_custo), 0) as valor_total
            FROM produtos
        """)
        valor_estoque_todos = cursor.fetchone()[0] or 0
        print(f"  - Valor total em estoque (todos): MT {valor_estoque_todos:.2f}")
        
        # Valor potencial (ativo = 1)
        cursor.execute("""
            SELECT COALESCE(SUM(estoque * preco_venda), 0) as valor_total
            FROM produtos
            WHERE ativo = 1
        """)
        valor_potencial = cursor.fetchone()[0] or 0
        print(f"  - Valor potencial (ativo=1): MT {valor_potencial:.2f}")
        
        # Valor potencial (todos)
        cursor.execute("""
            SELECT COALESCE(SUM(estoque * preco_venda), 0) as valor_total
            FROM produtos
        """)
        valor_potencial_todos = cursor.fetchone()[0] or 0
        print(f"  - Valor potencial (todos): MT {valor_potencial_todos:.2f}")
        
        # Verificar produtos com estoque
        print("\n8. Produtos com estoque > 0:")
        cursor.execute("""
            SELECT id, codigo, nome, estoque, preco_custo, preco_venda, ativo
            FROM produtos 
            WHERE estoque > 0 
            ORDER BY estoque DESC
        """)
        
        produtos_estoque = cursor.fetchall()
        if produtos_estoque:
            for produto in produtos_estoque:
                valor_estoque_produto = produto[3] * produto[4]
                valor_potencial_produto = produto[3] * produto[5]
                print(f"  - ID {produto[0]}: {produto[2]} (Código: {produto[1]})")
                print(f"    Estoque: {produto[3]} | Custo: MT {produto[4]:.2f} | Venda: MT {produto[5]:.2f}")
                print(f"    Valor estoque: MT {valor_estoque_produto:.2f} | Valor potencial: MT {valor_potencial_produto:.2f}")
                print(f"    Ativo: {'Sim' if produto[6] else 'Não'}")
        else:
            print("  - Nenhum produto com estoque encontrado")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco APPDATA: {e}")

def main():
    print("=== VERIFICAÇÃO DO BANCO APPDATA ===\n")
    verificar_banco_appdata()
    print("\n🎉 Verificação concluída!")

if __name__ == "__main__":
    main()
