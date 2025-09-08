#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador de Integridade do Sistema PDV
Executa verificações preventivas para evitar problemas intermitentes
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

# Configurar encoding
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database

class VerificadorIntegridade:
    def __init__(self):
        self.db = None
        self.alertas = []
        self.status = "OK"
        
    def conectar(self):
        """Conecta ao banco de dados"""
        try:
            self.db = Database()
            return True
        except Exception as e:
            self.alertas.append(f"CRÍTICO: Falha na conexão com banco: {e}")
            self.status = "ERRO"
            return False
    
    def verificar_estrutura_critica(self):
        """Verifica estruturas críticas do banco"""
        print("Verificando estruturas críticas...")
        
        try:
            cursor = self.db.conn.cursor()
            
            # Verificar tabelas essenciais
            tabelas_essenciais = [
                'usuarios', 'produtos', 'vendas', 'itens_venda', 
                'retiradas_caixa', 'printer_config'
            ]
            
            for tabela in tabelas_essenciais:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabela}'")
                if not cursor.fetchone():
                    self.alertas.append(f"CRÍTICO: Tabela '{tabela}' não encontrada")
                    self.status = "ERRO"
            
            # Verificar coluna 'total' na tabela vendas
            cursor.execute("PRAGMA table_info(vendas)")
            colunas_vendas = [col[1] for col in cursor.fetchall()]
            if 'total' not in colunas_vendas:
                self.alertas.append("CRÍTICO: Coluna 'total' não encontrada na tabela vendas")
                self.status = "ERRO"
            
            print("✓ Estruturas críticas verificadas")
            
        except Exception as e:
            self.alertas.append(f"ERRO: Falha na verificação de estrutura: {e}")
            self.status = "ERRO"
    
    def verificar_dependencias_relatorios(self):
        """Verifica se dependências para relatórios estão disponíveis"""
        print("Verificando dependências de relatórios...")
        
        dependencias = {
            'pandas': 'Geração de relatórios Excel',
            'reportlab': 'Geração de relatórios PDF',
            'plotly': 'Gráficos nos relatórios',
            'flet': 'Interface gráfica'
        }
        
        for dep, desc in dependencias.items():
            try:
                __import__(dep)
                print(f"✓ {dep}: OK")
            except ImportError:
                self.alertas.append(f"AVISO: Dependência '{dep}' não encontrada - {desc}")
                if self.status == "OK":
                    self.status = "AVISO"
    
    def verificar_configuracao_impressora(self):
        """Verifica configuração da impressora"""
        print("Verificando configuração da impressora...")
        
        try:
            config = self.db.get_printer_config()
            if not config:
                self.alertas.append("AVISO: Nenhuma configuração de impressora encontrada")
                if self.status == "OK":
                    self.status = "AVISO"
            else:
                print("✓ Configuração de impressora encontrada")
                
        except Exception as e:
            self.alertas.append(f"ERRO: Falha ao verificar impressora: {e}")
            if self.status != "ERRO":
                self.status = "ERRO"
    
    def verificar_backups_recentes(self):
        """Verifica se existem backups recentes"""
        print("Verificando backups recentes...")
        
        try:
            # Verificar pasta de backups
            backup_dir = Path("backups")
            if not backup_dir.exists():
                self.alertas.append("AVISO: Pasta de backups não encontrada")
                if self.status == "OK":
                    self.status = "AVISO"
                return
            
            # Verificar backups dos últimos 7 dias
            agora = datetime.now()
            backups_recentes = []
            
            for arquivo in backup_dir.glob("*.db"):
                try:
                    mod_time = datetime.fromtimestamp(arquivo.stat().st_mtime)
                    if agora - mod_time <= timedelta(days=7):
                        backups_recentes.append(arquivo)
                except:
                    continue
            
            if len(backups_recentes) == 0:
                self.alertas.append("AVISO: Nenhum backup encontrado nos últimos 7 dias")
                if self.status == "OK":
                    self.status = "AVISO"
            else:
                print(f"✓ {len(backups_recentes)} backups encontrados nos últimos 7 dias")
                
        except Exception as e:
            self.alertas.append(f"ERRO: Falha ao verificar backups: {e}")
    
    def verificar_dados_vendas_hoje(self):
        """Verifica se há dados de vendas inconsistentes hoje"""
        print("Verificando dados de vendas de hoje...")
        
        try:
            cursor = self.db.conn.cursor()
            
            # Verificar vendas sem itens
            cursor.execute("""
                SELECT COUNT(*) FROM vendas v
                LEFT JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE DATE(v.data_venda) = DATE('now') 
                AND iv.id IS NULL
                AND (v.status IS NULL OR v.status != 'Anulada')
            """)
            vendas_sem_itens = cursor.fetchone()[0]
            
            if vendas_sem_itens > 0:
                self.alertas.append(f"AVISO: {vendas_sem_itens} vendas hoje sem itens associados")
                if self.status == "OK":
                    self.status = "AVISO"
            
            # Verificar vendas com total zero
            cursor.execute("""
                SELECT COUNT(*) FROM vendas 
                WHERE DATE(data_venda) = DATE('now') 
                AND total = 0
                AND (status IS NULL OR status != 'Anulada')
            """)
            vendas_zero = cursor.fetchone()[0]
            
            if vendas_zero > 0:
                self.alertas.append(f"AVISO: {vendas_zero} vendas hoje com total zero")
                if self.status == "OK":
                    self.status = "AVISO"
            
            print("✓ Dados de vendas verificados")
            
        except Exception as e:
            self.alertas.append(f"ERRO: Falha ao verificar vendas: {e}")
    
    def verificar_estoque_critico(self):
        """Verifica produtos com estoque crítico"""
        print("Verificando estoque crítico...")
        
        try:
            cursor = self.db.conn.cursor()
            
            # Produtos com estoque abaixo do mínimo
            cursor.execute("""
                SELECT COUNT(*) FROM produtos 
                WHERE ativo = 1 
                AND estoque < estoque_minimo 
                AND estoque_minimo > 0
            """)
            estoque_baixo = cursor.fetchone()[0]
            
            if estoque_baixo > 0:
                self.alertas.append(f"AVISO: {estoque_baixo} produtos com estoque abaixo do mínimo")
                if self.status == "OK":
                    self.status = "AVISO"
            
            # Produtos com estoque negativo
            cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque < 0")
            estoque_negativo = cursor.fetchone()[0]
            
            if estoque_negativo > 0:
                self.alertas.append(f"CRÍTICO: {estoque_negativo} produtos com estoque negativo")
                self.status = "ERRO"
            
            print("✓ Estoque verificado")
            
        except Exception as e:
            self.alertas.append(f"ERRO: Falha ao verificar estoque: {e}")
    
    def gerar_relatorio_status(self):
        """Gera relatório de status do sistema"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print("\n" + "="*60)
        print(f"RELATÓRIO DE INTEGRIDADE DO SISTEMA - {timestamp}")
        print("="*60)
        
        # Status geral
        if self.status == "OK":
            print("🟢 STATUS GERAL: SISTEMA SAUDÁVEL")
        elif self.status == "AVISO":
            print("🟡 STATUS GERAL: ATENÇÃO NECESSÁRIA")
        else:
            print("🔴 STATUS GERAL: PROBLEMAS CRÍTICOS")
        
        # Alertas
        if self.alertas:
            print(f"\nALERTAS ENCONTRADOS ({len(self.alertas)}):")
            for i, alerta in enumerate(self.alertas, 1):
                print(f"  {i}. {alerta}")
        else:
            print("\n✓ Nenhum alerta encontrado")
        
        print("\n" + "="*60)
        
        # Salvar relatório em arquivo
        try:
            relatorio_data = {
                'timestamp': timestamp,
                'status': self.status,
                'alertas': self.alertas
            }
            
            with open('ultimo_relatorio_integridade.json', 'w', encoding='utf-8') as f:
                json.dump(relatorio_data, f, ensure_ascii=False, indent=2)
                
            print("Relatório salvo em: ultimo_relatorio_integridade.json")
            
        except Exception as e:
            print(f"Erro ao salvar relatório: {e}")
    
    def executar_verificacao_completa(self):
        """Executa verificação completa do sistema"""
        print("INICIANDO VERIFICAÇÃO DE INTEGRIDADE DO SISTEMA")
        print("="*50)
        
        if not self.conectar():
            self.gerar_relatorio_status()
            return False
        
        # Executar todas as verificações
        self.verificar_estrutura_critica()
        self.verificar_dependencias_relatorios()
        self.verificar_configuracao_impressora()
        self.verificar_backups_recentes()
        self.verificar_dados_vendas_hoje()
        self.verificar_estoque_critico()
        
        # Gerar relatório final
        self.gerar_relatorio_status()
        
        return self.status != "ERRO"

def main():
    """Função principal"""
    verificador = VerificadorIntegridade()
    
    try:
        sucesso = verificador.executar_verificacao_completa()
        
        if sucesso:
            print("\n✓ Verificação concluída - sistema operacional")
            return 0
        else:
            print("\n✗ Problemas críticos encontrados - ação necessária")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nVerificação cancelada pelo usuário")
        return 2
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
