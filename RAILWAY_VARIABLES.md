# 🔧 Variáveis de Ambiente para PDV3 no Railway

## 📋 Variáveis Necessárias

### 1. **PORT** (Automática)
- **Valor:** Fornecida automaticamente pelo Railway
- **Descrição:** Porta onde a aplicação será executada
- **Configuração:** Não precisa configurar

### 2. **BACKEND_URL** (Opcional)
- **Valor:** `https://prototipo-production-c729.up.railway.app/api`
- **Descrição:** URL do backend para sincronização
- **Configuração:** Opcional (já configurado no config.json)

### 3. **FLET_WEB_RENDERER** (Opcional)
- **Valor:** `auto`
- **Descrição:** Renderer web do Flet
- **Configuração:** Opcional (padrão: auto)

### 4. **PYTHONPATH** (Opcional)
- **Valor:** `/app`
- **Descrição:** Path Python para imports
- **Configuração:** Opcional (configurado no código)

## 🚀 Como Configurar no Railway

### Via Railway Dashboard:
1. Acesse seu projeto PDV3 no Railway
2. Vá na aba **"Variables"**
3. Adicione apenas se necessário:

```
BACKEND_URL=https://prototipo-production-c729.up.railway.app/api
```

### Via Railway CLI:
```bash
railway variables set BACKEND_URL="https://prototipo-production-c729.up.railway.app/api"
```

## ✅ Variáveis Já Configuradas

- **PORT:** Railway fornece automaticamente
- **server_url:** Configurado no config.json
- **sync_enabled:** Configurado no config.json (true)
- **sync_interval_seconds:** Configurado no config.json (30)

## 🔍 Verificar Configuração

Após deploy, verifique se a aplicação está usando as configurações corretas:
- URL do backend deve apontar para produção
- Sincronização deve estar habilitada
- Porta deve ser dinâmica (Railway)

## ⚠️ Importante

O PDV3 web funcionará principalmente com as configurações do `config.json`. As variáveis de ambiente são opcionais e servem para sobrescrever configurações se necessário.
