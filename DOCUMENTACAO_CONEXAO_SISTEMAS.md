# 🔗 Documentação de Conexão entre Sistemas Offline e Online

## 📋 Visão Geral

Esta documentação descreve o que precisa ser implementado e melhorado para conectar completamente o sistema offline existente com o sistema online (backend).

## ✅ O que JÁ ESTÁ IMPLEMENTADO

### Backend Pronto para Sincronização
- ✅ **Endpoints de Sincronização** para todas as tabelas:
  - `/sync/products` (GET/POST)
  - `/sync/customers` (GET/POST) 
  - `/sync/sales` (GET/POST)
  - `/sync/users` (GET/POST)
  - `/sync/employees` (GET/POST)
  - `/sync/debts` (GET/POST) ✅ **NOVO**
  - `/sync/accounts-payable` (GET/POST) ✅ **NOVO**
  - `/sync/cash-movements` (GET/POST) ✅ **NOVO**

- ✅ **Estrutura de Dados** com campos de sincronização:
  - `last_updated` timestamp
  - `synced` boolean
  - `device_id` para resolução de conflitos

- ✅ **Lógica de Sincronização** genérica:
  - Download incremental baseado em timestamp
  - Upload com resolução de conflitos
  - Estratégia "Last-Write-Wins"

### Sistema Offline Existente
- ✅ Aplicação cliente desenvolvida
- ✅ Interface de usuário funcional
- ✅ Coleta de dados offline

## 🚨 O que PRECISA SER MELHORADO/CONECTADO

### 1. **Implementação da Lógica de Sincronização no Cliente**

#### 📱 No Aplicativo Offline:
```javascript
// 1. Sistema de Fila para Operações Offline
class SyncQueue {
  constructor() {
    this.queue = [];
    this.isSyncing = false;
  }
  
  addOperation(operation) {
    this.queue.push(operation);
    this.processQueue();
  }
  
  async processQueue() {
    if (this.isSyncing || this.queue.length === 0) return;
    
    this.isSyncing = true;
    const operation = this.queue.shift();
    
    try {
      await this.executeOperation(operation);
    } catch (error) {
      console.error('Sync error:', error);
      this.queue.unshift(operation); // Re-add to queue
    } finally {
      this.isSyncing = false;
      this.processQueue();
    }
  }
}

// 2. Service Worker para Sincronização em Background
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-data') {
    event.waitUntil(syncAllData());
  }
});

async function syncAllData() {
  const tables = ['sales', 'products', 'customers', 'debts', 'accounts-payable', 'cash-movements'];
  
  for (const table of tables) {
    const unsyncedData = await getUnsyncedData(table);
    if (unsyncedData.length > 0 && navigator.onLine) {
      await api.post(`/sync/${table}`, {
        device_id: getDeviceId(),
        data: unsyncedData
      });
      await markAsSynced(table, unsyncedData);
    }
  }
}
```

### 2. **Armazenamento Local Eficiente**

#### 🗄️ Configuração do IndexedDB:
```javascript
// Database schema para dados offline
const db = new Dexie('OfflineStore');

db.version(2).stores({
  sales: 'id, sale_number, user_id, last_updated, synced',
  products: 'id, name, price, last_updated, synced',
  customers: 'id, name, email, last_updated, synced',
  debts: 'id, customer_id, amount, due_date, last_updated, synced',
  accounts_payable: 'id, supplier_id, amount, due_date, last_updated, synced',
  cash_movements: 'id, type, amount, description, last_updated, synced',
  sync_queue: '++id, operation, data, retry_count',
  sync_status: 'table, last_sync_time, pending_count'
});
```

### 3. **Interface de Sincronização no Frontend**

#### 🎨 Botão e Indicador de Sincronização:
```javascript
// Componente de Status de Sincronização
function SyncStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingSync, setPendingSync] = useState(0);
  const [lastSync, setLastSync] = useState(null);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleSync = async () => {
    try {
      await syncAllData();
      setPendingSync(0);
      setLastSync(new Date());
    } catch (error) {
      console.error('Sync failed:', error);
    }
  };

  return (
    <div className="sync-status">
      <span className={`status ${isOnline ? 'online' : 'offline'}`}>
        {isOnline ? '🟢 Online' : '🔴 Offline'}
      </span>
      {pendingSync > 0 && (
        <span className="pending">
          {pendingSync} pendentes
        </span>
      )}
      <button onClick={handleSync} disabled={!isOnline}>
        🔄 Sincronizar
      </button>
      {lastSync && (
        <span className="last-sync">
          Última sincronização: {formatDate(lastSync)}
        </span>
      )}
    </div>
  );
}
```

### 4. **Tratamento de Erros e Retry Automático**

