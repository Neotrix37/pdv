@echo off
echo Configurando deploy do PDV3 como aplicacao web...
echo.

cd /d "c:\Users\saide\sinc\pdv3"

echo 1. Inicializando repositorio Git...
git init

echo 2. Adicionando arquivos...
git add .

echo 3. Fazendo commit inicial...
git commit -m "feat: configurar PDV3 para deploy web - Flet app hospedada"

echo 4. Configurando branch main...
git branch -M main

echo.
echo ✅ Repositorio configurado!
echo.
echo Proximos passos:
echo 1. Criar repositorio no GitHub
echo 2. Adicionar remote: git remote add origin https://github.com/seu-usuario/pdv3-web.git
echo 3. Push: git push -u origin main
echo 4. Conectar no Railway Dashboard
echo.
echo Ou usar Railway CLI:
echo railway login
echo railway init
echo railway up
echo.
pause
