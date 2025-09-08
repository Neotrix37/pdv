# Sistema Híbrido PDV3 - Guia Completo

## Visão Geral

O Sistema Híbrido PDV3 é uma solução **offline-first** que permite operação contínua mesmo sem conexão com a internet, sincronizando automaticamente os dados quando a conexão é restabelecida.

## Arquitetura

### Componentes Principais

1. **Cliente PDV3 (Flet + SQLite)**
   - Interface desktop em Python/Flet
   - Banco de dados local SQLite (`sistema.db`)
   - Repositórios híbridos para cada entidade
   - Sincronizador master centralizado

2. **Backend API (FastAPI + PostgreSQL)**
   - API REST para sincronização
   - Banco de dados PostgreSQL na nuvem
   - Endpoints de CRUD para todas as entidades

### Repositórios Híbridos Implementados

- ✅ **ProdutoRepository** - Produtos com bulk sync
- ✅ **UsuarioRepository** - Usuários do sistema  
- ✅ **ClienteRepository** - Clientes/compradores
- ✅ **VendaRepository** - Vendas e transações
- ✅ **SyncManager** - Coordenador central

## Funcionalidades

### 1. Operação Offline-First
- Todas as operações funcionam localmente
- Dados armazenados no SQLite local
- Interface responsiva sem dependência de internet

### 2. Sincronização Automática
- Detecção automática de conectividade
- Sincronização em background
- Resolução de conflitos automática
- Bulk sync para dados pré-existentes

### 3. Change Log System
- Rastreamento de todas as mudanças locais
- Operações CREATE, UPDATE, DELETE registradas
- Status de sincronização por mudança
- Limpeza automática de logs antigos

### 4. Indicador de Status
- Status visual de conectividade no dashboard
- Feedback em tempo real durante sincronização
- Contadores de mudanças pendentes

## Como Usar

### Inicialização do Sistema

1. **Primeira execução:**
   ```bash
   cd pdv3
   python main.py
   ```

2. **Configurar backend (opcional):**
   ```bash
   # Definir URL do backend
   set BACKEND_URL=http://localhost:8000
   # ou
   set BACKEND_URL=https://seu-backend.railway.app
   ```

### Sincronização Manual

1. **Via Interface:**
   - Clique no botão "Sincronizar" no header do dashboard
   - Aguarde a conclusão da operação
   - Verifique o status no indicador de conexão

2. **Via Código:**
   ```python
   from repositories.sync_manager import SyncManager
   
   async def sincronizar():
       sync_manager = SyncManager()
       resultado = await sync_manager.sincronizar_todas_entidades()
       print(f"Status: {resultado['status']}")
   ```

### Operações Suportadas

#### Produtos
```python
from repositories.produto_repository import ProdutoRepository

repo = ProdutoRepository()

# Criar produto (funciona offline)
produto = repo.create({
    'nome': 'Produto Teste',
    'codigo': '001',
    'preco_venda': 10.0,
    'quantidade': 100
})

# Buscar produtos (híbrido: servidor -> local)
produtos = repo.get_all()

# Atualizar produto
repo.update(produto['id'], {'preco_venda': 12.0})

# Deletar produto
repo.delete(produto['id'])
```

#### Usuários
```python
from repositories.usuario_repository import UsuarioRepository

repo = UsuarioRepository()

# Operações CRUD similares aos produtos
usuarios = repo.get_all()
usuario = repo.create({
    'nome': 'João Silva',
    'usuario': 'joao',
    'senha': 'hash_senha',
    'is_admin': False
})
```

#### Clientes e Vendas
- Mesma interface dos repositórios acima
- Suporte completo a operações offline
- Sincronização automática quando online

## Estrutura de Arquivos

```
pdv3/
├── repositories/
│   ├── produto_repository.py      # Repositório de produtos
│   ├── usuario_repository.py      # Repositório de usuários
│   ├── cliente_repository.py      # Repositório de clientes
│   ├── venda_repository.py        # Repositório de vendas
│   └── sync_manager.py            # Sincronizador master
├── database/
│   ├── sistema.db                 # Banco SQLite local
│   └── migrations.py              # Migrações de esquema
├── views/
│   └── dashboard_view.py          # Interface principal
└── utils/
    └── status_indicator.py        # Indicador de status
```

