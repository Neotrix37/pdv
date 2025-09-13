"""
Testes automatizados para o sistema de sincronização PDV3.
"""
import unittest
import asyncio
import sqlite3
import tempfile
import os
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
import sys
import logging

# Adicionar o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sync_manager import SyncManager, sync_all_tables

class TestSyncManager(unittest.TestCase):
    """Testes para o SyncManager"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        # Criar banco de dados temporário
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Configurar logging para testes
        logging.getLogger('PDVSync').setLevel(logging.CRITICAL)
        
        # Criar tabelas de teste
        self._create_test_tables()
        
        # Inicializar SyncManager
        self.sync_manager = SyncManager(self.db_path)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        try:
            if hasattr(self.sync_manager, 'client') and self.sync_manager.client:
                asyncio.run(self.sync_manager.client.aclose())
        except:
            pass
        
        # Remover arquivo temporário
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_test_tables(self):
        """Cria tabelas de teste no banco SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela produtos
            cursor.execute("""
                CREATE TABLE produtos (
                    id INTEGER PRIMARY KEY,
                    uuid TEXT UNIQUE,
                    codigo TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    preco_venda REAL NOT NULL,
                    estoque REAL DEFAULT 0,
                    synced INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela usuarios
            cursor.execute("""
                CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY,
                    uuid TEXT UNIQUE,
                    nome TEXT NOT NULL,
                    usuario TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    synced INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela change_log
            cursor.execute("""
                CREATE TABLE change_log (
                    id INTEGER PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    data_json TEXT,
                    created_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending'
                )
            """)
            
            conn.commit()
    
    def _insert_test_data(self):
        """Insere dados de teste"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Produtos não sincronizados
            cursor.execute("""
                INSERT INTO produtos (uuid, codigo, nome, preco_venda, estoque, synced)
                VALUES ('uuid-1', 'PROD001', 'Produto Teste 1', 10.50, 100, 0)
            """)
            
            cursor.execute("""
                INSERT INTO produtos (uuid, codigo, nome, preco_venda, estoque, synced)
                VALUES ('uuid-2', 'PROD002', 'Produto Teste 2', 25.00, 50, 0)
            """)
            
            # Produto já sincronizado
            cursor.execute("""
                INSERT INTO produtos (uuid, codigo, nome, preco_venda, estoque, synced)
                VALUES ('uuid-3', 'PROD003', 'Produto Sincronizado', 15.00, 75, 1)
            """)
            
            conn.commit()
    
    def test_get_unsynced_data(self):
        """Testa busca de dados não sincronizados"""
        self._insert_test_data()
        
        async def run_test():
            unsynced = await self.sync_manager._get_unsynced_data('produtos')
            
            # Deve retornar apenas os 2 produtos não sincronizados
            self.assertEqual(len(unsynced), 2)
            self.assertIn('PROD001', [p['codigo'] for p in unsynced])
            self.assertIn('PROD002', [p['codigo'] for p in unsynced])
            self.assertNotIn('PROD003', [p['codigo'] for p in unsynced])
        
        asyncio.run(run_test())
    
    def test_get_unsynced_data_batch_limit(self):
        """Testa limite de lote na busca de dados não sincronizados"""
        # Inserir muitos produtos não sincronizados
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for i in range(1500):  # Mais que o limite padrão de 1000
                cursor.execute("""
                    INSERT INTO produtos (uuid, codigo, nome, preco_venda, synced)
                    VALUES (?, ?, ?, ?, 0)
                """, (f'uuid-{i}', f'PROD{i:04d}', f'Produto {i}', 10.0))
            conn.commit()
        
        async def run_test():
            unsynced = await self.sync_manager._get_unsynced_data('produtos', batch_size=100)
            
            # Deve retornar apenas 100 registros (limite do lote)
            self.assertEqual(len(unsynced), 100)
        
        asyncio.run(run_test())
    
    def test_mark_as_synced(self):
        """Testa marcação de registros como sincronizados"""
        self._insert_test_data()
        
        # Marcar produtos como sincronizados
        self.sync_manager._mark_as_synced('produtos', ['1', '2'])
        
        # Verificar se foram marcados
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT synced FROM produtos WHERE id IN (1, 2)")
            results = cursor.fetchall()
            
            for row in results:
                self.assertEqual(row[0], 1)  # synced = 1
    
    @patch('httpx.AsyncClient.request')
    def test_send_to_server_success(self, mock_request):
        """Testa envio bem-sucedido para o servidor"""
        # Mock da resposta do servidor
        mock_response = Mock()
        mock_response.json.return_value = {'success': True, 'conflicts': []}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        self._insert_test_data()
        
        async def run_test():
            unsynced = await self.sync_manager._get_unsynced_data('produtos')
            success, conflicts = await self.sync_manager.send_to_server('produtos', unsynced)
            
            self.assertTrue(success)
            self.assertEqual(len(conflicts), 0)
        
        asyncio.run(run_test())
    
    @patch('httpx.AsyncClient.request')
    def test_send_to_server_with_conflicts(self, mock_request):
        """Testa envio com conflitos"""
        # Mock da resposta com conflitos
        mock_response = Mock()
        mock_response.json.return_value = {
            'success': True,
            'conflicts': [
                {
                    'local_id': '1',
                    'server_data': {'codigo': 'PROD001', 'nome': 'Produto Server'},
                    'local_data': {'codigo': 'PROD001', 'nome': 'Produto Local'}
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        self._insert_test_data()
        
        async def run_test():
            unsynced = await self.sync_manager._get_unsynced_data('produtos')
            success, conflicts = await self.sync_manager.send_to_server('produtos', unsynced)
            
            self.assertTrue(success)
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0]['local_id'], '1')
        
        asyncio.run(run_test())
    
    @patch('httpx.AsyncClient.request')
    def test_fetch_from_server(self, mock_request):
        """Testa busca de dados do servidor"""
        # Mock da resposta do servidor
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 'server-uuid-1',
                    'codigo': 'SERVPROD001',
                    'nome': 'Produto do Servidor',
                    'preco_venda': 20.0,
                    'estoque': 200
                }
            ],
            'has_more': False,
            'conflicts': []
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        async def run_test():
            server_data, conflicts = await self.sync_manager.fetch_from_server('produtos')
            
            self.assertEqual(len(server_data), 1)
            self.assertEqual(server_data[0]['codigo'], 'SERVPROD001')
            self.assertEqual(len(conflicts), 0)
        
        asyncio.run(run_test())
    
    def test_update_local_data(self):
        """Testa atualização de dados locais"""
        server_data = [
            {
                'id': 'new-uuid',
                'codigo': 'NEWPROD',
                'nome': 'Produto Novo',
                'preco_venda': 30.0,
                'estoque': 150
            }
        ]
        
        async def run_test():
            updated = await self.sync_manager._update_local_data('produtos', server_data)
            
            self.assertEqual(len(updated), 1)
            
            # Verificar se foi inserido no banco
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM produtos WHERE codigo = 'NEWPROD'")
                result = cursor.fetchone()
                
                self.assertIsNotNone(result)
                self.assertEqual(result[2], 'NEWPROD')  # codigo
                self.assertEqual(result[3], 'Produto Novo')  # nome
        
        asyncio.run(run_test())


class TestSyncAllTables(unittest.TestCase):
    """Testes para a função sync_all_tables"""
    
    def setUp(self):
        """Configuração inicial"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Configurar logging para testes
        logging.getLogger('PDVSync').setLevel(logging.CRITICAL)
        
        # Criar estrutura mínima
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE produtos (
                    id INTEGER PRIMARY KEY,
                    codigo TEXT,
                    nome TEXT,
                    synced INTEGER DEFAULT 0
                )
            """)
            conn.commit()
    
    def tearDown(self):
        """Limpeza"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch.dict(os.environ, {'APPDATA': os.path.dirname(os.path.abspath(__file__))})
    @patch('utils.sync_manager.SyncManager')
    def test_sync_all_tables_success(self, mock_sync_manager_class):
        """Testa sincronização bem-sucedida de todas as tabelas"""
        # Mock do SyncManager
        mock_manager = AsyncMock()
        mock_manager._get_unsynced_data.return_value = []
        mock_manager.send_to_server.return_value = (True, [])
        mock_manager.fetch_from_server.return_value = ([], [])
        mock_manager._update_local_data.return_value = []
        
        # Mock do context manager
        mock_sync_manager_class.return_value.__aenter__.return_value = mock_manager
        mock_sync_manager_class.return_value.__aexit__.return_value = None
        
        async def run_test():
            result = await sync_all_tables()
            
            self.assertEqual(result['summary']['status'], 'success')
            self.assertIn('tables', result)
            self.assertIn('summary', result)
            self.assertGreaterEqual(result['summary']['duration_seconds'], 0)
        
        asyncio.run(run_test())


class TestSyncPerformance(unittest.TestCase):
    """Testes de performance para sincronização"""
    
    def setUp(self):
        """Configuração para testes de performance"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Configurar logging
        logging.getLogger('PDVSync').setLevel(logging.CRITICAL)
        
        # Criar tabela com muitos registros
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE produtos (
                    id INTEGER PRIMARY KEY,
                    uuid TEXT,
                    codigo TEXT,
                    nome TEXT,
                    preco_venda REAL,
                    synced INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Inserir 10000 registros para teste de performance
            for i in range(10000):
                cursor.execute("""
                    INSERT INTO produtos (uuid, codigo, nome, preco_venda, synced)
                    VALUES (?, ?, ?, ?, 0)
                """, (f'uuid-{i}', f'PROD{i:05d}', f'Produto {i}', 10.0 + i))
            
            conn.commit()
        
        self.sync_manager = SyncManager(self.db_path)
    
    def tearDown(self):
        """Limpeza"""
        try:
            if hasattr(self.sync_manager, 'client') and self.sync_manager.client:
                asyncio.run(self.sync_manager.client.aclose())
        except:
            pass
        
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_large_dataset_query_performance(self):
        """Testa performance de query com grande volume de dados"""
        async def run_test():
            start_time = datetime.now()
            unsynced = await self.sync_manager._get_unsynced_data('produtos', batch_size=1000)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            # Query deve completar em menos de 5 segundos
            self.assertLess(duration, 5.0)
            # Deve respeitar o limite de lote
            self.assertEqual(len(unsynced), 1000)
        
        asyncio.run(run_test())
    
    def test_mark_as_synced_performance(self):
        """Testa performance da marcação de sincronização"""
        # Preparar lista de IDs
        ids = [str(i) for i in range(1, 1001)]  # 1000 IDs
        
        start_time = datetime.now()
        self.sync_manager._mark_as_synced('produtos', ids)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Marcação deve completar em menos de 2 segundos
        self.assertLess(duration, 2.0)
        
        # Verificar se foram marcados corretamente
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM produtos WHERE synced = 1")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1000)


if __name__ == '__main__':
    # Configurar logging para os testes
    logging.basicConfig(level=logging.CRITICAL)
    
    # Executar testes
    unittest.main(verbosity=2)
