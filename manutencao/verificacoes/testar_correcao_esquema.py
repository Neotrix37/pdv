#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a correção automática do esquema funciona
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def testar_correcao_esquema():
    """Testa se a correção automática de esquema funciona"""
    try:
        print("TESTE DE CORREÇÃO AUTOMÁTICA DO ESQUEMA")
        print("=" * 50)
        
        from database.database import Database
        
        # Criar instância do banco
        db = Database()
        
        # Verificar se a função existe
        if hasattr(db, 'verificar_e_corrigir_esquema_pos_restauracao'):
            print("✅ Função verificar_e_corrigir_esquema_pos_restauracao encontrada")
            
            # Testar se as colunas críticas existem
            cursor = db.conn.cursor()
            colunas = cursor.execute("PRAGMA table_info(vendas)").fetchall()
            
            # Verificar coluna 'total'
            tem_total = any(col[1] == 'total' for col in colunas)
            if tem_total:
                print("✅ Coluna 'total' confirmada na tabela vendas")
            else:
                print("❌ Coluna 'total' não encontrada - isso será corrigido automaticamente")
            
            # Verificar coluna 'status'
            tem_status = any(col[1] == 'status' for col in colunas)
            if tem_status:
                print("✅ Coluna 'status' confirmada na tabela vendas")
            else:
                print("❌ Coluna 'status' não encontrada - isso será corrigido automaticamente")
            
            # Testar a função de correção
            print("\nExecutando verificação de esquema...")
            resultado = db.verificar_e_corrigir_esquema_pos_restauracao()
            
            if resultado:
                print("✅ Verificação de esquema executada com sucesso")
                
                # Verificar novamente após a correção
                colunas_apos = cursor.execute("PRAGMA table_info(vendas)").fetchall()
                tem_total_apos = any(col[1] == 'total' for col in colunas_apos)
                tem_status_apos = any(col[1] == 'status' for col in colunas_apos)
                
                if tem_total_apos and tem_status_apos:
                    print("✅ Todas as colunas críticas estão presentes após verificação")
                    
                    # Testar uma consulta que usa a coluna 'total'
                    try:
                        resultado_consulta = db.fetchone("SELECT COUNT(*) as count FROM vendas WHERE total >= 0")
                        if resultado_consulta:
                            print(f"✅ Consulta usando coluna 'total' executada com sucesso: {resultado_consulta['count']} registros")
                        else:
                            print("✅ Consulta executada (sem registros)")
                    except Exception as e:
                        print(f"❌ Erro ao executar consulta com coluna 'total': {e}")
                        return False
                    
                    print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
                    print("O sistema agora deve funcionar corretamente mesmo com backups antigos.")
                    return True
                else:
                    print("❌ Algumas colunas ainda estão faltando após correção")
                    return False
            else:
                print("❌ Falha na verificação de esquema")
                return False
        else:
            print("❌ Função verificar_e_corrigir_esquema_pos_restauracao não encontrada")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_correcao_esquema()
    if sucesso:
        print("\n✅ CORREÇÃO IMPLEMENTADA COM SUCESSO!")
        print("Agora, sempre que um backup for restaurado, o esquema será automaticamente verificado e corrigido.")
        print("O erro 'no such column: total' não deve mais ocorrer.")
    else:
        print("\n❌ TESTE FALHOU - Verifique os logs acima para mais detalhes.")
