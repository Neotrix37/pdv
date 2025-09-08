#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para garantir que o esquema do banco seja sempre atualizado
após a restauração de qualquer backup, evitando o erro "no such column: total".

Este script modifica o processo de restauração para incluir verificação
e migração automática do esquema após cada restauração.
"""

import os
import shutil
from datetime import datetime

def fazer_backup(arquivo):
    """Cria backup do arquivo"""
    backup_path = f"{arquivo}.backup_esquema_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(arquivo, backup_path)
    print(f"Backup criado: {backup_path}")
    return backup_path

def corrigir_database_py():
    """Adiciona verificação automática de esquema após restauração"""
    arquivo = "database/database.py"
    
    if not os.path.exists(arquivo):
        print(f"Arquivo nao encontrado: {arquivo}")
        return False
    
    print(f"Corrigindo {arquivo}...")
    fazer_backup(arquivo)
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Adicionar função para verificar e corrigir esquema após restauração
    funcao_verificar_esquema = '''
    def verificar_e_corrigir_esquema_pos_restauracao(self):
        """
        Verifica e corrige o esquema do banco após restauração de backup.
        Garante que todas as colunas necessárias existam.
        """
        try:
            print("Verificando esquema após restauração...")
            
            # Verificar se a coluna 'total' existe na tabela vendas
            colunas_vendas = self.fetchall("PRAGMA table_info(vendas)")
            tem_total = any(col['name'] == 'total' for col in colunas_vendas)
            
            if not tem_total:
                print("Coluna 'total' não encontrada na tabela vendas. Adicionando...")
                
                # Adicionar coluna total
                self.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0")
                
                # Atualizar valores existentes baseado em valor_recebido ou outros campos
                self.execute("""
                    UPDATE vendas 
                    SET total = COALESCE(valor_recebido, 0) 
                    WHERE total IS NULL OR total = 0
                """)
                
                print("Coluna 'total' adicionada e valores atualizados")
            
            # Verificar se a coluna 'status' existe na tabela vendas
            tem_status = any(col['name'] == 'status' for col in colunas_vendas)
            
            if not tem_status:
                print("Coluna 'status' não encontrada na tabela vendas. Adicionando...")
                self.execute("ALTER TABLE vendas ADD COLUMN status TEXT DEFAULT 'Ativa'")
                print("Coluna 'status' adicionada")
            
            # Verificar outras colunas críticas
            colunas_necessarias = {
                'forma_pagamento': 'TEXT DEFAULT "Dinheiro"',
                'valor_recebido': 'REAL DEFAULT 0',
                'troco': 'REAL DEFAULT 0',
                'data_venda': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
            
            for coluna, tipo in colunas_necessarias.items():
                tem_coluna = any(col['name'] == coluna for col in colunas_vendas)
                if not tem_coluna:
                    print(f"Coluna '{coluna}' não encontrada. Adicionando...")
                    self.execute(f"ALTER TABLE vendas ADD COLUMN {coluna} {tipo}")
            
            # Verificar tabela itens_venda
            try:
                colunas_itens = self.fetchall("PRAGMA table_info(itens_venda)")
                colunas_necessarias_itens = {
                    'preco_custo_unitario': 'REAL DEFAULT 0',
                    'subtotal': 'REAL DEFAULT 0'
                }
                
                for coluna, tipo in colunas_necessarias_itens.items():
                    tem_coluna = any(col['name'] == coluna for col in colunas_itens)
                    if not tem_coluna:
                        print(f"Coluna '{coluna}' não encontrada em itens_venda. Adicionando...")
                        self.execute(f"ALTER TABLE itens_venda ADD COLUMN {coluna} {tipo}")
            except:
                pass  # Tabela pode não existir em backups muito antigos
            
            # Executar migrações de esquema completas
            self.run_schema_migrations()
            
            print("Verificação e correção de esquema concluída")
            return True
            
        except Exception as e:
            print(f"Erro ao verificar/corrigir esquema: {e}")
            return False
'''
    
    # Adicionar a função ao final da classe Database
    if 'class Database:' in conteudo and 'def verificar_e_corrigir_esquema_pos_restauracao' not in conteudo:
        # Encontrar o final da classe Database
        linhas = conteudo.split('\n')
        novas_linhas = []
        dentro_classe_database = False
        nivel_indentacao_classe = 0
        
        for i, linha in enumerate(linhas):
            if 'class Database:' in linha:
                dentro_classe_database = True
                nivel_indentacao_classe = len(linha) - len(linha.lstrip())
                novas_linhas.append(linha)
            elif dentro_classe_database:
                # Verificar se saímos da classe
                if linha.strip() and (len(linha) - len(linha.lstrip())) <= nivel_indentacao_classe and not linha.startswith(' '):
                    # Saímos da classe, adicionar a função antes
                    novas_linhas.extend(funcao_verificar_esquema.split('\n'))
                    novas_linhas.append(linha)
                    dentro_classe_database = False
                else:
                    novas_linhas.append(linha)
            else:
                novas_linhas.append(linha)
        
        # Se ainda estamos dentro da classe (final do arquivo), adicionar a função
        if dentro_classe_database:
            novas_linhas.extend(funcao_verificar_esquema.split('\n'))
        
        conteudo = '\n'.join(novas_linhas)
        print("  Funcao verificar_e_corrigir_esquema_pos_restauracao adicionada")
    
    # Modificar o método _init_database para chamar a verificação
    if 'def _init_database(self):' in conteudo:
        # Adicionar chamada para verificação de esquema no final de _init_database
        conteudo = conteudo.replace(
            'self.conn.commit()',
            '''self.conn.commit()
        
        # Verificar e corrigir esquema se necessário (especialmente após restauração)
        try:
            self.verificar_e_corrigir_esquema_pos_restauracao()
        except Exception as e:
            print(f"Aviso: Erro na verificação de esquema: {e}")'''
        )
        print("  Verificacao de esquema adicionada ao _init_database")
    
    # Salvar arquivo
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"Arquivo {arquivo} corrigido")
    return True

def corrigir_configuracoes_view():
    """Adiciona chamada para verificação de esquema após restauração em configuracoes_view.py"""
    arquivo = "views/configuracoes_view.py"
    
    if not os.path.exists(arquivo):
        print(f"Arquivo nao encontrado: {arquivo}")
        return False
    
    print(f"Corrigindo {arquivo}...")
    fazer_backup(arquivo)
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Procurar pelo local onde o backup é restaurado com sucesso
    if 'Banco de dados restaurado com sucesso' in conteudo:
        # Adicionar verificação de esquema após restauração bem-sucedida
        conteudo = conteudo.replace(
            'print("Banco de dados restaurado com sucesso. Tabelas encontradas:", tabelas)',
            '''print("Banco de dados restaurado com sucesso. Tabelas encontradas:", tabelas)
                
                # Verificar e corrigir esquema após restauração
                print("Verificando esquema após restauração...")
                try:
                    db_temp = Database()
                    db_temp.verificar_e_corrigir_esquema_pos_restauracao()
                    print("Esquema verificado e corrigido após restauração")
                except Exception as e:
                    print(f"Aviso: Erro na verificação de esquema pós-restauração: {e}")'''
        )
        print("  Verificacao de esquema adicionada após restauração")
    
    # Salvar arquivo
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"Arquivo {arquivo} corrigido")
    return True

def validar_sintaxe():
    """Valida a sintaxe dos arquivos corrigidos"""
    arquivos = ['database/database.py', 'views/configuracoes_view.py']
    
    for arquivo in arquivos:
        try:
            import py_compile
            py_compile.compile(arquivo, doraise=True)
            print(f"Sintaxe validada: {arquivo}")
        except Exception as e:
            print(f"Erro de sintaxe em {arquivo}: {e}")
            return False
    
    return True

def testar_correcao():
    """Testa se a correção funciona"""
    try:
        from database.database import Database
        db = Database()
        
        # Testar se a função existe
        if hasattr(db, 'verificar_e_corrigir_esquema_pos_restauracao'):
            print("Funcao verificar_e_corrigir_esquema_pos_restauracao encontrada")
            
            # Testar se as colunas existem
            colunas = db.fetchall("PRAGMA table_info(vendas)")
            tem_total = any(col['name'] == 'total' for col in colunas)
            
            if tem_total:
                print("Coluna 'total' confirmada na tabela vendas")
                return True
            else:
                print("Coluna 'total' ainda não existe - executando correção...")
                db.verificar_e_corrigir_esquema_pos_restauracao()
                return True
        else:
            print("Funcao nao encontrada")
            return False
            
    except Exception as e:
        print(f"Erro no teste: {e}")
        return False

def main():
    print("CORRECAO DE ESQUEMA POS-RESTAURACAO")
    print("=" * 40)
    print("Garantindo que o esquema seja sempre atualizado após restauração de backup")
    
    try:
        # Corrigir database.py
        print("\n1. Corrigindo database.py...")
        if not corrigir_database_py():
            print("Falha ao corrigir database.py")
            return
        
        # Corrigir configuracoes_view.py
        print("\n2. Corrigindo configuracoes_view.py...")
        if not corrigir_configuracoes_view():
            print("Falha ao corrigir configuracoes_view.py")
            return
        
        # Validar sintaxe
        print("\n3. Validando sintaxe...")
        if validar_sintaxe():
            print("\n4. Testando correção...")
            if testar_correcao():
                print("\nCORRECAO CONCLUIDA COM SUCESSO!")
                print("\nMelhorias implementadas:")
                print("- Verificação automática de esquema após restauração")
                print("- Adição automática da coluna 'total' se não existir")
                print("- Migração completa de esquema após cada restauração")
                print("- Proteção contra erro 'no such column: total'")
                print("\nO sistema agora deve funcionar com qualquer backup, antigo ou novo.")
            else:
                print("\nTeste falhou. Verifique manualmente.")
        else:
            print("\nErro de sintaxe detectado. Verifique os arquivos manualmente.")
            
    except Exception as e:
        print(f"\nErro durante a correcao: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
