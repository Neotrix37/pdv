import os
import json
import httpx
import sqlite3
from pathlib import Path
import platform

# Resolve backend URL similar to other scripts
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

# Resolve local DB path (same as ProdutoRepository)
sistema = platform.system().lower()
if sistema == 'windows' and 'APPDATA' in os.environ:
    db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
else:
    db_dir = Path(Path.home()) / '.sistemagestao' / 'database'
db_path = db_dir / 'sistema.db'


def fetch_server_products():
    with httpx.Client(timeout=15.0) as client:
        r = client.get(f"{api_base}/produtos/")
        r.raise_for_status()
        return r.json() or []


def fetch_local_products():
    rows = []
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT codigo, nome, preco_custo, preco_venda, estoque, ativo, COALESCE(uuid, '') as uuid FROM produtos")
        for r in cur.fetchall():
            rows.append(dict(r))
    return rows


def index_by_codigo(items):
    m = {}
    for p in items:
        cod = (p.get('codigo') or '').strip()
        if cod:
            m[cod] = p
    return m


def main():
    print("Carregando produtos do servidor e local...")
    server = fetch_server_products()
    local = fetch_local_products()

    by_cod_srv = index_by_codigo(server)
    by_cod_loc = index_by_codigo(local)

    updates = []
    for cod, lp in by_cod_loc.items():
        sp = by_cod_srv.get(cod)
        if not sp:
            continue
        try:
            estoque_l = float(lp.get('estoque') or 0.0)
            estoque_s = float(sp.get('estoque') or 0.0)
            preco_custo_l = float(lp.get('preco_custo') or 0.0)
            preco_venda_l = float(lp.get('preco_venda') or 0.0)
        except Exception:
            continue
        if abs(estoque_l - estoque_s) > 0.001 or abs(float(sp.get('preco_custo') or 0.0) - preco_custo_l) > 0.001 or abs(float(sp.get('preco_venda') or 0.0) - preco_venda_l) > 0.001:
            updates.append((sp, estoque_l, preco_custo_l, preco_venda_l))

    if not updates:
        print("Nenhuma divergência relevante encontrada. Nada a reconciliar.")
        return

    print(f"Encontradas {len(updates)} divergências. Reconciliando no servidor...")

    ok, fail = 0, 0
    with httpx.Client(timeout=15.0) as client:
        for sp, est_l, pc_l, pv_l in updates:
            target_id = str(sp.get('id') or sp.get('uuid') or '').strip()
            if not target_id:
                print(f"[PULAR] Produto sem id/uuid: {sp}")
                fail += 1
                continue
            payload = {
                # Parciais permitem update sem apagar outros campos
                'estoque': float(est_l),
                'preco_custo': float(pc_l),
                'preco_venda': float(pv_l),
            }
            try:
                r = client.put(f"{api_base}/produtos/{target_id}", json=payload)
                if r.status_code == 200:
                    ok += 1
                    print(f"[OK] {sp.get('codigo')} {sp.get('nome')} -> estoque: {est_l} | custo: {pc_l} | venda: {pv_l}")
                else:
                    fail += 1
                    print(f"[ERRO] {sp.get('codigo')} {sp.get('nome')} HTTP {r.status_code}: {r.text}")
            except Exception as e:
                fail += 1
                print(f"[ERRO] {sp.get('codigo')} {sp.get('nome')} exceção: {e}")

    print(f"Concluído. Sucesso: {ok} | Falhas: {fail}")


if __name__ == "__main__":
    if not db_path.exists():
        print(f"[ERRO] Banco local não encontrado: {db_path}")
        raise SystemExit(1)
    main()
