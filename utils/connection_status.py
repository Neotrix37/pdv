import asyncio
import httpx
import json
import os
from typing import Optional, Dict, Any

class ConnectionStatus:
    def __init__(self):
        self.is_online = False
        self.last_check = None
        self.server_url = self._get_server_url()
        
    def _get_server_url(self) -> str:
        """Obtém a URL do servidor do arquivo de configuração."""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('server_url', 'http://127.0.0.1:8000')
        except Exception:
            pass
        return 'http://127.0.0.1:8000'
    
    async def check_connection(self) -> bool:
        """Verifica se o backend está online fazendo uma requisição ao endpoint /healthz."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Tentar primeiro o endpoint /healthz direto
                try:
                    response = await client.get(f"{self.server_url}/healthz")
                    if response.status_code == 200:
                        self.is_online = True
                        return True
                except:
                    pass
                
                # Se falhar, tentar sem /api no final (caso server_url já inclua /api)
                base_url = self.server_url.replace('/api', '') if self.server_url.endswith('/api') else self.server_url
                response = await client.get(f"{base_url}/healthz")
                self.is_online = response.status_code == 200
                return self.is_online
        except Exception as e:
            print(f"Erro na verificação de conexão: {e}")
            self.is_online = False
            return False
    
    def get_status_text(self) -> str:
        """Retorna o texto do status de conexão."""
        return "🌐 Online" if self.is_online else "⚡ Offline"
    
    def get_status_color(self):
        """Retorna a cor do status de conexão."""
        import flet as ft
        return ft.colors.GREEN if self.is_online else ft.colors.ORANGE

# Instância global para ser usada em toda a aplicação
connection_status = ConnectionStatus()
