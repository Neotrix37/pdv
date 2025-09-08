#!/usr/bin/env python3
"""
Script para verificar estoque e produtos no banco
"""

import sys
import os
import sqlite3

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database

def verificar_produtos():
    """Verifica os produtos no banco de dados"""
    print("=== VERIFICAÇÃO DE PRODUTOS ===\n")
    
    try:
        db = Database()
        cursor = db.conn.cursor()
        
        # 1. Verificar se a tabela produtos existe
        print("1. Verificando tabela produtos...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='produtos'
        """)
        
        if not cursor.fetchone():
            print("❌ ERRO: Tabela produtos não existe!")
            return False
        
        print("✅ Tabela produtos existe")
        
        # 2. Contar produtos
        cursor.execute("SELECT COUNT(*) as total FROM produtos")
        total_produtos = cursor.fetchone()[0]
        print(f"  - Total de produtos: {total_produtos}")
        
        # 3. Contar produtos ativos
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE ativo = 1")
        produtos_ativos = cursor.fetchone()[0]
        print(f"  - Produtos ativos: {produtos_ativos}")
        
        # 4. Verificar produtos com estoque
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque > 0")
        produtos_com_estoque = cursor.fetchone()[0]
        print(f"  - Produtos com estoque > 0: {produtos_com_estoque}")
        
        # 5. Calcular valor total do estoque
        cursor.execute("""
            SELECT COALESCE(SUM(estoque * preco_custo), 0) as valor_total
            FROM produtos
            WHERE ativo = 1
        """)
        valor_estoque = cursor.fetchone()[0] or 0
        print(f"  - Valor total em estoque: MT {valor_estoque:.2f}")
        
        # 6. Calcular valor potencial de vendas
        cursor.execute("""
            SELECT COALESCE(SUM(estoque * preco_venda), 0) as valor_total
            FROM produtos
            WHERE ativo = 1
        """)
        valor_potencial = cursor.fetchone()[0] or 0
        print(f"  - Valor potencial de vendas: MT {valor_potencial:.2f}")
        
        # 7. Mostrar alguns produtos com estoque
        print("\n2. Produtos com estoque (top 5):")
        cursor.execute("""
            SELECT id, codigo, nome, estoque, preco_custo, preco_venda, ativo
            FROM produtos 
            WHERE estoque > 0 
            ORDER BY estoque DESC 
            LIMIT 5
        """)
        
        produtos = cursor.fetchall()
        if produtos:
            for produto in produtos:
                valor_estoque_produto = produto[3] * produto[4]
                valor_potencial_produto = produto[3] * produto[5]
                print(f"  - ID {produto[0]}: {produto[2]} (Código: {produto[1]})")
                print(f"    Estoque: {produto[3]} | Custo: MT {produto[4]:.2f} | Venda: MT {produto[5]:.2f}")
                print(f"    Valor estoque: MT {valor_estoque_produto:.2f} | Valor potencial: MT {valor_potencial_produto:.2f}")
                print(f"    Ativo: {'Sim' if produto[6] else 'Não'}")
        else:
            print("  - Nenhum produto com estoque encontrado")
        
        # 8. Verificar produtos inativos
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE ativo = 0")
        produtos_inativos = cursor.fetchone()[0]
        print(f"\n3. Produtos inativos: {produtos_inativos}")
        
        # 9. Verificar produtos com estoque zero
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE estoque = 0")
        produtos_sem_estoque = cursor.fetchone()[0]
        print(f"4. Produtos com estoque zero: {produtos_sem_estoque}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar produtos: {e}")
        return False

def testar_metodos_estoque():
    """Testa os métodos de estoque do banco"""
    print("\n=== TESTE DOS MÉTODOS DE ESTOQUE ===\n")
    
    try:
        db = Database()
        
        # Testar get_valor_estoque
        print("1. Testando get_valor_estoque():")
        valor_estoque = db.get_valor_estoque()
        print(f"   Resultado: MT {valor_estoque:.2f}")
        
        # Testar get_valor_venda_estoque
        print("\n2. Testando get_valor_venda_estoque():")
        valor_potencial = db.get_valor_venda_estoque()
        print(f"   Resultado: MT {valor_potencial:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar métodos de estoque: {e}")
        return False

def main():
    print("=== VERIFICAÇÃO DE ESTOQUE ===\n")
    
    # 1. Verificar produtos
    if not verificar_produtos():
        print("❌ Falha na verificação de produtos!")
        return
    
    # 2. Testar métodos de estoque
    if not testar_metodos_estoque():
        print("❌ Falha no teste dos métodos de estoque!")
        return
    
    print("\n🎉 Verificação concluída com sucesso!")

if __name__ == "__main__":
    main()
