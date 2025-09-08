#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from pathlib import Path
import platform

def analisar_banco_ativo():
    """Analisa o banco de dados atualmente ativo no sistema"""
    print("VERIFICAÇÃO DO BANCO DE DADOS ATIVO")
    print("=" * 60)
    
    # Determinar localização do banco ativo (mesmo lógica do Database.__init__)
    raiz_projeto_db_dir = Path(os.path.dirname(__file__)) / 'database'
    sistema = platform.system().lower()
    
    if sistema == 'windows' and 'APPDATA' in os.environ:
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
    else:
        app_data_db_dir = Path(os.path.expanduser('~')) / '.sistemagestao' / 'database'

    # Caminhos possíveis
    antigo_db = raiz_projeto_db_dir / 'sistema.db'
    appdata_db = app_data_db_dir / 'sistema.db'
    
    # Determinar qual banco está sendo usado
    banco_ativo = None
    if appdata_db.exists():
        banco_ativo = appdata_db
        print(f"[OK] Banco ativo encontrado: {banco_ativo}")
    elif antigo_db.exists():
        banco_ativo = antigo_db
        print(f"[OK] Banco ativo encontrado: {banco_ativo}")
    else:
        print("[ERRO] Nenhum banco de dados ativo encontrado!")
        return
    
    # Analisar conteúdo do banco ativo
    try:
        conn = sqlite3.connect(str(banco_ativo))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Informações básicas do arquivo
        stat = os.stat(banco_ativo)
        tamanho_mb = stat.st_size / (1024 * 1024)
        print(f"[INFO] Tamanho: {tamanho_mb:.2f} MB")
        print(f"[INFO] Modificado: {os.path.getmtime(banco_ativo)}")
        
        # Verificar vendas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_vendas,
                COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) as valor_total,
                MIN(data_venda) as primeira_venda,
                MAX(data_venda) as ultima_venda
            FROM vendas
        """)
        vendas = cursor.fetchone()
        
        if vendas and vendas['total_vendas'] > 0:
            print(f"[VENDAS] Vendas: {vendas['total_vendas']} registros")
            print(f"[VENDAS] Valor total: MT {vendas['valor_total']:.2f}")
            print(f"[VENDAS] Período: {vendas['primeira_venda']} até {vendas['ultima_venda']}")
        else:
            print("[AVISO] BANCO VAZIO - Sem vendas registradas")
        
        # Verificar produtos
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE ativo = 1")
        produtos = cursor.fetchone()
        print(f"[PRODUTOS] Produtos ativos: {produtos['total']}")
        
        # Verificar estoque
        cursor.execute("SELECT COALESCE(SUM(estoque * preco_custo), 0) as valor_estoque FROM produtos WHERE ativo = 1")
        estoque = cursor.fetchone()
        print(f"[ESTOQUE] Valor em estoque: MT {estoque['valor_estoque']:.2f}")
        
        # Verificar usuários
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE ativo = 1")
        usuarios = cursor.fetchone()
        print(f"[USUARIOS] Usuários ativos: {usuarios['total']}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        
        # Comparar com meu.db
        backup_meu_db = Path(os.path.dirname(__file__)) / 'backups' / 'meu.db'
        if backup_meu_db.exists():
            print("COMPARAÇÃO COM meu.db:")
            print("-" * 30)
            
            conn_backup = sqlite3.connect(str(backup_meu_db))
            conn_backup.row_factory = sqlite3.Row
            cursor_backup = conn_backup.cursor()
            
            cursor_backup.execute("""
                SELECT 
                    COUNT(*) as total_vendas,
                    COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) as valor_total
                FROM vendas
            """)
            vendas_backup = cursor_backup.fetchone()
            
            print(f"meu.db - Vendas: {vendas_backup['total_vendas']} registros")
            print(f"meu.db - Valor: MT {vendas_backup['valor_total']:.2f}")
            
            if vendas and vendas_backup:
                if vendas['valor_total'] != vendas_backup['valor_total']:
                    print("[ALERTA] DIFERENÇA DETECTADA!")
                    print(f"   Banco ativo: MT {vendas['valor_total']:.2f}")
                    print(f"   meu.db: MT {vendas_backup['valor_total']:.2f}")
                    print("   -> Recomenda-se restaurar o meu.db")
                else:
                    print("[OK] Bancos são idênticos em valor")
            
            conn_backup.close()
        
    except Exception as e:
        print(f"[ERRO] Erro ao analisar banco: {e}")

if __name__ == "__main__":
    analisar_banco_ativo()
