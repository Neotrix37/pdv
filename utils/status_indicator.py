import flet as ft
import asyncio
import threading
import time
from datetime import datetime, timedelta
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
        self.last_sync_text = ft.Text(
            value="Nunca sincronizado",
            size=10,
            color=ft.colors.GREY_600,
            italic=True
        )
        self.sync_progress = ft.ProgressBar(
            width=100,
            height=3,
            visible=False,
            color=ft.colors.BLUE,
            bgcolor=ft.colors.GREY_300
        )
        self.is_checking = False
        self.is_syncing = False
        self.monitoring_thread = None
        self.stop_monitoring = False
        self.last_sync_time = None
        self.connection_quality = "unknown"  # unknown, good, poor, offline
        
    def build(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.sync_icon,
                            self.status_text
                        ],
                        spacing=5,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    self.sync_progress,
                    self.last_sync_text
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=15,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_300),
            tooltip="Status da conexão e sincronização"
        )
    
    def start_monitoring(self):
        """Inicia o monitoramento de conexão em background usando threading."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
    
    def _monitoring_loop(self):
        """Loop de monitoramento aprimorado que roda em thread separada."""
        while not self.stop_monitoring:
            try:
                if not self.is_checking and not self.is_syncing:
                    self.is_checking = True
                    
                    # Animar ícone durante verificação
                    self.sync_icon.name = ft.icons.SYNC
                    self.sync_icon.color = ft.colors.BLUE
                    if self.page:
                        self.update()
                    
                    # Verificar conexão com medição de latência
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        start_time = time.time()
                        is_online = loop.run_until_complete(connection_status.check_connection())
                        response_time = time.time() - start_time
                        
                        # Determinar qualidade da conexão
                        if is_online:
                            if response_time < 1.0:
                                self.connection_quality = "good"
                            elif response_time < 3.0:
                                self.connection_quality = "poor"
                            else:
                                self.connection_quality = "poor"
                        else:
                            self.connection_quality = "offline"
                            
                    finally:
                        loop.close()
                    
                    # Atualizar interface baseado na qualidade da conexão
                    if is_online:
                        if self.connection_quality == "good":
                            self.status_text.value = "🌐 Online (Boa)"
                            self.status_text.color = ft.colors.GREEN
                            self.sync_icon.name = ft.icons.CLOUD_DONE
                            self.sync_icon.color = ft.colors.GREEN
                        else:
                            self.status_text.value = "🌐 Online (Lenta)"
                            self.status_text.color = ft.colors.AMBER
                            self.sync_icon.name = ft.icons.CLOUD_QUEUE
                            self.sync_icon.color = ft.colors.AMBER
                    else:
                        self.status_text.value = "⚡ Offline"
                        self.status_text.color = ft.colors.ORANGE
                        self.sync_icon.name = ft.icons.CLOUD_OFF
                        self.sync_icon.color = ft.colors.ORANGE
                    
                    # Atualizar texto da última sincronização
                    self._update_last_sync_display()
                    
                    if self.page:
                        self.update()
                    
                    self.is_checking = False
                
                # Aguardar baseado na qualidade da conexão
                sleep_time = 15 if self.connection_quality == "good" else 30
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Erro no monitoramento de conexão: {e}")
                self.is_checking = False
                time.sleep(30)
    
    def _update_last_sync_display(self):
        """Atualiza o texto da última sincronização."""
        if self.last_sync_time:
            now = datetime.now()
            diff = now - self.last_sync_time
            
            if diff.total_seconds() < 60:
                self.last_sync_text.value = "Sincronizado agora"
                self.last_sync_text.color = ft.colors.GREEN_700
            elif diff.total_seconds() < 3600:  # < 1 hora
                minutes = int(diff.total_seconds() / 60)
                self.last_sync_text.value = f"Sincronizado há {minutes}min"
                self.last_sync_text.color = ft.colors.BLUE_700
            elif diff.total_seconds() < 86400:  # < 1 dia
                hours = int(diff.total_seconds() / 3600)
                self.last_sync_text.value = f"Sincronizado há {hours}h"
                self.last_sync_text.color = ft.colors.AMBER_700
            else:
                days = int(diff.total_seconds() / 86400)
                self.last_sync_text.value = f"Sincronizado há {days}d"
                self.last_sync_text.color = ft.colors.RED_700
        else:
            self.last_sync_text.value = "Nunca sincronizado"
            self.last_sync_text.color = ft.colors.GREY_600
    
    def start_sync_animation(self):
        """Inicia animação de sincronização."""
        self.is_syncing = True
        self.sync_progress.visible = True
        self.sync_icon.name = ft.icons.SYNC
        self.sync_icon.color = ft.colors.BLUE
        self.status_text.value = "🔄 Sincronizando..."
        self.status_text.color = ft.colors.BLUE
        if self.page:
            self.update()
    
    def stop_sync_animation(self, success: bool = True):
        """Para animação de sincronização."""
        self.is_syncing = False
        self.sync_progress.visible = False
        
        if success:
            self.last_sync_time = datetime.now()
            self.sync_icon.name = ft.icons.CHECK_CIRCLE
            self.sync_icon.color = ft.colors.GREEN
            self.status_text.value = "✅ Sincronizado"
            self.status_text.color = ft.colors.GREEN
        else:
            self.sync_icon.name = ft.icons.ERROR
            self.sync_icon.color = ft.colors.RED
            self.status_text.value = "❌ Erro na sync"
            self.status_text.color = ft.colors.RED
        
        self._update_last_sync_display()
        if self.page:
            self.update()
    
    def stop_monitoring_thread(self):
        """Para o monitoramento de conexão."""
        self.stop_monitoring = True
