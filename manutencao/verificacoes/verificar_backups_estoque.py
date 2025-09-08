#!/usr/bin/env python3
"""
Script para verificar qual backup tem produtos com estoque
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verificar_backup_estoque(caminho_backup):
    """Verifica se um backup tem produtos com estoque"""
    try:
        conn = sqlite3.connect(str(caminho_backup))
        cursor = conn.cursor()
        
        # Verificar se tabela produtos existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='produtos'
        """)
        
        if not cursor.fetchone():
            return None
        
        # Contar produtos
        cursor.execute("SELECT COUNT(*) FROM produtos")
        total_produtos = cursor.fetchone()[0]
        
        # Contar produtos com estoque
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque > 0")
        produtos_com_estoque = cursor.fetchone()[0]
        
        # Calcular valor estoque
        cursor.execute("""
            SELECT COALESCE(SUM(estoque * preco_custo), 0) as valor_total
            FROM produtos
            WHERE ativo = 1
        """)
        valor_estoque = cursor.fetchone()[0] or 0
        
        # Calcular valor potencial
        cursor.execute("""
            SELECT COALESCE(SUM(estoque * preco_venda), 0) as valor_total
            FROM produtos
            WHERE ativo = 1
        """)
        valor_potencial = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_produtos': total_produtos,
            'produtos_com_estoque': produtos_com_estoque,
            'valor_estoque': valor_estoque,
            'valor_potencial': valor_potencial
        }
        
    except Exception as e:
        print(f"❌ Erro ao verificar {caminho_backup.name}: {e}")
        return None

def main():
    print("=== VERIFICAÇÃO DE BACKUPS COM ESTOQUE ===\n")
    
    # Caminho dos backups
    backups_dir = Path("backups")
    
    if not backups_dir.exists():
        print("❌ Diretório de backups não encontrado!")
        return
    
    # Listar todos os backups
    backups = list(backups_dir.glob("*.db"))
    
    if not backups:
        print("❌ Nenhum backup encontrado!")
        return
    
    print(f"Encontrados {len(backups)} backups:\n")
    
    # Verificar cada backup
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup.name}")
        
        resultado = verificar_backup_estoque(backup)
        
        if resultado:
            print(f"   - Total produtos: {resultado['total_produtos']}")
            print(f"   - Produtos com estoque: {resultado['produtos_com_estoque']}")
            print(f"   - Valor estoque: MT {resultado['valor_estoque']:.2f}")
            print(f"   - Valor potencial: MT {resultado['valor_potencial']:.2f}")
            
            if resultado['produtos_com_estoque'] > 0:
                print(f"   ✅ ESTE BACKUP TEM PRODUTOS COM ESTOQUE!")
        else:
            print("   ❌ Erro ao verificar backup")
        
        print()
    
    print("🎉 Verificação concluída!")

if __name__ == "__main__":
    main()
