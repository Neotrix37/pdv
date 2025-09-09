import flet as ft
import os
if os.getenv('WEB_MODE') == 'true':
    from utils.rongta_printer_web import RongtaPrinter
else:
    from utils.rongta_printer import RongtaPrinter
from database.database import Database

class PrinterConfigView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario=None):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE  # Definindo background branco
        self.usuario = usuario
        self.printer = RongtaPrinter()
        self.db = Database()
        
        # Carrega configurações existentes
        self.config = self.carregar_configuracoes()
        
        # Campos de configuração
        self.empresa_field = ft.TextField(
            label="Nome da Empresa",
            hint_text="Digite o nome da empresa",
            width=400
        )
        
        self.endereco_field = ft.TextField(
            label="Endereço",
            hint_text="Digite o endereço completo",
            width=400,
            multiline=True,
            min_lines=2
        )
        
        self.telefone_field = ft.TextField(
            label="Telefone",
            hint_text="Digite o telefone",
            width=200
        )
        
        self.nuit_field = ft.TextField(
            label="NUIT",
            hint_text="Digite o NUIT",
            width=200
        )
        
        self.rodape_field = ft.TextField(
            label="Mensagem de Rodapé",
            hint_text="Digite a mensagem que aparecerá no rodapé do cupom",
            width=400,
            multiline=True,
            min_lines=2
        )
        
        self.imprimir_automatico = ft.Switch(
            label="Imprimir Automaticamente",
            value=bool(self.config.get('imprimir_automatico', 0))
        )
        
        # Componentes
        self.status_text = ft.Text(
            "Status: Desconectado",
            color=ft.colors.RED,
            size=16,
            weight=ft.FontWeight.BOLD
        )
        
        self.connection_type = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="USB",
                    icon=ft.icons.USB
                ),
                ft.Tab(
                    text="Bluetooth",
                    icon=ft.icons.BLUETOOTH
                ),
            ],
            on_change=self.change_connection_type
        )
        
        self.printer_list = ft.Column(spacing=10)
        
        self.test_btn = ft.ElevatedButton(
            "Testar Impressão",
            icon=ft.icons.PRINT,
            disabled=True,
            on_click=self.testar_impressao,
            bgcolor=ft.colors.GREEN
        )

    def build(self):
        return ft.Column([
            # Cabeçalho (mantém fora do scroll)
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/configuracoes"),
                        icon_color=ft.colors.WHITE
                    ),
                    ft.Text(
                        "Configuração de Impressora",
                        color=ft.colors.WHITE,
                        size=20,
                        weight=ft.FontWeight.BOLD
                    )
                ]),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
                ),
                padding=20,
                border_radius=ft.border_radius.only(
                    bottom_left=10,
                    bottom_right=10
                )
            ),

            # Container principal com scroll
            ft.Container(
                content=ft.Column(
                    [
                        # Todo o conteúdo existente
                        ft.Column([
                            # Configurações da Empresa
                            ft.Card(
                                content=ft.Container(
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Icon(ft.icons.BUSINESS, color=ft.colors.BLUE),
                                            ft.Text("Dados da Empresa",
                                                   weight=ft.FontWeight.BOLD,
                                                   size=16)
                                        ]),
                                        self.empresa_field,
                                        self.endereco_field,
                                        ft.Row([
                                            self.telefone_field,
                                            self.nuit_field
                                        ]),
                                        self.rodape_field,
                                        ft.ElevatedButton(
                                            "Salvar Configurações",
                                            icon=ft.icons.SAVE,
                                            on_click=self.salvar_configuracoes,
                                            bgcolor=ft.colors.GREEN
                                        )
                                    ], spacing=10),
                                    padding=15
                                )
                            ),
                            
                            # Status Card
                            ft.Card(
                                content=ft.Container(
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Icon(ft.icons.INFO, color=ft.colors.BLUE),
                                            ft.Text("Status da Conexão", 
                                                   weight=ft.FontWeight.BOLD,
                                                   size=16)
                                        ]),
                                        self.status_text
                                    ], spacing=10),
                                    padding=15
                                )
                            ),
                            
                            # Tipo de Conexão
                            ft.Card(
                                content=ft.Container(
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Icon(ft.icons.SETTINGS_INPUT_COMPONENT, 
                                                   color=ft.colors.BLUE),
                                            ft.Text("Tipo de Conexão",
                                                   weight=ft.FontWeight.BOLD,
                                                   size=16)
                                        ]),
                                        self.connection_type
                                    ], spacing=10),
                                    padding=15
                                )
                            ),
                            
                            # Área de Busca
                            ft.Card(
                                content=ft.Container(
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Icon(ft.icons.PRINT, color=ft.colors.BLUE),
                                            ft.Text("Impressoras Disponíveis",
                                                   weight=ft.FontWeight.BOLD,
                                                   size=16)
                                        ]),
                                        ft.ElevatedButton(
                                            "Buscar Impressoras",
                                            icon=ft.icons.SEARCH,
                                            on_click=lambda _: self.buscar_impressoras(),
                                            bgcolor=ft.colors.BLUE
                                        ),
                                        ft.Container(
                                            content=self.printer_list,
                                            bgcolor=ft.colors.GREY_50,
                                            border_radius=5,
                                            padding=10,
                                            visible=True
                                        ),
                                    ], spacing=10),
                                    padding=15
                                )
                            ),
                            
                            # Área de Teste
                            ft.Card(
                                content=ft.Container(
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Icon(ft.icons.BUILD, color=ft.colors.BLUE),
                                            ft.Text("Ferramentas",
                                                   weight=ft.FontWeight.BOLD,
                                                   size=16)
                                        ]),
                                        self.test_btn
                                    ], spacing=10),
                                    padding=15
                                )
                            ),
                            
                            # Opções de Impressão
                            ft.Card(
                                content=ft.Container(
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Icon(ft.icons.SETTINGS, color=ft.colors.BLUE),
                                            ft.Text("Opções de Impressão",
                                                   weight=ft.FontWeight.BOLD,
                                                   size=16)
                                        ]),
                                        self.imprimir_automatico
                                    ], spacing=10),
                                    padding=15
                                )
                            ),
                            
                        ], spacing=20),
                    ],
                    scroll=ft.ScrollMode.AUTO  # Habilita scroll automático
                ),
                height=900,  # Altura fixa para o container
                padding=20,
                border=ft.border.all(1, ft.colors.BLACK26),
                border_radius=10
            )
        ])

    def change_connection_type(self, e):
        """Altera o tipo de conexão"""
        # Limpa a lista ao trocar
        self.printer_list.controls.clear()
        self.printer_list.controls.append(
            ft.Text("Clique em 'Buscar Impressoras' para iniciar a busca",
                   color=ft.colors.GREY)
        )
        self.update()

    def buscar_impressoras(self):
        try:
            print("Iniciando busca de impressoras...")
            self.printer_list.controls.clear()
            
            # Adiciona indicador de busca
            self.printer_list.controls.append(
                ft.Text("Buscando impressoras...", color=ft.colors.BLUE)
            )
            self.update()
            
            # Busca baseada no tipo selecionado
            if self.connection_type.selected_index == 0:  # USB
                print("Buscando impressoras USB...")
                printers = self.printer.list_usb_printers()
                print(f"Impressoras USB encontradas: {printers}")
            else:  # Bluetooth
                print("Buscando impressoras Bluetooth...")
                printers = self.printer.list_bluetooth_printers()
                print(f"Impressoras Bluetooth encontradas: {printers}")
            
            self.printer_list.controls.clear()
            
            if not printers:
                print("Nenhuma impressora encontrada")
                self.printer_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.ERROR, color=ft.colors.RED, size=40),
                            ft.Text(
                                "Nenhuma impressora encontrada",
                                color=ft.colors.RED,
                                weight=ft.FontWeight.BOLD,
                                size=16
                            ),
                            ft.Text(
                                "Verifique se a impressora está:",
                                color=ft.colors.GREY
                            ),
                            ft.Text("1. Conectada ao computador", color=ft.colors.GREY),
                            ft.Text("2. Ligada", color=ft.colors.GREY),
                            ft.Text("3. Com drivers instalados", color=ft.colors.GREY),
                            ft.Text("4. No modo de descoberta (para Bluetooth)", color=ft.colors.GREY)
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                        padding=20,
                        alignment=ft.alignment.center
                    )
                )
            else:
                print(f"Processando {len(printers)} impressoras encontradas")
                for p in printers:
                    print(f"Adicionando impressora à lista: {p}")
                    self.printer_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.icons.PRINT, color=ft.colors.BLUE),
                                        ft.Text(p['name'],
                                               weight=ft.FontWeight.BOLD,
                                               size=14)
                                    ]),
                                    ft.Text(f"Porta: {p['port']}",
                                           color=ft.colors.GREY),
                                    ft.Text(f"Tipo: {p['type']}",
                                           color=ft.colors.GREY),
                                    ft.ElevatedButton(
                                        "Conectar",
                                        icon=ft.icons.LINK,
                                        on_click=lambda e, name=p['name'], type=p['type']: 
                                            self.conectar_impressora(name, type)
                                    )
                                ]),
                                padding=10
                            )
                        )
                    )
            
            self.update()
            
        except Exception as e:
            print(f"Erro detalhado ao buscar impressoras: {str(e)}")
            import traceback
            print(f"Stacktrace: {traceback.format_exc()}")
            self.printer_list.controls.clear()
            self.printer_list.controls.append(
                ft.Text(f"Erro ao buscar impressoras: {str(e)}",
                       color=ft.colors.RED)
            )
            self.update()

    def conectar_impressora(self, printer_name, printer_type):
        try:
            if printer_type == 'USB':
                success = self.printer.connect_usb(printer_name)
            else:
                success = self.printer.connect_bluetooth(printer_name)
                
            if success:
                self.status_text.value = f"Status: Conectado a {printer_name}"
                self.status_text.color = ft.colors.GREEN
                self.test_btn.disabled = False
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Impressora conectada com sucesso!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            else:
                raise Exception("Falha ao conectar")
                
            self.update()
            
        except Exception as e:
            print(f"Erro ao conectar impressora: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao conectar impressora!"),
                    bgcolor=ft.colors.RED
                )
            )

    def testar_impressao(self, e):
        try:
            if self.printer.print_test():
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Teste impresso com sucesso!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            else:
                raise Exception("Falha ao imprimir")
                
        except Exception as e:
            print(f"Erro ao imprimir teste: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao imprimir teste!"),
                    bgcolor=ft.colors.RED
                )
            )

    def carregar_configuracoes(self):
        """Carrega configurações do banco de dados"""
        try:
            result = self.db.execute(
                "SELECT * FROM printer_config ORDER BY id DESC LIMIT 1"
            ).fetchone()
            
            return dict(result) if result else {}
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            return {}

    def salvar_configuracoes(self, e):
        """Salva configurações no banco de dados"""
        try:
            dados = {
                'empresa': self.empresa_field.value,
                'endereco': self.endereco_field.value,
                'telefone': self.telefone_field.value,
                'nuit': self.nuit_field.value,
                'rodape': self.rodape_field.value,
                'impressora_padrao': self.printer.status if self.printer else None,
                'imprimir_automatico': 1 if self.imprimir_automatico.value else 0
            }
            
            self.db.execute("""
                INSERT INTO printer_config 
                (empresa, endereco, telefone, nuit, rodape, 
                 impressora_padrao, imprimir_automatico)
                VALUES 
                (:empresa, :endereco, :telefone, :nuit, :rodape,
                 :impressora_padrao, :imprimir_automatico)
            """, dados)
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Configurações salvas com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao salvar configurações!"),
                    bgcolor=ft.colors.RED
                )
            ) 