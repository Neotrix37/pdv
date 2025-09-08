#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir erro 'NoneType' object is not subscriptable
nas funções de cálculo de vendas e lucro.

O problema ocorre quando fetchone() retorna None e o código tenta
acessar result['campo'] sem verificar se result não é None.
"""

import os
import sys
import re
import shutil
from datetime import datetime

def fazer_backup(arquivo):
    """Cria backup do arquivo antes de modificar"""
    backup_path = f"{arquivo}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(arquivo, backup_path)
    print(f"Backup criado: {backup_path}")
    return backup_path

def corrigir_funcoes_database():
    """Corrige as funções que podem ter erro de NoneType"""
    arquivo = "database/database.py"
    
    if not os.path.exists(arquivo):
        print(f"❌ Arquivo não encontrado: {arquivo}")
        return False
    
    print(f"Corrigindo funcoes em {arquivo}...")
    fazer_backup(arquivo)
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Padrões problemáticos e suas correções
    correcoes = [
        # Padrão: result_vendas['total'] if result_vendas['total'] else 0
        # Correção: result_vendas['total'] if result_vendas and result_vendas['total'] else 0
        {
            'padrao': r"(\w+)\['(\w+)'\]\s+if\s+\1\['(\w+)'\]\s+else\s+0",
            'correcao': r"\1['\2'] if \1 and \1['\3'] else 0",
            'descricao': "Verificação de None antes de acessar campos"
        },
        
        # Padrão: result['campo'] if result else 0 (já correto, mas garantir)
        # Adicionar verificação extra para casos específicos
        {
            'padrao': r"result_vendas = self\.fetchone\(query_vendas\)\s*\n\s*total_vendas = result_vendas\['total'\] if result_vendas\['total'\] else 0",
            'correcao': "result_vendas = self.fetchone(query_vendas)\n        total_vendas = result_vendas['total'] if result_vendas and result_vendas['total'] else 0",
            'descricao': "Correção específica para get_vendas_disponiveis_mes"
        },
        
        {
            'padrao': r"result_saques = self\.fetchone\(query_saques\)\s*\n\s*total_saques = result_saques\['total_saques'\] if result_saques\['total_saques'\] else 0",
            'correcao': "result_saques = self.fetchone(query_saques)\n        total_saques = result_saques['total_saques'] if result_saques and result_saques['total_saques'] else 0",
            'descricao': "Correção específica para saques"
        },
        
        {
            'padrao': r"result_lucro = self\.fetchone\(query_lucro\)\s*\n\s*lucro_bruto = result_lucro\['lucro'\] if result_lucro\['lucro'\] else 0",
            'correcao': "result_lucro = self.fetchone(query_lucro)\n        lucro_bruto = result_lucro['lucro'] if result_lucro and result_lucro['lucro'] else 0",
            'descricao': "Correção específica para lucro"
        }
    ]
    
    conteudo_original = conteudo
    alteracoes_feitas = 0
    
    for correcao in correcoes:
        matches = re.findall(correcao['padrao'], conteudo, re.MULTILINE)
        if matches:
            print(f"  Aplicando: {correcao['descricao']} ({len(matches)} ocorrencias)")
            conteudo = re.sub(correcao['padrao'], correcao['correcao'], conteudo, flags=re.MULTILINE)
            alteracoes_feitas += len(matches)
    
    # Correção manual específica para get_vendas_disponiveis_mes
    funcao_problema = """def get_vendas_disponiveis_mes(self):
    \"\"\"Retorna o total de vendas do mês atual MENOS os saques realizados\"\"\"
    try:
        # Total de vendas do mês
        query_vendas = \"\"\"
            SELECT COALESCE(SUM(
                CASE 
                    WHEN status = 'Anulada' THEN 0 
                    ELSE total 
                END
            ), 0) as total
            FROM vendas
            WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
        \"\"\"
        
        result_vendas = self.fetchone(query_vendas)
        total_vendas = result_vendas['total'] if result_vendas and result_vendas['total'] else 0
        
        # Total de saques de vendas do mês
        query_saques = \"\"\"
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'vendas'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND status = 'Completo'
        \"\"\"
        
        result_saques = self.fetchone(query_saques)
        total_saques = result_saques['total_saques'] if result_saques and result_saques['total_saques'] else 0
        
        # Debug: imprimir valores para verificação
        print(f"[DEBUG] Vendas brutas do mês: MT {total_vendas:.2f}")
        print(f"[DEBUG] Saques de vendas do mês: MT {total_saques:.2f}")
        print(f"[DEBUG] Vendas disponíveis: MT {max(0, total_vendas - total_saques):.2f}")
        
        # Retorna vendas menos saques
        return max(0, total_vendas - total_saques)
    except Exception as e:
        print(f"Erro ao calcular vendas disponíveis do mês: {e}")
        return 0"""
    
    # Procurar e substituir a função específica
    padrao_funcao = r"def get_vendas_disponiveis_mes\(self\):.*?return 0"
    if re.search(padrao_funcao, conteudo, re.DOTALL):
        print("  Corrigindo funcao get_vendas_disponiveis_mes especificamente")
        conteudo = re.sub(padrao_funcao, funcao_problema, conteudo, flags=re.DOTALL)
        alteracoes_feitas += 1
    
    # Correção similar para get_lucro_disponivel_mes
    funcao_lucro = """def get_lucro_disponivel_mes(self):
    \"\"\"Retorna o lucro do mês atual MENOS os saques de lucro realizados\"\"\"
    try:
        # Lucro bruto do mês
        query_lucro = \"\"\"
            SELECT COALESCE(SUM(
                CASE 
                    WHEN v.status = 'Anulada' THEN 0 
                    ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                END
            ), 0) as lucro
            FROM vendas v
            JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE strftime('%Y-%m', v.data_venda) = strftime('%Y-%m', 'now')
        \"\"\"
        
        result_lucro = self.fetchone(query_lucro)
        lucro_bruto = result_lucro['lucro'] if result_lucro and result_lucro['lucro'] else 0
        
        # Total de saques de lucro do mês
        query_saques = \"\"\"
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'lucro'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND status = 'Completo'
        \"\"\"
        
        result_saques = self.fetchone(query_saques)
        total_saques = result_saques['total_saques'] if result_saques and result_saques['total_saques'] else 0
        
        # Debug: imprimir valores para verificação
        print(f"[DEBUG] Lucro bruto do mês: MT {lucro_bruto:.2f}")
        print(f"[DEBUG] Saques de lucro do mês: MT {total_saques:.2f}")
        print(f"[DEBUG] Lucro disponível: MT {max(0, lucro_bruto - total_saques):.2f}")
        
        # Retorna lucro menos saques
        return max(0, lucro_bruto - total_saques)
    except Exception as e:
        print(f"Erro ao calcular lucro disponível do mês: {e}")
        return 0"""
    
    padrao_lucro = r"def get_lucro_disponivel_mes\(self\):.*?return 0"
    if re.search(padrao_lucro, conteudo, re.DOTALL):
        print("  Corrigindo funcao get_lucro_disponivel_mes especificamente")
        conteudo = re.sub(padrao_lucro, funcao_lucro, conteudo, flags=re.DOTALL)
        alteracoes_feitas += 1
    
    if alteracoes_feitas > 0:
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"{alteracoes_feitas} correcoes aplicadas em {arquivo}")
        return True
    else:
        print("Nenhuma correcao necessaria encontrada")
        return True

def validar_sintaxe():
    """Valida a sintaxe do arquivo corrigido"""
    try:
        import py_compile
        py_compile.compile('database/database.py', doraise=True)
        print("Sintaxe validada com sucesso!")
        return True
    except py_compile.PyCompileError as e:
        print(f"Erro de sintaxe: {e}")
        return False

def main():
    print("CORRECAO DE ERRO 'NoneType' object is not subscriptable")
    print("=" * 60)
    
    try:
        # Corrigir funções
        if corrigir_funcoes_database():
            print("\nValidando sintaxe...")
            if validar_sintaxe():
                print("\nCORRECAO CONCLUIDA COM SUCESSO!")
                print("\nO erro 'NoneType' object is not subscriptable foi corrigido.")
                print("As funcoes agora verificam se o resultado nao e None antes de acessar os campos.")
            else:
                print("\nErro de sintaxe detectado. Verifique o arquivo manualmente.")
        else:
            print("\nFalha na correcao.")
            
    except Exception as e:
        print(f"\nErro durante a correcao: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
