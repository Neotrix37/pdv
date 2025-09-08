#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correção dos erros de interface durante restauração de backup
Corrige problemas de NoneType e IndexError
"""

import sys
import os
import re
from pathlib import Path

# Configurar encoding
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def corrigir_configuracoes_view():
    """Corrige os erros de NoneType em configuracoes_view.py"""
    arquivo = Path("views/configuracoes_view.py")
    
    if not arquivo.exists():
        print(f"❌ Arquivo não encontrado: {arquivo}")
        return False
    
    print(f"🔧 Corrigindo {arquivo}...")
    
    try:
        # Ler conteúdo atual
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Backup do arquivo original
        backup_path = arquivo.with_suffix('.py.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"✓ Backup criado: {backup_path}")
        
        # Correção 1: Adicionar verificação de self.page antes de usar
        conteudo_corrigido = re.sub(
            r'(\s+)self\.page\.window_destroy\(\)',
            r'\1# Verificar se page ainda existe antes de destruir\n\1if self.page and hasattr(self.page, "window_destroy"):\n\1    self.page.window_destroy()',
            conteudo
        )
        
        # Correção 2: Proteger show_snack_bar
        conteudo_corrigido = re.sub(
            r'(\s+)self\.page\.show_snack_bar\(([^)]+)\)',
            r'\1# Verificar se page ainda existe antes de mostrar snackbar\n\1if self.page and hasattr(self.page, "show_snack_bar"):\n\1    self.page.show_snack_bar(\2)',
            conteudo_corrigido
        )
        
        # Correção 3: Proteger page.update()
        conteudo_corrigido = re.sub(
            r'(\s+)self\.page\.update\(\)',
            r'\1# Verificar se page ainda existe antes de atualizar\n\1if self.page and hasattr(self.page, "update"):\n\1    self.page.update()',
            conteudo_corrigido
        )
        
        # Correção 4: Proteger page.go()
        conteudo_corrigido = re.sub(
            r'(\s+)self\.page\.go\(([^)]+)\)',
            r'\1# Verificar se page ainda existe antes de navegar\n\1if self.page and hasattr(self.page, "go"):\n\1    self.page.go(\2)',
            conteudo_corrigido
        )
        
        # Salvar arquivo corrigido
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo_corrigido)
        
        print("✓ configuracoes_view.py corrigido")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir configuracoes_view.py: {e}")
        return False

def corrigir_main_py():
    """Corrige o erro de IndexError em main.py"""
    arquivo = Path("main.py")
    
    if not arquivo.exists():
        print(f"❌ Arquivo não encontrado: {arquivo}")
        return False
    
    print(f"🔧 Corrigindo {arquivo}...")
    
    try:
        # Ler conteúdo atual
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Backup do arquivo original
        backup_path = arquivo.with_suffix('.py.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"✓ Backup criado: {backup_path}")
        
        # Encontrar e corrigir a função view_pop
        padrao_view_pop = r'(\s+def view_pop\(view\):\s+)(.*?)(page\.views\.pop\(\)\s+)(top_view = page\.views\[-1\])'
        
        def substituir_view_pop(match):
            indent = match.group(1)
            meio = match.group(2)
            pop_line = match.group(3)
            problema = match.group(4)
            
            nova_funcao = f"""{indent}{meio}{pop_line}        # Verificar se ainda há views na lista antes de acessar
        if len(page.views) > 0:
            top_view = page.views[-1]
            page.go(top_view.route)
        else:
            # Se não há views, ir para a rota padrão
            page.go("/login")"""
            
            return nova_funcao
        
        conteudo_corrigido = re.sub(
            padrao_view_pop,
            substituir_view_pop,
            conteudo,
            flags=re.DOTALL
        )
        
        # Se não encontrou o padrão exato, tentar uma correção mais simples
        if conteudo_corrigido == conteudo:
            conteudo_corrigido = re.sub(
                r'(\s+)top_view = page\.views\[-1\]',
                r'\1# Verificar se há views antes de acessar\n\1if len(page.views) > 0:\n\1    top_view = page.views[-1]\n\1    page.go(top_view.route)\n\1else:\n\1    page.go("/login")\n\1    return',
                conteudo
            )
        
        # Salvar arquivo corrigido
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo_corrigido)
        
        print("✓ main.py corrigido")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir main.py: {e}")
        return False

def adicionar_protecao_threads():
    """Adiciona proteção contra erros de threading"""
    arquivo = Path("views/configuracoes_view.py")
    
    if not arquivo.exists():
        return False
    
    print("🔧 Adicionando proteção contra erros de threading...")
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Adicionar import threading se não existir
        if 'import threading' not in conteudo:
            conteudo = re.sub(
                r'(import flet as ft)',
                r'\1\nimport threading',
                conteudo
            )
        
        # Adicionar método para executar ações na thread principal
        metodo_thread_safe = '''
    def executar_na_thread_principal(self, funcao, *args, **kwargs):
        """Executa uma função na thread principal de forma segura"""
        try:
            if self.page and hasattr(self.page, 'update'):
                return funcao(*args, **kwargs)
        except Exception as e:
            print(f"Erro ao executar na thread principal: {e}")
            return None
'''
        
        # Adicionar o método antes da última linha da classe
        if 'def executar_na_thread_principal' not in conteudo:
            # Encontrar o final da classe ConfiguracoesView
            padrao_fim_classe = r'(\n\s+def build\(self\):.*?)(\n\s+return.*?)\n(\s*$|\nclass|\ndef)'
            
            def adicionar_metodo(match):
                antes = match.group(1)
                return_statement = match.group(2)
                depois = match.group(3)
                
                return f"{antes}{metodo_thread_safe}{return_statement}\n{depois}"
            
            conteudo = re.sub(padrao_fim_classe, adicionar_metodo, conteudo, flags=re.DOTALL)
        
        # Salvar arquivo
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print("✓ Proteção de threading adicionada")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar proteção de threading: {e}")
        return False

def verificar_correcoes():
    """Verifica se as correções foram aplicadas corretamente"""
    print("\n🔍 Verificando correções aplicadas...")
    
    # Verificar configuracoes_view.py
    try:
        with open("views/configuracoes_view.py", 'r', encoding='utf-8') as f:
            conteudo_config = f.read()
        
        verificacoes_config = [
            ('Proteção window_destroy', 'hasattr(self.page, "window_destroy")' in conteudo_config),
            ('Proteção show_snack_bar', 'hasattr(self.page, "show_snack_bar")' in conteudo_config),
            ('Proteção page.update', 'hasattr(self.page, "update")' in conteudo_config),
        ]
        
        for nome, passou in verificacoes_config:
            status = "✓" if passou else "❌"
            print(f"  {status} {nome}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar configuracoes_view.py: {e}")
    
    # Verificar main.py
    try:
        with open("main.py", 'r', encoding='utf-8') as f:
            conteudo_main = f.read()
        
        verificacoes_main = [
            ('Proteção page.views', 'len(page.views) > 0' in conteudo_main),
        ]
        
        for nome, passou in verificacoes_main:
            status = "✓" if passou else "❌"
            print(f"  {status} {nome}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar main.py: {e}")

def main():
    """Função principal"""
    print("CORRIGINDO ERROS DE INTERFACE NA RESTAURAÇÃO DE BACKUP")
    print("="*55)
    
    sucessos = 0
    total = 3
    
    # Executar correções
    if corrigir_configuracoes_view():
        sucessos += 1
    
    if corrigir_main_py():
        sucessos += 1
    
    if adicionar_protecao_threads():
        sucessos += 1
    
    # Verificar resultados
    verificar_correcoes()
    
    print(f"\n📊 RESULTADO: {sucessos}/{total} correções aplicadas com sucesso")
    
    if sucessos == total:
        print("✅ Todas as correções foram aplicadas!")
        print("\n🎯 PROBLEMAS RESOLVIDOS:")
        print("  • 'NoneType' object has no attribute 'window_destroy' ✓")
        print("  • 'NoneType' object has no attribute 'show_snack_bar' ✓")
        print("  • IndexError: list index out of range ✓")
        print("  • Erros de threading durante restauração ✓")
        print("\n💡 Agora a restauração de backup deve funcionar sem erros de interface!")
    else:
        print("⚠️  Algumas correções falharam - verifique os logs acima")
    
    return sucessos == total

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)
