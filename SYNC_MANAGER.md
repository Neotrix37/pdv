# Sistema de Sincronização PDV

## Visão Geral
Módulo responsável por gerenciar a sincronização entre o banco de dados local e o servidor remoto.

## Índice
- [Configuração](#configuração)
- [Uso Básico](#uso-básico)
- [Referência da API](#referência-da-api)
- [Tratamento de Erros](#tratamento-de-erros)
- [Exemplos](#exemplos)
- [Logs](#logs)

## Configuração

### Variáveis de Ambiente
```env
SYNC_AUTH_TOKEN=seu_token_aqui
```

### Tabelas Sincronizadas
- ✅ Produtos
- ✅ Categorias
- ✅ Clientes
- ✅ Vendas
- ✅ Itens de Venda
- ⬇️ Apenas Download: Usuários
- ✅ Fornecedores
- ✅ Despesas
- ✅ Contas a Pagar
- ✅ Contas a Receber

## Uso Básico

### Sincronização Completa
```python
from utils.sync_manager import sync_all_tables

async def executar_sincronizacao():
    resultado = await sync_all_tables()
    print(f"Sincronização concluída: {resultado['summary']['status']}")
```

### Uso Avançado
```python
from utils.sync_manager import SyncManager

async def sincronizar_produtos():
    async with SyncManager('caminho/banco.db') as manager:
        # Enviar dados locais
        sucesso, conflitos = await manager.send_to_server('produtos', produtos)
        
        # Buscar atualizações
        dados, conflitos = await manager.fetch_from_server('produtos')
```

## Referência da API

### `SyncManager`
Classe principal para gerenciar a sincronização.

#### Métodos
- `send_to_server(table_name, records)`
  - Envia registros para o servidor
  - Retorna: `(sucesso: bool, conflitos: List[Dict])`

- `fetch_from_server(table_name)`
  - Busca atualizações do servidor
  - Retorna: `(dados: List[Dict], conflitos: List[Dict])`

## Tratamento de Erros
O sistema implementa:
- ✅ Retry automático (3 tentativas)
- ✅ Log detalhado
- ✅ Armazenamento de conflitos
- ✅ Tratamento de falhas de rede

## Exemplos

### Enviar Dados
```python
produtos = [
    {"id": 1, "nome": "Produto A", "preco": 10.99},
    {"id": 2, "nome": "Produto B", "preco": 20.50}
]
sucesso, conflitos = await manager.send_to_server('produtos', produtos)
```

### Buscar Atualizações
```python
dados, conflitos = await manager.fetch_from_server('produtos')
for produto in dados:
    print(f"Produto: {produto['nome']}")
```

## Logs
Os logs são armazenados em:
```
~/pdv_sync.log
```

### Níveis de Log
- `INFO`: Operações normais
- `WARNING`: Problemas recuperáveis
- `ERROR`: Falhas graves
- `CRITICAL`: Erros fatais

## Dicas
1. Sempre use `async with` para garantir o fechamento correto das conexões
2. Verifique sempre o status de retorno das operações
3. Monitore os logs regularmente
4. Implemente um mecanismo de notificação para erros críticos

## Suporte
Para suporte, entre em contato com a equipe de desenvolvimento.
