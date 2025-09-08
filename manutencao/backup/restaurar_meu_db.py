#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import shutil
import time
from pathlib import Path
from datetime import datetime
import platform

def restaurar_meu_db_manualmente():
    """Restaura manualmente o backup meu.db para o banco ativo do sistema"""
    print("RESTAURAÇÃO MANUAL DO MEU.DB")
    print("=" * 60)
    
    # Determinar caminhos (mesma lógica do Database.__init__)
    raiz_projeto_db_dir = Path(os.path.dirname(__file__)) / 'database'
    sistema = platform.system().lower()
    
    if sistema == 'windows' and 'APPDATA' in os.environ:
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
    else:
        app_data_db_dir = Path(os.path.expanduser('~')) / '.sistemagestao' / 'database'

    # Caminhos importantes
    antigo_db = raiz_projeto_db_dir / 'sistema.db'
    appdata_db = app_data_db_dir / 'sistema.db'
    backup_meu_db = Path(os.path.dirname(__file__)) / 'backups' / 'meu.db'
    
    # Determinar qual é o banco ativo
    banco_ativo = None
    if appdata_db.exists():
        banco_ativo = appdata_db
        print(f"[INFO] Banco ativo identificado: {banco_ativo}")
    elif antigo_db.exists():
        banco_ativo = antigo_db
        print(f"[INFO] Banco ativo identificado: {banco_ativo}")
    else:
        # Se não existe, usar o APPDATA como padrão
        banco_ativo = appdata_db
        app_data_db_dir.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Criando novo banco em: {banco_ativo}")
    
    # Verificar se meu.db existe
    if not backup_meu_db.exists():
        print(f"[ERRO] Arquivo meu.db não encontrado em: {backup_meu_db}")
        return False
    
    # Analisar meu.db antes da restauração
    print("\n[ANÁLISE] Verificando conteúdo do meu.db...")
    try:
        conn_backup = sqlite3.connect(str(backup_meu_db))
        conn_backup.row_factory = sqlite3.Row
        cursor_backup = conn_backup.cursor()
        
        # Verificar vendas no backup
        cursor_backup.execute("""
            SELECT 
                COUNT(*) as total_vendas,
                COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) as valor_total,
                MIN(data_venda) as primeira_venda,
                MAX(data_venda) as ultima_venda
            FROM vendas
        """)
        vendas_backup = cursor_backup.fetchone()
        
        if vendas_backup and vendas_backup['total_vendas'] > 0:
            print(f"[BACKUP] Vendas: {vendas_backup['total_vendas']} registros")
            print(f"[BACKUP] Valor total: MT {vendas_backup['valor_total']:.2f}")
            print(f"[BACKUP] Período: {vendas_backup['primeira_venda']} até {vendas_backup['ultima_venda']}")
        else:
            print("[AVISO] meu.db parece estar vazio!")
            conn_backup.close()
            return False
        
        conn_backup.close()
        
    except Exception as e:
        print(f"[ERRO] Não foi possível analisar meu.db: {e}")
        return False
    
    # Fazer backup do banco atual antes de restaurar
    print("\n[BACKUP] Criando backup de segurança do banco atual...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_atual = Path(os.path.dirname(__file__)) / 'backups' / f'pre_manual_restore_{timestamp}.db'
    
    try:
        if banco_ativo.exists():
            shutil.copy2(str(banco_ativo), str(backup_atual))
            print(f"[BACKUP] Backup criado: {backup_atual}")
        else:
            print("[INFO] Nenhum banco atual para fazer backup")
    except Exception as e:
        print(f"[AVISO] Erro ao criar backup: {e}")
    
    # Executar a restauração
    print("\n[RESTAURAÇÃO] Iniciando processo de restauração...")
    
    try:
        # 1. Remover banco atual se existir
        if banco_ativo.exists():
            print("[RESTAURAÇÃO] Removendo banco atual...")
            os.remove(str(banco_ativo))
            time.sleep(1)  # Aguardar liberação do arquivo
        
        # 2. Copiar meu.db para a localização ativa
        print(f"[RESTAURAÇÃO] Copiando meu.db para {banco_ativo}...")
        shutil.copy2(str(backup_meu_db), str(banco_ativo))
        
        # 3. Verificar se a cópia foi bem-sucedida
        if not banco_ativo.exists():
            raise Exception("Falha ao copiar o arquivo")
        
        # 4. Verificar integridade do banco restaurado
        print("[VERIFICAÇÃO] Testando integridade do banco restaurado...")
        conn_teste = sqlite3.connect(str(banco_ativo))
        conn_teste.row_factory = sqlite3.Row
        cursor_teste = conn_teste.cursor()
        
        # Verificar se as tabelas existem
        cursor_teste.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor_teste.fetchall()
        
        if not tabelas:
            raise Exception("Banco restaurado não contém tabelas")
        
        print(f"[VERIFICAÇÃO] Tabelas encontradas: {len(tabelas)}")
        
        # Verificar vendas no banco restaurado
        cursor_teste.execute("""
            SELECT 
                COUNT(*) as total_vendas,
                COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) as valor_total
            FROM vendas
        """)
        vendas_restauradas = cursor_teste.fetchone()
        
        if vendas_restauradas:
            print(f"[SUCESSO] Vendas restauradas: {vendas_restauradas['total_vendas']} registros")
            print(f"[SUCESSO] Valor total: MT {vendas_restauradas['valor_total']:.2f}")
            
            # Comparar com o backup original
            if (vendas_restauradas['total_vendas'] == vendas_backup['total_vendas'] and 
                abs(vendas_restauradas['valor_total'] - vendas_backup['valor_total']) < 0.01):
                print("[SUCESSO] Dados restaurados corretamente!")
            else:
                print("[AVISO] Dados restaurados podem estar inconsistentes")
        
        conn_teste.close()
        
        print("\n" + "=" * 60)
        print("[CONCLUÍDO] Restauração manual executada com sucesso!")
        print("Reinicie o sistema PDV para carregar os dados restaurados.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"[ERRO] Falha na restauração: {e}")
        
        # Tentar restaurar o backup de segurança
        if backup_atual.exists():
            print("[RECUPERAÇÃO] Tentando restaurar backup de segurança...")
            try:
                if banco_ativo.exists():
                    os.remove(str(banco_ativo))
                shutil.copy2(str(backup_atual), str(banco_ativo))
                print("[RECUPERAÇÃO] Backup de segurança restaurado")
            except Exception as recovery_error:
                print(f"[ERRO] Falha na recuperação: {recovery_error}")
        
        return False

if __name__ == "__main__":
    sucesso = restaurar_meu_db_manualmente()
    if sucesso:
        print("\n[PRÓXIMO PASSO] Reinicie o sistema PDV para ver os dados restaurados.")
    else:
        print("\n[ERRO] Restauração falhou. Verifique os logs acima.")
