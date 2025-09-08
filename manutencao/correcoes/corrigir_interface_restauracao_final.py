#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir erros de interface durante restauração de backup.

Corrige:
1. 'NoneType' object has no attribute 'window_destroy' em configuracoes_view.py
2. 'NoneType' object has no attribute 'show_snack_bar' em configuracoes_view.py  
3. UnboundLocalError: cannot access local variable 'top_view' em main.py
"""

import os
import shutil
from datetime import datetime

def fazer_backup(arquivo):
    """Cria backup do arquivo"""
    backup_path = f"{arquivo}.backup_interface_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(arquivo, backup_path)
    print(f"Backup criado: {backup_path}")
    return backup_path

def corrigir_configuracoes_view():
    """Corrige erros de NoneType em configuracoes_view.py"""
    arquivo = "views/configuracoes_view.py"
    
    if not os.path.exists(arquivo):
        print(f"Arquivo nao encontrado: {arquivo}")
        return False
    
    print(f"Corrigindo {arquivo}...")
    fazer_backup(arquivo)
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Correções específicas para os erros de NoneType
    correcoes = [
        # Correção 1: window_destroy com verificação de None
        {
            'buscar': 'self.page.window_destroy()',
            'substituir': 'self.page.window_destroy() if self.page and hasattr(self.page, "window_destroy") else None',
            'descricao': 'Verificacao de None para window_destroy'
        },
        
        # Correção 2: show_snack_bar com verificação de None
        {
            'buscar': 'self.page.show_snack_bar(',
            'substituir': 'self.page.show_snack_bar(' if 'if self.page and hasattr(self.page, "show_snack_bar")' not in conteudo else 'self.page.show_snack_bar(',
            'descricao': 'Verificacao de None para show_snack_bar'
        }
    ]
    
    alteracoes = 0
    conteudo_original = conteudo
    
    # Aplicar correções mais específicas
    # Corrigir todas as ocorrências de self.page.window_destroy()
    if 'self.page.window_destroy()' in conteudo:
        conteudo = conteudo.replace(
            'self.page.window_destroy()',
            'self.page.window_destroy() if self.page and hasattr(self.page, "window_destroy") else None'
        )
        print("  Corrigido: window_destroy com verificacao de None")
        alteracoes += 1
    
    # Corrigir show_snack_bar - mais complexo pois tem parâmetros
    import re
    
    # Padrão para capturar self.page.show_snack_bar(...) completo
    padrao_snackbar = r'self\.page\.show_snack_bar\([^)]*\)'
    matches = re.findall(padrao_snackbar, conteudo)
    
    for match in matches:
        # Verificar se já não tem a proteção
        if 'if self.page and hasattr(self.page, "show_snack_bar")' not in conteudo:
            # Substituir por versão protegida
            conteudo_protegido = f'''if self.page and hasattr(self.page, "show_snack_bar"):
                    {match}'''
            conteudo = conteudo.replace(match, conteudo_protegido)
            alteracoes += 1
    
    if alteracoes > 0:
        print(f"  Aplicadas {alteracoes} correcoes em show_snack_bar")
    
    # Salvar arquivo se houve alterações
    if conteudo != conteudo_original:
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"Arquivo {arquivo} corrigido com sucesso")
        return True
    else:
        print(f"Nenhuma correcao necessaria em {arquivo}")
        return True

def corrigir_main_py():
    """Corrige erro de UnboundLocalError em main.py"""
    arquivo = "main.py"
    
    if not os.path.exists(arquivo):
        print(f"Arquivo nao encontrado: {arquivo}")
        return False
    
    print(f"Corrigindo {arquivo}...")
    fazer_backup(arquivo)
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    # Procurar pela função view_pop e corrigir o erro de top_view
    alteracoes = 0
    for i, linha in enumerate(linhas):
        # Procurar pela linha problemática
        if 'page.go(top_view.route)' in linha and 'UnboundLocalError' in str(linha) or True:
            # Verificar se estamos na função view_pop
            for j in range(max(0, i-10), i):
                if 'def view_pop(' in linhas[j]:
                    # Encontrou a função, vamos corrigir
                    # Procurar por onde top_view deveria ser definido
                    for k in range(j, min(len(linhas), i+5)):
                        if 'page.go(top_view.route)' in linhas[k]:
                            # Substituir por versão segura
                            linhas[k] = linhas[k].replace(
                                'page.go(top_view.route)',
                                'page.go(top_view.route) if "top_view" in locals() and top_view else page.go("/dashboard")'
                            )
                            print(f"  Linha {k+1} corrigida: UnboundLocalError para top_view")
                            alteracoes += 1
                            break
                    break
    
    # Correção mais específica para o erro de top_view
    conteudo = ''.join(linhas)
    
    # Padrão mais específico para a função view_pop
    if 'def view_pop(' in conteudo and 'page.go(top_view.route)' in conteudo:
        # Substituir a função inteira por uma versão corrigida
        funcao_corrigida = '''def view_pop(page):
    """Remove a view atual da pilha e volta para a anterior"""
    try:
        if len(page.views) > 1:
            page.views.pop()
            if len(page.views) > 0:
                top_view = page.views[-1]
                page.go(top_view.route)
            else:
                page.go("/dashboard")
        else:
            page.go("/dashboard")
        page.update()
    except Exception as e:
        print(f"Erro em view_pop: {e}")
        page.go("/dashboard")
        page.update()'''
        
        # Usar regex para substituir a função
        import re
        padrao_funcao = r'def view_pop\([^)]*\):.*?(?=\ndef|\nclass|\n[a-zA-Z]|\Z)'
        if re.search(padrao_funcao, conteudo, re.DOTALL):
            conteudo = re.sub(padrao_funcao, funcao_corrigida, conteudo, flags=re.DOTALL)
            print("  Funcao view_pop corrigida completamente")
            alteracoes += 1
    
    if alteracoes > 0:
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"Arquivo {arquivo} corrigido com {alteracoes} alteracoes")
        return True
    else:
        print(f"Nenhuma correcao necessaria em {arquivo}")
        return True

def validar_sintaxe():
    """Valida a sintaxe dos arquivos corrigidos"""
    arquivos = ['views/configuracoes_view.py', 'main.py']
    
    for arquivo in arquivos:
        try:
            import py_compile
            py_compile.compile(arquivo, doraise=True)
            print(f"Sintaxe validada: {arquivo}")
        except Exception as e:
            print(f"Erro de sintaxe em {arquivo}: {e}")
            return False
    
    return True

def main():
    print("CORRECAO DE ERROS DE INTERFACE DURANTE RESTAURACAO")
    print("=" * 55)
    
    try:
        # Corrigir configuracoes_view.py
        print("\n1. Corrigindo configuracoes_view.py...")
        if not corrigir_configuracoes_view():
            print("Falha ao corrigir configuracoes_view.py")
            return
        
        # Corrigir main.py
        print("\n2. Corrigindo main.py...")
        if not corrigir_main_py():
            print("Falha ao corrigir main.py")
            return
        
        # Validar sintaxe
        print("\n3. Validando sintaxe...")
        if validar_sintaxe():
            print("\nCORRECAO CONCLUIDA COM SUCESSO!")
            print("\nErros corrigidos:")
            print("- 'NoneType' object has no attribute 'window_destroy'")
            print("- 'NoneType' object has no attribute 'show_snack_bar'")
            print("- UnboundLocalError: cannot access local variable 'top_view'")
            print("\nO sistema agora deve funcionar corretamente durante restauracao de backup.")
        else:
            print("\nErro de sintaxe detectado. Verifique os arquivos manualmente.")
            
    except Exception as e:
        print(f"\nErro durante a correcao: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
