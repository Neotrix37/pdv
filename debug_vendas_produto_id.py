#!/usr/bin/env python3
"""
Script para diagnosticar produto_id nas vendas
"""
import sqlite3
import uuid

def debug_vendas_produto_id():
    """Verificar produto_id nos itens de venda"""
    print("🔍 DIAGNOSTICANDO PRODUTO_ID NAS VENDAS")
    print("=" * 50)
    
    conn = sqlite3.connect('sistema.db')
    cursor = conn.cursor()
    
    try:
        # Verificar vendas com UUID
        cursor.execute("""
            SELECT v.id, v.uuid, v.data_venda, v.total
            FROM vendas v
            WHERE v.uuid IS NOT NULL AND v.uuid != '' AND v.status != 'Anulada'
            LIMIT 5
        """)
        vendas = cursor.fetchall()
        
        print(f"Encontradas {len(vendas)} vendas com UUID:")
        
        for venda in vendas:
            venda_id, venda_uuid, data_venda, total = venda
            print(f"\n📋 VENDA {venda_id}:")
            print(f"   UUID: {venda_uuid}")
            print(f"   Data: {data_venda}")
            print(f"   Total: MT {total}")
            
            # Verificar UUID da venda
            try:
                uuid.UUID(venda_uuid)
                print(f"   ✅ UUID da venda válido")
            except ValueError:
                print(f"   ❌ UUID da venda INVÁLIDO: {venda_uuid}")
            
            # Verificar itens da venda
            cursor.execute("""
                SELECT produto_id, quantidade, preco_unitario, subtotal
                FROM itens_venda 
                WHERE venda_id = ?
            """, (venda_id,))
            itens = cursor.fetchall()
            
            print(f"   📦 {len(itens)} itens:")
            for i, item in enumerate(itens, 1):
                produto_id, quantidade, preco_unitario, subtotal = item
                print(f"      Item {i}: produto_id={produto_id} (tipo: {type(produto_id)})")
                
                # Verificar se produto_id é UUID válido
                try:
                    if isinstance(produto_id, str):
                        uuid.UUID(produto_id)
                        print(f"         ✅ produto_id é UUID válido")
                    else:
                        print(f"         ⚠️  produto_id é numérico: {produto_id}")
                        
                        # Buscar UUID do produto pelo ID
                        cursor.execute("SELECT uuid FROM produtos WHERE id = ?", (produto_id,))
                        produto_uuid_result = cursor.fetchone()
                        if produto_uuid_result and produto_uuid_result[0]:
                            produto_uuid = produto_uuid_result[0]
                            print(f"         📝 UUID do produto: {produto_uuid}")
                            try:
                                uuid.UUID(produto_uuid)
                                print(f"         ✅ UUID do produto válido")
                            except ValueError:
                                print(f"         ❌ UUID do produto INVÁLIDO: {produto_uuid}")
                        else:
                            print(f"         ❌ Produto não tem UUID")
                            
                except ValueError as e:
                    print(f"         ❌ produto_id INVÁLIDO: {produto_id} - {e}")
                    
        print("\n" + "=" * 50)
        print("✅ DIAGNÓSTICO CONCLUÍDO")
        
    except Exception as e:
        print(f"❌ Erro durante diagnóstico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    debug_vendas_produto_id()
