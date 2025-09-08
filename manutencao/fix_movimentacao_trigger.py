#!/usr/bin/env python3
"""Script para corrigir o trigger after_venda_insert que está causando erro no caixa"""

import sqlite3
import os
from pathlib import Path

def fix_movimentacao_trigger():
    db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("PROBLEMA IDENTIFICADO:")
        print("- Trigger 'after_venda_insert' usa NEW.total (que pode ser NULL)")
        print("- Coluna 'valor' em movimentacao_caixa tem constraint NOT NULL")
        print("- Quando NEW.total eh NULL, o trigger falha")
        
        print("\nCorrigindo trigger...")
        
        # Remover trigger problemático
        cursor.execute("DROP TRIGGER IF EXISTS after_venda_insert")
        
        # Recriar trigger corrigido usando COALESCE para usar valor_total ou total
        cursor.execute("""
            CREATE TRIGGER after_venda_insert 
            AFTER INSERT ON vendas
            BEGIN
                INSERT INTO movimentacao_caixa (
                    data_movimento,
                    tipo,
                    valor,
                    descricao,
                    usuario_id
                )
                VALUES (
                    NEW.data_venda,
                    'Entrada',
                    COALESCE(NEW.valor_total, NEW.total, 0),
                    'Venda #' || NEW.id,
                    NEW.usuario_id
                );
            END
        """)
        
        conn.commit()
        print("Trigger corrigido com sucesso!")
        print("Agora usa: COALESCE(NEW.valor_total, NEW.total, 0)")
        print("Isso garante que sempre tenha um valor valido para o caixa")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    fix_movimentacao_trigger()