## Fluxo de Sincronização

### 1. Verificação de Conectividade
```
Cliente → GET /healthz → Backend
```

### 2. Bulk Sync (Primeira sincronização)
```
1. Identificar produtos locais não sincronizados
2. Enviar produtos para o servidor
3. Resolver conflitos por código de produto
4. Marcar produtos como sincronizados
```

### 3. Sync Incremental
```
1. Buscar mudanças pendentes no change_log
2. Processar operações CREATE, UPDATE, DELETE
3. Enviar para endpoints correspondentes
4. Marcar mudanças como sincronizadas
```

### 4. Resolução de Conflitos
- **Produtos duplicados:** Atualização por código
- **Registros não encontrados:** Fallback UPDATE→CREATE
- **Erros de rede:** Retry automático com backoff

## Endpoints Backend

### Produtos
- `GET /api/produtos/` - Listar produtos
- `POST /api/produtos/` - Criar produto
- `PUT /api/produtos/{uuid}` - Atualizar produto
- `DELETE /api/produtos/{uuid}` - Deletar produto

### Outras Entidades (Pendentes)
- `GET/POST/PUT/DELETE /api/usuarios/{uuid}`
- `GET/POST/PUT/DELETE /api/clientes/{uuid}`
- `GET/POST/PUT/DELETE /api/vendas/{uuid}`

## Monitoramento e Debug

### Logs de Sincronização
```python
# Verificar status de sincronização
sync_manager = SyncManager()
status = await sync_manager.obter_status_sincronizacao()

print(f"Backend online: {status['backend_online']}")
for entidade, info in status['entidades'].items():
    print(f"{entidade}: {info['mudancas_pendentes']} pendentes")
```

### Limpeza de Change Log
```python
# Limpar entradas antigas (>7 dias)
resultado = await sync_manager.limpar_change_log_sincronizado()
print(f"Removidas: {resultado['entradas_removidas']} entradas")
```

### Verificação de Integridade
```sql
-- Verificar mudanças pendentes
SELECT entity_type, COUNT(*) 
FROM change_log 
WHERE status = 'pending' 
GROUP BY entity_type;

-- Verificar produtos não sincronizados
SELECT COUNT(*) 
FROM produtos 
WHERE synced = 0 OR synced IS NULL;
```

## Troubleshooting

### Problemas Comuns

1. **Backend offline**
   - Verificar URL em `BACKEND_URL`
   - Confirmar que o servidor está rodando
   - Testar conectividade: `curl http://localhost:8000/healthz`

2. **Sincronização falha**
   - Verificar logs de erro no console
   - Confirmar esquemas de dados compatíveis
   - Limpar change_log se necessário

3. **Produtos duplicados**
   - Sistema resolve automaticamente por código
   - Verificar unicidade dos códigos de produto

4. **Performance lenta**
   - Limpar change_log periodicamente
   - Verificar índices no SQLite
   - Monitorar tamanho do banco de dados

### Comandos Úteis

```bash
# Verificar tamanho do banco
ls -lh database/sistema.db

# Backup do banco
cp database/sistema.db database/backup_$(date +%Y%m%d).db

# Reset completo (cuidado!)
rm database/sistema.db
python database/migrations.py
```

## Próximos Passos

### Pendente no Backend
- [ ] Implementar endpoints para usuários
- [ ] Implementar endpoints para clientes  
- [ ] Implementar endpoints para vendas
- [ ] Adicionar autenticação JWT
- [ ] Implementar paginação nas listagens

### Melhorias Futuras
- [ ] Sincronização em tempo real (WebSockets)
- [ ] Compressão de dados na sincronização
- [ ] Sincronização seletiva por período
- [ ] Interface de administração web
- [ ] Relatórios de sincronização detalhados

## Conclusão

O Sistema Híbrido PDV3 oferece uma solução robusta para operação offline/online, garantindo continuidade do negócio mesmo com problemas de conectividade. A arquitetura modular permite fácil extensão e manutenção, enquanto a sincronização automática mantém os dados consistentes entre cliente e servidor.

Para suporte técnico ou dúvidas, consulte os logs de sincronização e verifique a conectividade com o backend antes de reportar problemas.
