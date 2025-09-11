import os
import json
import httpx
import sqlite3
from pathlib import Path
import platform
from datetime import datetime

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

# Resolve local DB path (same as repositories)
sistema = platform.system().lower()
if sistema == 'windows' and 'APPDATA' in os.environ:
    db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
else:
    db_dir = Path(Path.home()) / '.sistemagestao' / 'database'
db_path = db_dir / 'sistema.db'


def fetch_server_sales():
    with httpx.Client(timeout=20.0) as client:
        r = client.get(f"{api_base}/vendas/")
        r.raise_for_status()
        return r.json() or []


def fetch_local_unsynced_sales(conn):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, data_venda, total, desconto_aplicado_divida, forma_pagamento, status, uuid
        FROM vendas
        WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND TRIM(uuid) <> ''
          AND (status IS NULL OR status != 'Anulada')
        ORDER BY id
        """
    )
    return cur.fetchall()


def build_venda_payload(conn, venda_row):
    v_id, data_venda, total, desconto, forma_pagamento, status, uuid_val = venda_row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT produto_id, quantidade, preco_unitario, subtotal, COALESCE(peso_kg, 0) as peso_kg
        FROM itens_venda WHERE venda_id = ?
        """,
        (v_id,),
    )
    itens = cur.fetchall()

    itens_data = []
    for (produto_id_local, quantidade, preco_unitario, subtotal, peso_kg) in itens:
        # get product uuid (server id)
        cur.execute("SELECT uuid, codigo FROM produtos WHERE id = ?", (produto_id_local,))
        rowp = cur.fetchone()
        if not rowp or not rowp[0]:
            raise RuntimeError(f"Produto local id={produto_id_local} sem UUID para venda {v_id}")
        produto_uuid, codigo = rowp

        qtd_raw = float(quantidade or 0.0)
        qtd_int = int(qtd_raw) if qtd_raw >= 1 else 1  # backend exige inteiro > 0
        peso_val = float(peso_kg or 0.0)
        if abs(qtd_raw - int(qtd_raw)) > 1e-6 and peso_val <= 0.0:
            peso_val = round(qtd_raw - int(qtd_raw), 3)

        item_payload = {
            "produto_id": str(produto_uuid),
            "quantidade": qtd_int,
            "preco_unitario": float(preco_unitario or 0.0),
            "subtotal": float(subtotal or 0.0),
        }
        if peso_val > 0:
            item_payload["peso_kg"] = peso_val
        itens_data.append(item_payload)

    venda_payload = {
        "uuid": uuid_val,
        "total": float(total or 0.0),
        "desconto": float(desconto or 0.0),
        "forma_pagamento": forma_pagamento or "Dinheiro",
        "itens": itens_data,
    }
    return venda_payload


def main():
    if not db_path.exists():
        print(f"[ERRO] Banco local não encontrado: {db_path}")
        return

    with sqlite3.connect(str(db_path)) as conn:
        server_sales = fetch_server_sales()
        server_ids = {str(s.get('id')) for s in server_sales if s.get('id')}
        print(f"Servidor: {len(server_ids)} vendas")

        unsynced = fetch_local_unsynced_sales(conn)
        print(f"Locais não sincronizadas: {len(unsynced)}")

        to_push = []
        for venda_row in unsynced:
            v_uuid = venda_row[6]
            if v_uuid and str(v_uuid) in server_ids:
                # já existe no servidor, marcar como sync
                conn.execute("UPDATE vendas SET synced = 1 WHERE id = ?", (venda_row[0],))
                continue
            to_push.append(venda_row)

        print(f"Enviar para servidor: {len(to_push)}")

        ok, fail = 0, 0
        with httpx.Client(timeout=20.0) as client:
            for venda_row in to_push:
                try:
                    payload = build_venda_payload(conn, venda_row)
                    resumo = {
                        'uuid': payload.get('uuid'),
                        'total': payload.get('total'),
                        'itens': len(payload.get('itens') or []),
                    }
                    print(f"[POST] Venda {venda_row[0]} -> {resumo}")
                    r = client.post(f"{api_base}/vendas/", json=payload)
                    if r.status_code in (200, 201):
                        conn.execute("UPDATE vendas SET synced = 1 WHERE id = ?", (venda_row[0],))
                        conn.commit()
                        ok += 1
                        print(f"[OK] Venda {venda_row[0]} sincronizada")
                    elif r.status_code == 409:
                        conn.execute("UPDATE vendas SET synced = 1 WHERE id = ?", (venda_row[0],))
                        conn.commit()
                        ok += 1
                        print(f"[OK] Venda {venda_row[0]} já existia no servidor (409)")
                    else:
                        fail += 1
                        detail = None
                        try:
                            j = r.json()
                            if isinstance(j, dict):
                                detail = j.get('detail')
                        except Exception:
                            pass
                        print(f"[ERRO] Venda {venda_row[0]} HTTP {r.status_code}: {r.text}")
                        if detail:
                            print(f"        detail: {detail}")
                except Exception as e:
                    fail += 1
                    print(f"[EXC] Falha ao enviar venda {venda_row[0]}: {e}")
        print(f"Concluído. Sucesso: {ok} | Falhas: {fail}")


if __name__ == "__main__":
    main()
