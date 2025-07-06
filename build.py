import PyInstaller.__main__
import os

# Obter o diretório atual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Caminho absoluto para o ícone
icon_path = os.path.join(current_dir, 'assets', 'icon.ico')

# Verificar se o ícone existe
if not os.path.exists(icon_path):
    raise FileNotFoundError(f"Arquivo de ícone não encontrado: {icon_path}")

print(f"Usando ícone: {icon_path}")

# Configurar os argumentos do PyInstaller
args = [
    'main.py',  # Seu arquivo principal
    '--name=PDV',  # Nome do executável
    '--onedir',  # Criar um diretório com todos os arquivos
    '--windowed',  # Não mostrar console
    f'--icon={icon_path}',  # Ícone do executável com caminho absoluto
    '--add-data=views;views',  # Incluir diretório views
    '--add-data=database;database',  # Incluir diretório database
    '--add-data=utils;utils',  # Incluir diretório utils
    '--add-data=assets;assets',  # Incluir diretório assets
    '--add-data=backups;backups',  # Incluir diretório backups
    '--hidden-import=flet',
    '--hidden-import=plotly',
    '--hidden-import=plotly.graph_objs',
    '--hidden-import=plotly.express',
    '--hidden-import=plotly.graph_objs._scatter',
    '--hidden-import=plotly.graph_objs._scattergl',
    '--hidden-import=plotly.graph_objs._scatterpolar',
    '--hidden-import=plotly.graph_objs._scatterpolargl',
    '--hidden-import=plotly.graph_objs._scatterternary',
    '--hidden-import=plotly.graph_objs._scatter3d',
    '--hidden-import=plotly.graph_objs._scattermapbox',
    '--hidden-import=plotly.graph_objs._scattergeo',
    '--hidden-import=plotly.graph_objs._scattercarpet',
    '--hidden-import=plotly.graph_objs._histogram',
    '--hidden-import=plotly.graph_objs._histogram2d',
    '--hidden-import=plotly.graph_objs._histogram2dcontour',
    '--hidden-import=pandas',
    '--hidden-import=numpy',
    '--collect-all=plotly',
    '--collect-all=pandas',
    '--clean',  # Limpar cache antes de construir
    '--noconfirm',  # Não pedir confirmação
]

# Executar o PyInstaller
PyInstaller.__main__.run(args) 