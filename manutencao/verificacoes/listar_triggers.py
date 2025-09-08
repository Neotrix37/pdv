import sqlite3
import os
from pathlib import Path

def listar_triggers():
    # Caminho para o banco de dados
    if 'APPDATA' in os.environ:
        db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    else:
        db_path = Path("database/sistema.db")
    
    if not db_path.exists():
        print(f"[ERRO] Banco de dados não encontrado em: {db_path}")
        return
    
    print(f"[INFO] Verificando triggers no banco: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Lista todos os triggers
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type = 'trigger'")
        triggers = cursor.fetchall()
        
        if not triggers:
            print("[INFO] Nenhum trigger encontrado no banco de dados.")
            return
            
        print(f"\n[INFO] {len(triggers)} triggers encontrados:")
        print("-" * 80)
        
        for name, sql in sorted(triggers, key=lambda x: x[0].lower()):
            print(f"- {name}")
            print(f"SQL: {sql}")
            print("-" * 80)
        
        # Verificar triggers relacionados a dívidas
        divida_triggers = [t for t in triggers if 'divida' in t[0].lower()]
        
        if divida_triggers:
            print("\n[ATENCAO] Foram encontrados os seguintes triggers relacionados a dívidas:")
            for name, sql in divida_triggers:
                print(f"\n[TRIGGER] {name}:")
                print(sql)
        
        conn.close()
        
    except Exception as e:
        print(f"[ERRO] Erro ao acessar o banco de dados: {e}")

if __name__ == "__main__":
    listar_triggers()
