"""
Repositório para entidade Produtos com fallback local/servidor.
Implementa padrão Repository com sincronização híbrida.
"""
import sqlite3
import uuid
import json
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import platform
from utils.migration_helper import MigrationHelper

class ProdutoRepository:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.db_path = self._get_database_path()
        self._ensure_migration()
        
    def _get_database_path(self):
        """Obtém o caminho do banco de dados SQLite local."""
        sistema = platform.system().lower()
        if sistema == 'windows' and 'APPDATA' in os.environ:
            app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
        else:
            app_data_db_dir = Path(os.path.expanduser('~')) / '.sistemagestao' / 'database'
        
        app_data_db_dir.mkdir(parents=True, exist_ok=True)
        return app_data_db_dir / 'sistema.db'
    
    def _is_online(self) -> bool:
        """Verifica se o backend está online."""
        try:
            response = httpx.get(f"{self.backend_url}/healthz", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    def _ensure_migration(self):
        """Garante que as colunas de sincronização existam na tabela produtos."""
        try:
            migration_helper = MigrationHelper()
            if migration_helper.check_migration_needed():
                print("[PRODUTO_REPO] Executando migração automática...")
                migration_helper.migrate_produtos_table()
        except Exception as e:
            print(f"[PRODUTO_REPO] Erro durante migração: {e}")
    
    async def is_backend_online(self) -> bool:
        """Versão assíncrona para verificar se o backend está online."""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"Testando conexão com: {self.backend_url}/healthz (tentativa {attempt + 1})")
                async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
                    response = await client.get(f"{self.backend_url}/healthz")
                    print(f"Status da resposta: {response.status_code}")
                    if response.status_code == 200:
                        print(f"Backend online - {response.json().get('status', 'ok')}")
                        return True
                    else:
                        print(f"Backend retornou status {response.status_code}")
            except httpx.TimeoutException as e:
                print(f"Timeout na tentativa {attempt + 1}: {e}")
            except httpx.ConnectError as e:
                print(f"Erro de conexao na tentativa {attempt + 1}: {e}")
            except Exception as e:
                print(f"Erro inesperado na tentativa {attempt + 1}: {type(e).__name__}: {e}")
            
            if attempt < max_retries - 1:
                print("Tentando novamente em 1 segundo...")
                import asyncio
                await asyncio.sleep(1)
        
        print("Backend offline apos todas as tentativas")
        return False
    
    def _log_change(self, entity_id: str, operation: str, data: Dict[Any, Any]):
        """Registra mudança no change_log para sincronização posterior."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO change_log (entity_type, entity_id, operation, data_json, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'produtos', 
                entity_id, 
                operation, 
                json.dumps(data), 
                datetime.now().isoformat(),
                'pending'
            ))
            conn.commit()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Obtém todos os produtos. Tenta servidor primeiro, fallback para local."""
        if self._is_online():
            try:
                response = httpx.get(f"{self.backend_url}/api/produtos/", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Erro ao buscar produtos do servidor: {e}")
        
        # Fallback para dados locais
        return self._get_all_local()
    
    def _get_all_local(self) -> List[Dict[str, Any]]:
        """Obtém todos os produtos do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar se as colunas uuid e synced existem
            cursor.execute("PRAGMA table_info(produtos)")
            columns = [col[1] for col in cursor.fetchall()]
            has_uuid = 'uuid' in columns
            has_synced = 'synced' in columns
            
            if has_uuid and has_synced:
                cursor.execute("""
                    SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                           estoque, estoque_minimo, categoria_id, venda_por_peso,
                           unidade_medida, ativo, created_at, updated_at,
                           COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                    FROM produtos 
                    WHERE ativo = 1
                    ORDER BY nome
                """)
            else:
                cursor.execute("""
                    SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                           estoque, estoque_minimo, categoria_id, venda_por_peso,
                           unidade_medida, ativo, created_at, updated_at
                    FROM produtos 
                    WHERE ativo = 1
                    ORDER BY nome
                """)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if not has_uuid:
                    result['uuid'] = ''
                if not has_synced:
                    result['synced'] = 0
                results.append(result)
            
            return results
    
    def get_by_id(self, produto_id: int) -> Optional[Dict[str, Any]]:
        """Obtém produto por ID. Tenta servidor primeiro, fallback para local."""
        if self._is_online():
            try:
                response = httpx.get(f"{self.backend_url}/api/produtos/{produto_id}", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Erro ao buscar produto do servidor: {e}")
        
        # Fallback para dados locais
        return self._get_local_produto_by_id(produto_id)
    
    def get_by_uuid(self, produto_uuid: str) -> Optional[Dict[str, Any]]:
        """Obtém produto por UUID. Tenta servidor primeiro, fallback para local."""
        if self._is_online():
            try:
                response = httpx.get(f"{self.backend_url}/api/produtos/{produto_uuid}", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Erro ao buscar produto do servidor: {e}")
        
        # Fallback para dados locais
        return self._get_local_produto_by_uuid(produto_uuid)
    
    def _get_local_produto_by_uuid(self, produto_uuid: str) -> Optional[Dict[str, Any]]:
        """Obtém produto por UUID do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar se as colunas uuid e synced existem
            cursor.execute("PRAGMA table_info(produtos)")
            columns = [col[1] for col in cursor.fetchall()]
            has_uuid = 'uuid' in columns
            has_synced = 'synced' in columns
            
            if has_uuid:
                if has_synced:
                    cursor.execute("""
                        SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                               estoque, estoque_minimo, categoria_id, venda_por_peso,
                               unidade_medida, ativo, created_at, updated_at,
                               COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                        FROM produtos 
                        WHERE uuid = ? AND ativo = 1
                    """, (produto_uuid,))
                else:
                    cursor.execute("""
                        SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                               estoque, estoque_minimo, categoria_id, venda_por_peso,
                               unidade_medida, ativo, created_at, updated_at, uuid
                        FROM produtos 
                        WHERE uuid = ? AND ativo = 1
                    """, (produto_uuid,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    if not has_synced:
                        result['synced'] = 0
                    return result
            
            return None
    
    def _get_local_produto_by_id(self, produto_id: int) -> Optional[Dict[str, Any]]:
        """Obtém produto por ID do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar se as colunas uuid e synced existem
            cursor.execute("PRAGMA table_info(produtos)")
            columns = [col[1] for col in cursor.fetchall()]
            has_uuid = 'uuid' in columns
            has_synced = 'synced' in columns
            
            if has_uuid and has_synced:
                cursor.execute("""
                    SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                           estoque, estoque_minimo, categoria_id, venda_por_peso,
                           unidade_medida, ativo, created_at, updated_at,
                           COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                    FROM produtos 
                    WHERE id = ? AND ativo = 1
                """, (produto_id,))
            else:
                cursor.execute("""
                    SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                           estoque, estoque_minimo, categoria_id, venda_por_peso,
                           unidade_medida, ativo, created_at, updated_at
                    FROM produtos 
                    WHERE id = ? AND ativo = 1
                """, (produto_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if not has_uuid:
                    result['uuid'] = ''
                if not has_synced:
                    result['synced'] = 0
                return result
            return None
    
    def create(self, produto_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria novo produto. Tenta servidor primeiro, sempre salva local."""
        # Gerar UUID se não existir
        if 'uuid' not in produto_data:
            produto_data['uuid'] = str(uuid.uuid4())
        
        produto_data['created_at'] = datetime.now().isoformat()
        produto_data['updated_at'] = produto_data['created_at']
        produto_data['synced'] = 0
        
        # Tentar criar no servidor primeiro
        if self._is_online():
            try:
                response = httpx.post(
                    f"{self.backend_url}/api/produtos", 
                    json=produto_data,
                    timeout=5.0
                )
                if response.status_code == 201:
                    produto_data['synced'] = 1
                    server_produto = response.json()
                    # Usar dados do servidor se disponível
                    produto_data.update(server_produto)
            except Exception as e:
                print(f"Erro ao criar produto no servidor: {e}")
        
        # Sempre salvar localmente
        produto_local = self._create_local_produto(produto_data)
        
        # Log para sincronização se não foi sincronizado
        if produto_data['synced'] == 0:
            self._log_change(produto_data['uuid'], 'CREATE', produto_data)
        
        return produto_local
    
    def _create_local_produto(self, produto_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria produto no banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO produtos (codigo, nome, descricao, preco_custo, preco_venda,
                                    estoque, estoque_minimo, categoria_id, venda_por_peso,
                                    unidade_medida, ativo, uuid, created_at, updated_at, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                produto_data.get('codigo', ''),
                produto_data['nome'],
                produto_data.get('descricao', ''),
                produto_data.get('preco_custo', 0),
                produto_data.get('preco_venda', 0),
                produto_data.get('estoque', 0),
                produto_data.get('estoque_minimo', 0),
                produto_data.get('categoria_id', None),
                produto_data.get('venda_por_peso', False),
                produto_data.get('unidade_medida', 'un'),
                1,  # ativo
                produto_data['uuid'],
                produto_data['created_at'],
                produto_data['updated_at'],
                produto_data['synced']
            ))
            
            produto_id = cursor.lastrowid
            conn.commit()
            
            # Retornar produto criado
            produto_data['id'] = produto_id
            return produto_data
    
    def update(self, produto_id: int, produto_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualiza produto. Tenta servidor primeiro, sempre atualiza local."""
        produto_data['updated_at'] = datetime.now().isoformat()
        produto_data['synced'] = 0
        
        # Obter UUID do produto local
        produto_local = self._get_local_produto_by_id(produto_id)
        if not produto_local:
            return None
        
        produto_uuid = produto_local['uuid']
        
        # Tentar atualizar no servidor
        if self._is_online():
            try:
                print(f"Tentando atualizar produto {produto_uuid} no servidor...")
                response = httpx.put(
                    f"{self.backend_url}/api/produtos/{produto_uuid}",
                    json=produto_data,
                    timeout=5.0
                )
                print(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    produto_data['synced'] = 1
                    server_produto = response.json()
                    produto_data.update(server_produto)
                    print(f"Produto atualizado no servidor com sucesso")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao atualizar produto no servidor: {e}")
        else:
            print(f"Backend offline, produto sera atualizado apenas localmente")
        
        # Sempre atualizar localmente
        produto_atualizado = self._update_local_produto(produto_id, produto_data)
        
        # Log para sincronização se não foi sincronizado
        if produto_data['synced'] == 0:
            print(f"Registrando mudanca UPDATE para produto {produto_uuid}")
            self._log_change(produto_uuid, 'UPDATE', produto_data)
        else:
            print(f"Produto {produto_uuid} ja sincronizado, nao registrando mudanca")
        
        return produto_atualizado
    
    def _update_local_produto(self, produto_id: int, produto_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza produto no banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE produtos 
                SET codigo = ?, nome = ?, descricao = ?, preco_custo = ?, preco_venda = ?,
                    estoque = ?, estoque_minimo = ?, categoria_id = ?, venda_por_peso = ?,
                    unidade_medida = ?, updated_at = ?, synced = ?
                WHERE id = ?
            """, (
                produto_data.get('codigo', ''),
                produto_data['nome'],
                produto_data.get('descricao', ''),
                produto_data.get('preco_custo', 0),
                produto_data.get('preco_venda', 0),
                produto_data.get('estoque', 0),
                produto_data.get('estoque_minimo', 0),
                produto_data.get('categoria_id', None),
                produto_data.get('venda_por_peso', False),
                produto_data.get('unidade_medida', 'un'),
                produto_data['updated_at'],
                produto_data['synced'],
                produto_id
            ))
            conn.commit()
            
            # Retornar produto atualizado
            return self._get_local_produto_by_id(produto_id)
    
    def delete(self, produto_id: int) -> bool:
        """Deleta produto (soft delete). Tenta servidor primeiro, sempre deleta local."""
        # Obter produto local para UUID
        produto_local = self._get_local_produto_by_id(produto_id)
        if not produto_local:
            return False
        
        produto_uuid = produto_local['uuid']
        synced = 0
        
        # Tentar deletar no servidor
        if self._is_online():
            try:
                response = httpx.delete(
                    f"{self.backend_url}/api/produtos/{produto_uuid}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    synced = 1
            except Exception as e:
                print(f"Erro ao deletar produto no servidor: {e}")
        
        # Sempre fazer soft delete local
        success = self._delete_local_produto(produto_id, synced)
        
        # Log para sincronização se não foi sincronizado
        if synced == 0:
            self._log_change(produto_uuid, 'DELETE', {'id': produto_id})
        
        return success
    
    async def listar_produtos(self) -> List[Dict[str, Any]]:
        """Lista todos os produtos (versão async)."""
        return self.get_all()
    
    async def criar_produto(self, produto_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria produto (versão async)."""
        return self.create(produto_data)
    
    async def buscar_produto(self, produto_uuid: str) -> Optional[Dict[str, Any]]:
        """Busca produto por UUID (versão async)."""
        return self.get_by_uuid(produto_uuid)
    
    async def atualizar_produto(self, produto_uuid: str, produto_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza produto (versão async)."""
        # Buscar produto local por UUID para obter ID
        produto_local = self.get_by_uuid(produto_uuid)
        if not produto_local:
            raise ValueError(f"Produto com UUID {produto_uuid} não encontrado")
        
        return self.update(produto_local['id'], produto_data)
    
    async def obter_mudancas_pendentes(self) -> List[Dict[str, Any]]:
        """Obtém mudanças pendentes de sincronização."""
        # Garantir que a tabela change_log existe
        self._ensure_change_log_table()
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM change_log 
                WHERE status = 'pending' 
                ORDER BY created_at DESC
            """)
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
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
            print("Tabela change_log criada/verificada")
    
    async def sincronizar_mudancas(self) -> Dict[str, Any]:
        """Sincroniza mudanças bidirecionalmente com o servidor."""
        print("=== INICIANDO SINCRONIZACAO BIDIRECIONAL ===")
        
        if not await self.is_backend_online():
            print("Backend offline, cancelando sincronizacao")
            return {"status": "offline", "message": "Backend offline"}
        
        try:
            # FASE 1: PULL - Buscar dados novos/atualizados do servidor
            print("FASE 1: Buscando dados do servidor...")
            produtos_recebidos = await self._pull_produtos_do_servidor()
            
            # FASE 2: PUSH - Enviar produtos antigos não sincronizados
            print("FASE 2: Enviando produtos antigos...")
            produtos_antigos_enviados = await self._sincronizar_produtos_antigos()
            
            # FASE 3: PUSH - Enviar mudanças pendentes
            print("FASE 3: Enviando mudancas pendentes...")
            mudancas = await self.obter_mudancas_pendentes()
            print(f"Encontradas {len(mudancas)} mudancas pendentes")
            
            if len(mudancas) == 0 and produtos_antigos_enviados == 0 and produtos_recebidos == 0:
                print("Nenhuma sincronizacao necessaria")
                return {
                    "status": "success",
                    "enviadas": 0,
                    "recebidas": 0,
                    "message": "Sincronização concluída. Nenhuma mudança necessária."
                }
            
            enviadas = 0
            
            for mudanca in mudancas:
                try:
                    print(f"Processando mudanca {mudanca['operation']} para {mudanca['entity_id']}")
                    
                    # Processar mudança baseada na operação
                    if mudanca['operation'] == 'CREATE':
                        data = json.loads(mudanca['data_json'])
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                f"{self.backend_url}/api/produtos/",
                                json=data,
                                timeout=5.0
                            )
                            print(f"CREATE response: {response.status_code}")
                            if response.status_code in [200, 201]:
                                self._mark_change_synced(mudanca['id'])
                                enviadas += 1
                                print(f"Mudanca CREATE sincronizada")
                            else:
                                print(f"Erro CREATE: {response.text}")
                    
                    elif mudanca['operation'] == 'UPDATE':
                        data = json.loads(mudanca['data_json'])
                        async with httpx.AsyncClient() as client:
                            response = await client.put(
                                f"{self.backend_url}/api/produtos/{mudanca['entity_id']}",
                                json=data,
                                timeout=5.0
                            )
                            print(f"UPDATE response: {response.status_code}")
                            if response.status_code == 200:
                                self._mark_change_synced(mudanca['id'])
                                enviadas += 1
                                print(f"Mudanca UPDATE sincronizada")
                            elif response.status_code == 404:
                                # Produto não existe no servidor, verificar se existe produto com mesmo código
                                print(f"Produto nao encontrado, verificando codigo duplicado...")
                                
                                # Buscar produtos por código para evitar duplicação
                                list_response = await client.get(
                                    f"{self.backend_url}/api/produtos/",
                                    timeout=5.0
                                )
                                
                                produto_existente = None
                                if list_response.status_code == 200:
                                    produtos_servidor = list_response.json()
                                    for p in produtos_servidor:
                                        if p.get('codigo') == data.get('codigo'):
                                            produto_existente = p
                                            break
                                
                                if produto_existente:
                                    # Produto existe com mesmo código, fazer UPDATE no produto correto
                                    print(f"Encontrado produto com codigo {data.get('codigo')}, fazendo UPDATE...")
                                    update_response = await client.put(
                                        f"{self.backend_url}/api/produtos/{produto_existente['id']}",
                                        json=data,
                                        timeout=5.0
                                    )
                                    print(f"UPDATE por codigo response: {update_response.status_code}")
                                    if update_response.status_code == 200:
                                        self._mark_change_synced(mudanca['id'])
                                        enviadas += 1
                                        print(f"Mudanca UPDATE por codigo sincronizada")
                                    else:
                                        print(f"Erro UPDATE por codigo: {update_response.text}")
                                else:
                                    # Produto realmente não existe, criar novo
                                    print(f"Produto nao encontrado, tentando CREATE...")
                                    create_response = await client.post(
                                        f"{self.backend_url}/api/produtos/",
                                        json=data,
                                        timeout=5.0
                                    )
                                    print(f"CREATE fallback response: {create_response.status_code}")
                                    if create_response.status_code in [200, 201]:
                                        self._mark_change_synced(mudanca['id'])
                                        enviadas += 1
                                        print(f"Mudanca UPDATE->CREATE sincronizada")
                                    else:
                                        print(f"Erro CREATE fallback: {create_response.text}")
                            else:
                                print(f"Erro UPDATE: {response.text}")
                    
                    elif mudanca['operation'] == 'DELETE':
                        async with httpx.AsyncClient() as client:
                            response = await client.delete(
                                f"{self.backend_url}/api/produtos/{mudanca['entity_id']}",
                                timeout=5.0
                            )
                            print(f"DELETE response: {response.status_code}")
                            if response.status_code == 200:
                                self._mark_change_synced(mudanca['id'])
                                enviadas += 1
                                print(f"Mudanca DELETE sincronizada")
                            else:
                                print(f"Erro DELETE: {response.text}")
                                
                except Exception as e:
                    print(f"Erro ao sincronizar mudanca {mudanca['id']}: {e}")
            
            total_enviadas = produtos_antigos_enviados + enviadas
            print(f"=== SINCRONIZACAO CONCLUIDA ===")
            print(f"Produtos recebidos: {produtos_recebidos}")
            print(f"Produtos antigos enviados: {produtos_antigos_enviados}")
            print(f"Mudancas enviadas: {enviadas}")
            
            return {
                "status": "success",
                "enviadas": enviadas + produtos_antigos_enviados,
                "recebidas": produtos_recebidos,
                "message": f"Sincronização concluída. {produtos_recebidos} produtos recebidos, {enviadas + produtos_antigos_enviados} mudanças enviadas."
            }
            
        except Exception as e:
            print(f"Erro geral na sincronizacao: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _pull_produtos_do_servidor(self) -> int:
        """Busca produtos novos/atualizados do servidor e os integra localmente."""
        try:
            async with httpx.AsyncClient() as client:
                # Buscar todos os produtos do servidor
                response = await client.get(
                    f"{self.backend_url}/api/produtos/",
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    print(f"Erro ao buscar produtos do servidor: {response.status_code}")
                    return 0
                
                produtos_servidor = response.json()
                print(f"Encontrados {len(produtos_servidor)} produtos no servidor")
                
                produtos_recebidos = 0
                produtos_atualizados = 0
                
                for produto_servidor in produtos_servidor:
                    try:
                        # Se produto não tem UUID, pular (produto antigo sem sincronização)
                        if 'uuid' not in produto_servidor or not produto_servidor['uuid']:
                            print(f"Produto {produto_servidor['nome']} sem UUID - pulando")
                            continue
                            
                        # Verificar se produto já existe localmente pelo UUID
                        produto_local = self._get_produto_by_uuid(produto_servidor['uuid'])
                        
                        if produto_local is None:
                            # Produto novo - inserir localmente
                            if self._inserir_produto_do_servidor(produto_servidor):
                                produtos_recebidos += 1
                                print(f"Produto novo inserido: {produto_servidor['nome']}")
                        else:
                            # Produto existe - verificar se precisa atualizar
                            if self._produto_servidor_mais_recente(produto_local, produto_servidor):
                                if self._atualizar_produto_do_servidor(produto_local['id'], produto_servidor):
                                    produtos_atualizados += 1
                                    print(f"Produto atualizado: {produto_servidor['nome']}")
                    
                    except Exception as e:
                        print(f"Erro ao processar produto {produto_servidor.get('nome', 'N/A')}: {e}")
                
                total_recebidos = produtos_recebidos + produtos_atualizados
                print(f"Pull concluído: {produtos_recebidos} novos, {produtos_atualizados} atualizados")
                return total_recebidos
                
        except Exception as e:
            print(f"Erro no pull de produtos: {e}")
            return 0
    
    async def _sincronizar_produtos_antigos(self) -> int:
        """Sincroniza produtos antigos que não foram sincronizados (bulk sync)."""
        print("Verificando produtos antigos nao sincronizados...")
        
        # Primeiro verificar se o servidor tem produtos
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/api/produtos/", timeout=5.0)
                produtos_servidor = response.json() if response.status_code == 200 else []
                servidor_vazio = len(produtos_servidor) == 0
        except Exception:
            servidor_vazio = False
        
        # Buscar produtos locais para sincronizar
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if servidor_vazio:
                # Se servidor vazio, sincronizar TODOS os produtos locais
                print("Servidor vazio - sincronizando TODOS os produtos locais...")
                cursor.execute("""
                    SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                           estoque, estoque_minimo, categoria_id, venda_por_peso,
                           unidade_medida, ativo, created_at, updated_at,
                           COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                    FROM produtos 
                    WHERE ativo = 1
                    ORDER BY created_at
                """)
            else:
                # Se servidor tem dados, sincronizar apenas não sincronizados
                cursor.execute("""
                    SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                           estoque, estoque_minimo, categoria_id, venda_por_peso,
                           unidade_medida, ativo, created_at, updated_at,
                           COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                    FROM produtos 
                    WHERE ativo = 1 AND (synced = 0 OR synced IS NULL)
                    ORDER BY created_at
                """)
            
            produtos_nao_sincronizados = [dict(row) for row in cursor.fetchall()]
        
        if not produtos_nao_sincronizados:
            print("Todos os produtos ja estao sincronizados")
            return 0
        
        print(f"Encontrados {len(produtos_nao_sincronizados)} produtos nao sincronizados")
        enviados = 0
        
        async with httpx.AsyncClient() as client:
            for produto in produtos_nao_sincronizados:
                try:
                    # Gerar UUID se não existir
                    if not produto['uuid']:
                        produto['uuid'] = str(uuid.uuid4())
                        self._update_produto_uuid(produto['id'], produto['uuid'])
                    
                    # Preparar dados para envio
                    produto_data = {
                        'uuid': produto['uuid'],  # Incluir UUID
                        'codigo': produto['codigo'] or '',
                        'nome': produto['nome'],
                        'descricao': produto['descricao'] or '',
                        'preco_custo': produto['preco_custo'] or 0,
                        'preco_venda': produto['preco_venda'] or 0,
                        'estoque': int(produto['estoque'] or 0),  # Converter para inteiro
                        'estoque_minimo': int(produto['estoque_minimo'] or 0),  # Converter para inteiro
                        'categoria_id': produto['categoria_id'],
                        'venda_por_peso': produto['venda_por_peso'] or False,
                        'unidade_medida': produto['unidade_medida'] or 'un'
                    }
                    
                    print(f"Enviando produto antigo: {produto['nome']} (codigo: {produto['codigo']})")
                    
                    # Tentar criar no servidor
                    response = await client.post(
                        f"{self.backend_url}/api/produtos/",
                        json=produto_data,
                        timeout=10.0
                    )
                    
                    if response.status_code in [200, 201]:
                        # Marcar como sincronizado
                        self._mark_produto_sincronizado(produto['id'])
                        enviados += 1
                        print(f"Produto {produto['nome']} sincronizado")
                    elif (response.status_code == 400 and "duplicate key" in response.text.lower()) or \
                         (response.status_code == 500 and "duplicate key" in response.text.lower()):
                        # Produto já existe, buscar e atualizar
                        print(f"Produto {produto['nome']} ja existe, tentando atualizar...")
                        
                        # Buscar produto existente por código
                        list_response = await client.get(f"{self.backend_url}/api/produtos/", timeout=5.0)
                        if list_response.status_code == 200:
                            produtos_servidor = list_response.json()
                            produto_existente = None
                            for p in produtos_servidor:
                                if p.get('codigo') == produto['codigo']:
                                    produto_existente = p
                                    break
                            
                            if produto_existente:
                                # Atualizar produto existente
                                update_response = await client.put(
                                    f"{self.backend_url}/api/produtos/{produto_existente['id']}",
                                    json=produto_data,
                                    timeout=5.0
                                )
                                if update_response.status_code == 200:
                                    self._mark_produto_sincronizado(produto['id'])
                                    enviados += 1
                                    print(f"Produto {produto['nome']} atualizado no servidor")
                                else:
                                    print(f"Erro ao atualizar produto {produto['nome']}: {update_response.text}")
                            else:
                                # Marcar como sincronizado mesmo se não conseguir atualizar
                                # pois o produto já existe no servidor
                                self._mark_produto_sincronizado(produto['id'])
                                enviados += 1
                                print(f"Produto {produto['nome']} ja existe no servidor, marcado como sincronizado")
                    else:
                        print(f"Erro ao enviar produto {produto['nome']}: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    print(f"Erro ao processar produto {produto.get('nome', 'N/A')}: {e}")
        
        print(f"Sincronizacao de produtos antigos concluida: {enviados}/{len(produtos_nao_sincronizados)} enviados")
        return enviados
    
    def _update_produto_uuid(self, produto_id: int, uuid_value: str):
        """Atualiza UUID de um produto."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE produtos SET uuid = ? WHERE id = ?
            """, (uuid_value, produto_id))
            conn.commit()
    
    def _mark_produto_sincronizado(self, produto_id: int):
        """Marca produto como sincronizado."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                # Verificar se o produto existe primeiro
                cursor.execute("SELECT id FROM produtos WHERE id = ?", (produto_id,))
                if not cursor.fetchone():
                    print(f"Produto ID {produto_id} nao encontrado")
                    return
                
                # Atualizar produto
                cursor.execute("""
                    UPDATE produtos 
                    SET synced = 1, updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), produto_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    print(f"Produto ID {produto_id} marcado como sincronizado")
                else:
                    print(f"Nenhuma linha atualizada para produto ID {produto_id}")
        except Exception as e:
            print(f"Erro ao marcar produto {produto_id} como sincronizado: {e}")

    def _mark_change_synced(self, change_id: int):
        """Marca mudança como sincronizada."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE change_log 
                SET status = 'synced'
                WHERE id = ?
            """, (change_id,))
            conn.commit()
    
    def _delete_local_produto(self, produto_id: int, synced: int) -> bool:
        """Faz soft delete do produto no banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE produtos 
                SET ativo = 0, updated_at = ?, synced = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), synced, produto_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
    
    def _get_produto_by_uuid(self, uuid: str) -> Dict[str, Any]:
        """Busca produto local pelo UUID."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                       categoria_id, fornecedor_id, estoque_atual, estoque_minimo, 
                       uuid, synced, created_at, updated_at
                FROM produtos 
                WHERE uuid = ?
            """, (uuid,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _inserir_produto_do_servidor(self, produto_servidor: Dict[str, Any]) -> bool:
        """Insere produto recebido do servidor no banco local."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO produtos (
                        codigo, nome, descricao, preco_custo, preco_venda,
                        categoria_id, fornecedor_id, estoque_atual, estoque_minimo,
                        uuid, synced, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """, (
                    produto_servidor['codigo'],
                    produto_servidor['nome'],
                    produto_servidor.get('descricao', ''),
                    produto_servidor['preco_custo'],
                    produto_servidor['preco_venda'],
                    produto_servidor.get('categoria_id'),
                    produto_servidor.get('fornecedor_id'),
                    produto_servidor.get('estoque_atual', 0),
                    produto_servidor.get('estoque_minimo', 0),
                    produto_servidor['uuid'],
                    produto_servidor.get('created_at'),
                    produto_servidor.get('updated_at')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao inserir produto do servidor: {e}")
            return False
    
    def _produto_servidor_mais_recente(self, produto_local: Dict[str, Any], produto_servidor: Dict[str, Any]) -> bool:
        """Verifica se o produto do servidor é mais recente que o local."""
        try:
            # Se o produto local não foi sincronizado, não sobrescrever
            if not produto_local.get('synced', False):
                print(f"Produto local {produto_local['nome']} tem mudanças não sincronizadas - mantendo versão local")
                return False
            
            # Comparar timestamps de updated_at
            local_updated = produto_local.get('updated_at')
            servidor_updated = produto_servidor.get('updated_at')
            
            if not local_updated or not servidor_updated:
                return True  # Se não temos timestamps, assumir que servidor é mais recente
            
            # Converter para datetime para comparação
            from datetime import datetime
            try:
                local_dt = datetime.fromisoformat(local_updated.replace('Z', '+00:00'))
                servidor_dt = datetime.fromisoformat(servidor_updated.replace('Z', '+00:00'))
                return servidor_dt > local_dt
            except:
                return True  # Em caso de erro na conversão, assumir servidor mais recente
                
        except Exception as e:
            print(f"Erro ao comparar timestamps: {e}")
            return False
    
    def _atualizar_produto_do_servidor(self, produto_id: int, produto_servidor: Dict[str, Any]) -> bool:
        """Atualiza produto local com dados do servidor."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE produtos SET
                        codigo = ?, nome = ?, descricao = ?, preco_custo = ?, preco_venda = ?,
                        categoria_id = ?, fornecedor_id = ?, estoque_atual = ?, estoque_minimo = ?,
                        synced = 1, updated_at = ?
                    WHERE id = ?
                """, (
                    produto_servidor['codigo'],
                    produto_servidor['nome'],
                    produto_servidor.get('descricao', ''),
                    produto_servidor['preco_custo'],
                    produto_servidor['preco_venda'],
                    produto_servidor.get('categoria_id'),
                    produto_servidor.get('fornecedor_id'),
                    produto_servidor.get('estoque_atual', 0),
                    produto_servidor.get('estoque_minimo', 0),
                    produto_servidor.get('updated_at'),
                    produto_id
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar produto do servidor: {e}")
            return False
