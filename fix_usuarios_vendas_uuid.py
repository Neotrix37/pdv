#!/usr/bin/env python3
"""
Script para corrigir UUIDs de usuários e vendas
"""
import sqlite3
import os
import uuid

def fix_usuarios_vendas_uuid():
    """Corrigir UUIDs ausentes em usuários e vendas"""
    db_path = os.path.expanduser("~/AppData/Roaming/SistemaGestao/database/sistema.db")
    
    print("=== CORRIGINDO UUIDs DE USUÁRIOS E VENDAS ===")
    print(f"Banco: {db_path}")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Verificar e corrigir usuários sem UUID
        print("1. VERIFICANDO USUÁRIOS...")
        cursor.execute("""
            SELECT id, nome, usuario, uuid, synced
            FROM usuarios
            WHERE ativo = 1
            ORDER BY id
        """)
        usuarios = cursor.fetchall()
        
        usuarios_corrigidos = 0
        for usuario in usuarios:
            user_id, nome, login, user_uuid, synced = usuario
            print(f"Usuário ID {user_id}: {nome} (login: {login})")
            print(f"  UUID atual: {user_uuid}")
            print(f"  Synced: {synced}")
            
            if not user_uuid or user_uuid.strip() == '':
                # Gerar novo UUID
                novo_uuid = str(uuid.uuid4())
                cursor.execute("""
                    UPDATE usuarios 
                    SET uuid = ?, synced = 0, updated_at = datetime('now')
                    WHERE id = ?
                """, (novo_uuid, user_id))
                print(f"  ✅ UUID corrigido: {novo_uuid}")
                usuarios_corrigidos += 1
            else:
                # Verificar se UUID é válido
                try:
                    uuid.UUID(user_uuid)
                    print(f"  ✅ UUID válido")
                    # Marcar como não sincronizado se necessário
                    if synced != 0:
                        cursor.execute("""
                            UPDATE usuarios 
                            SET synced = 0, updated_at = datetime('now')
                            WHERE id = ?
                        """, (user_id,))
                        print(f"  🔄 Marcado para sincronização")
                except ValueError:
                    # UUID inválido - gerar novo
                    novo_uuid = str(uuid.uuid4())
                    cursor.execute("""
                        UPDATE usuarios 
                        SET uuid = ?, synced = 0, updated_at = datetime('now')
                        WHERE id = ?
                    """, (novo_uuid, user_id))
                    print(f"  ✅ UUID inválido corrigido: {novo_uuid}")
                    usuarios_corrigidos += 1
            
            print()
        
        # 2. Verificar e corrigir vendas sem UUID
        print("2. VERIFICANDO VENDAS...")
        cursor.execute("""
            SELECT id, data_venda, total, uuid, synced
            FROM vendas
            WHERE status != 'Anulada'
            ORDER BY id
        """)
        vendas = cursor.fetchall()
        
        vendas_corrigidas = 0
        for venda in vendas:
            venda_id, data_venda, total, venda_uuid, synced = venda
            print(f"Venda ID {venda_id}: {data_venda} - MT {total}")
            print(f"  UUID atual: {venda_uuid}")
            print(f"  Synced: {synced}")
            
            if not venda_uuid or venda_uuid.strip() == '':
                # Gerar novo UUID
                novo_uuid = str(uuid.uuid4())
                cursor.execute("""
                    UPDATE vendas 
                    SET uuid = ?, synced = 0, updated_at = datetime('now')
                    WHERE id = ?
                """, (novo_uuid, venda_id))
                print(f"  ✅ UUID corrigido: {novo_uuid}")
                vendas_corrigidas += 1
            else:
                # Verificar se UUID é válido
                try:
                    uuid.UUID(venda_uuid)
                    print(f"  ✅ UUID válido")
                    # Marcar como não sincronizado se necessário
                    if synced != 0:
                        cursor.execute("""
                            UPDATE vendas 
                            SET synced = 0, updated_at = datetime('now')
                            WHERE id = ?
                        """, (venda_id,))
                        print(f"  🔄 Marcado para sincronização")
                except ValueError:
                    # UUID inválido - gerar novo
                    novo_uuid = str(uuid.uuid4())
                    cursor.execute("""
                        UPDATE vendas 
                        SET uuid = ?, synced = 0, updated_at = datetime('now')
                        WHERE id = ?
                    """, (novo_uuid, venda_id))
                    print(f"  ✅ UUID inválido corrigido: {novo_uuid}")
                    vendas_corrigidas += 1
            
            print()
        
        # Salvar mudanças
        conn.commit()
        conn.close()
        
        print("=== CORREÇÃO CONCLUÍDA ===")
        print(f"Usuários corrigidos: {usuarios_corrigidos}")
        print(f"Vendas corrigidas: {vendas_corrigidas}")
        print()
        print("Agora você pode tentar a sincronização novamente!")
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    fix_usuarios_vendas_uuid()
