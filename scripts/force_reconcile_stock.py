"""
Script para forçar reconciliação de estoque usando PATCH em vez de PUT
"""
import os
import json
import httpx
import sqlite3
from pathlib import Path
import platform

# Resolve backend URL
ROOT = Path(__file__).resolve().parents[1]
config_path = ROOT / "config.json"
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
if config_path.exists():
    try:
        conf = json.loads(config_path.read_text(encoding="utf-8"))
        backend_url = conf.get("server_url", backend_url)
    except Exception:
        pass

api_base = backend_url.rstrip('/')
if not api_base.endswith('/api'):
    api_base = api_base + '/api'

# Resolve local DB path
sistema = platform.system().lower()
if sistema == 'windows' and 'APPDATA' in os.environ:
    db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
else:
    db_dir = Path(Path.home()) / '.sistemagestao' / 'database'
db_path = db_dir / 'sistema.db'

def fetch_server_products():
    """Busca produtos do servidor"""
    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{api_base}/produtos/")
        r.raise_for_status()
        return r.json() or []

def fetch_local_products():
    """Busca produtos locais"""
    rows = []
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT codigo, nome, preco_custo, preco_venda, estoque, ativo, 
                   COALESCE(uuid, '') as uuid, id
            FROM produtos 
            WHERE ativo = 1
        """)
        for r in cur.fetchall():
            rows.append(dict(r))
    return rows

def update_server_product(client, produto_servidor, estoque_local, custo_local, venda_local):
    """Atualiza produto no servidor usando diferentes métodos"""
    produto_id = produto_servidor.get('id')
    codigo = produto_servidor.get('codigo', 'N/A')
    nome = produto_servidor.get('nome', 'N/A')
    
    if not produto_id:
        print(f"[PULAR] {codigo} - {nome}: Sem ID no servidor")
        return False
    
    # Payload com apenas os campos que queremos atualizar
    payload = {
        'estoque': float(estoque_local),
        'preco_custo': float(custo_local),
        'preco_venda': float(venda_local)
    }
    
    # Tentar diferentes métodos HTTP
    methods_to_try = [
        ('PATCH', f"{api_base}/produtos/{produto_id}"),
        ('PUT', f"{api_base}/produtos/{produto_id}"),
        ('POST', f"{api_base}/produtos/{produto_id}/update")
    ]
    
    for method, url in methods_to_try:
        try:
            if method == 'PATCH':
                response = client.patch(url, json=payload)
            elif method == 'PUT':
                # Para PUT, incluir todos os campos do produto original
                full_payload = dict(produto_servidor)
                full_payload.update(payload)
                response = client.put(url, json=full_payload)
            else:  # POST
                response = client.post(url, json=payload)
            
            if response.status_code in [200, 201, 204]:
                print(f"[OK] {codigo} - {nome} -> estoque: {estoque_local} | custo: {custo_local} | venda: {venda_local} ({method})")
                return True
            else:
                print(f"[FALHA {method}] {codigo} - HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"[ERRO {method}] {codigo} - {nome}: {e}")
            continue
    
    return False

def main():
    print("🔄 RECONCILIAÇÃO FORÇADA DE ESTOQUE")
    print("=" * 50)
    
    try:
        print("📡 Buscando produtos do servidor...")
        server_products = fetch_server_products()
        print(f"✅ {len(server_products)} produtos encontrados no servidor")
        
        print("💾 Buscando produtos locais...")
        local_products = fetch_local_products()
        print(f"✅ {len(local_products)} produtos encontrados localmente")
        
        # Indexar por código
        server_by_code = {p.get('codigo', '').strip(): p for p in server_products if p.get('codigo', '').strip()}
        local_by_code = {p.get('codigo', '').strip(): p for p in local_products if p.get('codigo', '').strip()}
        
        # Encontrar divergências
        divergencias = []
        for codigo, local_prod in local_by_code.items():
            if codigo not in server_by_code:
                continue
                
            server_prod = server_by_code[codigo]
            
            try:
                estoque_local = float(local_prod.get('estoque', 0))
                estoque_server = float(server_prod.get('estoque', 0))
                custo_local = float(local_prod.get('preco_custo', 0))
                custo_server = float(server_prod.get('preco_custo', 0))
                venda_local = float(local_prod.get('preco_venda', 0))
                venda_server = float(server_prod.get('preco_venda', 0))
                
                # Verificar se há diferenças significativas
                if (abs(estoque_local - estoque_server) > 0.001 or 
                    abs(custo_local - custo_server) > 0.001 or 
                    abs(venda_local - venda_server) > 0.001):
                    
                    divergencias.append({
                        'codigo': codigo,
                        'nome': local_prod.get('nome', ''),
                        'server_prod': server_prod,
                        'estoque_local': estoque_local,
                        'custo_local': custo_local,
                        'venda_local': venda_local,
                        'estoque_server': estoque_server,
                        'custo_server': custo_server,
                        'venda_server': venda_server
                    })
                    
            except (ValueError, TypeError) as e:
                print(f"⚠️ Erro ao processar produto {codigo}: {e}")
                continue
        
        if not divergencias:
            print("✅ Nenhuma divergência encontrada!")
            return
        
        print(f"🔍 Encontradas {len(divergencias)} divergências")
        print("\n📊 TOP 10 DIVERGÊNCIAS:")
        for i, div in enumerate(divergencias[:10], 1):
            delta_estoque = div['estoque_local'] - div['estoque_server']
            print(f"{i:2d}. {div['codigo']} - {div['nome'][:30]}")
            print(f"    Estoque L/S: {div['estoque_local']:.1f} / {div['estoque_server']:.1f} (Δ {delta_estoque:+.1f})")
        
        print(f"\n🔧 Iniciando reconciliação de {len(divergencias)} produtos...")
        
        sucessos = 0
        falhas = 0
        
        with httpx.Client(timeout=30.0) as client:
            for div in divergencias:
                sucesso = update_server_product(
                    client, 
                    div['server_prod'], 
                    div['estoque_local'], 
                    div['custo_local'], 
                    div['venda_local']
                )
                
                if sucesso:
                    sucessos += 1
                else:
                    falhas += 1
        
        print("\n" + "=" * 50)
        print(f"📊 RESULTADO FINAL:")
        print(f"✅ Sucessos: {sucessos}")
        print(f"❌ Falhas: {falhas}")
        print(f"📈 Taxa de sucesso: {sucessos/(sucessos+falhas)*100:.1f}%" if (sucessos+falhas) > 0 else "N/A")
        
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        raise

if __name__ == "__main__":
    if not db_path.exists():
        print(f"❌ Banco local não encontrado: {db_path}")
        raise SystemExit(1)
    main()
