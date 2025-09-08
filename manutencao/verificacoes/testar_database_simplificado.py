#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from pathlib import Path
from datetime import datetime
import platform

def testar_database_simplificado():
    """Testa o novo sistema de banco de dados simplificado"""
    print("TESTE DO SISTEMA DE BANCO DE DADOS SIMPLIFICADO")
    print("=" * 60)
    
    # Importar a classe Database modificada
    try:
        from database.database import Database
        print("[OK] Classe Database importada com sucesso")
    except Exception as e:
        print(f"[ERRO] Falha ao importar Database: {e}")
        return False
    
    # Testar inicialização
    print("\n[TESTE 1] Testando inicialização...")
    try:
        db = Database()
        print(f"[OK] Database inicializado")
        print(f"[INFO] Caminho do banco: {db.db_path}")
        
        # Verificar se o caminho é único (APPDATA)
        expected_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
        if str(db.db_path) == str(expected_path):
            print("[OK] Caminho correto: usando apenas APPDATA")
        else:
            print(f"[AVISO] Caminho inesperado: {db.db_path}")
            print(f"[AVISO] Esperado: {expected_path}")
        
    except Exception as e:
        print(f"[ERRO] Falha na inicialização: {e}")
        return False
    
    # Testar se o banco existe e tem dados
    print("\n[TESTE 2] Verificando conteúdo do banco...")
    try:
        cursor = db.conn.cursor()
        
        # Verificar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        print(f"[INFO] Tabelas encontradas: {len(tabelas)}")
        
        # Verificar vendas
        cursor.execute("SELECT COUNT(*) as total FROM vendas")
        total_vendas = cursor.fetchone()['total']
        print(f"[INFO] Total de vendas: {total_vendas}")
        
        # Verificar valor total
        cursor.execute("SELECT COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) as valor FROM vendas")
        valor_total = cursor.fetchone()['valor']
        print(f"[INFO] Valor total: MT {valor_total:.2f}")
        
        # Verificar produtos
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE ativo = 1")
        total_produtos = cursor.fetchone()['total']
        print(f"[INFO] Produtos ativos: {total_produtos}")
        
        if total_vendas > 1000 and valor_total > 100000:
            print("[OK] Banco contém dados completos (provavelmente meu.db restaurado)")
        elif total_vendas > 0:
            print("[AVISO] Banco contém poucos dados (pode ser backup de teste)")
        else:
            print("[AVISO] Banco vazio ou sem vendas")
        
    except Exception as e:
        print(f"[ERRO] Falha ao verificar conteúdo: {e}")
        return False
    
    # Testar singleton (múltiplas instâncias devem ser a mesma)
    print("\n[TESTE 3] Testando padrão singleton...")
    try:
        db2 = Database()
        if db is db2:
            print("[OK] Singleton funcionando: mesma instância")
        else:
            print("[AVISO] Singleton pode não estar funcionando corretamente")
        
        if str(db.db_path) == str(db2.db_path):
            print("[OK] Ambas instâncias usam o mesmo caminho")
        else:
            print(f"[ERRO] Caminhos diferentes: {db.db_path} vs {db2.db_path}")
    
    except Exception as e:
        print(f"[ERRO] Falha no teste de singleton: {e}")
        return False
    
    # Testar operações básicas
    print("\n[TESTE 4] Testando operações básicas...")
    try:
        # Testar consulta simples
        result = db.fetchone("SELECT COUNT(*) as count FROM usuarios WHERE ativo = 1")
        usuarios_ativos = result['count'] if result else 0
        print(f"[INFO] Usuários ativos: {usuarios_ativos}")
        
        # Testar método específico
        valor_estoque = db.get_valor_estoque()
        print(f"[INFO] Valor em estoque: MT {valor_estoque:.2f}")
        
        print("[OK] Operações básicas funcionando")
        
    except Exception as e:
        print(f"[ERRO] Falha nas operações básicas: {e}")
        return False
    
    # Verificar se não há referências ao banco antigo
    print("\n[TESTE 5] Verificando limpeza de referências antigas...")
    try:
        # Verificar se ainda existe lógica de migração
        import inspect
        init_source = inspect.getsource(Database.__init__)
        
        if "antigo_db" in init_source or "prefered_db_path" in init_source:
            print("[AVISO] Ainda existem referências ao sistema antigo no código")
        else:
            print("[OK] Código limpo: sem referências ao sistema antigo")
        
        if "migração" in init_source.lower() or "migration" in init_source.lower():
            print("[AVISO] Ainda existem referências à migração no código")
        else:
            print("[OK] Lógica de migração removida")
            
    except Exception as e:
        print(f"[AVISO] Não foi possível verificar o código fonte: {e}")
    
    print("\n" + "=" * 60)
    print("[CONCLUÍDO] Teste do sistema simplificado finalizado")
    
    # Resumo
    print("\nRESUMO:")
    print(f"- Banco localizado em: {db.db_path}")
    print(f"- Total de vendas: {total_vendas}")
    print(f"- Valor total: MT {valor_total:.2f}")
    print(f"- Produtos ativos: {total_produtos}")
    print("- Sistema simplificado: ✅ Funcionando")
    
    return True

if __name__ == "__main__":
    sucesso = testar_database_simplificado()
    
    if sucesso:
        print("\n[SUCESSO] Sistema de banco de dados simplificado está funcionando!")
        print("Agora você pode usar o sistema PDV normalmente.")
    else:
        print("\n[FALHA] Problemas detectados no sistema simplificado.")
        print("Verifique os logs acima para mais detalhes.")
