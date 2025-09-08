#!/usr/bin/env python3
"""
Script para corrigir o estoque de vendas anuladas que têm origem 'divida_quitada'
Este script deve ser executado uma vez para corrigir problemas de estoque
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database

def main():
    print("=== Script de Correção de Estoque ===")
    print("Este script corrige o estoque de vendas anuladas que têm origem 'divida_quitada'")
    print()
    
    # Confirmar execução
    resposta = input("Deseja continuar? (s/N): ").strip().lower()
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("Operação cancelada.")
        return
    
    try:
        # Conectar ao banco de dados
        db = Database()
        
        # Executar correção
        print("\nExecutando correção...")
        sucesso = db.corrigir_estoque_vendas_anuladas()
        
        if sucesso:
            print("\n✅ Correção concluída com sucesso!")
            
            # Mostrar valores atualizados
            valor_estoque = db.get_valor_estoque()
            valor_potencial = db.get_valor_venda_estoque()
            
            print(f"\nValores atualizados:")
            print(f"  - Valor em estoque: MT {valor_estoque:.2f}")
            print(f"  - Valor potencial: MT {valor_potencial:.2f}")
        else:
            print("\n❌ Erro ao executar correção!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return
    
    print("\n=== Fim do script ===")

if __name__ == "__main__":
    main() 