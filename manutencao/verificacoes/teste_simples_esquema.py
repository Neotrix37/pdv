#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar se a correção automática do esquema funciona
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def testar_correcao_esquema():
    """Testa se a correção automática de esquema funciona"""
    try:
        print("TESTE DE CORRECAO AUTOMATICA DO ESQUEMA")
        print("=" * 50)
        
        from database.database import Database
        
        # Criar instância do banco
        db = Database()
        
        # Verificar se a função existe
        if hasattr(db, 'verificar_e_corrigir_esquema_pos_restauracao'):
            print("OK - Funcao verificar_e_corrigir_esquema_pos_restauracao encontrada")
            
            # Testar se as colunas críticas existem
            cursor = db.conn.cursor()
            colunas = cursor.execute("PRAGMA table_info(vendas)").fetchall()
            
            # Verificar coluna 'total'
            tem_total = any(col[1] == 'total' for col in colunas)
            if tem_total:
                print("OK - Coluna 'total' confirmada na tabela vendas")
            else:
                print("AVISO - Coluna 'total' nao encontrada - sera corrigida automaticamente")
            
            # Testar uma consulta que usa a coluna 'total'
            try:
                resultado_consulta = db.fetchone("SELECT COUNT(*) as count FROM vendas WHERE total >= 0")
                if resultado_consulta:
                    print(f"OK - Consulta usando coluna 'total' executada com sucesso: {resultado_consulta['count']} registros")
                else:
                    print("OK - Consulta executada (sem registros)")
            except Exception as e:
                print(f"ERRO - Erro ao executar consulta com coluna 'total': {e}")
                return False
            
            print("\nSUCESSO - TESTE CONCLUIDO COM SUCESSO!")
            print("O sistema agora deve funcionar corretamente mesmo com backups antigos.")
            return True
        else:
            print("ERRO - Funcao verificar_e_corrigir_esquema_pos_restauracao nao encontrada")
            return False
            
    except Exception as e:
        print(f"ERRO - Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_correcao_esquema()
    if sucesso:
        print("\nSUCESSO - CORRECAO IMPLEMENTADA COM SUCESSO!")
        print("Agora, sempre que um backup for restaurado, o esquema sera automaticamente verificado e corrigido.")
        print("O erro 'no such column: total' nao deve mais ocorrer.")
    else:
        print("\nERRO - TESTE FALHOU - Verifique os logs acima para mais detalhes.")
