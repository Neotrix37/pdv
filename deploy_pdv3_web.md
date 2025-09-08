# 🌐 Deploy PDV3 como Aplicação Web

## ✅ Arquivos de Deploy Criados

### 1. Arquivos de Configuração
- ✅ **main_web.py** - Entry point para hospedagem web
- ✅ **Procfile** - Comando de inicialização
- ✅ **runtime.txt** - Versão Python (3.10.12)
- ✅ **railway.json** - Configurações Railway
- ✅ **requirements.txt** - Dependências atualizadas
- ✅ **.gitignore** - Arquivos a ignorar no Git

### 2. Configurações Aplicadas
- **Flet atualizado** para versão 0.24.1 (suporte web melhorado)
- **Entry point web** configurado para porta dinâmica
- **Modo web forçado** para compatibilidade com hospedagem
- **Healthcheck** configurado para rota raiz

## 🚀 Deploy no Railway

### Comandos Git:
```bash
cd c:\Users\saide\sinc\pdv3
git init
git add .
git commit -m "feat: configurar PDV3 para deploy web"
git branch -M main
git remote add origin https://github.com/seu-usuario/pdv3-web.git
git push -u origin main
```

### Via Railway Dashboard:
1. Criar novo projeto no Railway
2. Conectar repositório GitHub
3. Deploy automático será iniciado

### Via Railway CLI:
```bash
cd c:\Users\saide\sinc\pdv3
railway login
railway init
railway up
```

## 🔧 Configurações Técnicas

- **Porta:** Dinâmica (Railway fornece via $PORT)
- **Host:** 0.0.0.0 (aceita conexões externas)
- **Renderer:** Auto (otimizado para web)
- **Assets:** Diretório assets/ incluído
- **Uploads:** Diretório uploads/ configurado

## 📱 Funcionalidades Web

O PDV3 funcionará como aplicação web com:
- Interface responsiva
- Sincronização com backend
- Armazenamento local (browser storage)
- Todas as funcionalidades do desktop

## 🌐 Acesso

Após deploy, a aplicação estará disponível em:
`https://seu-projeto.railway.app`

## ⚠️ Considerações

- **Banco local:** SQLite funcionará via browser storage
- **Arquivos:** Uploads limitados pelo browser
- **Performance:** Pode ser mais lenta que versão desktop
- **Offline:** Funcionalidade limitada sem conexão
