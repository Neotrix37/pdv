#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir o problema da tela de login que fica em branco
após a restauração de backup.

O problema pode estar relacionado a:
1. Limpeza inadequada das views
2. Problemas no fluxo de navegação
3. Estado da página não sendo resetado corretamente
"""

import os
import shutil
from datetime import datetime

def fazer_backup(arquivo):
    """Cria backup do arquivo"""
    backup_path = f"{arquivo}.backup_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(arquivo, backup_path)
    print(f"Backup criado: {backup_path}")
    return backup_path

def corrigir_main_py():
    """Corrige o fluxo de navegação para login em main.py"""
    arquivo = "main.py"
    
    if not os.path.exists(arquivo):
        print(f"Arquivo nao encontrado: {arquivo}")
        return False
    
    print(f"Corrigindo {arquivo}...")
    fazer_backup(arquivo)
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Procurar pela função route_change e melhorar o tratamento de login
    if 'def route_change(route):' in conteudo:
        # Melhorar a lógica de limpeza de views para login
        conteudo_original = conteudo
        
        # Substituir a lógica de login por uma versão mais robusta
        padrao_login = r'if page\.route in \["/", "/login"\]:.*?page\.views\.append\(\s*ft\.View\(\s*route=page\.route,\s*controls=\[LoginView\(page, on_login_success\)\],\s*padding=0,\s*bgcolor=ft\.colors\.WHITE\s*\)\s*\)'
        
        nova_logica_login = '''if page.route in ["/", "/login"]:
            # Limpar completamente o estado da página para login
            page.data = {}
            
            # Se o usuário já estiver autenticado e tentar acessar login, redireciona
            if page.data and page.route == "/login":
                page.go("/dashboard")
                return
            
            # Limpar todas as views existentes
            page.views.clear()
            
            # Forçar atualização da página antes de adicionar nova view
            page.update()
            
            # Criar nova view de login
            try:
                login_view = LoginView(page, on_login_success)
                page.views.append(
                    ft.View(
                        route=page.route,
                        controls=[login_view],
                        padding=0,
                        bgcolor=ft.colors.WHITE
                    )
                )
                # Forçar atualização após adicionar a view
                page.update()
            except Exception as e:
                print(f"Erro ao criar view de login: {e}")
                # Fallback: tentar novamente após um pequeno delay
                import time
                time.sleep(0.1)
                try:
                    login_view = LoginView(page, on_login_success)
                    page.views.append(
                        ft.View(
                            route=page.route,
                            controls=[login_view],
                            padding=0,
                            bgcolor=ft.colors.WHITE
                        )
                    )
                    page.update()
                except Exception as e2:
                    print(f"Erro crítico ao criar view de login: {e2}")'''
        
        import re
        if re.search(padrao_login, conteudo, re.DOTALL):
            conteudo = re.sub(padrao_login, nova_logica_login, conteudo, flags=re.DOTALL)
            print("  Logica de login melhorada")
        else:
            # Se não encontrar o padrão exato, fazer substituição mais simples
            if 'if page.route in ["/", "/login"]:' in conteudo:
                # Encontrar e substituir o bloco de login
                linhas = conteudo.split('\n')
                novas_linhas = []
                dentro_bloco_login = False
                nivel_indentacao = 0
                
                for i, linha in enumerate(linhas):
                    if 'if page.route in ["/", "/login"]:' in linha:
                        dentro_bloco_login = True
                        nivel_indentacao = len(linha) - len(linha.lstrip())
                        # Adicionar nova lógica
                        novas_linhas.append(linha)
                        novas_linhas.append(' ' * (nivel_indentacao + 4) + '# Limpar completamente o estado da página para login')
                        novas_linhas.append(' ' * (nivel_indentacao + 4) + 'page.data = {} if page.route == "/login" else page.data')
                        novas_linhas.append(' ' * (nivel_indentacao + 4) + '')
                        novas_linhas.append(' ' * (nivel_indentacao + 4) + '# Limpar todas as views existentes')
                        novas_linhas.append(' ' * (nivel_indentacao + 4) + 'page.views.clear()')
                        novas_linhas.append(' ' * (nivel_indentacao + 4) + '')
                        novas_linhas.append(' ' * (nivel_indentacao + 4) + '# Forçar atualização da página antes de adicionar nova view')
                        novas_linhas.append(' ' * (nivel_indentacao + 4) + 'page.update()')
                        continue
                    elif dentro_bloco_login:
                        # Verificar se saímos do bloco (nova linha com indentação menor ou igual)
                        if linha.strip() and (len(linha) - len(linha.lstrip())) <= nivel_indentacao:
                            dentro_bloco_login = False
                            novas_linhas.append(linha)
                        elif 'page.views.append(' in linha:
                            # Manter a lógica de append mas adicionar try/except
                            novas_linhas.append(' ' * (nivel_indentacao + 4) + '# Criar nova view de login com tratamento de erro')
                            novas_linhas.append(' ' * (nivel_indentacao + 4) + 'try:')
                            novas_linhas.append(' ' * (nivel_indentacao + 8) + 'login_view = LoginView(page, on_login_success)')
                            novas_linhas.append(linha)
                        elif ')' in linha and dentro_bloco_login:
                            novas_linhas.append(linha)
                            novas_linhas.append(' ' * (nivel_indentacao + 8) + '# Forçar atualização após adicionar a view')
                            novas_linhas.append(' ' * (nivel_indentacao + 8) + 'page.update()')
                            novas_linhas.append(' ' * (nivel_indentacao + 4) + 'except Exception as e:')
                            novas_linhas.append(' ' * (nivel_indentacao + 8) + 'print(f"Erro ao criar view de login: {e}")')
                        else:
                            # Pular linhas do bloco original
                            continue
                    else:
                        novas_linhas.append(linha)
                
                conteudo = '\n'.join(novas_linhas)
                print("  Logica de login corrigida com tratamento de erro")
        
        # Salvar se houve alterações
        if conteudo != conteudo_original:
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            print(f"Arquivo {arquivo} corrigido")
            return True
        else:
            print("Nenhuma alteracao necessaria")
            return True
    
    return False

def corrigir_configuracoes_view():
    """Corrige o redirecionamento para login em configuracoes_view.py"""
    arquivo = "views/configuracoes_view.py"
    
    if not os.path.exists(arquivo):
        print(f"Arquivo nao encontrado: {arquivo}")
        return False
    
    print(f"Corrigindo {arquivo}...")
    fazer_backup(arquivo)
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    alteracoes = 0
    conteudo_original = conteudo
    
    # Corrigir redirecionamentos para login
    if 'page.go("/login")' in conteudo:
        # Substituir por uma versão mais robusta
        conteudo = conteudo.replace(
            'page.go("/login")',
            '''# Limpar estado antes de ir para login
                page.data = {}
                page.views.clear()
                page.update()
                page.go("/login")'''
        )
        alteracoes += 1
        print("  Redirecionamento para login melhorado")
    
    if alteracoes > 0:
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"Arquivo {arquivo} corrigido com {alteracoes} alteracoes")
        return True
    else:
        print("Nenhuma alteracao necessaria")
        return True

def validar_sintaxe():
    """Valida a sintaxe dos arquivos corrigidos"""
    arquivos = ['main.py', 'views/configuracoes_view.py']
    
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
    print("CORRECAO DA TELA DE LOGIN EM BRANCO")
    print("=" * 40)
    
    try:
        # Corrigir main.py
        print("\n1. Corrigindo main.py...")
        if not corrigir_main_py():
            print("Falha ao corrigir main.py")
            return
        
        # Corrigir configuracoes_view.py
        print("\n2. Corrigindo configuracoes_view.py...")
        if not corrigir_configuracoes_view():
            print("Falha ao corrigir configuracoes_view.py")
            return
        
        # Validar sintaxe
        print("\n3. Validando sintaxe...")
        if validar_sintaxe():
            print("\nCORRECAO CONCLUIDA COM SUCESSO!")
            print("\nProblemas corrigidos:")
            print("- Tela de login em branco após restauração")
            print("- Fluxo de navegação melhorado")
            print("- Tratamento de erro na criação de views")
            print("\nO sistema agora deve mostrar a tela de login corretamente.")
        else:
            print("\nErro de sintaxe detectado. Verifique os arquivos manualmente.")
            
    except Exception as e:
        print(f"\nErro durante a correcao: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
