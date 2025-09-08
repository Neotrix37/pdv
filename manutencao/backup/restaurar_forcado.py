#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import shutil
import time
from pathlib import Path
from datetime import datetime
import platform
import subprocess
import sys

def forcar_restauracao_meu_db():
    """Força a restauração do meu.db com verificações mais rigorosas"""
    print("RESTAURAÇÃO FORÇADA DO MEU.DB")
    print("=" * 60)
    
    # Determinar caminhos
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
    
    # Garantir que o diretório existe
    app_data_db_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Diretório APPDATA: {app_data_db_dir}")
    print(f"[INFO] Arquivo destino: {appdata_db}")
    print(f"[INFO] Arquivo origem: {backup_meu_db}")
    
    # Verificar se meu.db existe e tem conteúdo
    if not backup_meu_db.exists():
        print(f"[ERRO] meu.db não encontrado: {backup_meu_db}")
        return False
    
    tamanho_origem = backup_meu_db.stat().st_size
    print(f"[INFO] Tamanho do meu.db: {tamanho_origem / (1024*1024):.2f} MB")
    
    if tamanho_origem < 100000:  # Menos de 100KB é suspeito
        print("[AVISO] meu.db parece muito pequeno!")
    
    # Verificar conteúdo do meu.db
    print("\n[VERIFICAÇÃO] Analisando conteúdo do meu.db...")
    try:
        conn_origem = sqlite3.connect(str(backup_meu_db))
        cursor_origem = conn_origem.cursor()
        
        # Contar vendas
        cursor_origem.execute("SELECT COUNT(*) FROM vendas")
        total_vendas = cursor_origem.fetchone()[0]
        
        # Somar valores
        cursor_origem.execute("SELECT COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) FROM vendas")
        valor_total = cursor_origem.fetchone()[0]
        
        print(f"[ORIGEM] Vendas: {total_vendas}")
        print(f"[ORIGEM] Valor: MT {valor_total:.2f}")
        
        if total_vendas == 0:
            print("[ERRO] meu.db está vazio!")
            conn_origem.close()
            return False
        
        conn_origem.close()
        
    except Exception as e:
        print(f"[ERRO] Não foi possível ler meu.db: {e}")
        return False
    
    # Parar qualquer processo que possa estar usando o banco
    print("\n[PREPARAÇÃO] Preparando para restauração...")
    
    # Fazer backup do arquivo atual
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_atual = Path(os.path.dirname(__file__)) / 'backups' / f'pre_forced_restore_{timestamp}.db'
    
    if appdata_db.exists():
        try:
            shutil.copy2(str(appdata_db), str(backup_atual))
            print(f"[BACKUP] Backup criado: {backup_atual}")
        except Exception as e:
            print(f"[AVISO] Erro ao criar backup: {e}")
    
    # Executar restauração com múltiplas tentativas
    print("\n[RESTAURAÇÃO] Iniciando restauração forçada...")
    
    for tentativa in range(3):
        print(f"\n[TENTATIVA {tentativa + 1}] Executando restauração...")
        
        try:
            # 1. Remover arquivo existente com força
            if appdata_db.exists():
                print("[PASSO 1] Removendo arquivo existente...")
                try:
                    os.chmod(str(appdata_db), 0o777)  # Dar permissões totais
                    os.remove(str(appdata_db))
                    print("[PASSO 1] Arquivo removido")
                except Exception as e:
                    print(f"[PASSO 1] Erro ao remover: {e}")
                    # Tentar renomear em vez de remover
                    try:
                        temp_name = f"{appdata_db}.old_{tentativa}"
                        os.rename(str(appdata_db), temp_name)
                        print(f"[PASSO 1] Arquivo renomeado para: {temp_name}")
                    except Exception as e2:
                        print(f"[PASSO 1] Erro ao renomear: {e2}")
                        if tentativa < 2:
                            time.sleep(2)
                            continue
                        else:
                            raise e2
            
            # 2. Aguardar liberação do arquivo
            time.sleep(1)
            
            # 3. Copiar arquivo
            print("[PASSO 2] Copiando meu.db...")
            shutil.copy2(str(backup_meu_db), str(appdata_db))
            
            # 4. Verificar se a cópia foi bem-sucedida
            if not appdata_db.exists():
                raise Exception("Arquivo não foi copiado")
            
            tamanho_destino = appdata_db.stat().st_size
            print(f"[PASSO 2] Arquivo copiado. Tamanho: {tamanho_destino / (1024*1024):.2f} MB")
            
            # 5. Verificar se os tamanhos coincidem
            if abs(tamanho_origem - tamanho_destino) > 1000:  # Tolerância de 1KB
                raise Exception(f"Tamanhos diferentes: origem={tamanho_origem}, destino={tamanho_destino}")
            
            # 6. Verificar conteúdo do arquivo copiado
            print("[PASSO 3] Verificando integridade...")
            conn_destino = sqlite3.connect(str(appdata_db))
            cursor_destino = conn_destino.cursor()
            
            # Verificar vendas no destino
            cursor_destino.execute("SELECT COUNT(*) FROM vendas")
            vendas_destino = cursor_destino.fetchone()[0]
            
            cursor_destino.execute("SELECT COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) FROM vendas")
            valor_destino = cursor_destino.fetchone()[0]
            
            conn_destino.close()
            
            print(f"[DESTINO] Vendas: {vendas_destino}")
            print(f"[DESTINO] Valor: MT {valor_destino:.2f}")
            
            # 7. Comparar dados
            if vendas_destino == total_vendas and abs(valor_destino - valor_total) < 0.01:
                print(f"\n[SUCESSO] Restauração concluída na tentativa {tentativa + 1}!")
                print("=" * 60)
                print("DADOS RESTAURADOS:")
                print(f"- Vendas: {vendas_destino} registros")
                print(f"- Valor: MT {valor_destino:.2f}")
                print("=" * 60)
                return True
            else:
                raise Exception(f"Dados inconsistentes: origem={total_vendas}/{valor_total}, destino={vendas_destino}/{valor_destino}")
        
        except Exception as e:
            print(f"[ERRO] Tentativa {tentativa + 1} falhou: {e}")
            if tentativa < 2:
                print("[INFO] Aguardando antes da próxima tentativa...")
                time.sleep(3)
            else:
                print("[ERRO] Todas as tentativas falharam!")
                return False
    
    return False

if __name__ == "__main__":
    print("ATENÇÃO: Este script irá forçar a restauração do meu.db")
    print("Certifique-se de que o sistema PDV está fechado!")
    print()
    
    sucesso = forcar_restauracao_meu_db()
    
    if sucesso:
        print("\n[CONCLUÍDO] Restauração forçada bem-sucedida!")
        print("Agora inicie o sistema PDV para ver os dados corretos.")
    else:
        print("\n[FALHA] Não foi possível restaurar o backup.")
        print("Verifique se:")
        print("1. O arquivo meu.db existe e não está corrompido")
        print("2. Você tem permissões de escrita no diretório APPDATA")
        print("3. Nenhum processo está usando o banco de dados")
