import os
import sys
import json
import httpx
import sqlite3
from pathlib import Path

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

# Resolve local SQLite path (same logic as ProdutoRepository)
import platform
sistema = platform.system().lower()
if sistema == 'windows' and 'APPDATA' in os.environ:
    db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
else:
    db_dir = Path(Path.home()) / '.sistemagestao' / 'database'
db_path = db_dir / 'sistema.db'


def fetch_server_products():
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{api_base}/produtos/")
            resp.raise_for_status()
            return resp.json() or []
    except Exception as e:
        print(f"[ERRO] Falha ao buscar produtos do servidor: {e}")
        return []


def fetch_local_products():
    if not db_path.exists():
        print(f"[ERRO] Banco local não encontrado: {db_path}")
        return []
    rows = []
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            PRAGMA table_info(produtos)
            """
        )
        cols = [c[1] for c in cur.fetchall()]
        has_uuid = 'uuid' in cols
        cur.execute(
            f"""
            SELECT codigo, nome, preco_custo, preco_venda, estoque, ativo
                   {', uuid' if has_uuid else ''}
            FROM produtos
            WHERE 1=1
            """
        )
        for r in cur.fetchall():
            d = dict(r)
            if 'uuid' not in d:
                d['uuid'] = None
            rows.append(d)
    return rows


def summarize(products):
    total_custo = 0.0
    total_venda = 0.0
    ativos = 0
    for p in products:
        ativo = p.get('ativo', True)
        if isinstance(ativo, (int, float)):
            ativo = int(ativo) == 1
        if not ativo:
            continue
        estoque = float(p.get('estoque') or 0.0)
        total_custo += estoque * float(p.get('preco_custo') or 0.0)
        total_venda += estoque * float(p.get('preco_venda') or 0.0)
        ativos += 1
    return total_custo, total_venda, ativos


def index_by_key(products):
    by_uuid = {}
    by_codigo = {}
    for p in products:
        uuid = str(p.get('uuid') or p.get('id') or '').strip()
        codigo = (p.get('codigo') or '').strip()
        if uuid:
            by_uuid[uuid] = p
        if codigo:
            by_codigo[codigo] = p
    return by_uuid, by_codigo


def main():
    server = fetch_server_products()
    local = fetch_local_products()

    sc, sv, sa = summarize(server)
    lc, lv, la = summarize(local)

    print("\n=== RESUMO ===")
    print(f"Servidor -> Valor estoque (custo): MT {sc:.2f} | Valor potencial (venda): MT {sv:.2f} | ativos: {sa}")
    print(f"Local    -> Valor estoque (custo): MT {lc:.2f} | Valor potencial (venda): MT {lv:.2f} | ativos: {la}")
    print(f"Diferenças -> custo: MT {(lc-sc):.2f} | potencial: MT {(lv-sv):.2f}")

    by_uuid_s, by_codigo_s = index_by_key(server)
    by_uuid_l, by_codigo_l = index_by_key(local)

    print("\n=== TOP DIVERGÊNCIAS POR CÓDIGO ===")
    divergencias = []
    codigos = set(by_codigo_l.keys()) | set(by_codigo_s.keys())
    for cod in codigos:
        ls = by_codigo_l.get(cod)
        ss = by_codigo_s.get(cod)
        if not ls or not ss:
            continue
        est_l = float(ls.get('estoque') or 0.0)
        est_s = float(ss.get('estoque') or 0.0)
        pv_l = float(ls.get('preco_venda') or 0.0)
        pv_s = float(ss.get('preco_venda') or 0.0)
        pc_l = float(ls.get('preco_custo') or 0.0)
        pc_s = float(ss.get('preco_custo') or 0.0)
        diff_pot = (est_l*pv_l) - (est_s*pv_s)
        diff_cus = (est_l*pc_l) - (est_s*pc_s)
        if abs(diff_pot) > 0.005 or abs(diff_cus) > 0.005:
            divergencias.append((cod, ls.get('nome') or ss.get('nome') or cod, est_l, est_s, pv_l, pv_s, pc_l, pc_s, diff_pot, diff_cus))
    divergencias.sort(key=lambda x: abs(x[8])+abs(x[9]), reverse=True)
    for i, d in enumerate(divergencias[:25], 1):
        cod, nome, est_l, est_s, pv_l, pv_s, pc_l, pc_s, diff_pot, diff_cus = d
        print(f"{i:02d}. {cod} - {nome}")
        print(f"    Estoque L/S: {est_l} / {est_s}")
        print(f"    Preço venda L/S: {pv_l} / {pv_s}")
        print(f"    Preço custo L/S: {pc_l} / {pc_s}")
        print(f"    Δ Potencial: MT {diff_pot:.2f} | Δ Custo: MT {diff_cus:.2f}")

    print("\nConcluído.")


if __name__ == "__main__":
    main()
