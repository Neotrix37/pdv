# Instruções para Correção de Problemas do Sistema PDV

Este documento contém instruções para corrigir os seguintes problemas no sistema PDV:

1. Erro "no such column named total" ao finalizar vendas
2. Erro ao gerar relatório financeiro
3. Valores incorretos após restauração de backup

## Diagnóstico dos Problemas

### 1. Erro "no such column named total"

Este erro ocorre porque a coluna `total` está ausente na tabela `vendas` em algumas instalações ou após restauração de backups antigos. O sistema tenta acessar esta coluna, mas ela não existe no banco de dados.

### 2. Erro ao gerar relatório financeiro

Este problema está relacionado ao primeiro, pois o relatório financeiro também utiliza a coluna `total` da tabela `vendas` para calcular métricas financeiras.

### 3. Valores incorretos após restauração de backup

Este problema ocorre porque os backups antigos podem não ter a coluna `total` ou podem ter valores inconsistentes nesta coluna. Além disso, alguns backups podem não ter a tabela `retiradas_caixa` ou podem ter uma estrutura incompleta.

## Solução

Foi criado um script de correção que resolve todos estes problemas automaticamente. O script:

1. Adiciona a coluna `total` à tabela `vendas` se ela não existir
2. Atualiza os valores da coluna `total` com base nos itens de venda
3. Corrige os backups existentes, adicionando a coluna `total` e a tabela `retiradas_caixa`
4. Cria índices para melhorar o desempenho do banco de dados

## Como Usar o Script de Correção

### Passo 1: Fechar o Sistema

Certifique-se de que o sistema PDV não está em execução antes de iniciar a correção.

### Passo 2: Executar o Script de Correção

1. Abra o prompt de comando (cmd) ou PowerShell
2. Navegue até o diretório do sistema PDV
3. Execute o comando:

```
python corrigir_problemas_sistema.py
```

### Passo 3: Verificar os Resultados

O script exibirá um resumo das correções realizadas. Certifique-se de que todos os problemas foram corrigidos com sucesso.

### Passo 4: Reiniciar o Sistema

Após a execução do script, reinicie o sistema PDV para aplicar todas as alterações.

## Observações Importantes

- O script faz backup dos arquivos originais antes de realizar qualquer alteração
- Se ocorrer algum erro durante a execução do script, os logs exibidos ajudarão a identificar o problema
- Recomenda-se fazer um backup manual do banco de dados antes de executar o script, por precaução

## Prevenção de Problemas Futuros

Para evitar que estes problemas ocorram novamente:

1. Sempre use a versão mais recente do sistema
2. Não restaure backups muito antigos sem executar o script de correção
3. Após restaurar qualquer backup, execute o script de correção para garantir a integridade dos dados

## Suporte

Se precisar de ajuda adicional, entre em contato com o suporte técnico.