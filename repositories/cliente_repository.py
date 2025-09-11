import sqlite3
import httpx
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import os
import json
from utils.migration_helper import MigrationHelper

class ClienteRepository:
    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or self._get_backend_url()
        # Base normalizada da API: garante exatamente um sufixo /api
        self.api_base = self._make_api_base(self.backend_url)
        self.db_path = self._get_database_path()
        self._ensure_migration()
        self._ensure_change_log_table()
    
    def _get_backend_url(self) -> str:
        """Obtém a URL do backend do arquivo de configuração."""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('server_url', 'http://localhost:8000')
        except Exception:
            pass
        return os.getenv("BACKEND_URL", "http://localhost:8000")

    def _make_api_base(self, base_url: str) -> str:
        """Normaliza a base da API para conter exatamente um /api no final."""
        if base_url.endswith('/api'):
            return base_url
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        return base_url + '/api'
    
    def _get_database_path(self) -> Path:
        """Obtém o caminho do banco de dados unificado com Database (APPDATA no Windows)."""
        try:
            import platform, os
            from pathlib import Path as _Path
            sistema = platform.system().lower()
            if sistema == 'windows' and 'APPDATA' in os.environ:
                app_data_db_dir = _Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
            else:
                app_data_db_dir = _Path(os.path.expanduser('~')) / '.sistemagestao' / 'database'
            app_data_db_dir.mkdir(parents=True, exist_ok=True)
            return app_data_db_dir / 'sistema.db'
        except Exception:
            # Fallback para o caminho antigo do projeto (evitar crash)
            return Path(__file__).parent.parent / 'database' / 'sistema.db'
    
    def _is_online(self) -> bool:
        """Verifica se o backend está online (versão síncrona)."""
        try:
            response = httpx.get(f"{self.backend_url}/healthz", timeout=3.0)
            return response.status_code == 200
        except:
            return False
    
    async def is_backend_online(self) -> bool:
        """Versão assíncrona para verificar se o backend está online."""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
                    url1 = f"{self.backend_url}/healthz"
                    try:
                        resp1 = await client.get(url1)
                        if resp1.status_code == 200:
                            return True
                    except Exception:
                        pass

                    if self.backend_url.endswith('/api'):
                        base_url = self.backend_url[:-4]
                        url2 = f"{base_url}/healthz"
                        try:
                            resp2 = await client.get(url2)
                            if resp2.status_code == 200:
                                return True
                        except Exception:
                            pass
            except Exception:
                pass

            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(1)

        return False
    
    def _ensure_migration(self):
        """Garante que as colunas de sincronização existam na tabela clientes."""
        try:
            migration_helper = MigrationHelper()
            if migration_helper.check_migration_needed():
                print("[CLIENTE_REPO] Executando migração automática...")
                migration_helper.migrate_clientes_table()
        except Exception as e:
            print(f"[CLIENTE_REPO] Erro durante migração: {e}")
        # Garantir que a tabela clientes exista mesmo sem MigrationHelper
        try:
            self._ensure_clientes_table()
        except Exception as ee:
            print(f"[CLIENTE_REPO] Aviso ao garantir tabela clientes: {ee}")

    def _ensure_clientes_table(self):
        """Garante a existência da tabela clientes no SQLite atual."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE,
                    nome TEXT NOT NULL,
                    nuit TEXT,
                    telefone TEXT,
                    email TEXT,
                    endereco TEXT,
                    especial INTEGER DEFAULT 0,
                    desconto_divida REAL DEFAULT 0,
                    synced INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Obtém todos os clientes (híbrido: servidor primeiro, fallback local)."""
        if self._is_online():
            try:
                response = httpx.get(f"{self.api_base}/clientes/", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Erro ao buscar clientes do servidor: {e}")
        
        # Fallback para dados locais
        return self._get_all_local()
    
    def _get_all_local(self) -> List[Dict[str, Any]]:
        """Obtém todos os clientes do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome, nuit, telefone, email, endereco, especial, desconto_divida,
                       created_at, updated_at, 
                       COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                FROM clientes 
                ORDER BY nome
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_id(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        """Obtém cliente por ID (híbrido)."""
        if self._is_online():
            try:
                # Buscar UUID do cliente local
                cliente_local = self._get_local_cliente_by_id(cliente_id)
                if cliente_local and cliente_local.get('uuid'):
                    response = httpx.get(
                        f"{self.api_base}/clientes/{cliente_local['uuid']}", 
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        return response.json()
            except Exception as e:
                print(f"Erro ao buscar cliente do servidor: {e}")
        
        # Fallback para dados locais
        return self._get_local_cliente_by_id(cliente_id)
    
    def _get_local_cliente_by_id(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        """Obtém cliente por ID do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome, nuit, telefone, email, endereco, especial, desconto_divida,
                       created_at, updated_at, 
                       COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                FROM clientes 
                WHERE id = ?
            """, (cliente_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create(self, cliente_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cria novo cliente (híbrido)."""
        # Gerar UUID se não existir
        if 'uuid' not in cliente_data or not cliente_data['uuid']:
            cliente_data['uuid'] = str(uuid.uuid4())
        
        # Tentar criar no servidor primeiro
        if self._is_online():
            try:
                # Mapear payload para o backend: 'id' = uuid
                server_payload = {
                    "id": cliente_data['uuid'],
                    "nome": cliente_data['nome'],
                    "documento": cliente_data.get('nuit') or cliente_data.get('documento'),
                    "telefone": cliente_data.get('telefone', ''),
                    "endereco": cliente_data.get('endereco', ''),
                    "ativo": True,
                }
                response = httpx.post(f"{self.api_base}/clientes/", json=server_payload, timeout=5.0)
                if response.status_code in [200, 201]:
                    cliente_data['synced'] = 1
                    server_cliente = response.json()
                    # Backend retorna 'id' como UUID -> garantir refleto em uuid
                    if server_cliente.get('id'):
                        cliente_data['uuid'] = server_cliente['id']
                    # Espelhar outros campos que façam sentido
                    print("Cliente criado no servidor com sucesso")
                elif response.status_code in (409, 500) and 'duplicate key value violates unique constraint' in response.text:
                    # Já existe no servidor com esse UUID -> considerar sincronizado
                    cliente_data['synced'] = 1
                    print("[CLIENTES][CREATE] Duplicado no servidor, marcando como sincronizado")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao criar cliente no servidor: {e}")
        else:
            print("Backend offline, cliente sera criado apenas localmente")
        
        # Sempre criar localmente
        cliente_criado = self._create_local_cliente(cliente_data)
        
        # Log para sincronização se não foi sincronizado
        if cliente_data.get('synced', 0) == 0:
            self._log_change(cliente_data['uuid'], 'CREATE', cliente_data)
        
        return cliente_criado
    
    def _create_local_cliente(self, cliente_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria cliente no banco local."""
        # Garantir tabela antes de inserir
        try:
            self._ensure_clientes_table()
        except Exception:
            pass
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clientes (nome, nuit, telefone, email, endereco, especial, 
                                    desconto_divida, created_at, updated_at, uuid, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_data['nome'],
                cliente_data.get('nuit', ''),
                cliente_data.get('telefone', ''),
                cliente_data.get('email', ''),
                cliente_data.get('endereco', ''),
                cliente_data.get('especial', 0),
                cliente_data.get('desconto_divida', 0.0),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                cliente_data['uuid'],
                cliente_data.get('synced', 0)
            ))
            
            cliente_id = cursor.lastrowid
            conn.commit()
            
            # Retornar cliente criado
            return self._get_local_cliente_by_id(cliente_id)
    
    def update(self, cliente_id: int, cliente_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualiza cliente (híbrido)."""
        # Obter UUID do cliente local
        cliente_local = self._get_local_cliente_by_id(cliente_id)
        if not cliente_local:
            return None
        
        cliente_uuid = cliente_local['uuid']
        
        # Tentar atualizar no servidor
        if self._is_online():
            try:
                response = httpx.put(
                    f"{self.api_base}/clientes/{cliente_uuid}",
                    json=cliente_data,
                    timeout=5.0
                )
                if response.status_code == 200:
                    cliente_data['synced'] = 1
                    server_cliente = response.json()
                    cliente_data.update(server_cliente)
                    print("Cliente atualizado no servidor com sucesso")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao atualizar cliente no servidor: {e}")
        else:
            print("Backend offline, cliente sera atualizado apenas localmente")
        
        # Sempre atualizar localmente
        cliente_atualizado = self._update_local_cliente(cliente_id, cliente_data)
        
        # Log para sincronização se não foi sincronizado
        if cliente_data.get('synced', 0) == 0:
            self._log_change(cliente_uuid, 'UPDATE', cliente_data)
        
        return cliente_atualizado
    
    def _update_local_cliente(self, cliente_id: int, cliente_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza cliente no banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clientes 
                SET nome = ?, nuit = ?, telefone = ?, email = ?, endereco = ?, 
                    especial = ?, desconto_divida = ?, updated_at = ?, synced = ?
                WHERE id = ?
            """, (
                cliente_data['nome'],
                cliente_data.get('nuit', ''),
                cliente_data.get('telefone', ''),
                cliente_data.get('email', ''),
                cliente_data.get('endereco', ''),
                cliente_data.get('especial', 0),
                cliente_data.get('desconto_divida', 0.0),
                datetime.now().isoformat(),
                cliente_data.get('synced', 0),
                cliente_id
            ))
            conn.commit()
            
            # Retornar cliente atualizado
            return self._get_local_cliente_by_id(cliente_id)
    
    def delete(self, cliente_id: int) -> bool:
        """Deleta cliente (hard delete híbrido)."""
        cliente_local = self._get_local_cliente_by_id(cliente_id)
        if not cliente_local:
            return False
        
        cliente_uuid = cliente_local['uuid']
        
        # Tentar deletar no servidor
        if self._is_online():
            try:
                response = httpx.delete(
                    f"{self.api_base}/clientes/{cliente_uuid}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    print("Cliente deletado no servidor com sucesso")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao deletar cliente no servidor: {e}")
        
        # Sempre deletar localmente
        success = self._delete_local_cliente(cliente_id)
        
        # Log para sincronização
        if success:
            self._log_change(cliente_uuid, 'DELETE', {})
        
        return success
    
    def _delete_local_cliente(self, cliente_id: int) -> bool:
        """Deleta cliente do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
    
    def _log_change(self, entity_id: str, operation: str, data: Dict[Any, Any]):
        """Registra mudança no change_log para sincronização posterior."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO change_log (entity_type, entity_id, operation, data_json, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'clientes',
                entity_id,
                operation,
                json.dumps(data),
                datetime.now().isoformat(),
                'pending'
            ))
            conn.commit()
    
    def _ensure_change_log_table(self):
        """Garante que a tabela change_log existe."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS change_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    data_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    status TEXT DEFAULT 'pending'
                )
            """)
            conn.commit()
    
    async def sincronizar_mudancas(self) -> Dict[str, Any]:
        """Sincroniza mudanças bidirecionalmente com o servidor."""
        print("=== INICIANDO SINCRONIZACAO BIDIRECIONAL DE CLIENTES ===")
        
        # Verificar conectividade
        if not await self.is_backend_online():
            return {
                "status": "offline",
                "message": "Backend offline - operando localmente",
                "enviadas": 0,
                "recebidas": 0,
                "mudancas_pendentes": 0
            }
        
        try:
            # Heurística de primeira sincronização: se houver clientes locais pendentes, priorizar PUSH primeiro
            clientes_recebidos = 0
            clientes_antigos_enviados = 0
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT COUNT(*) FROM clientes 
                        WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND TRIM(uuid) <> ''
                    """)
                    pendentes = cur.fetchone()[0]
            except Exception:
                pendentes = 0

            if pendentes > 0:
                clientes_antigos_enviados = await self._sincronizar_clientes_antigos()
                clientes_recebidos = await self._pull_clientes_do_servidor()
            else:
                clientes_recebidos = await self._pull_clientes_do_servidor()
                clientes_antigos_enviados = await self._sincronizar_clientes_antigos()

            # FASE 3: Push - enviar mudanças pendentes
            mudancas = await self._obter_mudancas_pendentes()
            mudancas_enviadas = 0

            print(f"FASE 3: Enviando mudancas pendentes de clientes...")
            print(f"Encontradas {len(mudancas)} mudancas pendentes de clientes")

            if len(mudancas) == 0:
                print("Nenhuma sincronizacao necessaria para clientes")
            else:
                async with httpx.AsyncClient() as client:
                    for ch in mudancas:
                        try:
                            op = ch['operation']
                            data = json.loads(ch['data_json']) if ch.get('data_json') else {}
                            entity_uuid = ch['entity_id']
                            if op == 'CREATE':
                                # Mapear payload para o backend
                                payload = {
                                    "id": data.get('uuid') or data.get('id'),
                                    "nome": data.get('nome'),
                                    "documento": data.get('nuit') or data.get('documento'),
                                    "telefone": data.get('telefone', ''),
                                    "endereco": data.get('endereco', ''),
                                    "ativo": True,
                                }
                                resp = await client.post(f"{self.api_base}/clientes/", json=payload, timeout=8.0)
                                print(f"[CLIENTES][CREATE] status: {resp.status_code}")
                                if resp.status_code in (200, 201):
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                                    # Marcar local como sincronizado
                                    try:
                                        with sqlite3.connect(str(self.db_path)) as conn:
                                            cur2 = conn.cursor()
                                            cur2.execute("UPDATE clientes SET synced = 1, updated_at = CURRENT_TIMESTAMP WHERE uuid = ?", (payload.get('id'),))
                                            conn.commit()
                                    except Exception:
                                        pass
                                elif resp.status_code == 409 or (resp.status_code == 500 and 'duplicate key value violates unique constraint' in (await resp.text())):
                                    # Já existe no servidor: marcar como sincronizada e local synced
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                                    try:
                                        with sqlite3.connect(str(self.db_path)) as conn:
                                            cur2 = conn.cursor()
                                            cur2.execute("UPDATE clientes SET synced = 1, updated_at = CURRENT_TIMESTAMP WHERE uuid = ?", (payload.get('id'),))
                                            conn.commit()
                                    except Exception:
                                        pass
                                else:
                                    print(f"[CLIENTES][CREATE] erro: {resp.text}")
                            elif op == 'UPDATE':
                                # Mapear payload para o backend (id no path)
                                payload = {
                                    "nome": data.get('nome'),
                                    "documento": data.get('nuit') or data.get('documento'),
                                    "telefone": data.get('telefone', ''),
                                    "endereco": data.get('endereco', ''),
                                    "ativo": data.get('ativo', True),
                                }
                                entity_id = data.get('uuid') or entity_uuid
                                resp = await client.put(f"{self.api_base}/clientes/{entity_id}", json=payload, timeout=8.0)
                                print(f"[CLIENTES][UPDATE] status: {resp.status_code}")
                                if resp.status_code == 200:
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                                elif resp.status_code == 404:
                                    # Tentar criar com o mesmo UUID
                                    create_payload = {
                                        "id": entity_id,
                                        "nome": data.get('nome'),
                                        "documento": data.get('nuit') or data.get('documento'),
                                        "telefone": data.get('telefone', ''),
                                        "endereco": data.get('endereco', ''),
                                        "ativo": True,
                                    }
                                    post = await client.post(f"{self.api_base}/clientes/", json=create_payload, timeout=8.0)
                                    print(f"[CLIENTES][UPDATE->CREATE] status: {post.status_code}")
                                    if post.status_code in (200, 201):
                                        self._mark_change_synced(ch['id'])
                                        mudancas_enviadas += 1
                                else:
                                    print(f"[CLIENTES][UPDATE] erro: {resp.text}")
                            elif op == 'DELETE':
                                resp = await client.delete(f"{self.api_base}/clientes/{entity_uuid}", timeout=8.0)
                                print(f"[CLIENTES][DELETE] status: {resp.status_code}")
                                if resp.status_code in (200, 204, 404):
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                            else:
                                print(f"[CLIENTES] Operacao nao suportada: {op}")
                        except Exception as e:
                            print(f"[CLIENTES] Erro ao processar mudança pendente {ch.get('id')}: {e}")
            
            return {
                "status": "success",
                "message": f"Sincronização de clientes concluída. {clientes_antigos_enviados} clientes antigos enviados, {mudancas_enviadas} mudanças enviadas.",
                "enviadas": clientes_antigos_enviados + mudancas_enviadas,
                "recebidas": clientes_recebidos,
                "mudancas_pendentes": len(mudancas)
            }
            
        except Exception as e:
            print(f"Erro na sincronização de clientes: {e}")
            return {
                "status": "error",
                "message": f"Erro na sincronização: {str(e)}",
                "enviadas": 0,
                "recebidas": 0,
                "mudancas_pendentes": 0
            }
    
    async def _sincronizar_clientes_antigos(self) -> int:
        """Sincroniza clientes antigos não sincronizados com o servidor."""
        print("FASE 2: Enviando clientes antigos...")
        print("Verificando clientes antigos nao sincronizados...")
        
        # Primeiro verificar se o servidor tem clientes
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/clientes/", timeout=5.0)
                clientes_servidor = response.json() if response.status_code == 200 else []
                servidor_vazio = len(clientes_servidor) == 0
        except Exception:
            servidor_vazio = False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se a tabela clientes existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
            if not cursor.fetchone():
                print("Tabela clientes não encontrada - executando migração...")
                from utils.migration_helper import MigrationHelper
                migration_helper = MigrationHelper()
                migration_helper.migrate_clientes_table()
            
            if servidor_vazio:
                # Se servidor vazio, sincronizar TODOS os clientes locais
                print("Servidor vazio - sincronizando TODOS os clientes locais...")
                cursor.execute("""
                    SELECT id, nome, telefone, endereco, uuid, created_at, updated_at
                    FROM clientes 
                    WHERE uuid IS NOT NULL AND uuid != ''
                """)
            else:
                # Se servidor tem dados, sincronizar apenas não sincronizados
                cursor.execute("""
                    SELECT id, nome, telefone, endereco, uuid, created_at, updated_at
                    FROM clientes 
                    WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND uuid != ''
                """)
            
            clientes_nao_sync = cursor.fetchall()
            
            if not clientes_nao_sync:
                print("Todos os clientes ja estao sincronizados")
                return 0
            
            print(f"Encontrados {len(clientes_nao_sync)} clientes nao sincronizados")
            
            enviados = 0
            async with httpx.AsyncClient() as client:
                for cliente in clientes_nao_sync:
                    try:
                        cliente_data = {
                            "uuid": cliente[4],
                            "nome": cliente[1],
                            "telefone": cliente[2] or "",
                            "endereco": cliente[3] or "",
                            "ativo": True
                        }
                        
                        print(f"Enviando cliente antigo: {cliente[1]}")
                        
                        # Tentar criar primeiro
                        response = await client.post(
                            f"{self.api_base}/clientes/",
                            json=cliente_data,
                            timeout=10.0
                        )
                        
                        if response.status_code in [200, 201]:
                            # Marcar como sincronizado
                            cursor.execute("""
                                UPDATE clientes 
                                SET synced = 1, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (cliente[0],))
                            conn.commit()
                            enviados += 1
                            print(f"Cliente {cliente[1]} sincronizado")
                            
                        elif response.status_code == 400 or response.status_code == 500:
                            # Cliente já existe, marcar como sincronizado
                            print(f"Cliente {cliente[1]} ja existe no servidor, marcando como sincronizado")
                            cursor.execute("""
                                UPDATE clientes 
                                SET synced = 1, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (cliente[0],))
                            conn.commit()
                            enviados += 1
                        else:
                            print(f"Erro ao enviar cliente: {response.status_code} - {response.text}")
                            
                    except Exception as e:
                        print(f"Erro ao processar cliente {cliente[1]}: {e}")
            
            conn.close()
            print(f"Sincronizacao de clientes antigos concluida: {enviados}/{len(clientes_nao_sync)} enviados")
            return enviados
            
        except Exception as e:
            print(f"Erro na sincronizacao de clientes antigos: {e}")
            return 0
    
    async def _obter_mudancas_pendentes(self) -> List[Dict[str, Any]]:
        """Obtém mudanças pendentes de clientes."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, entity_type, entity_id, operation, data_json, created_at
                FROM change_log 
                WHERE entity_type = 'clientes' AND status = 'pending'
                ORDER BY created_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def _mark_change_synced(self, change_id: int):
        """Marca mudança como sincronizada."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE change_log 
                SET status = 'synced', updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), change_id))
            conn.commit()
    
    def listar_todos(self) -> List[Dict[str, Any]]:
        """Lista todos os clientes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome, nuit, telefone, endereco, email, especial, desconto_divida, uuid, synced
                FROM clientes 
                ORDER BY nome
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def buscar_por_nome_ou_nuit(self, termo: str) -> List[Dict[str, Any]]:
        """Busca clientes por nome ou NUIT."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome, nuit, telefone, endereco, email, especial, desconto_divida, uuid, synced
                FROM clientes 
                WHERE LOWER(nome) LIKE ? OR LOWER(nuit) LIKE ?
                ORDER BY nome
            """, (f"%{termo.lower()}%", f"%{termo.lower()}%"))
            return [dict(row) for row in cursor.fetchall()]
    
    async def _pull_clientes_do_servidor(self) -> int:
        """Busca clientes do servidor e atualiza localmente."""
        print("FASE 1: Buscando clientes do servidor...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/clientes/",
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    print(f"Erro ao buscar clientes do servidor: {response.status_code}")
                    return 0
                
                clientes_servidor = response.json()
                print(f"Encontrados {len(clientes_servidor)} clientes no servidor")
                
                clientes_recebidos = 0
                clientes_atualizados = 0
                
                for cliente_servidor in clientes_servidor:
                    try:
                        # Aceitar 'uuid' ou 'id' do servidor como UUID
                        server_uuid = (cliente_servidor.get('uuid') or cliente_servidor.get('id') or '').strip()
                        if not server_uuid:
                            nome_dbg = cliente_servidor.get('nome', 'N/A')
                            print(f"Cliente {nome_dbg} sem UUID/ID - pulando")
                            continue
                        
                        # Verificar se cliente já existe localmente pelo UUID
                        cliente_local = self._get_cliente_by_uuid(server_uuid)
                        
                        if cliente_local is None:
                            # Cliente novo - inserir localmente
                            # Forçar 'uuid' no payload local
                            cliente_servidor = {**cliente_servidor, 'uuid': server_uuid}
                            if self._inserir_cliente_do_servidor(cliente_servidor):
                                clientes_recebidos += 1
                                print(f"Cliente novo inserido: {cliente_servidor.get('nome','(sem nome)')}")
                        else:
                            # Cliente existe - verificar se precisa atualizar
                            if self._cliente_servidor_mais_recente(cliente_local, cliente_servidor):
                                # Garantir 'uuid' no payload
                                cliente_servidor = {**cliente_servidor, 'uuid': server_uuid}
                                if self._atualizar_cliente_do_servidor(cliente_local['id'], cliente_servidor):
                                    clientes_atualizados += 1
                                    print(f"Cliente atualizado: {cliente_servidor.get('nome','(sem nome)')}")
                    
                    except Exception as e:
                        print(f"Erro ao processar cliente {cliente_servidor.get('nome', 'N/A')}: {e}")
                
                total_recebidos = clientes_recebidos + clientes_atualizados
                print(f"Pull de clientes concluído: {clientes_recebidos} novos, {clientes_atualizados} atualizados")
                return total_recebidos
                
        except Exception as e:
            print(f"Erro no pull de clientes: {e}")
            return 0
    
    def _get_cliente_by_uuid(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Busca cliente pelo UUID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clientes WHERE uuid = ?", (uuid,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _inserir_cliente_do_servidor(self, cliente_data: Dict[str, Any]) -> bool:
        """Insere cliente recebido do servidor."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO clientes (nome, telefone, endereco, uuid, synced, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    cliente_data['nome'],
                    cliente_data.get('telefone', ''),
                    cliente_data.get('endereco', ''),
                    cliente_data['uuid']
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao inserir cliente do servidor: {e}")
            return False
    
    def _cliente_servidor_mais_recente(self, cliente_local: Dict, cliente_servidor: Dict) -> bool:
        """Verifica se o cliente do servidor é mais recente."""
        # Por simplicidade, sempre considerar servidor mais recente
        return True
    
    def _atualizar_cliente_do_servidor(self, cliente_id: int, cliente_data: Dict[str, Any]) -> bool:
        """Atualiza cliente local com dados do servidor."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE clientes 
                    SET nome = ?, telefone = ?, endereco = ?, synced = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    cliente_data['nome'],
                    cliente_data.get('telefone', ''),
                    cliente_data.get('endereco', ''),
                    cliente_id
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao atualizar cliente do servidor: {e}")
            return False
