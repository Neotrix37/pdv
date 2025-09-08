#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir erro 'NoneType' object has no attribute 'window_reload'
e outros métodos de página que podem causar problemas similares.
"""

import os
import shutil
from datetime import datetime

def fazer_backup(arquivo):
    """Cria backup do arquivo"""
    backup_path = f"{arquivo}.backup_reload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(arquivo, backup_path)
    print(f"Backup criado: {backup_path}")
    return backup_path

def corrigir_configuracoes_view():
    """Corrige todos os métodos de página em configuracoes_view.py"""
    arquivo = "views/configuracoes_view.py"
    
    if not os.path.exists(arquivo):
        print(f"Arquivo nao encontrado: {arquivo}")
        return False
    
    print(f"Corrigindo {arquivo}...")
    fazer_backup(arquivo)
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Lista de métodos de página que precisam de proteção
    metodos_pagina = [
        'window_reload',
        'window_destroy', 
        'show_snack_bar',
        'update',
        'go'
    ]
    
    alteracoes = 0
    conteudo_original = conteudo
    
    # Corrigir cada método individualmente
    for metodo in metodos_pagina:
        # Padrão: self.page.metodo()
        padrao_simples = f"self.page.{metodo}()"
        if padrao_simples in conteudo:
            conteudo = conteudo.replace(
                padrao_simples,
                f"self.page.{metodo}() if self.page and hasattr(self.page, \"{metodo}\") else None"
            )
            print(f"  Corrigido: {metodo}() com verificacao de None")
            alteracoes += 1
        
        # Padrão: self.page.metodo(parametros)
        import re
        padrao_com_params = rf"self\.page\.{metodo}\([^)]*\)"
        matches = re.findall(padrao_com_params, conteudo)
        
        for match in matches:
            # Verificar se já não tem proteção
            if f"if self.page and hasattr(self.page, \"{metodo}\")" not in conteudo:
                # Substituir por versão protegida
                conteudo_protegido = f'''if self.page and hasattr(self.page, "{metodo}"):
                    {match}'''
                conteudo = conteudo.replace(match, conteudo_protegido)
                alteracoes += 1
    
    # Correção específica para casos onde há múltiplas chamadas em sequência
    # Procurar por blocos problemáticos
    linhas = conteudo.split('\n')
    linhas_corrigidas = []
    
    for i, linha in enumerate(linhas):
        linha_original = linha
        
        # Se a linha contém self.page. mas não tem verificação de None
        if 'self.page.' in linha and 'if self.page and hasattr' not in linha:
            # Verificar se é uma chamada de método
            for metodo in metodos_pagina:
                if f'self.page.{metodo}(' in linha:
                    # Adicionar verificação
                    indentacao = len(linha) - len(linha.lstrip())
                    espacos = ' ' * indentacao
                    
                    # Extrair a chamada do método
                    import re
                    match = re.search(rf'self\.page\.{metodo}\([^)]*\)', linha)
                    if match:
                        chamada = match.group(0)
                        linha = linha.replace(
                            chamada,
                            f'{chamada} if self.page and hasattr(self.page, "{metodo}") else None'
                        )
                        if linha != linha_original:
                            alteracoes += 1
                            break
        
        linhas_corrigidas.append(linha)
    
    conteudo_final = '\n'.join(linhas_corrigidas)
    
    if alteracoes > 0 or conteudo_final != conteudo_original:
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo_final)
        print(f"Arquivo corrigido com {alteracoes} alteracoes")
        return True
    else:
        print("Nenhuma correcao necessaria encontrada")
        return True

def validar_sintaxe():
    """Valida a sintaxe do arquivo corrigido"""
    try:
        import py_compile
        py_compile.compile('views/configuracoes_view.py', doraise=True)
        print("Sintaxe validada com sucesso!")
        return True
    except Exception as e:
        print(f"Erro de sintaxe: {e}")
        return False

def main():
    print("CORRECAO DE ERRO window_reload E OUTROS METODOS DE PAGINA")
    print("=" * 60)
    
    try:
        if corrigir_configuracoes_view():
            print("\nValidando sintaxe...")
            if validar_sintaxe():
                print("\nCORRECAO CONCLUIDA COM SUCESSO!")
                print("\nErros corrigidos:")
                print("- 'NoneType' object has no attribute 'window_reload'")
                print("- Outros metodos de pagina protegidos contra NoneType")
                print("\nO sistema agora deve funcionar corretamente durante restauracao.")
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