#### 🔄 Lógica de Retry:
```javascript
class SyncManager {
  constructor() {
    this.maxRetries = 3;
    this.retryDelay = 5000; // 5 seconds
  }
  
  async syncWithRetry(table, data) {
    let retries = 0;
    
    while (retries < this.maxRetries) {
      try {
        const response = await api.post(`/sync/${table}`, {
          device_id: getDeviceId(),
          data: data
        });
        
        return response.data;
      } catch (error) {
        retries++;
        
        if (retries === this.maxRetries) {
          throw new Error(`Sync failed after ${this.maxRetries} attempts`);
        }
        
        await this.delay(this.retryDelay * retries);
      }
    }
  }
  
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### 5. **Monitoramento e Logs**

#### 📊 Dashboard de Sincronização:
```javascript
// Coletar métricas de sincronização
const syncMetrics = {
  totalOperations: 0,
  successfulOperations: 0,
  failedOperations: 0,
  averageSyncTime: 0,
  lastSyncTimestamp: null,
  pendingOperations: 0
};

// Enviar métricas para análise
function sendSyncMetrics() {
  if (navigator.onLine) {
    analytics.track('sync_metrics', syncMetrics);
  }
}

// Logs detalhados para debugging
function logSyncOperation(operation, success, details = {}) {
  console.log(`[SYNC] ${operation}: ${success ? '✅' : '❌'}`, details);
  
  // Armazenar log localmente
  const logEntry = {
    timestamp: new Date(),
    operation,
    success,
    details,
    deviceId: getDeviceId()
  };
  
  storeLogEntry(logEntry);
}
```

## 🧪 Testes Necessários

### 1. **Teste de Conectividade**
```javascript
// Testar se os endpoints respondem
testEndpoints() {
  const endpoints = [
    '/sync/sales',
    '/sync/products', 
    '/sync/debts',
    '/sync/accounts-payable',
    '/sync/cash-movements'
  ];
  
  endpoints.forEach(async endpoint => {
    try {
      const response = await api.get(endpoint);
      console.log(`${endpoint}: ✅`);
    } catch (error) {
      console.log(`${endpoint}: ❌`, error.message);
    }
  });
}
```

### 2. **Teste de Sincronização Offline/Online**
```javascript
// Simular cenários de conexão
async function testSyncScenarios() {
  // 1. Criar dados offline
  const offlineData = createTestData();
  
  // 2. Simular offline
  mockNetworkStatus(false);
  
  // 3. Tentar sincronizar (deve falhar)
  try {
    await syncData();
    console.log('❌ Sync should have failed in offline mode');
  } catch (error) {
    console.log('✅ Sync correctly failed in offline mode');
  }
  
  // 4. Simular online
  mockNetworkStatus(true);
  
  // 5. Sincronizar deve funcionar
  try {
    await syncData();
    console.log('✅ Sync worked in online mode');
  } catch (error) {
    console.log('❌ Sync failed in online mode:', error);
  }
}
```

### 3. **Teste de Conflitos**
```javascript
// Testar resolução de conflitos
testConflictResolution() {
  // Criar versões conflitantes do mesmo registro
  const localRecord = { id: 1, last_updated: new Date('2024-01-01') };
  const remoteRecord = { id: 1, last_updated: new Date('2024-01-02') };
  
  // A versão remota deve "vencer" por ser mais recente
  const result = resolveConflict(localRecord, remoteRecord);
  
  if (result === remoteRecord) {
    console.log('✅ Conflict resolution working correctly');
  } else {
    console.log('❌ Conflict resolution failed');
  }
}
```

## 🔧 Próximos Passos de Implementação

### Fase 1: Implementação Básica (1-2 dias)
1. ✅ Configurar IndexedDB no cliente
2. ✅ Implementar fila de sincronização
3. ✅ Criar service worker para sync em background
4. ✅ Adicionar botão de sincronização na UI

### Fase 2: Tratamento de Erros (1 dia)
1. ✅ Implementar retry automático
2. ✅ Adicionar logs de erro
3. ✅ Criar dashboard de status

### Fase 3: Otimização (1 dia)
1. ✅ Compressão de dados
2. ✅ Sincronização delta
3. ✅ Cache inteligente

### Fase 4: Monitoramento (1 dia)
1. ✅ Métricas de performance
2. ✅ Alertas de falha
3. ✅ Dashboard administrativo

## 🆘 Troubleshooting Comum

### Problema: "Sync não inicia"
**Solução**: Verificar se o service worker está registrado corretamente

### Problema: "Dados não aparecem após sync"
**Solução**: Verificar se os IDs estão sendo gerados corretamente no cliente

### Problema: "Conflitos não resolvidos"
**Solução**: Implementar estratégia de merge específica por tabela

### Problema: "Sync muito lento"
**Solução**: Implementar compressão e sincronização delta

## 📞 Suporte

Para issues de sincronização, incluir:
- ID do dispositivo
- Timestamp do erro
- Logs do console
- Status da conexão
- Quantidade de registros pendentes

**Última atualização**: {{DATA_ATUAL}}
**Versão do Sync**: 1.0.0
```