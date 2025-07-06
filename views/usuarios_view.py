import flet as ft
from database.database import Database
from werkzeug.security import generate_password_hash
from views.generic_table_style import apply_table_style

class UsuariosView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        
        # Campos do formulário
        self.nome_field = ft.TextField(
            label="Nome",
            width=400,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.usuario_field = ft.TextField(
            label="Usuário",
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.senha_field = ft.TextField(
            label="Senha",
            width=200,
            height=50,
            password=True,
            can_reveal_password=True,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.salario_field = ft.TextField(
            label="Salário",
            width=200,
            height=50,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            prefix_text="MT ",
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.is_admin_switch = ft.Switch(
            label="Administrador",
            value=False,
        )
        
        # ID do usuário em edição
        self.usuario_em_edicao = None
        
        # DataTable para listar usuários
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("Usuário")),
                ft.DataColumn(ft.Text("Admin")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Salário")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[]
        )
        apply_table_style(self.table)

    def build(self):
        # Cabeçalho
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/dashboard")
                ),
                ft.Icon(
                    name=ft.icons.PEOPLE,
                    size=30,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Gerenciar Funcionários",
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
                    "Novo Funcionário",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLACK
                ),
                ft.Row([
                    self.nome_field,
                    self.usuario_field
                ]),
                ft.Row([
                    self.senha_field,
                    self.salario_field,
                    self.is_admin_switch
                ]),
                ft.Row([
                    ft.ElevatedButton(
                        "Salvar",
                        on_click=self.salvar_usuario,
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
                        "Lista de Funcionários",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                    ft.TextField(
                        label="Buscar",
                        width=300,
                        height=40,
                        prefix_icon=ft.icons.SEARCH,
                        on_change=self.filtrar_usuarios,
                        color=ft.colors.BLACK,
                        label_style=ft.TextStyle(color=ft.colors.BLACK)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=ft.Column(
                        [self.table],
                        scroll=ft.ScrollMode.AUTO
                    ),
                    height=300,  # Altura fixa para o container
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

        # Layout principal corrigido
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

    def carregar_usuarios(self):
        try:
            usuarios = self.db.fetchall("""
                SELECT id, nome, usuario, is_admin, ativo, salario 
                FROM usuarios 
                ORDER BY nome
            """)
            
            self.table.rows.clear()
            for usuario in usuarios:
                if usuario['usuario'] == 'admin':
                    acoes = [ft.Text("Admin Principal", color=ft.colors.BLACK)]
                else:
                    acoes = [
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            icon_color=ft.colors.BLUE,
                            tooltip="Editar",
                            data=dict(usuario),  # Convertendo Row para dict
                            on_click=self.editar_usuario
                        ),
                        ft.IconButton(
                            icon=ft.icons.POWER_SETTINGS_NEW,
                            icon_color=ft.colors.RED if usuario['ativo'] else ft.colors.GREEN,
                            tooltip="Ativar/Desativar",
                            data=dict(usuario),  # Convertendo Row para dict
                            on_click=self.toggle_status_usuario
                        )
                    ]

                self.table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(usuario['nome'], color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(usuario['usuario'], color=ft.colors.GREY_900)),
                            ft.DataCell(
                                ft.Icon(
                                    name=ft.icons.CHECK_CIRCLE if usuario['is_admin'] else ft.icons.CANCEL,
                                    color=ft.colors.GREEN if usuario['is_admin'] else ft.colors.RED
                                )
                            ),
                            ft.DataCell(
                                ft.Icon(
                                    name=ft.icons.CHECK_CIRCLE if usuario['ativo'] else ft.icons.CANCEL,
                                    color=ft.colors.GREEN if usuario['ativo'] else ft.colors.RED
                                )
                            ),
                            ft.DataCell(ft.Text(f"MT {usuario['salario'] or 0:.2f}", color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Row(acoes))
                        ]
                    )
                )
            self.update()
        except Exception as e:
            print(f"Erro ao carregar usuários: {e}")

    def salvar_usuario(self, e):
        try:
            if not self.nome_field.value or not self.usuario_field.value:
                raise ValueError("Nome e usuário são obrigatórios!")
            
            # Converter salário para float, tratando campo vazio
            try:
                salario = float(self.salario_field.value or 0)
            except ValueError:
                salario = 0
            
            dados = {
                'nome': self.nome_field.value,
                'usuario': self.usuario_field.value,
                'is_admin': self.is_admin_switch.value,
                'salario': salario
            }
            
            if self.usuario_em_edicao:
                # Atualizar usuário existente
                if self.senha_field.value:  # Se uma nova senha foi fornecida
                    dados['senha'] = generate_password_hash(self.senha_field.value)
                
                self.db.execute("""
                    UPDATE usuarios 
                    SET nome = :nome, 
                        usuario = :usuario, 
                        is_admin = :is_admin,
                        salario = :salario
                        {senha_update}
                    WHERE id = :id
                """.format(
                    senha_update=", senha = :senha" if self.senha_field.value else ""
                ), {**dados, 'id': self.usuario_em_edicao})
                
            else:
                # Inserir novo usuário
                if not self.senha_field.value:
                    raise ValueError("Senha é obrigatória para novo usuário!")
                
                dados['senha'] = generate_password_hash(self.senha_field.value)
                self.db.execute("""
                    INSERT INTO usuarios (nome, usuario, senha, is_admin, salario)
                    VALUES (:nome, :usuario, :senha, :is_admin, :salario)
                """, dados)
            
            # Limpar formulário e recarregar lista
            self.limpar_formulario(None)
            self.carregar_usuarios()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ Usuário salvo com sucesso!"),
                    bgcolor=ft.colors.GREEN,
                    duration=3000
                )
            )
            
        except Exception as error:
            print(f"Erro ao salvar usuário: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao salvar usuário: {str(error)}"),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )

    def editar_usuario(self, e):
        try:
            usuario = e.control.data
            self.usuario_em_edicao = usuario['id']
            self.nome_field.value = usuario['nome']
            self.usuario_field.value = usuario['usuario']
            self.senha_field.value = ""  # Limpa o campo de senha
            self.is_admin_switch.value = bool(usuario['is_admin'])
            # Trata o campo salário com valor padrão caso seja None
            self.salario_field.value = str(usuario['salario'] if usuario['salario'] is not None else 0)
            self.update()
        except Exception as error:
            print(f"Erro ao editar usuário: {error}")

    def toggle_status_usuario(self, e):
        usuario = e.control.data
        try:
            novo_status = not usuario['ativo']
            self.db.execute(
                "UPDATE usuarios SET ativo = ? WHERE id = ?",
                (novo_status, usuario['id'])
            )
            self.carregar_usuarios()
            status_texto = "ativado" if novo_status else "desativado"
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"✅ Usuário {status_texto} com sucesso!"),
                    bgcolor=ft.colors.GREEN,
                    duration=3000
                )
            )
        except Exception as e:
            print(f"Erro ao alterar status do usuário: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Erro ao alterar status do usuário!"),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )

    def limpar_formulario(self, e):
        self.usuario_em_edicao = None
        self.nome_field.value = ""
        self.usuario_field.value = ""
        self.senha_field.value = ""
        self.salario_field.value = ""
        self.is_admin_switch.value = False
        self.update()

    def filtrar_usuarios(self, e):
        termo = e.control.value.lower()
        try:
            usuarios = self.db.fetchall("""
                SELECT * FROM usuarios 
                WHERE LOWER(nome) LIKE ? OR LOWER(usuario) LIKE ?
                ORDER BY nome
            """, (f"%{termo}%", f"%{termo}%"))
            
            self.table.rows.clear()
            for usuario in usuarios:
                if usuario['usuario'] == 'admin':
                    acoes = [ft.Text("Admin Principal", color=ft.colors.BLACK)]
                else:
                    acoes = [
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            icon_color=ft.colors.BLUE,
                            tooltip="Editar",
                            data=usuario,
                            on_click=self.editar_usuario
                        ),
                        ft.IconButton(
                            icon=ft.icons.POWER_SETTINGS_NEW,
                            icon_color=ft.colors.RED if usuario['ativo'] else ft.colors.GREEN,
                            tooltip="Ativar/Desativar",
                            data=usuario,
                            on_click=self.toggle_status_usuario
                        )
                    ]

                self.table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(usuario['nome'], color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(usuario['usuario'], color=ft.colors.GREY_900)),
                            ft.DataCell(
                                ft.Icon(
                                    name=ft.icons.CHECK_CIRCLE if usuario['is_admin'] else ft.icons.CANCEL,
                                    color=ft.colors.GREEN if usuario['is_admin'] else ft.colors.RED
                                )
                            ),
                            ft.DataCell(
                                ft.Icon(
                                    name=ft.icons.CHECK_CIRCLE if usuario['ativo'] else ft.icons.CANCEL,
                                    color=ft.colors.GREEN if usuario['ativo'] else ft.colors.RED
                                )
                            ),
                            ft.DataCell(ft.Text(f"MT {usuario['salario']:.2f}", color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Row(acoes))
                        ]
                    )
                )
            self.update()
        except Exception as e:
            print(f"Erro ao filtrar usuários: {e}")

    def did_mount(self):
        self.carregar_usuarios() 