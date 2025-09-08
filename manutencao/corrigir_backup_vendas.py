#!/usr/bin/env python3
"""
Script para corrigir backups antigos que não possuem a coluna 'valor_total' na tabela vendas
"""

import sqlite3
import os
from pathlib import Path

def corrigir_backup_vendas():
    """Adiciona a coluna valor_total em backups restaurados que não a possuem"""
    
    # Caminho do banco de dados
    db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    
    print(f"Verificando banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar se a coluna valor_total existe
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = cursor.fetchall()
        colunas_nomes = [col[1] for col in colunas]
        
        print(f"Colunas existentes na tabela vendas: {colunas_nomes}")
        
        if 'valor_total' not in colunas_nomes:
            print("ERRO: Coluna 'valor_total' nao encontrada. Adicionando...")
            
            # Adicionar a coluna valor_total
            cursor.execute("ALTER TABLE vendas ADD COLUMN valor_total REAL")
            print("OK: Coluna 'valor_total' adicionada")
            
            # Verificar se existe coluna 'total' para migrar dados
            if 'total' in colunas_nomes:
                print("INFO: Migrando dados da coluna 'total' para 'valor_total'...")
                cursor.execute("UPDATE vendas SET valor_total = total WHERE valor_total IS NULL")
                rows_updated = cursor.rowcount
                print(f"OK: {rows_updated} registros migrados")
            else:
                print("AVISO: Coluna 'total' nao encontrada. Definindo valor_total como 0 para registros existentes")
                cursor.execute("UPDATE vendas SET valor_total = 0 WHERE valor_total IS NULL")
            
            # Recriar o trigger corrigido
            print("INFO: Recriando trigger after_divida_quitada...")
            
            # Remover trigger antigo se existir
            cursor.execute("DROP TRIGGER IF EXISTS after_divida_quitada")
            
            # Criar novo trigger com valor_total
            cursor.execute("""
                CREATE TRIGGER after_divida_quitada
                AFTER UPDATE ON dividas
                WHEN NEW.status = 'Quitado' AND OLD.status = 'Pendente'
                BEGIN
                    -- Inserir na tabela de vendas (sem afetar estoque)
                    INSERT INTO vendas ( 
                        usuario_id,
                        valor_total,
                        forma_pagamento,
                        valor_recebido,
                        troco,
                        data_venda,
                        origem,
                        valor_original_divida,
                        desconto_aplicado_divida
                    )
                    SELECT 
                        d.usuario_id,
                        d.valor_total,
                        (SELECT forma_pagamento FROM pagamentos_divida 
                         WHERE divida_id = d.id 
                         ORDER BY data_pagamento DESC LIMIT 1),
                        d.valor_total,
                        0,
                        datetime('now', 'localtime'),
                        'divida_quitada',
                        d.valor_original,
                        d.desconto_aplicado
                    FROM dividas d
                    WHERE d.id = NEW.id;

                    -- Inserir itens da venda (sem afetar estoque)
                    INSERT INTO itens_venda (
                        venda_id,
                        produto_id,
                        quantidade,
                        preco_unitario,
                        preco_custo_unitario,
                        subtotal,
                        peso_kg
                    )
                    SELECT 
                        last_insert_rowid(),
                        id.produto_id,
                        id.quantidade,
                        id.preco_unitario,
                        (SELECT preco_custo FROM produtos WHERE id = id.produto_id),
                        id.subtotal,
                        COALESCE(id.peso_kg, 0)
                    FROM itens_divida id
                    WHERE id.divida_id = NEW.id;
                END
            """)
            print("OK: Trigger recriado com sucesso")
            
            # Commit das alterações
            conn.commit()
            print("SALVO: Alteracoes salvas com sucesso")
            
        else:
            print("OK: Coluna 'valor_total' ja existe. Nenhuma correcao necessaria.")
        
        # Verificar se existem outras colunas necessárias
        colunas_obrigatorias = [
            'valor_original_divida',
            'desconto_aplicado_divida'
        ]
        
        for coluna in colunas_obrigatorias:
            if coluna not in colunas_nomes:
                print(f"INFO: Adicionando coluna '{coluna}'...")
                cursor.execute(f"ALTER TABLE vendas ADD COLUMN {coluna} REAL DEFAULT 0")
                print(f"OK: Coluna '{coluna}' adicionada")
        
        conn.commit()
        conn.close()
        
        print("\nSUCESSO: Correcao do backup concluida com sucesso!")
        print("Agora voce pode quitar dividas normalmente.")
        
    except Exception as e:
        print(f"ERRO: Erro durante a correcao: {e}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    corrigir_backup_vendas()
