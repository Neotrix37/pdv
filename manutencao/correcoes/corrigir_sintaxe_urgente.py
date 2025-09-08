#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correção urgente dos erros de sintaxe introduzidos pelo script anterior
"""

import sys
import os
import re

# Configurar encoding
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def corrigir_lambdas_quebrados():
    """Corrige os lambdas que foram quebrados pelo script anterior"""
    arquivo = "views/configuracoes_view.py"
    
    print(f"🔧 Corrigindo lambdas quebrados em {arquivo}...")
    
    try:
        # Ler arquivo
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Padrão para encontrar lambdas quebrados
        # Procura por: lambda _: # comentário\n if self.page...
        padrao_lambda_quebrado = r'(lambda _:)\s*#[^\n]*\n\s*if self\.page and hasattr\(self\.page, "([^"]+)"\):\s*\n\s*self\.page\.([^(]+)\(([^)]*)\)'
        
        def corrigir_lambda(match):
            lambda_part = match.group(1)  # "lambda _:"
            metodo = match.group(2)       # "go" ou "show_snack_bar" etc
            funcao = match.group(3)       # "go" ou "show_snack_bar" etc  
            parametros = match.group(4)   # parâmetros da função
            
            # Construir lambda corrigido
            if parametros.strip():
                return f"{lambda_part} self.page.{funcao}({parametros}) if self.page and hasattr(self.page, \"{metodo}\") else None"
            else:
                return f"{lambda_part} self.page.{funcao}() if self.page and hasattr(self.page, \"{metodo}\") else None"
        
        # Aplicar correção
        conteudo_corrigido = re.sub(padrao_lambda_quebrado, corrigir_lambda, conteudo, flags=re.MULTILINE)
        
        # Correção específica para casos mais complexos
        # Padrão: on_click=lambda _: # comentário\n if self.page...
        padrao_especifico = r'(on_click=lambda _:)\s*#[^\n]*\n\s*if self\.page and hasattr\(self\.page, "[^"]+"\):\s*\n\s*self\.page\.go\("([^"]+)"\)'
        
        def corrigir_especifico(match):
            inicio = match.group(1)
            rota = match.group(2)
            return f'{inicio} self.page.go("/{rota}") if self.page and hasattr(self.page, "go") else None'
        
        conteudo_corrigido = re.sub(padrao_especifico, corrigir_especifico, conteudo_corrigido, flags=re.MULTILINE)
        
        # Salvar arquivo corrigido
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo_corrigido)
        
        print("✓ Lambdas corrigidos")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir lambdas: {e}")
        return False

def restaurar_backup_se_necessario():
    """Restaura o backup se as correções falharem"""
    arquivo_backup = "views/configuracoes_view.py.backup"
    arquivo_original = "views/configuracoes_view.py"
    
    if os.path.exists(arquivo_backup):
        print("🔄 Restaurando backup original...")
        try:
            with open(arquivo_backup, 'r', encoding='utf-8') as f:
                conteudo_backup = f.read()
            
            with open(arquivo_original, 'w', encoding='utf-8') as f:
                f.write(conteudo_backup)
            
            print("✓ Backup restaurado")
            return True
        except Exception as e:
            print(f"❌ Erro ao restaurar backup: {e}")
            return False
    else:
        print("❌ Backup não encontrado")
        return False

def aplicar_correcoes_manuais():
    """Aplica correções manuais específicas conhecidas"""
    arquivo = "views/configuracoes_view.py"
    
    print("🔧 Aplicando correções manuais...")
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Correções específicas conhecidas
        correcoes = [
            # Correção 1: lambda para voltar ao dashboard
            (
                r'on_click=lambda _:\s*#[^\n]*\n\s*if self\.page and hasattr\(self\.page, "go"\):\s*\n\s*self\.page\.go\("/dashboard"\)',
                'on_click=lambda _: self.page.go("/dashboard") if self.page and hasattr(self.page, "go") else None'
            ),
            # Correção 2: lambda para ir para printer
            (
                r'on_click=lambda _:\s*#[^\n]*\n\s*if self\.page and hasattr\(self\.page, "go"\):\s*\n\s*self\.page\.go\("/printer"\)',
                'on_click=lambda _: self.page.go("/printer") if self.page and hasattr(self.page, "go") else None'
            ),
            # Correção 3: qualquer outro lambda quebrado
            (
                r'on_click=lambda _:\s*#[^\n]*\n\s*if self\.page and hasattr\(self\.page, "([^"]+)"\):\s*\n\s*self\.page\.([^(]+)\(([^)]*)\)',
                r'on_click=lambda _: self.page.\2(\3) if self.page and hasattr(self.page, "\1") else None'
            )
        ]
        
        for padrao, substituicao in correcoes:
            conteudo = re.sub(padrao, substituicao, conteudo, flags=re.MULTILINE)
        
        # Salvar
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print("✓ Correções manuais aplicadas")
        return True
        
    except Exception as e:
        print(f"❌ Erro nas correções manuais: {e}")
        return False

def testar_sintaxe():
    """Testa se o arquivo tem sintaxe válida"""
    print("🧪 Testando sintaxe...")
    
    try:
        import py_compile
        py_compile.compile("views/configuracoes_view.py", doraise=True)
        print("✅ Sintaxe válida!")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Erro de sintaxe: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        return False

def main():
    """Função principal"""
    print("CORREÇÃO URGENTE DE SINTAXE")
    print("="*30)
    
    # Tentar correção automática primeiro
    if corrigir_lambdas_quebrados():
        if testar_sintaxe():
            print("✅ Correção automática bem-sucedida!")
            return True
    
    # Se falhou, tentar correções manuais
    print("⚠️  Correção automática falhou, tentando correções manuais...")
    if aplicar_correcoes_manuais():
        if testar_sintaxe():
            print("✅ Correções manuais bem-sucedidas!")
            return True
    
    # Se tudo falhou, restaurar backup
    print("❌ Todas as correções falharam, restaurando backup...")
    if restaurar_backup_se_necessario():
        if testar_sintaxe():
            print("✅ Backup restaurado com sucesso!")
            print("⚠️  ATENÇÃO: Proteções de interface foram removidas")
            print("   Você precisará aplicar as correções manualmente")
            return True
    
    print("❌ Falha completa - arquivo pode estar corrompido")
    return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)
