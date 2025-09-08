#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para corrigir todos os problemas identificados no sistema PDV
Resolve problemas de encoding, estrutura de banco e inconsistências
"""

import sys
import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

# Configurar encoding para evitar problemas de caracteres
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database

class CorretorSistema:
    def __init__(self):
        self.db = None
        self.problemas_encontrados = []
        self.correcoes_aplicadas = []
        
    def conectar_banco(self):
        """Conecta ao banco de dados principal"""
        try:
            self.db = Database()
            print("✓ Conexão com banco de dados estabelecida")
            return True
        except Exception as e:
            print(f"✗ Erro ao conectar com banco: {e}")
            return False
    
    def verificar_estrutura_vendas(self):
        """Verifica se a tabela vendas tem todas as colunas necessárias"""
        print("\n=== Verificando Estrutura da Tabela Vendas ===")
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("PRAGMA table_info(vendas)")
            colunas = cursor.fetchall()
            colunas_nomes = [col[1] for col in colunas]
            
            # Colunas obrigatórias
            colunas_obrigatorias = [
                'id', 'usuario_id', 'total', 'forma_pagamento', 
                'valor_recebido', 'troco', 'data_venda'
            ]
            
            # Colunas opcionais que devem existir
            colunas_opcionais = [
                'status', 'motivo_alteracao', 'alterado_por', 
                'data_alteracao', 'origem'
            ]
            
            faltando = []
            for col in colunas_obrigatorias:
                if col not in colunas_nomes:
                    faltando.append(col)
                    self.problemas_encontrados.append(f"Coluna obrigatória '{col}' faltando na tabela vendas")
            
            if faltando:
                print(f"✗ Colunas obrigatórias faltando: {', '.join(faltando)}")
                return False
            else:
                print("✓ Todas as colunas obrigatórias estão presentes")
                
            # Verificar colunas opcionais
            for col in colunas_opcionais:
                if col not in colunas_nomes:
                    print(f"! Coluna opcional '{col}' não encontrada - será adicionada")
                    self.adicionar_coluna_vendas(col)
                    
            return True
            
        except Exception as e:
            print(f"✗ Erro ao verificar estrutura de vendas: {e}")
            self.problemas_encontrados.append(f"Erro na verificação de vendas: {e}")
            return False
    
    def adicionar_coluna_vendas(self, coluna):
        """Adiciona coluna faltante na tabela vendas"""
        try:
            cursor = self.db.conn.cursor()
            
            if coluna == 'status':
                cursor.execute("ALTER TABLE vendas ADD COLUMN status TEXT DEFAULT 'Ativa'")
            elif coluna == 'motivo_alteracao':
                cursor.execute("ALTER TABLE vendas ADD COLUMN motivo_alteracao TEXT")
            elif coluna == 'alterado_por':
                cursor.execute("ALTER TABLE vendas ADD COLUMN alterado_por INTEGER REFERENCES usuarios(id)")
            elif coluna == 'data_alteracao':
                cursor.execute("ALTER TABLE vendas ADD COLUMN data_alteracao TIMESTAMP")
            elif coluna == 'origem':
                cursor.execute("ALTER TABLE vendas ADD COLUMN origem TEXT DEFAULT 'pdv'")
                
            self.db.conn.commit()
            print(f"✓ Coluna '{coluna}' adicionada com sucesso")
            self.correcoes_aplicadas.append(f"Adicionada coluna '{coluna}' na tabela vendas")
            
        except Exception as e:
            print(f"✗ Erro ao adicionar coluna '{coluna}': {e}")
    
    def verificar_tabela_retiradas_caixa(self):
        """Verifica e cria a tabela retiradas_caixa se necessário"""
        print("\n=== Verificando Tabela retiradas_caixa ===")
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='retiradas_caixa'
            """)
            
            if not cursor.fetchone():
                print("! Tabela retiradas_caixa não existe - criando...")
                self.criar_tabela_retiradas_caixa()
            else:
                print("✓ Tabela retiradas_caixa já existe")
                
            return True
            
        except Exception as e:
            print(f"✗ Erro ao verificar tabela retiradas_caixa: {e}")
            return False
    
    def criar_tabela_retiradas_caixa(self):
        """Cria a tabela retiradas_caixa com estrutura completa"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute('''
                CREATE TABLE retiradas_caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    aprovador_id INTEGER,
                    valor REAL NOT NULL,
                    motivo TEXT NOT NULL,
                    observacao TEXT,
                    origem TEXT NOT NULL DEFAULT 'vendas',
                    status TEXT NOT NULL DEFAULT 'pendente',
                    data_retirada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_aprovacao TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (aprovador_id) REFERENCES usuarios(id)
                )
            ''')
            
            # Criar trigger para atualização automática
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS retiradas_caixa_updated_at 
                AFTER UPDATE ON retiradas_caixa
                BEGIN
                    UPDATE retiradas_caixa 
                    SET updated_at = datetime('now', 'localtime') 
                    WHERE id = NEW.id;
                END
            ''')
            
            self.db.conn.commit()
            print("✓ Tabela retiradas_caixa criada com sucesso")
            self.correcoes_aplicadas.append("Criada tabela retiradas_caixa")
            
        except Exception as e:
            print(f"✗ Erro ao criar tabela retiradas_caixa: {e}")
            self.problemas_encontrados.append(f"Erro ao criar retiradas_caixa: {e}")
    
    def verificar_tipos_dados_estoque(self):
        """Verifica se as colunas de estoque têm tipos corretos"""
        print("\n=== Verificando Tipos de Dados do Estoque ===")
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("PRAGMA table_info(produtos)")
            colunas = cursor.fetchall()
            
            for col in colunas:
                if col[1] in ['estoque', 'estoque_minimo', 'preco_custo', 'preco_venda']:
                    if col[2].upper() != 'REAL':
                        print(f"! Coluna '{col[1]}' tem tipo '{col[2]}' mas deveria ser REAL")
                        self.problemas_encontrados.append(f"Tipo incorreto na coluna {col[1]}: {col[2]}")
                    else:
                        print(f"✓ Coluna '{col[1]}': {col[2]} (correto)")
            
            # Verificar produtos com estoque NULL ou negativo
            cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque IS NULL")
            null_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque < 0")
            negative_count = cursor.fetchone()[0]
            
            if null_count > 0:
                print(f"! Encontrados {null_count} produtos com estoque NULL")
                self.corrigir_estoque_null()
                
            if negative_count > 0:
                print(f"! Encontrados {negative_count} produtos com estoque negativo")
                
            return True
            
        except Exception as e:
            print(f"✗ Erro ao verificar tipos de dados: {e}")
            return False
    
    def corrigir_estoque_null(self):
        """Corrige produtos com estoque NULL"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("UPDATE produtos SET estoque = 0 WHERE estoque IS NULL")
            cursor.execute("UPDATE produtos SET estoque_minimo = 0 WHERE estoque_minimo IS NULL")
            self.db.conn.commit()
            print("✓ Valores NULL no estoque corrigidos")
            self.correcoes_aplicadas.append("Corrigidos valores NULL no estoque")
        except Exception as e:
            print(f"✗ Erro ao corrigir estoque NULL: {e}")
    
    def verificar_localizacao_banco(self):
        """Verifica qual banco está sendo usado e sua localização"""
        print("\n=== Verificando Localização do Banco de Dados ===")
        try:
            banco_atual = str(self.db.db_path.absolute())
            print(f"Banco ativo: {banco_atual}")
            
            # Verificar se existe banco no AppData
            import platform
            sistema = platform.system().lower()
            if sistema == 'windows' and 'APPDATA' in os.environ:
                appdata_db = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
            else:
                appdata_db = Path(os.path.expanduser('~')) / '.sistemagestao' / 'database' / 'sistema.db'
            
            local_db = Path(os.path.dirname(os.path.dirname(__file__))) / 'database' / 'sistema.db'
            
            print(f"Banco AppData: {appdata_db} ({'existe' if appdata_db.exists() else 'não existe'})")
            print(f"Banco Local: {local_db} ({'existe' if local_db.exists() else 'não existe'})")
            
            if appdata_db.exists() and local_db.exists():
                appdata_size = appdata_db.stat().st_size
                local_size = local_db.stat().st_size
                appdata_time = appdata_db.stat().st_mtime
                local_time = local_db.stat().st_mtime
                
                print(f"Tamanho AppData: {appdata_size} bytes")
                print(f"Tamanho Local: {local_size} bytes")
                print(f"Modificação AppData: {datetime.fromtimestamp(appdata_time)}")
                print(f"Modificação Local: {datetime.fromtimestamp(local_time)}")
                
                if abs(appdata_size - local_size) > 1024:  # Diferença > 1KB
                    print("! Os bancos têm tamanhos muito diferentes - possível inconsistência")
                    self.problemas_encontrados.append("Bancos AppData e Local têm tamanhos diferentes")
            
            return True
            
        except Exception as e:
            print(f"✗ Erro ao verificar localização do banco: {e}")
            return False
    
    def criar_backup_seguranca(self):
        """Cria backup de segurança antes das correções"""
        print("\n=== Criando Backup de Segurança ===")
        try:
            banco_atual = str(self.db.db_path.absolute())
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{banco_atual}.backup_correcao_{timestamp}"
            
            shutil.copy2(banco_atual, backup_path)
            print(f"✓ Backup criado: {backup_path}")
            self.correcoes_aplicadas.append(f"Backup de segurança criado: {os.path.basename(backup_path)}")
            return True
            
        except Exception as e:
            print(f"✗ Erro ao criar backup: {e}")
            return False
    
    def gerar_relatorio(self):
        """Gera relatório final das correções aplicadas"""
        print("\n" + "="*60)
        print("RELATÓRIO FINAL DE CORREÇÕES")
        print("="*60)
        
        print(f"\nProblemas encontrados: {len(self.problemas_encontrados)}")
        for i, problema in enumerate(self.problemas_encontrados, 1):
            print(f"  {i}. {problema}")
        
        print(f"\nCorreções aplicadas: {len(self.correcoes_aplicadas)}")
        for i, correcao in enumerate(self.correcoes_aplicadas, 1):
            print(f"  {i}. {correcao}")
        
        if len(self.problemas_encontrados) == 0:
            print("\n✓ Sistema está consistente - nenhum problema crítico encontrado")
        else:
            print(f"\n! Ainda existem {len(self.problemas_encontrados)} problemas que precisam de atenção")
        
        print("\n" + "="*60)
    
    def executar_correcoes(self):
        """Executa todas as correções necessárias"""
        print("INICIANDO CORREÇÃO COMPLETA DO SISTEMA PDV")
        print("="*50)
        
        if not self.conectar_banco():
            return False
        
        # Criar backup antes de qualquer alteração
        if not self.criar_backup_seguranca():
            print("✗ Falha ao criar backup - abortando correções")
            return False
        
        # Executar verificações e correções
        self.verificar_localizacao_banco()
        self.verificar_estrutura_vendas()
        self.verificar_tabela_retiradas_caixa()
        self.verificar_tipos_dados_estoque()
        
        # Gerar relatório final
        self.gerar_relatorio()
        
        return True

def main():
    """Função principal"""
    corretor = CorretorSistema()
    
    try:
        sucesso = corretor.executar_correcoes()
        if sucesso:
            print("\n✓ Correções concluídas com sucesso!")
        else:
            print("\n✗ Algumas correções falharam - verifique o relatório")
            
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário")
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
