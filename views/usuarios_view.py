import flet as ft
from database.database import Database
from repositories.usuario_repository import UsuarioRepository
from werkzeug.security import generate_password_hash
from views.generic_table_style import apply_table_style

class UsuariosView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        self.usuario_repo = UsuarioRepository()
        
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
        
        self.pode_abastecer_switch = ft.Switch(
            label="Pode Abastecer Produtos",
            value=False,
        )
        
        self.pode_gerenciar_despesas_switch = ft.Switch(
            label="Pode Gerenciar Despesas",
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
                ft.DataColumn(ft.Text("Abastecimento")),
                ft.DataColumn(ft.Text("Despesas")),
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
                    self.is_admin_switch,
                    self.pode_abastecer_switch,
                    self.pode_gerenciar_despesas_switch
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
            usuarios = self.usuario_repo.listar_todos()
            
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
                            icon=ft.icons.DELETE,
                            icon_color=ft.colors.RED,
                            tooltip="Excluir",
                            data=dict(usuario),  # Convertendo Row para dict
                            on_click=self.excluir_usuario
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
                                    name=ft.icons.CHECK_CIRCLE if usuario['pode_abastecer'] else ft.icons.CANCEL,
                                    color=ft.colors.GREEN if usuario['pode_abastecer'] else ft.colors.RED
                                )
                            ),
                            ft.DataCell(
                                ft.Icon(
                                    name=ft.icons.CHECK_CIRCLE if (usuario['pode_gerenciar_despesas'] if 'pode_gerenciar_despesas' in usuario.keys() else 0) else ft.icons.CANCEL,
                                    color=ft.colors.GREEN if (usuario['pode_gerenciar_despesas'] if 'pode_gerenciar_despesas' in usuario.keys() else 0) else ft.colors.RED
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
                'pode_abastecer': self.pode_abastecer_switch.value,
                'pode_gerenciar_despesas': self.pode_gerenciar_despesas_switch.value,
                'salario': salario
            }
            # LOG: Detalhes do formulário antes de salvar
            print("[USUARIOS_VIEW] Salvando usuário...")
            print(f"  - nome: {dados['nome']}")
            print(f"  - usuario: {dados['usuario']}")
            print(f"  - is_admin: {dados['is_admin']}")
            print(f"  - pode_abastecer: {dados['pode_abastecer']}")
            print(f"  - pode_gerenciar_despesas: {dados['pode_gerenciar_despesas']}")
            print(f"  - salario: {dados['salario']}")
            
            if self.usuario_em_edicao:
                # Atualizar usuário existente
                if self.senha_field.value:  # Se uma nova senha foi fornecida
                    raw_pwd = self.senha_field.value
                    sanitized = raw_pwd.strip()
                    print(f"  - senha (raw): {repr(raw_pwd)}")
                    print(f"  - senha (sanitizada): {repr(sanitized)}")
                    hash_gerado = generate_password_hash(sanitized)
                    print(f"  - senha (hash): {hash_gerado[:30]}... (len={len(hash_gerado)})")
                    dados['senha'] = hash_gerado
                
                resultado = self.usuario_repo.update(self.usuario_em_edicao, dados)
                if not resultado:
                    raise Exception("Falha ao atualizar usuário")
                
            else:
                # Inserir novo usuário
                if not self.senha_field.value:
                    raise ValueError("Senha é obrigatória para novo usuário!")
                
                raw_pwd = self.senha_field.value
                sanitized = raw_pwd.strip()
                print(f"  - senha (raw): {repr(raw_pwd)}")
                print(f"  - senha (sanitizada): {repr(sanitized)}")
                hash_gerado = generate_password_hash(sanitized)
                print(f"  - senha (hash): {hash_gerado[:30]}... (len={len(hash_gerado)})")
                dados['senha'] = hash_gerado
                resultado = self.usuario_repo.create(dados)
                if not resultado:
                    raise Exception("Falha ao criar usuário")
            
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
            self.pode_abastecer_switch.value = bool(usuario['pode_abastecer'])
            self.pode_gerenciar_despesas_switch.value = bool(usuario['pode_gerenciar_despesas'] if 'pode_gerenciar_despesas' in usuario.keys() else 0)
            # Trata o campo salário com valor padrão caso seja None
            self.salario_field.value = str(usuario['salario'] if usuario['salario'] is not None else 0)
            self.update()
        except Exception as error:
            print(f"Erro ao editar usuário: {error}")

    def excluir_usuario(self, e):
        usuario = e.control.data
        
        # Proteger o usuário admin principal
        if usuario['usuario'] == 'admin':
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Não é possível excluir o usuário administrador principal!"),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )
            return
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Tem certeza que deseja excluir o usuário '{usuario['nome']}'?\n\nEsta ação não pode ser desfeita."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.TextButton("Excluir", on_click=lambda _: self._confirmar_exclusao(usuario['id']))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda _: setattr(self.page.dialog, 'open', False) or self.page.update()
        )
        self.page.dialog.open = True
        self.page.update()

    def _confirmar_exclusao(self, usuario_id):
        try:
            resultado = self.usuario_repo.delete(usuario_id)
            if not resultado:
                raise Exception("Falha ao excluir usuário")
            self.carregar_usuarios()
            
            # Fechar o modal
            self.page.dialog.open = False
            self.page.update()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ Usuário excluído com sucesso!"),
                    bgcolor=ft.colors.GREEN,
                    duration=3000
                )
            )
        except Exception as e:
            print(f"Erro ao excluir usuário: {e}")
            
            # Fechar o modal mesmo em caso de erro
            self.page.dialog.open = False
            self.page.update()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Erro ao excluir usuário!"),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )

    def toggle_status_usuario(self, e):
        usuario = e.control.data
        try:
            novo_status = not usuario['ativo']
            dados_atualizacao = {'ativo': novo_status}
            resultado = self.usuario_repo.update(usuario['id'], dados_atualizacao)
            if not resultado:
                raise Exception("Falha ao alterar status do usuário")
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
        self.pode_abastecer_switch.value = False
        self.pode_gerenciar_despesas_switch.value = False
        self.update()

    def filtrar_usuarios(self, e):
        termo = e.control.value.lower()
        try:
            # Usar o repositório para buscar usuários
            if termo:
                usuarios = self.usuario_repo.buscar_por_nome_ou_usuario(termo)
            else:
                usuarios = self.usuario_repo.listar_todos()
            
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
                            icon=ft.icons.DELETE,
                            icon_color=ft.colors.RED,
                            tooltip="Excluir",
                            data=usuario,
                            on_click=self.excluir_usuario
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
                                    name=ft.icons.CHECK_CIRCLE if usuario['pode_abastecer'] else ft.icons.CANCEL,
                                    color=ft.colors.GREEN if usuario['pode_abastecer'] else ft.colors.RED
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