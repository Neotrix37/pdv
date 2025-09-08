#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpar backups mantendo apenas o meu.db
"""

import os
import shutil
from datetime import datetime

def limpar_backups():
    """Remove todos os backups exceto meu.db"""
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        print(f"Diretorio de backups nao encontrado: {backup_dir}")
        return
    
    print("LIMPEZA DE BACKUPS")
    print("=" * 40)
    print("Mantendo apenas: meu.db")
    print("Removendo todos os outros backups...")
    
    # Listar todos os arquivos no diretório de backups
    arquivos = os.listdir(backup_dir)
    backups_db = [f for f in arquivos if f.endswith('.db')]
    
    print(f"\nEncontrados {len(backups_db)} arquivos de backup:")
    
    # Separar meu.db dos outros
    meu_db = "meu.db"
    outros_backups = [f for f in backups_db if f != meu_db]
    
    if meu_db in backups_db:
        print(f"  MANTER: {meu_db}")
    else:
        print(f"  AVISO: {meu_db} nao encontrado!")
        return
    
    print(f"\nBackups a serem removidos ({len(outros_backups)}):")
    
    # Criar backup de segurança antes de remover
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_seguranca_dir = f"backups_removidos_{timestamp}"
    
    if outros_backups:
        print(f"\nCriando backup de seguranca em: {backup_seguranca_dir}")
        os.makedirs(backup_seguranca_dir, exist_ok=True)
        
        removidos = 0
        erros = 0
        
        for backup in outros_backups:
            try:
                backup_path = os.path.join(backup_dir, backup)
                backup_seguranca_path = os.path.join(backup_seguranca_dir, backup)
                
                # Copiar para backup de segurança
                shutil.copy2(backup_path, backup_seguranca_path)
                
                # Remover do diretório original
                os.remove(backup_path)
                
                print(f"  REMOVIDO: {backup}")
                removidos += 1
                
            except Exception as e:
                print(f"  ERRO ao remover {backup}: {e}")
                erros += 1
        
        print(f"\nRESUMO:")
        print(f"  Backups removidos: {removidos}")
        print(f"  Erros: {erros}")
        print(f"  Backup mantido: {meu_db}")
        
        if removidos > 0:
            print(f"\nBackups removidos foram salvos em: {backup_seguranca_dir}")
            print("Voce pode apagar essa pasta depois se nao precisar mais dos backups antigos.")
        
        # Verificar resultado final
        arquivos_restantes = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        print(f"\nArquivos restantes no diretorio backups/:")
        for arquivo in arquivos_restantes:
            tamanho_mb = round(os.path.getsize(os.path.join(backup_dir, arquivo)) / (1024 * 1024), 2)
            print(f"  {arquivo} ({tamanho_mb} MB)")
        
        if len(arquivos_restantes) == 1 and arquivos_restantes[0] == meu_db:
            print(f"\nSUCESSO! Apenas {meu_db} foi mantido no diretorio backups/")
        else:
            print(f"\nAVISO: Resultado inesperado. Verifique o diretorio backups/")
            
    else:
        print("\nNenhum backup para remover. Apenas meu.db existe.")

def main():
    try:
        # Confirmar operação
        print("ATENCAO: Esta operacao ira remover todos os backups exceto meu.db")
        print("Os backups removidos serao salvos em uma pasta de seguranca.")
        
        resposta = input("\nDeseja continuar? (s/N): ").lower().strip()
        
        if resposta in ['s', 'sim', 'y', 'yes']:
            limpar_backups()
        else:
            print("Operacao cancelada pelo usuario.")
            
    except KeyboardInterrupt:
        print("\nOperacao cancelada pelo usuario.")
    except Exception as e:
        print(f"\nErro durante a limpeza: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
