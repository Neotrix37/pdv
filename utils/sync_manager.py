import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import httpx
import asyncio

# Configuração de logging aprimorada
def setup_sync_logger():
    """Configura o sistema de logging para sincronização com rotação e níveis detalhados"""
    logger = logging.getLogger('PDVSync')
    logger.setLevel(logging.DEBUG)  # Nível mais detalhado
    
    # Limpar handlers existentes para evitar duplicação
    logger.handlers.clear()
    
    # Formatar as mensagens de log com mais detalhes
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    
    # Handler para arquivo principal com rotação
    from logging.handlers import RotatingFileHandler
    log_dir = os.path.join(os.path.expanduser('~'), 'pdv_logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Log principal com rotação (5MB, 3 backups)
    main_log = os.path.join(log_dir, 'pdv_sync.log')
    file_handler = RotatingFileHandler(
        main_log, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Log separado para erros
    error_log = os.path.join(log_dir, 'pdv_sync_errors.log')
    error_handler = RotatingFileHandler(
        error_log, maxBytes=2*1024*1024, backupCount=2, encoding='utf-8'
    )
    error_handler.setFormatter(detailed_formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)
    
    # Handler para console (apenas INFO e acima)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    return logger

# Configurar o logger principal
logger = setup_sync_logger()

async def sync_all_tables() -> Dict[str, Any]:
    """
    Sincroniza todas as tabelas e retorna um resumo detalhado.
    
    Returns:
        Dict com o formato:
        {
            'tables': {
                'table1': {
                    'status': 'success', 
                    'uploaded': 5, 
                    'downloaded': 3, 
                    'conflicts': 1,
                    'message': ''
                },
                ...
            },
            'summary': {
                'total_uploaded': 0,
                'total_downloaded': 0,
                'total_conflicts': 0,
                'status': 'success',  # 'success', 'partial' ou 'error'
                'message': '',
                'start_time': '2023-01-01T00:00:00',
                'end_time': '2023-01-01T00:01:30',
                'duration_seconds': 90
            }
        }
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"Iniciando sincronização em {start_time.isoformat()}")
    
    # Configuração do caminho do banco de dados
    db_path = os.path.join(os.getenv('APPDATA', ''), 'SistemaGestao', 'database', 'sistema.db')
    
    # Garantir que o diretório existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Estrutura de resultados
    results = {
        'tables': {},
        'summary': {
            'total_uploaded': 0,
            'total_downloaded': 0,
            'total_conflicts': 0,
            'status': 'success',
            'message': '',
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration_seconds': 0
        }
    }
    
    # Tabelas a serem sincronizadas com suas configurações
    tables_config = [
        {'name': 'produtos', 'upload': True, 'download': True},
        {'name': 'categorias', 'upload': True, 'download': True},
        {'name': 'clientes', 'upload': True, 'download': True},
        {'name': 'vendas', 'upload': True, 'download': True},
        {'name': 'itens_venda', 'upload': True, 'download': True},
        {'name': 'usuarios', 'upload': True, 'download': True},
        {'name': 'funcionarios', 'upload': True, 'download': True},
        {'name': 'relatorios', 'upload': True, 'download': True},
        {'name': 'dividas', 'upload': True, 'download': True},
        {'name': 'contas_pagar', 'upload': True, 'download': True},
        {'name': 'movimentacoes_caixa', 'upload': True, 'download': True},
        {'name': 'fornecedores', 'upload': True, 'download': True},
        {'name': 'despesas_recorrentes', 'upload': True, 'download': True},

    ]
    
    try:
        async with SyncManager(db_path) as manager:
            logger.info("Conexão com o gerenciador de sincronização estabelecida")
            
            for table_config in tables_config:
                table_name = table_config['name']
                table_result = {
                    'status': 'success',
                    'uploaded': 0,
                    'downloaded': 0,
                    'conflicts': 0,
                    'message': ''
                }
                
                try:
                    logger.info(f"🔄 Iniciando sincronização da tabela: {table_name}")
                    sync_start = datetime.now(timezone.utc)
                    
                    # 1. Enviar dados locais para o servidor (se configurado)
                    if table_config['upload']:
                        try:
                            logger.debug(f"📤 Buscando dados não sincronizados de {table_name}")
                            unsynced = await manager._get_unsynced_data(table_name)
                            
                            if unsynced:
                                logger.info(f"📤 Enviando {len(unsynced)} registros não sincronizados de {table_name}")
                                logger.debug(f"📋 Registros a enviar: {[r.get('id', 'N/A') for r in unsynced[:5]]}{'...' if len(unsynced) > 5 else ''}")
                                
                                api_endpoint = manager.table_name_map.get(table_name, table_name)
                                upload_start = datetime.now(timezone.utc)
                                success, conflicts = await manager.send_to_server(api_endpoint, unsynced)
                                upload_duration = (datetime.now(timezone.utc) - upload_start).total_seconds()
                                
                                if success:
                                    table_result['uploaded'] = len(unsynced) - len(conflicts)
                                    table_result['conflicts'] += len(conflicts)
                                    table_result['message'] += f"Enviados {table_result['uploaded']} registros em {upload_duration:.2f}s. "
                                    
                                    logger.info(f"✅ Upload {table_name}: {table_result['uploaded']} enviados, {len(conflicts)} conflitos em {upload_duration:.2f}s")
                                    
                                    if conflicts:
                                        table_result['message'] += f"{len(conflicts)} conflitos encontrados. "
                                        table_result['status'] = 'partial'
                                        logger.warning(f"⚠️ Conflitos em {table_name}: {[c.get('local_id', 'N/A') for c in conflicts[:3]]}{'...' if len(conflicts) > 3 else ''}")
                                else:
                                    table_result['status'] = 'error'
                                    table_result['message'] += "Falha ao enviar dados. "
                                    logger.error(f"❌ Falha no upload de {table_name}")
                            else:
                                logger.debug(f"📤 Nenhum registro não sincronizado encontrado em {table_name}")
                                    
                        except Exception as e:
                            logger.error(f"❌ Erro ao enviar dados de {table_name}: {str(e)}", exc_info=True)
                            table_result['status'] = 'error'
                            table_result['message'] += f"Erro no envio: {str(e)}. "
                    
                    # 2. Buscar atualizações do servidor (se configurado)
                    if table_config['download'] and table_result['status'] != 'error':
                        try:
                            logger.debug(f"📥 Buscando atualizações do servidor para {table_name}")
                            api_endpoint = manager.table_name_map.get(table_name, table_name)
                            download_start = datetime.now(timezone.utc)
                            server_data, conflicts = await manager.fetch_from_server(api_endpoint)
                            download_duration = (datetime.now(timezone.utc) - download_start).total_seconds()
                            
                            if server_data:
                                logger.info(f"📥 Recebidos {len(server_data)} registros do servidor para {table_name}")
                                logger.debug(f"📋 Registros recebidos: {[r.get('id', 'N/A') for r in server_data[:5]]}{'...' if len(server_data) > 5 else ''}")
                                
                                # Atualizar dados locais
                                update_start = datetime.now(timezone.utc)
                                updated = await manager._update_local_data(table_name, server_data)
                                update_duration = (datetime.now(timezone.utc) - update_start).total_seconds()
                                
                                table_result['downloaded'] = len(updated)
                                table_result['message'] += f"Recebidos {len(updated)} registros em {download_duration:.2f}s, atualizados em {update_duration:.2f}s. "
                                
                                logger.info(f"✅ Download {table_name}: {len(updated)} atualizados em {download_duration + update_duration:.2f}s")
                                
                                # Atualizar último sync se houver dados novos
                                if updated:
                                    manager.last_sync = datetime.now(timezone.utc).isoformat()
                                    if hasattr(manager, 'config') and manager.config:
                                        manager.config.set('last_sync', manager.last_sync)
                            else:
                                logger.debug(f"📥 Nenhum dado novo recebido do servidor para {table_name}")
                            
                            # Processar conflitos
                            if conflicts:
                                table_result['conflicts'] += len(conflicts)
                                table_result['message'] += f"{len(conflicts)} conflitos no download. "
                                if table_result['status'] != 'error':
                                    table_result['status'] = 'partial'
                                logger.warning(f"⚠️ Conflitos no download de {table_name}: {len(conflicts)} encontrados")
                            
                        except Exception as e:
                            logger.error(f"❌ Erro ao buscar dados de {table_name}: {str(e)}", exc_info=True)
                            table_result['status'] = 'error'
                            table_result['message'] += f"Erro ao buscar: {str(e)}. "
                    
                    # Registrar resultado da tabela
                    results['tables'][table_name] = table_result
                    
                    # Atualizar totais
                    results['summary']['total_uploaded'] += table_result['uploaded']
                    results['summary']['total_downloaded'] += table_result['downloaded']
                    results['summary']['total_conflicts'] += table_result['conflicts']
                    
                    # Atualizar status geral
                    if table_result['status'] == 'error':
                        results['summary']['status'] = 'error'
                        results['summary']['message'] += f"{table_name}: {table_result['message']} "
                    elif table_result['status'] == 'partial' and results['summary']['status'] == 'success':
                        results['summary']['status'] = 'partial'
                    
                    logger.info(f"Tabela {table_name} sincronizada: {json.dumps(table_result, ensure_ascii=False)}")
                    
                except Exception as e:
                    error_msg = f"Erro inesperado ao sincronizar {table_name}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results['tables'][table_name] = {
                        'status': 'error',
                        'uploaded': 0,
                        'downloaded': 0,
                        'conflicts': 0,
                        'message': error_msg
                    }
                    results['summary']['status'] = 'error'
                    results['summary']['message'] += error_msg + " "
            
            # Finalização
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            results['summary'].update({
                'end_time': end_time.isoformat(),
                'duration_seconds': round(duration, 2)
            })
            
            # Mensagem de resumo
            if results['summary']['status'] == 'success':
                results['summary']['message'] = "Sincronização concluída com sucesso!"
            elif results['summary']['status'] == 'partial':
                results['summary']['message'] = "Sincronização concluída com avisos. "
            else:
                results['summary']['message'] = "Falha na sincronização. Verifique os logs para mais detalhes."
            
            logger.info(
                f"Sincronização finalizada em {duration:.2f} segundos. "
                f"Enviados: {results['summary']['total_uploaded']}, "
                f"Recebidos: {results['summary']['total_downloaded']}, "
                f"Conflitos: {results['summary']['total_conflicts']}"
            )
            
            return results
            
    except Exception as e:
        error_msg = f"Erro fatal na sincronização: {str(e)}"
        logger.critical(error_msg, exc_info=True)
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        results['summary'].update({
            'status': 'error',
            'message': error_msg,
            'end_time': end_time.isoformat(),
            'duration_seconds': round(duration, 2)
        })
        
        return results

class SyncManager:
    table_name_map = {
        'produtos': 'products',
        'categorias': 'categories',
        'clientes': 'customers',
        'vendas': 'sales',
        'itens_venda': 'sale-items',
        'usuarios': 'users',
        'funcionarios': 'employees',
        'relatorios': 'reports',
        'dividas': 'debts',
        'contas_pagar': 'accounts-payable',
        'movimentacoes_caixa': 'cash-movements',
        'fornecedores': 'suppliers',
        'despesas_recorrentes': 'recurring-expenses'
    }

    def _load_config(self) -> Dict[str, Any]:
        """
        Carrega as configurações do arquivo config.json.
        """
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar configurações do config.json: {e}")
                return {}
        return {}

    def __init__(self, db_path: str):
        """
        Inicializa o gerenciador de sincronização.
        
        Args:
            db_path: Caminho para o banco de dados SQLite local
        """
        self.db_path = db_path
        self.config = self._load_config()
        self.api_url = self.config.get('server_url', 'https://prototipo-production-c729.up.railway.app/api')
        self.auth_token = os.getenv("SYNC_AUTH_TOKEN", "")
        self.max_retries = 3
        self.retry_delay = 2  # segundos
        self.last_sync = None
        self.client = None
        
        # Configurar cliente HTTP
        self._init_http_client()
    
    def _init_http_client(self):
        """Inicializa o cliente HTTP com as configurações padrão."""
        if self.client:
            asyncio.create_task(self.client.aclose())
            
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'PDV-Sync/1.0',
                'Accept': 'application/json'
            },
            follow_redirects=True,
            http2=True
        )
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[httpx.Response]:
        """
        Executa uma requisição HTTP com tratamento de erros e retry.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE, etc.)
            url: URL da requisição
            **kwargs: Argumentos adicionais para a requisição
            
        Returns:
            Resposta da requisição ou None em caso de falha
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text}"
                if e.response.status_code in (401, 403):
                    logger.error(f"Erro de autenticação: {last_error}")
                    raise PermissionError("Falha na autenticação. Verifique o token de acesso.")
                
                if e.response.status_code >= 500:
                    logger.warning(f"Erro do servidor (tentativa {attempt + 1}/{self.max_retries}): {last_error}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                
                logger.error(f"Erro na requisição: {last_error}")
                raise
                
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error = str(e)
                logger.warning(f"Erro de conexão (tentativa {attempt + 1}/{self.max_retries}): {last_error}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                
                logger.error(f"Falha na conexão após {self.max_retries} tentativas: {last_error}")
                raise ConnectionError(f"Não foi possível conectar ao servidor: {last_error}")
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"Erro inesperado: {last_error}", exc_info=True)
                raise
        
        return None
    
    async def _get_unsynced_data(self, table_name: str, batch_size: int = 1000) -> List[Dict]:
        """
        Busca registros não sincronizados no banco local com otimização para grandes volumes.
        
        Args:
            table_name: Nome da tabela
            batch_size: Tamanho do lote para processamento (padrão: 1000)
            
        Returns:
            Lista de dicionários com os dados não sincronizados
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Verificar se a tabela tem a coluna 'synced'
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                has_synced = 'synced' in columns
                has_created_at = 'created_at' in columns
                
                # Construir a query otimizada baseada nas colunas disponíveis
                if has_synced:
                    # Usar índice na coluna synced para melhor performance
                    base_query = f"""
                    SELECT * FROM {table_name} 
                    WHERE (synced = 0 OR synced IS NULL)
                    """
                    
                    # Adicionar ordenação por data de criação se disponível
                    if has_created_at:
                        base_query += " ORDER BY created_at DESC"
                    else:
                        base_query += " ORDER BY id DESC"
                    
                    # Limitar resultados para evitar sobrecarga de memória
                    query = f"{base_query} LIMIT {batch_size}"
                else:
                    # Se não tiver coluna 'synced', considera que todos precisam ser sincronizados
                    # mas limita para evitar sobrecarga
                    query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {batch_size}"
                
                logger.debug(f"Executando query otimizada: {query}")
                start_time = datetime.now()
                cursor.execute(query)
                rows = cursor.fetchall()
                query_duration = (datetime.now() - start_time).total_seconds()
                
                # Converter para lista de dicionários
                result = [dict(row) for row in rows]
                
                logger.info(f"📊 Query {table_name}: {len(result)} registros não sincronizados encontrados em {query_duration:.3f}s")
                
                # Log de aviso se atingiu o limite do lote
                if len(result) == batch_size:
                    logger.warning(f"⚠️ Limite de lote atingido para {table_name}. Pode haver mais registros não sincronizados.")
                
                return result
                
        except sqlite3.Error as e:
            logger.error(f"❌ Erro ao buscar dados não sincronizados de {table_name}: {str(e)}")
            raise

    async def _update_local_data(self, table_name: str, records: List[Dict]) -> List[Dict]:
        """
        Atualiza os dados locais com os registros do servidor.
        
        Args:
            table_name: Nome da tabela
            records: Lista de dicionários com os dados a serem atualizados
            
        Returns:
            Lista de dicionários com os registros atualizados
        """
        if not records:
            return []
            
        updated_records = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Obter informações da tabela
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = {col[1]: col for col in cursor.fetchall()}
                
                # Verificar se a tabela tem as colunas necessárias
                has_synced = 'synced' in columns_info
                has_last_updated = 'last_updated' in columns_info
                
                # Preparar os campos para a query
                all_columns = list(columns_info.keys())
                
                # Construir a query de inserção/atualização
                placeholders = ', '.join(['?'] * len(all_columns))
                columns_str = ', '.join(all_columns)
                
                # Para cada coluna, criar a parte SET da query
                set_clause = ', '.join([f"{col} = ?" for col in all_columns])
                
                # Query para inserir ou substituir registros
                query = f"""
                INSERT OR REPLACE INTO {table_name} ({columns_str})
                VALUES ({placeholders})
                """
                
                # Processar cada registro
                for record in records:
                    try:
                        # Preparar os valores na ordem correta das colunas
                        values = []
                        for col in all_columns:
                            if col in record:
                                values.append(record[col])
                            elif col == 'synced' and has_synced:
                                values.append(1)  # Marcar como sincronizado
                            elif col == 'last_updated' and has_last_updated:
                                values.append(datetime.now(timezone.utc).isoformat())
                            else:
                                # Para colunas não nulas sem valor padrão, usar None
                                col_info = columns_info[col]
                                if col_info[3] == 1:  # NOT NULL
                                    if col_info[4] is not None:  # Tem valor padrão
                                        values.append(col_info[4])
                                    else:
                                        values.append(None)
                                else:
                                    values.append(None)
                        
                        # Executar a query
                        cursor.execute(query, values)
                        updated_records.append(record)
                        
                        # Log detalhado do registro atualizado no banco local
                        record_id = record.get('id', 'sem_id')
                        logger.info(f"ATUALIZADO LOCALMENTE [{table_name}] ID: {record_id} - Dados: {json.dumps(record, ensure_ascii=False)}")
                        
                    except sqlite3.Error as e:
                        logger.error(f"Erro ao atualizar registro em {table_name}: {str(e)}")
                        continue
                
                conn.commit()
                logger.info(f"Atualizados {len(updated_records)} registros em {table_name}")
                return updated_records
                
        except Exception as e:
            logger.error(f"Erro ao atualizar dados locais de {table_name}: {str(e)}", exc_info=True)
            raise
    
    async def send_to_server(self, table_name: str, records: List[Dict]) -> Tuple[bool, List[Dict]]:
        """
        Envia registros para o servidor.
        
        Args:
            table_name: Nome da tabela
            records: Lista de dicionários com os dados a serem enviados
            
        Returns:
            Tupla (sucesso, conflitos)
        """
        if not records:
            return True, []
            
        try:
            url = f"{self.api_url.rstrip('/')}/{table_name}"
            logger.info(f"Enviando {len(records)} registros para {url}")
            
            # Enviar em lotes para evitar requisições muito grandes
            batch_size = 50
            all_conflicts = []
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                try:
                    # Log detalhado dos dados sendo enviados
                    for record in batch:
                        record_id = record.get('id', 'sem_id')
                        logger.info(f"ENVIANDO [{table_name}] ID: {record_id} - Dados: {json.dumps(record, ensure_ascii=False)}")
                    
                    response = await self._make_request(
                        'POST',
                        url,
                        json={"data": batch},
                        timeout=60.0  # Tempo maior para envio de lotes
                    )
                    
                    if response is None:
                        continue
                        
                    result = response.json()
                    logger.info(f"RESPOSTA SERVIDOR [{table_name}]: {json.dumps(result, ensure_ascii=False)[:500]}...")
                    
                    batch_conflicts = result.get('conflicts', [])
                    all_conflicts.extend(batch_conflicts)
                    
                    # Log de conflitos encontrados
                    for conflict in batch_conflicts:
                        logger.warning(f"CONFLITO [{table_name}] ID Local: {conflict.get('local_id')} - Detalhes: {json.dumps(conflict, ensure_ascii=False)[:200]}...")
                    
                    # Marcar registros sem conflitos como sincronizados
                    synced_ids = [
                        str(r['id']) for r in batch 
                        if not any(c.get('local_id') == str(r.get('id')) for c in batch_conflicts)
                    ]
                    
                    if synced_ids:
                        self._mark_as_synced(table_name, synced_ids)
                    
                    logger.info(f"Lote {i//batch_size + 1} processado: {len(synced_ids)} enviados, {len(batch_conflicts)} conflitos")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar lote {i//batch_size + 1}: {str(e)}")
                    continue
            
            # Salvar conflitos se houver
            if all_conflicts:
                self._save_conflicts(table_name, all_conflicts)
                
            success = len(all_conflicts) < len(records)  # Considera sucesso se pelo menos um registro foi enviado
            return success, all_conflicts
            
        except Exception as e:
            logger.error(f"Erro ao enviar dados para {table_name}: {str(e)}", exc_info=True)
            return False, []
    
    async def fetch_from_server(self, table_name: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Busca registros atualizados do servidor.
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Tupla (dados, conflitos)
        """
        try:
            url = f"{self.api_url.rstrip('/')}/{table_name}"
            params = {
                "last_sync": self.last_sync,
                "limit": 1000,  # Limitar o número de registros por requisição
                "offset": 0
            }
            
            all_data = []
            has_more = True
            
            while has_more:
                try:
                    logger.info(f"REQUISIÇÃO [{table_name}] - Buscando dados de {url} (offset: {params['offset']}, last_sync: {params['last_sync']})")
                    response = await self._make_request('GET', url, params=params)
                    
                    if response is None:
                        break
                        
                    data = response.json()
                    logger.info(f"RESPOSTA RECEBIDA [{table_name}]: {json.dumps(data, ensure_ascii=False)}")
                    
                    batch_data = data.get('data', [])
                    all_data.extend(batch_data)
                    
                    # Log detalhado dos registros recebidos
                    for record in batch_data:
                        record_id = record.get('id', 'sem_id')
                        logger.info(f"RECEBIDO [{table_name}] ID: {record_id} - Dados: {json.dumps(record, ensure_ascii=False)}")
                    
                    # Verificar se há mais dados para buscar
                    has_more = data.get('has_more', False) and len(batch_data) > 0
                    params['offset'] += len(batch_data)
                    
                    logger.info(f"Recebidos {len(batch_data)} registros (total: {len(all_data)})")
                    
                    # Pequena pausa entre as requisições
                    if has_more:
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.error(f"Erro ao buscar lote de {table_name}: {str(e)}")
                    has_more = False
            
            # Processar conflitos se houver
            conflicts = data.get('conflicts', []) if 'data' in locals() else []
            if conflicts:
                logger.warning(f"CONFLITOS RECEBIDOS [{table_name}]: {len(conflicts)} conflitos")
                for conflict in conflicts:
                    logger.warning(f"DETALHE CONFLITO [{table_name}]: {json.dumps(conflict, ensure_ascii=False)}")
                self._save_conflicts(table_name, conflicts)
            
            logger.info(f"Total de {len(all_data)} registros recebidos de {table_name}")
            return all_data, conflicts
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados de {table_name}: {str(e)}", exc_info=True)
            return [], []
    
    def _mark_as_synced(self, table_name: str, record_ids: List[str]):
        """
        Marca registros como sincronizados no banco local.
        
        Args:
            table_name: Nome da tabela
            record_ids: Lista de IDs dos registros a serem marcados
        """
        if not record_ids:
            logger.info(f"Nenhum registro para marcar como sincronizado em {table_name}")
            return
            
        try:
            logger.info(f"MARCANDO COMO SINCRONIZADO [{table_name}]: {len(record_ids)} registros")
            # Mostrar os primeiros 10 IDs no log (ou todos se forem menos de 10)
            ids_to_show = record_ids[:10]
            logger.info(f"IDs sendo marcados como sincronizados: {', '.join(ids_to_show)}{' ...' if len(record_ids) > 10 else ''}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se a tabela tem a coluna 'synced'
                cursor.execute(f"PRAGMA table_info({table_name})")
                has_synced = any(col[1] == 'synced' for col in cursor.fetchall())
                
                if has_synced:
                    placeholders = ','.join(['?'] * len(record_ids))
                    query = f"""
                    UPDATE {table_name} 
                    SET synced = 1, 
                        last_sync = CURRENT_TIMESTAMP
                    WHERE id IN ({placeholders})
                    """
                    
                    cursor.execute(query, record_ids)
                    rows_affected = cursor.rowcount
                    conn.commit()
                    logger.info(f"ATUALIZADO [{table_name}]: {rows_affected} registros marcados como sincronizados")
                else:
                    logger.warning(f"AVISO [{table_name}]: Tabela não possui coluna 'synced', registros não foram marcados")
                
        except sqlite3.Error as e:
            logger.error(f"ERRO [{table_name}]: Falha ao marcar registros como sincronizados: {str(e)}")
            raise
    
    def _save_conflicts(self, table_name: str, conflicts: List[Dict]):
        """
        Salva conflitos para resolução posterior.
        
        Args:
            table_name: Nome da tabela
            conflicts: Lista de dicionários com informações dos conflitos
        """
        if not conflicts:
            logger.info(f"Nenhum conflito para salvar em {table_name}")
            return
            
        try:
            logger.info(f"SALVANDO CONFLITOS [{table_name}]: {len(conflicts)} conflitos encontrados")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Garantir que a tabela de conflitos existe
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_conflicts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    local_id TEXT,
                    server_data TEXT,
                    local_data TEXT,
                    resolved BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP NULL
                )
                """)
                
                novos_conflitos = 0
                conflitos_existentes = 0
                
                for conflict in conflicts:
                    local_id = str(conflict.get('local_id', ''))
                    logger.info(f"PROCESSANDO CONFLITO [{table_name}] ID Local: {local_id}")
                    
                    # Verificar se já existe um conflito não resolvido para este registro
                    cursor.execute(
                        """
                        SELECT id FROM sync_conflicts 
                        WHERE table_name = ? AND local_id = ? AND resolved = 0
                        """,
                        (table_name, local_id)
                    )
                    
                    if not cursor.fetchone():
                        # Inserir novo conflito
                        server_data = json.dumps(conflict.get('server_data', {}), ensure_ascii=False)
                        local_data = json.dumps(conflict.get('local_data', {}), ensure_ascii=False)
                        
                        logger.info(f"NOVO CONFLITO [{table_name}] ID: {local_id}")
                        logger.info(f"  - Dados do servidor: {server_data}")
                        logger.info(f"  - Dados locais: {local_data}")
                        
                        cursor.execute(
                            """
                            INSERT INTO sync_conflicts 
                            (table_name, local_id, server_data, local_data, resolved, created_at)
                            VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                            """,
                            (
                                table_name,
                                local_id,
                                server_data,
                                local_data
                            )
                        )
                        novos_conflitos += 1
                    else:
                        logger.info(f"CONFLITO EXISTENTE [{table_name}] ID: {local_id} - Ignorando")
                        conflitos_existentes += 1
                
                conn.commit()
                logger.info(f"CONFLITOS SALVOS [{table_name}]: {novos_conflitos} novos, {conflitos_existentes} já existentes")
                return novos_conflitos
                
        except sqlite3.Error as e:
            logger.error(f"ERRO AO SALVAR CONFLITOS [{table_name}]: {str(e)}")
            raise
    
    async def close(self):
        """Fecha a conexão HTTP."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
