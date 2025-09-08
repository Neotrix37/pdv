import sqlite3
import os
from pathlib import Path

def corrigir_trigger_divida():
    # Caminho para o banco de dados
    if 'APPDATA' in os.environ:
        db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    else:
        db_path = Path("database/sistema.db")
    
    if not db_path.exists():
        print(f"[ERRO] Banco de dados não encontrado em: {db_path}")
        return False
    
    print(f"[INFO] Conectando ao banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar se o trigger existe
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type = 'trigger' AND name = 'after_divida_quitada'")
        trigger = cursor.fetchone()
        
        if not trigger:
            print("[ERRO] Trigger 'after_divida_quitada' não encontrado no banco de dados.")
            return False
            
        print("[INFO] Trigger encontrado. Verificando necessidade de correção...")
        
        # Verificar se o trigger contém a linha problemática
        if "INSERT INTO sqlite_master" in trigger[1]:
            print("[INFO] Encontrada instrução problemática no trigger. Iniciando correção...")
            
            # Remover o trigger existente
            cursor.execute("DROP TRIGGER IF EXISTS after_divida_quitada")
            
            # Criar o novo trigger sem a instrução problemática
            novo_trigger = """
            CREATE TRIGGER after_divida_quitada
            AFTER UPDATE ON dividas
            WHEN NEW.status = 'Quitado' AND OLD.status = 'Pendente'
            BEGIN
                -- Inserir na tabela de vendas (sem afetar estoque)
                INSERT INTO vendas (
                    usuario_id,
                    total,
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
                    id.peso_kg
                FROM itens_divida id
                WHERE id.divida_id = NEW.id;
            END
            """
            
            # Executar o novo trigger
            cursor.executescript(novo_trigger)
            conn.commit()
            print("[SUCESSO] Trigger corrigido com sucesso!")
            return True
        else:
            print("[INFO] O trigger já está correto. Nenhuma alteração necessária.")
            return True
            
    except Exception as e:
        print(f"[ERRO] Erro ao corrigir o trigger: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if corrigir_trigger_divida():
        print("\n[SUCESSO] Operação concluída com sucesso!")
    else:
        print("\n[FALHA] Não foi possível concluir a operação. Verifique os logs acima.")
