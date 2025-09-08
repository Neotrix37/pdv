#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analisar o conteúdo dos backups e mostrar quais têm dados reais
"""

import os
import sqlite3
from datetime import datetime
import sys

def analisar_backup(backup_path):
    """Analisa um backup específico e retorna informações sobre seu conteúdo"""
    try:
        # Conectar ao backup
        conn = sqlite3.connect(backup_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        info = {
            'arquivo': os.path.basename(backup_path),
            'tamanho_mb': round(os.path.getsize(backup_path) / (1024 * 1024), 2),
            'data_modificacao': datetime.fromtimestamp(os.path.getmtime(backup_path)).strftime('%Y-%m-%d %H:%M:%S'),
            'tem_dados': False,
            'detalhes': {}
        }
        
        # Verificar se as tabelas existem
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [row[0] for row in cursor.fetchall()]
        
        if 'vendas' in tabelas:
            # Contar vendas totais
            cursor.execute("SELECT COUNT(*) as total FROM vendas")
            total_vendas = cursor.fetchone()['total']
            info['detalhes']['total_vendas'] = total_vendas
            
            if total_vendas > 0:
                info['tem_dados'] = True
                
                # Verificar se tem coluna 'total'
                cursor.execute("PRAGMA table_info(vendas)")
                colunas = [col[1] for col in cursor.fetchall()]
                info['detalhes']['tem_coluna_total'] = 'total' in colunas
                
                # Soma total das vendas (se coluna existir)
                if 'total' in colunas:
                    cursor.execute("SELECT COALESCE(SUM(total), 0) as soma FROM vendas WHERE status != 'Anulada' OR status IS NULL")
                    soma_vendas = cursor.fetchone()['soma']
                    info['detalhes']['valor_total_vendas'] = soma_vendas
                else:
                    # Tentar usar valor_recebido se total não existir
                    if 'valor_recebido' in colunas:
                        cursor.execute("SELECT COALESCE(SUM(valor_recebido), 0) as soma FROM vendas")
                        soma_vendas = cursor.fetchone()['soma']
                        info['detalhes']['valor_total_vendas'] = soma_vendas
                    else:
                        info['detalhes']['valor_total_vendas'] = 'N/A'
                
                # Período das vendas
                cursor.execute("SELECT MIN(data_venda) as primeira, MAX(data_venda) as ultima FROM vendas")
                periodo = cursor.fetchone()
                if periodo['primeira']:
                    info['detalhes']['periodo_vendas'] = f"{periodo['primeira']} até {periodo['ultima']}"
        
        if 'produtos' in tabelas:
            # Contar produtos
            cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE ativo = 1 OR ativo IS NULL")
            total_produtos = cursor.fetchone()['total']
            info['detalhes']['total_produtos'] = total_produtos
            
            if total_produtos > 0:
                info['tem_dados'] = True
                
                # Valor em estoque
                cursor.execute("SELECT COALESCE(SUM(preco_custo * estoque), 0) as valor_estoque FROM produtos WHERE ativo = 1 OR ativo IS NULL")
                valor_estoque = cursor.fetchone()['valor_estoque']
                info['detalhes']['valor_estoque'] = valor_estoque
        
        if 'usuarios' in tabelas:
            cursor.execute("SELECT COUNT(*) as total FROM usuarios")
            total_usuarios = cursor.fetchone()['total']
            info['detalhes']['total_usuarios'] = total_usuarios
        
        conn.close()
        return info
        
    except Exception as e:
        return {
            'arquivo': os.path.basename(backup_path),
            'erro': str(e),
            'tem_dados': False
        }

def main():
    print("ANÁLISE DE BACKUPS - VERIFICAÇÃO DE CONTEÚDO")
    print("=" * 60)
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        print(f"Diretório de backups não encontrado: {backup_dir}")
        return
    
    # Listar todos os arquivos .db no diretório de backups
    backups = []
    for arquivo in os.listdir(backup_dir):
        if arquivo.endswith('.db'):
            backup_path = os.path.join(backup_dir, arquivo)
            backups.append(backup_path)
    
    if not backups:
        print("Nenhum backup encontrado no diretório backups/")
        return
    
    print(f"Encontrados {len(backups)} backups para análise...\n")
    
    # Analisar cada backup
    backups_com_dados = []
    backups_vazios = []
    
    for backup_path in sorted(backups, key=os.path.getmtime, reverse=True):
        print(f"Analisando: {os.path.basename(backup_path)}...")
        info = analisar_backup(backup_path)
        
        if 'erro' in info:
            print(f"  ❌ ERRO: {info['erro']}")
            continue
        
        print(f"  Arquivo: {info['arquivo']}")
        print(f"  Tamanho: {info['tamanho_mb']} MB")
        print(f"  Modificado: {info['data_modificacao']}")
        
        if info['tem_dados']:
            backups_com_dados.append(info)
            print(f"  OK - TEM DADOS:")
            
            if 'total_vendas' in info['detalhes']:
                print(f"     - Vendas: {info['detalhes']['total_vendas']} registros")
                if 'valor_total_vendas' in info['detalhes'] and info['detalhes']['valor_total_vendas'] != 'N/A':
                    print(f"     - Valor total: MT {info['detalhes']['valor_total_vendas']:.2f}")
                if 'periodo_vendas' in info['detalhes']:
                    print(f"     - Periodo: {info['detalhes']['periodo_vendas']}")
                if 'tem_coluna_total' in info['detalhes']:
                    status_coluna = "SIM" if info['detalhes']['tem_coluna_total'] else "NAO"
                    print(f"     - Coluna 'total': {status_coluna}")
            
            if 'total_produtos' in info['detalhes']:
                print(f"     - Produtos: {info['detalhes']['total_produtos']} ativos")
                if 'valor_estoque' in info['detalhes']:
                    print(f"     - Estoque: MT {info['detalhes']['valor_estoque']:.2f}")
            
            if 'total_usuarios' in info['detalhes']:
                print(f"     - Usuarios: {info['detalhes']['total_usuarios']}")
        else:
            backups_vazios.append(info)
            print(f"  VAZIO - SEM DADOS (backup vazio ou de teste)")
        
        print()
    
    # Resumo final
    print("=" * 60)
    print("RESUMO DA ANALISE:")
    print(f"Total de backups: {len(backups)}")
    print(f"Com dados: {len(backups_com_dados)}")
    print(f"Vazios/teste: {len(backups_vazios)}")
    
    if backups_com_dados:
        print(f"\nBACKUPS RECOMENDADOS (com dados reais):")
        for info in backups_com_dados[:5]:  # Mostrar os 5 primeiros
            valor_vendas = info['detalhes'].get('valor_total_vendas', 0)
            if valor_vendas and valor_vendas != 'N/A' and valor_vendas > 0:
                print(f"  - {info['arquivo']} - MT {valor_vendas:.2f} em vendas")
            else:
                print(f"  - {info['arquivo']} - {info['detalhes'].get('total_vendas', 0)} vendas")
    
    print(f"\nEXPLICACAO:")
    print(f"Os valores MT 0.00 no dashboard sao normais quando:")
    print(f"  - O backup e de um periodo anterior (vendas de outros meses)")
    print(f"  - O backup e de teste/desenvolvimento")
    print(f"  - O backup foi criado apos reset do sistema")
    print(f"  - As vendas sao de datas diferentes da atual")

if __name__ == "__main__":
    main()
