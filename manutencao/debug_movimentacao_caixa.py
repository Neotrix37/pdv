#!/usr/bin/env python3
"""Script para investigar e corrigir constraint na tabela movimentacao_caixa"""

import sqlite3
import os
from pathlib import Path

def debug_movimentacao_caixa():
    db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar estrutura da tabela movimentacao_caixa
        cursor.execute("PRAGMA table_info(movimentacao_caixa)")
        colunas = cursor.fetchall()
        print("ESTRUTURA DA TABELA MOVIMENTACAO_CAIXA:")
        for col in colunas:
            not_null = "NOT NULL" if col[3] else "NULL"
            default = f"DEFAULT {col[4]}" if col[4] else "NO DEFAULT"
            print(f"- {col[1]} ({col[2]}) {not_null} {default}")
        
        print("\n" + "="*60 + "\n")
        
        # Verificar triggers relacionados a movimentacao_caixa
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND sql LIKE '%movimentacao_caixa%'")
        triggers = cursor.fetchall()
        
        print("TRIGGERS QUE AFETAM MOVIMENTACAO_CAIXA:")
        for trigger in triggers:
            print(f"Trigger: {trigger[0]}")
            print(trigger[1])
            print("-" * 40)
        
        # Verificar se existe trigger na tabela vendas que insere em movimentacao_caixa
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='vendas'")
        vendas_triggers = cursor.fetchall()
        
        print("\nTRIGGERS NA TABELA VENDAS:")
        for trigger in vendas_triggers:
            print(f"Trigger: {trigger[0]}")
            if 'movimentacao_caixa' in trigger[1]:
                print("*** ESTE TRIGGER AFETA MOVIMENTACAO_CAIXA ***")
            print(trigger[1])
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_movimentacao_caixa()
