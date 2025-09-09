#!/usr/bin/env python3
"""
Entry point para hospedagem web do PDV3
"""
import flet as ft
import os
import sys
import platform

# Adicionar o diretório atual ao path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar modo web antes de importar módulos
os.environ['WEB_MODE'] = 'true'

# Importar o main original
from main import main

def web_main(page: ft.Page):
    """Wrapper para execução web com configurações específicas."""
    # Forçar modo web
    page.platform = "web"
    
    # Configurações específicas para web
    page.title = "PDV3 - Sistema de Gestão"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    
    # Chamar o main original
    main(page)

if __name__ == "__main__":
    # Configurações para hospedagem web
    port = int(os.getenv("PORT", 8080))
    
    ft.app(
        target=web_main,
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host="0.0.0.0",
        assets_dir="assets",
        upload_dir="uploads",
        web_renderer="auto"
    )
