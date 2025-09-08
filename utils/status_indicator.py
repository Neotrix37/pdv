import flet as ft
import asyncio
import threading
import time
from utils.connection_status import connection_status

class StatusIndicator(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.status_text = ft.Text(
            value="⚡ Offline",
            size=12,
            color=ft.colors.ORANGE,
            weight=ft.FontWeight.BOLD
        )
        self.sync_icon = ft.Icon(
            ft.icons.SYNC,
            size=16,
            color=ft.colors.GREY_400
        )
        self.is_checking = False
        self.monitoring_thread = None
        self.stop_monitoring = False
        
    def build(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    self.sync_icon,
                    self.status_text
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=15,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_300)
        )
    
    def start_monitoring(self):
        """Inicia o monitoramento de conexão em background usando threading."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
    
    def _monitoring_loop(self):
        """Loop de monitoramento que roda em thread separada."""
        while not self.stop_monitoring:
            try:
                if not self.is_checking:
                    self.is_checking = True
                    
                    # Animar ícone durante verificação
                    self.sync_icon.name = ft.icons.SYNC
                    self.sync_icon.color = ft.colors.BLUE
                    if self.page:
                        self.update()
                    
                    # Verificar conexão usando asyncio em thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        is_online = loop.run_until_complete(connection_status.check_connection())
                    finally:
                        loop.close()
                    
                    # Atualizar interface
                    if is_online:
                        self.status_text.value = "🌐 Online"
                        self.status_text.color = ft.colors.GREEN
                        self.sync_icon.name = ft.icons.CLOUD_DONE
                        self.sync_icon.color = ft.colors.GREEN
                    else:
                        self.status_text.value = "⚡ Offline"
                        self.status_text.color = ft.colors.ORANGE
                        self.sync_icon.name = ft.icons.CLOUD_OFF
                        self.sync_icon.color = ft.colors.ORANGE
                    
                    if self.page:
                        self.update()
                    
                    self.is_checking = False
                
                # Aguardar 30 segundos antes da próxima verificação
                time.sleep(30)
                
            except Exception as e:
                print(f"Erro no monitoramento de conexão: {e}")
                self.is_checking = False
                time.sleep(30)
    
    def stop_monitoring_thread(self):
        """Para o monitoramento de conexão."""
        self.stop_monitoring = True
