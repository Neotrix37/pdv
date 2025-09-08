#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simples para corrigir erro 'NoneType' object is not subscriptable
na função get_vendas_disponiveis_mes
"""

import os
import shutil
from datetime import datetime

def corrigir_funcao():
    """Corrige a função get_vendas_disponiveis_mes"""
    arquivo = "database/database.py"
    
    # Fazer backup
    backup_path = f"{arquivo}.backup_nonetype_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(arquivo, backup_path)
    print(f"Backup criado: {backup_path}")
    
    # Ler arquivo
    with open(arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    # Procurar e corrigir as linhas problemáticas
    alteracoes = 0
    for i, linha in enumerate(linhas):
        # Corrigir linha com result_vendas['total']
        if "total_vendas = result_vendas['total'] if result_vendas['total'] else 0" in linha:
            linhas[i] = linha.replace(
                "result_vendas['total'] if result_vendas['total'] else 0",
                "result_vendas['total'] if result_vendas and result_vendas['total'] else 0"
            )
            print(f"Linha {i+1} corrigida: verificacao de None para result_vendas")
            alteracoes += 1
        
        # Corrigir linha com result_saques['total_saques']
        if "total_saques = result_saques['total_saques'] if result_saques['total_saques'] else 0" in linha:
            linhas[i] = linha.replace(
                "result_saques['total_saques'] if result_saques['total_saques'] else 0",
                "result_saques['total_saques'] if result_saques and result_saques['total_saques'] else 0"
            )
            print(f"Linha {i+1} corrigida: verificacao de None para result_saques")
            alteracoes += 1
        
        # Corrigir linha com result_lucro['lucro']
        if "lucro_bruto = result_lucro['lucro'] if result_lucro['lucro'] else 0" in linha:
            linhas[i] = linha.replace(
                "result_lucro['lucro'] if result_lucro['lucro'] else 0",
                "result_lucro['lucro'] if result_lucro and result_lucro['lucro'] else 0"
            )
            print(f"Linha {i+1} corrigida: verificacao de None para result_lucro")
            alteracoes += 1
    
    if alteracoes > 0:
        # Salvar arquivo corrigido
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.writelines(linhas)
        print(f"Arquivo salvo com {alteracoes} correcoes aplicadas")
        return True
    else:
        print("Nenhuma correcao necessaria encontrada")
        return True

def validar_sintaxe():
    """Valida a sintaxe do arquivo"""
    try:
        import py_compile
        py_compile.compile('database/database.py', doraise=True)
        print("Sintaxe validada com sucesso!")
        return True
    except Exception as e:
        print(f"Erro de sintaxe: {e}")
        return False

def testar_funcao():
    """Testa a função corrigida"""
    try:
        from database.database import Database
        db = Database()
        resultado = db.get_vendas_disponiveis_mes()
        print(f"Teste da funcao: MT {resultado:.2f}")
        return True
    except Exception as e:
        print(f"Erro no teste: {e}")
        return False

def main():
    print("CORRECAO SIMPLES DO ERRO NoneType")
    print("=" * 40)
    
    if corrigir_funcao():
        print("\nValidando sintaxe...")
        if validar_sintaxe():
            print("\nTestando funcao corrigida...")
            if testar_funcao():
                print("\nCORRECAO CONCLUIDA COM SUCESSO!")
                print("O erro 'NoneType' object is not subscriptable foi corrigido.")
            else:
                print("\nFuncao corrigida mas ainda ha erros no teste.")
        else:
            print("\nErro de sintaxe detectado.")
    else:
        print("\nFalha na correcao.")

if __name__ == "__main__":
    main()
