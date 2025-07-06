import flet as ft
from database.database import Database
from utils.translation_mixin import TranslationMixin
from views.generic_table_style import apply_table_style

class ClientesView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        print("Inicializando ClientesView")
        self.page = page
        self.usuario = usuario
        self.db = Database()
        self.lang = page.data.get("language", "pt")
        
        # Campos do formulário com estilo consistente
        self.nome_field = ft.TextField(
            label="Nome",
            width=400,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.nuit_field = ft.TextField(
            label="NUIT",
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.telefone_field = ft.TextField(
            label="Telefone",
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.endereco_field = ft.TextField(
            label="Endereço",
            width=400,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.email_field = ft.TextField(
            label="Email",
            width=300,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Campos para cliente especial
        self.especial_checkbox = ft.Checkbox(
            label="Cliente Especial (Desconto em Dívidas)",
            value=False,
            fill_color=ft.colors.BLUE
        )
        
        self.desconto_field = ft.TextField(
            label="Desconto (%)",
            width=150,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            suffix_text="%",
            keyboard_type=ft.KeyboardType.NUMBER,
            disabled=True
        )
        
        # DataTable para listar clientes
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("NUIT", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Telefone", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Email", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Especial", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Desconto", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.BLACK)),
            ],
            rows=[]
        )
        apply_table_style(self.table)
        
        # ID do cliente em edição
        self.cliente_em_edicao = None
        
        # Configurar evento do checkbox
        self.especial_checkbox.on_change = self.toggle_desconto_field
        
    def build(self):
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/dashboard"),
                    icon_color=ft.colors.WHITE
                ),
                ft.Icon(
                    name=ft.icons.PEOPLE_ALT,
                    size=30,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Gestão de Clientes",
                    size=20,
                    color=ft.colors.WHITE
                )
            ]),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.INDIGO_900, ft.colors.INDIGO_700]
            ),
            padding=20,
            border_radius=10
        )

        # Formulário
        form = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Novo Cliente",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLACK
                ),
                ft.Row([
                    self.nome_field,
                    self.nuit_field
                ]),
                ft.Row([
                    self.telefone_field,
                    self.email_field
                ]),
                self.endereco_field,
                ft.Row([
                    self.especial_checkbox,
                    self.desconto_field
                ]),
                ft.Row([
                    ft.ElevatedButton(
                        "Salvar",
                        on_click=self.salvar_cliente,
                        bgcolor=ft.colors.GREEN,
                        color=ft.colors.WHITE
                    ),
                    ft.OutlinedButton(
                        "Limpar",
                        on_click=self.limpar_formulario
                    )
                ])
            ]),
            bgcolor=ft.colors.WHITE,
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.1, ft.colors.BLACK)
            )
        )

        # Container da tabela
        table_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Lista de Clientes",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                    ft.TextField(
                        label="Buscar",
                        width=300,
                        height=40,
                        prefix_icon=ft.icons.SEARCH,
                        on_change=self.filtrar_clientes,
                        color=ft.colors.BLACK,
                        label_style=ft.TextStyle(color=ft.colors.BLACK)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=ft.Column(
                        [self.table],
                        scroll=ft.ScrollMode.AUTO
                    ),
                    height=300,
                    border=ft.border.all(1, ft.colors.BLACK26),
                    border_radius=10,
                    padding=10
                )
            ]),
            bgcolor=ft.colors.WHITE,
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.1, ft.colors.BLACK)
            )
        )

        # Layout principal
        return ft.Column(
            controls=[
                header,
                ft.Container(height=20),
                form,
                ft.Container(height=20),
                table_container
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0
        )

    def carregar_clientes(self):
        try:
            clientes = self.db.fetchall("""
                SELECT id, nome, nuit, telefone, email, especial, desconto_divida
                FROM clientes
                ORDER BY nome
            """)
            
            self.table.rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(c["nome"], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(c["nuit"] or "-", color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(c["telefone"] or "-", color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(c["email"] or "-", color=ft.colors.GREY_900)),
                        ft.DataCell(
                            ft.Text(
                                "Sim" if c["especial"] else "Não",
                                color=ft.colors.GREEN if c["especial"] else ft.colors.GREY_900,
                                weight=ft.FontWeight.BOLD if c["especial"] else ft.FontWeight.NORMAL
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"{c['desconto_divida'] * 100:.1f}%" if c["especial"] and c["desconto_divida"] else "-",
                                color=ft.colors.BLUE if c["especial"] and c["desconto_divida"] else ft.colors.GREY_900
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    icon_color=ft.colors.BLUE,
                                    tooltip="Editar",
                                    data=c["id"],
                                    on_click=lambda e, id=c["id"]: self.editar_cliente(e)
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=ft.colors.RED,
                                    tooltip="Excluir",
                                    data=c["id"],
                                    on_click=self.excluir_cliente
                                )
                            ])
                        )
                    ]
                ) for c in clientes
            ]
            self.update()
        except Exception as ex:
            print(f"Erro ao carregar clientes: {ex}")

    def filtrar_clientes(self, e):
        termo = e.control.value.lower()
        try:
            clientes = self.db.fetchall("""
                SELECT id, nome, nuit, telefone, email
                FROM clientes
                WHERE LOWER(nome) LIKE ? OR LOWER(nuit) LIKE ?
                ORDER BY nome
            """, (f"%{termo}%", f"%{termo}%"))
            
            self.carregar_clientes()  # Recarrega a tabela com os resultados filtrados
            
        except Exception as ex:
            print(f"Erro ao filtrar clientes: {ex}")

    def limpar_formulario(self, e):
        self.cliente_em_edicao = None  # Reseta o ID do cliente em edição
        self.nome_field.value = ""
        self.nuit_field.value = ""
        self.telefone_field.value = ""
        self.endereco_field.value = ""
        self.email_field.value = ""
        self.especial_checkbox.value = False
        self.desconto_field.value = ""
        self.desconto_field.disabled = True
        self.update()

    def salvar_cliente(self, e):
        try:
            if not self.nome_field.value:
                raise ValueError("Nome é obrigatório!")

            dados = {
                'nome': self.nome_field.value,
                'nuit': self.nuit_field.value,
                'telefone': self.telefone_field.value,
                'endereco': self.endereco_field.value,
                'email': self.email_field.value,
                'especial': 1 if self.especial_checkbox.value else 0,
                'desconto_divida': float(self.desconto_field.value or 0) / 100 if self.especial_checkbox.value else 0
            }
            


            if self.cliente_em_edicao:
                # Atualizar cliente existente
                self.db.execute("""
                    UPDATE clientes 
                    SET nome = :nome,
                        nuit = :nuit,
                        telefone = :telefone,
                        endereco = :endereco,
                        email = :email,
                        especial = :especial,
                        desconto_divida = :desconto_divida
                    WHERE id = :id
                """, {**dados, 'id': self.cliente_em_edicao})
                
                mensagem = "✅ Cliente atualizado com sucesso!"
            else:
                # Inserir novo cliente
                self.db.execute("""
                    INSERT INTO clientes (nome, nuit, telefone, endereco, email, especial, desconto_divida)
                    VALUES (:nome, :nuit, :telefone, :endereco, :email, :especial, :desconto_divida)
                """, dados)
                
                mensagem = "✅ Cliente cadastrado com sucesso!"

            self.limpar_formulario(None)
            self.carregar_clientes()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(mensagem),
                    bgcolor=ft.colors.GREEN,
                    duration=3000
                )
            )
            
        except Exception as error:
            print(f"Erro ao salvar cliente: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao salvar cliente: {str(error)}"),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )

    def editar_cliente(self, e):
        try:
            # Pega o ID diretamente do botão clicado
            cliente_id = e.control.data
            
            cliente = self.db.fetchone("""
                SELECT id, nome, nuit, telefone, endereco, email, especial, desconto_divida
                FROM clientes 
                WHERE id = ?
            """, (cliente_id,))
            
            if cliente:
                self.cliente_em_edicao = cliente['id']
                self.nome_field.value = cliente['nome']
                self.nuit_field.value = cliente['nuit'] or ""
                self.telefone_field.value = cliente['telefone'] or ""
                self.endereco_field.value = cliente['endereco'] or ""
                self.email_field.value = cliente['email'] or ""
                self.especial_checkbox.value = bool(cliente['especial'])
                self.desconto_field.value = f"{cliente['desconto_divida'] * 100:.1f}" if cliente['desconto_divida'] else ""
                self.desconto_field.disabled = not self.especial_checkbox.value
                
                # Atualiza os campos
                self.update()
                
                # Mostra feedback visual
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("📝 Editando cliente..."),
                        bgcolor=ft.colors.BLUE,
                        duration=2000
                    )
                )
                
        except Exception as error:
            print(f"Erro ao editar cliente: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Erro ao carregar dados do cliente!"),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )

    def excluir_cliente(self, e):
        try:
            if e.control.data:
                self.db.execute("DELETE FROM clientes WHERE id = ?", (e.control.data,))
                self.carregar_clientes()
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("✅ Cliente excluído com sucesso!"),
                        bgcolor=ft.colors.GREEN,
                        duration=3000
                    )
                )
        except Exception as ex:
            print(f"Erro ao excluir cliente: {ex}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Erro ao excluir cliente!"),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )

    def toggle_desconto_field(self, e):
        """Habilita/desabilita o campo de desconto baseado no checkbox"""
        self.desconto_field.disabled = not self.especial_checkbox.value
        if not self.especial_checkbox.value:
            self.desconto_field.value = ""
        self.update()

    def did_mount(self):
        print("ClientesView montada")
        self.carregar_clientes()
        self.update() 