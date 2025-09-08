# Instruções para Correção de Problemas do Sistema

## Problemas Identificados

### 1. Tabela retiradas_caixa
O sistema está apresentando erro `no such table: retiradas_caixa` quando você acessa a funcionalidade de saques. Isso acontece porque:

1. A tabela `retiradas_caixa` não foi criada no banco de dados atual
2. Quando você restaura um backup antigo, a tabela não existe no backup

### 2. Problema de Estoque
Quando você restaura um backup antigo, os produtos aparecem com 0 estoque. Isso pode acontecer por:

1. Valores NULL na coluna estoque
2. Tipos de dados incorretos (INTEGER em vez de REAL)
3. Valores negativos no estoque
4. Problemas na estrutura da tabela produtos

## Solução

## Solução

### Passo 1: Diagnosticar Problemas

Primeiro, execute o script de diagnóstico para identificar todos os problemas:

```bash
python diagnosticar_estoque.py
```

Este script irá:
- Verificar a estrutura da tabela produtos
- Identificar produtos com estoque zero
- Detectar valores NULL ou negativos
- Verificar tipos de dados incorretos

### Passo 2: Corrigir o Banco de Dados Atual

Execute o script de correção da tabela retiradas_caixa:

```bash
python corrigir_retiradas_caixa.py
```

Este script irá:
- Verificar se a tabela `retiradas_caixa` existe
- Criar a tabela se não existir
- Adicionar colunas ausentes se necessário
- Criar o trigger para atualização automática

### Passo 3: Corrigir Problemas de Estoque

Execute o script de correção de estoque:

```bash
python corrigir_estoque_backups.py
```

Este script irá:
- Corrigir valores NULL para 0
- Corrigir valores negativos para 0
- Converter tipos de dados incorretos
- Verificar a estrutura da tabela produtos

### Passo 4: Corrigir Backups Existentes (Opcional)

Se você tem backups antigos que também precisam ser corrigidos:

```bash
python corrigir_backups.py
```

Este script irá:
- Fazer backup dos backups originais
- Corrigir todos os backups existentes
- Adicionar a tabela `retiradas_caixa` em todos os backups

### Passo 5: Verificar se Funcionou

1. Execute o sistema: `python main.py`
2. Acesse a funcionalidade de saques
3. Verifique se os produtos têm estoque correto
4. Teste a funcionalidade de vendas

## Melhorias Implementadas

### 1. Inicialização Automática
- A tabela `retiradas_caixa` agora é criada automaticamente na inicialização do banco
- O trigger de atualização também é criado automaticamente

### 2. Restauração de Backup Melhorada
- Quando você restaura um backup, o sistema automaticamente verifica e cria a tabela se necessário

### 3. Estrutura Completa da Tabela retiradas_caixa
A tabela `retiradas_caixa` inclui todas as colunas necessárias:
- `id` - Identificador único
- `usuario_id` - ID do usuário que fez o saque
- `aprovador_id` - ID do usuário que aprovou (opcional)
- `valor` - Valor do saque
- `motivo` - Motivo do saque
- `observacao` - Observações adicionais
- `origem` - Origem do dinheiro (vendas, lucro, etc.)
- `status` - Status do saque (pendente, aprovado, etc.)
- `data_retirada` - Data da retirada
- `data_aprovacao` - Data da aprovação
- `created_at` - Data de criação
- `updated_at` - Data de atualização

### 4. Correção Automática de Estoque
- Verificação automática de valores NULL
- Correção de valores negativos
- Conversão de tipos de dados
- Verificação da estrutura da tabela produtos

## Prevenção de Problemas Futuros

### 1. Sempre Execute o Script Após Restaurar Backup
Se você restaurar um backup antigo, execute:
```bash
python corrigir_retiradas_caixa.py
python diagnosticar_estoque.py
```

### 2. Verificação Automática
O sistema agora verifica automaticamente:
- A existência da tabela retiradas_caixa na inicialização
- Problemas de estoque após restauração de backup

### 3. Backup dos Backups
Os scripts fazem backup dos backups originais antes de modificá-los:
- `corrigir_backups.py` - para tabela retiradas_caixa
- `corrigir_estoque_backups.py` - para problemas de estoque

## Troubleshooting

### Se o erro persistir:
1. Verifique se o script foi executado com sucesso
2. Verifique se não há erros de permissão de arquivo
3. Tente reiniciar o sistema
4. Se necessário, execute o script novamente

### Se houver problemas com backups:
1. Os backups originais estão salvos em `backups/original_YYYYMMDD_HHMMSS/`
2. Você pode restaurar um backup original se necessário
3. Execute o script de correção novamente

## Logs de Debug

Os scripts incluem logs detalhados para ajudar na identificação de problemas:
- ✅ Indica sucesso
- ❌ Indica erro
- 📁 Indica informações sobre arquivos

## Contato

Se você encontrar problemas que não foram resolvidos por estas instruções, verifique os logs de erro e entre em contato com o suporte técnico.
