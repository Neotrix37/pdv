import flet as ft
from datetime import datetime, date
import locale
import asyncio
from database.database import Database
from views.generic_header import create_header
from views.generic_table_style import apply_table_style

class ComprasDiaView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.usuario_id = usuario['id'] if usuario else None
        self.db = Database()
        # Configurar locale com fallback para ambientes que não suportam pt_PT.UTF-8
        try:
            locale.setlocale(locale.LC_ALL, 'pt_PT.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
                except locale.Error:
                    # Fallback final - usar locale padrão do sistema
                    pass
        
        print("\n=== Inicializando ComprasDiaView ===")
        print(f"Usuário logado: {self.usuario['nome']} (ID: {self.usuario['id']})") 
        
        # Dados em memória
        self.categorias = []
        self.itens_compra = []
        
        # Inicializa os controles da interface
        self.inicializar_controles()
        
        # Carrega os dados iniciais
        self.carregar_dados_na_thread()

    def build(self):
        """Constrói a interface do usuário"""
        # Cria o layout principal
        return self.criar_layout()
    
    def carregar_dados_na_thread(self):
        """Carrega os dados em uma thread separada"""
        import threading
        
        def _carregar():
            try:
                # Carrega categorias
                self.categorias = self.db.obter_categorias()
                
                # Inicializa a lista de itens de compra vazia
                self.itens_compra = []
                
                # Carrega compras do dia
                self.carregar_compras_dia()
                
                # Atualiza a interface
                self._atualizar_interface()
                
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
                import traceback
                traceback.print_exc()
        
        # Inicia a thread para carregar os dados
        threading.Thread(target=_carregar, daemon=True).start()
    
    def _atualizar_interface(self):
        """Atualiza a interface do usuário"""
        try:
            self.atualizar_tabela_itens()
            self.update()
        except Exception as e:
            print(f"Erro ao atualizar interface: {e}")
    
    def inicializar_controles(self):
        """Inicializa todos os controles da interface"""
        # Campo de fornecedor
        self.fornecedor_field = ft.TextField(
            label="Fornecedor",
            width=300,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
        )
        
        # Campos do formulário de itens
        self.codigo_field = ft.TextField(
            label="Código",
            width=150,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
            on_change=self.buscar_produto,
            suffix_icon=ft.icons.SEARCH
        )
        
        self.produto_field = ft.TextField(
            label="Produto",
            width=250,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
        )
        
        # Campo de categoria
        self.categoria_field = ft.Dropdown(
            label="Categoria",
            width=200,
            height=50,
            color=ft.colors.BLACK,
            text_style=ft.TextStyle(color=ft.colors.BLACK),
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            border_color=ft.colors.BLUE_200,
            focused_border_color=ft.colors.BLUE_100,
            bgcolor=ft.colors.WHITE,
            focused_bgcolor=ft.colors.WHITE,
            content_padding=10,
            options=[
                ft.dropdown.Option(
                    key="",
                    text="Selecione uma categoria"
                )
            ]
        )
        
        self.quantidade_field = ft.TextField(
            label="Quantidade",
            width=100,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="1"
        )
        
        self.preco_compra_field = ft.TextField(
            label="Preço Custo (MZN)",
            width=150,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="MZN "
        )
        
        self.preco_venda_field = ft.TextField(
            label="Preço Venda (MZN)",
            width=150,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="MZN "
        )
        
        self.observacoes_field = ft.TextField(
            label="Observações",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
        )
        
        # Botões
        self.btn_adicionar_item = ft.ElevatedButton(
            text="Adicionar",
            icon=ft.icons.ADD,
            style=ft.ButtonStyle(
                padding=15,
                bgcolor=ft.colors.BLUE_600,
                color=ft.colors.WHITE
            ),
            on_click=self.adicionar_item_compra
        )
        
        self.btn_salvar_compra = ft.ElevatedButton(
            text="Salvar Compra",
            icon=ft.icons.SAVE,
            style=ft.ButtonStyle(
                padding=15,
                bgcolor=ft.colors.GREEN_600,
                color=ft.colors.WHITE
            ),
            on_click=self.salvar_compra
        )
        
        # Tabela de itens
        self.tabela_itens = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Produto", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Categoria", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Quantidade", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Preço Custo", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Preço Venda", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.GREY_900)),
            ],
            rows=[],
        )
        apply_table_style(self.tabela_itens)
    
    def build(self):
        """Constrói a interface do usuário"""
        # Carrega os dados iniciais
        self.carregar_dados_na_thread()
        # Cria o layout principal
        return self.criar_layout()
    
    def carregar_dados_na_thread(self):
        """Carrega os dados em uma thread separada"""
        import threading
        
        def _carregar():
            try:
                # Carrega categorias
                self.categorias = self.db.obter_categorias()
                
                # Carrega compras do dia
                hoje = datetime.now().strftime('%Y-%m-%d')
                self.itens_compra = self.db.obter_compras_por_data(hoje)
                
                # Atualiza a interface
                self.page.update()
                
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
                import traceback
                traceback.print_exc()
        
        # Inicia a thread para carregar os dados
        threading.Thread(target=_carregar, daemon=True).start()
    
    def _atualizar_interface(self):
        """Atualiza a interface do usuário"""
        try:
            self.atualizar_tabela_itens()
            self.update()
        except Exception as e:
            print(f"Erro ao atualizar interface: {e}")
    
    def inicializar_controles(self):
        """Inicializa todos os controles da interface"""
        # Campo de fornecedor
        self.fornecedor_field = ft.TextField(
            label="Fornecedor",
            width=300,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
        )
        
        # Campos do formulário de itens
        self.codigo_field = ft.TextField(
            label="Código",
            width=150,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
            on_change=self.buscar_produto,
            suffix_icon=ft.icons.SEARCH
        )
        
        self.produto_field = ft.TextField(
            label="Produto",
            width=250,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
        )
        
        # Campo de categoria
        self.categoria_field = ft.Dropdown(
            label="Categoria",
            width=200,
            height=50,
            color=ft.colors.BLACK,
            text_style=ft.TextStyle(color=ft.colors.BLACK),
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            border_color=ft.colors.BLUE_200,
            focused_border_color=ft.colors.BLUE_100,
            bgcolor=ft.colors.WHITE,
            focused_bgcolor=ft.colors.WHITE,
            content_padding=10,
            options=[
                ft.dropdown.Option(
                    key="",
                    text="Selecione uma categoria"
                )
            ]
        )
        
        self.quantidade_field = ft.TextField(
            label="Quantidade",
            width=100,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="1"
        )
        
        self.preco_compra_field = ft.TextField(
            label="Preço Custo (MZN)",
            width=150,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="MZN "
        )
        
        self.preco_venda_field = ft.TextField(
            label="Preço Venda (MZN)",
            width=150,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="MZN "
        )
        
        self.observacoes_field = ft.TextField(
            label="Observações",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_color=ft.colors.BLUE_GREY_300,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=14,
            content_padding=10,
            border_radius=8,
        )
        
        # Botões
        self.btn_adicionar_item = ft.ElevatedButton(
            text="Adicionar",
            icon=ft.icons.ADD,
            style=ft.ButtonStyle(
                padding=15,
                bgcolor=ft.colors.BLUE_600,
                color=ft.colors.WHITE
            ),
            on_click=self.adicionar_item_compra
        )
        
        self.btn_salvar_compra = ft.ElevatedButton(
            text="Salvar Compra",
            icon=ft.icons.SAVE,
            style=ft.ButtonStyle(
                padding=15,
                bgcolor=ft.colors.GREEN_600,
                color=ft.colors.WHITE
            ),
            on_click=self.salvar_compra
        )
        
        # Tabela de itens
        self.tabela_itens = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Produto", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Categoria", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Quantidade", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Preço Custo", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Preço Venda", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.GREY_900)),
            ],
            rows=[],
        )
        apply_table_style(self.tabela_itens)
    
    
    # Método build removido pois estava duplicado e mostrava mensagem de desenvolvimento

    def did_mount(self):
        print("=== ComprasDiaView.did_mount() chamado ===")
        # Garante que a página está atualizada
        self.page.update()

    def criar_layout(self):
        print("Criando layout...")
        
        # Cria o cabeçalho com margem inferior e botão de voltar
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/dashboard"),
                        icon_color=ft.colors.BLUE_700
                    ),
                    ft.Text(
                        "Compras do Dia",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_700
                    )
                ]),
                create_header("Compras do Dia", self.page, self.usuario)
            ]),
            margin=ft.margin.only(bottom=20)
        )
        print("Cabeçalho criado")
        
        # Título da seção
        titulo_secao = ft.Container(
            content=ft.Text(
                "Nova Compra",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_700
            ),
            padding=ft.padding.only(bottom=10)
        )
        
        # Cria o formulário de adição de itens
        form = ft.Container(
            content=ft.Column(
                controls=[
                    titulo_secao,
                    self.fornecedor_field,
                    ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                    ft.Row(
                        controls=[
                            self.codigo_field,
                            self.produto_field,
                            self.categoria_field,
                        ],
                        spacing=10,
                        wrap=True,
                    ),
                    ft.Row(
                        controls=[
                            self.quantidade_field,
                            self.preco_compra_field,
                            self.preco_venda_field,
                            self.btn_adicionar_item
                        ],
                        spacing=10,
                        wrap=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=self.observacoes_field,
                                expand=True
                            ),
                        ]
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.colors.GREY_300),
            margin=ft.margin.only(bottom=20),
        )
        
        # Cria a tabela de itens
        tabela_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Itens da Compra", 
                           weight=ft.FontWeight.BOLD, 
                           size=16,
                           color=ft.colors.BLUE_700),
                    ft.Container(
                        content=self.tabela_itens,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=8,
                        padding=10,
                    ),
                ],
                spacing=10,
            ),
            padding=20,
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.colors.GREY_300),
            margin=ft.margin.only(bottom=20),
        )
        
        # Cria o botão de salvar
        botoes_container = ft.Container(
            content=ft.Row(
                controls=[
                    self.btn_salvar_compra,
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
            padding=ft.padding.only(right=20, bottom=20),
        )
        
        # Conteúdo principal com padding
        conteudo_principal = ft.Container(
            content=ft.Column(
                controls=[
                    form,
                    tabela_container,
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=ft.padding.only(top=20, left=20, right=20),
            expand=True,
        )
        
        # Layout principal com fundo branco
        layout = ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    conteudo_principal,
                    botoes_container
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            bgcolor=ft.colors.WHITE,
            padding=0,
            margin=0
        )
        
        print("Layout criado com sucesso")
        return layout
    
    def carregar_categorias(self):
        """Carrega as categorias do banco de dados"""
        try:
            self.categorias = self.db.obter_categorias()
            print(f"Categorias carregadas: {len(self.categorias)} categorias")
            
            # Limpa as opções atuais
            self.categoria_field.options = []
            
            # Adiciona a opção padrão
            self.categoria_field.options.append(
                ft.dropdown.Option(
                    key="",
                    text="Selecione uma categoria"
                )
            )
            
            # Adiciona as categorias do banco de dados
            for categoria in self.categorias:
                self.categoria_field.options.append(
                    ft.dropdown.Option(
                        key=str(categoria['id']),
                        text=categoria['nome']
                    )
                )
            
            # Atualiza o dropdown apenas se o controle já estiver na página
            if self.page is not None and self in self.page.controls:
                self.categoria_field.update()
            
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")
            # Só mostra o snackbar se a página estiver disponível
            if hasattr(self, 'page') and self.page is not None:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Erro ao carregar categorias: {e}", color=ft.colors.WHITE),
                    bgcolor=ft.colors.RED_400,
                )
                self.page.snack_bar.open = True
                self.page.update()
    
    def buscar_produto(self, e):
        """Busca um produto pelo código ou nome"""
        try:
            termo = self.codigo_field.value.strip()
            
            # Se o campo estiver vazio, limpa os campos
            if not termo:
                self.limpar_campos_produto()
                return
                
            # Busca o produto no banco de dados
            produto = self.db.buscar_produto_por_codigo_ou_nome(termo)
            
            if produto:
                # Preenche os campos com os dados do produto
                self.produto_field.value = produto.get('nome', '')
                
                # Usa get() com valor padrão para evitar KeyError
                preco_compra = produto.get('preco_compra', 0)
                preco_venda = produto.get('preco_venda', 0)
                
                # Converte para string, garantindo que temos um valor válido
                self.preco_compra_field.value = str(preco_compra) if preco_compra is not None else "0"
                self.preco_venda_field.value = str(preco_venda) if preco_venda is not None else "0"
                
                # Define a categoria do produto se existir
                if 'categoria_id' in produto and produto['categoria_id']:
                    self.categoria_field.value = str(produto['categoria_id'])
                else:
                    self.categoria_field.value = ""
                
                # Define o foco no campo de quantidade
                self.quantidade_field.focus()
            else:
                # Produto não encontrado, limpa os campos
                self.limpar_campos_produto()
                
                # Mostra mensagem informativa
                if hasattr(self, 'page') and self.page is not None:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text("Produto não encontrado", color=ft.colors.WHITE),
                        bgcolor=ft.colors.ORANGE_400,
                    )
                    self.page.snack_bar.open = True
                    
            # Atualiza a interface
            self.update()
            
        except Exception as e:
            print(f"Erro ao buscar produto: {e}")
            if hasattr(self, 'page') and self.page is not None:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Erro ao buscar produto: {e}", color=ft.colors.WHITE),
                    bgcolor=ft.colors.RED_400,
                )
                self.page.snack_bar.open = True
                self.page.update()
    
    def limpar_campos_produto(self):
        """Limpa os campos do formulário de produto"""
        self.produto_field.value = ""
        self.quantidade_field.value = "1"
        self.preco_compra_field.value = ""
        self.preco_venda_field.value = ""
        self.categoria_field.value = ""
        self.update()
    
    def carregar_compras_dia(self):
        """Carrega as compras do dia atual"""
        try:
            # Limpa a tabela de itens
            self.itens_compra = []
            self.tabela_itens.rows = []
            
            # Obtém a data atual no formato YYYY-MM-DD
            data_atual = datetime.now().strftime("%Y-%m-%d")
            
            # Busca as compras do dia no banco de dados
            compras = self.db.fetchall("""
                SELECT c.id, c.data_compra, c.fornecedor, c.valor_total, 
                       u.nome as usuario_nome
                FROM compras c
                JOIN usuarios u ON c.usuario_id = u.id
                WHERE DATE(c.data_compra) = ?
                ORDER BY c.data_compra DESC
            """, (data_atual,))
            
            # Adiciona as compras à lista
            for compra in compras:
                # Formata a data
                data_formatada = datetime.strptime(compra['data_compra'], "%Y-%m-%d %H:%M:%S")
                data_formatada = data_formatada.strftime("%d/%m/%Y %H:%M")
                
                # Adiciona à lista de itens
                self.itens_compra.append({
                    'id': compra['id'],
                    'data': data_formatada,
                    'fornecedor': compra['fornecedor'],
                    'valor_total': compra['valor_total'],
                    'usuario': compra['usuario_nome']
                })
            
            # Atualiza a tabela
            self.atualizar_tabela_compras()
            
        except Exception as e:
            print(f"Erro ao carregar compras do dia: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao carregar compras: {e}", color=ft.colors.WHITE),
                bgcolor=ft.colors.RED_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def atualizar_tabela_compras(self):
        """Atualiza a tabela de compras com os itens atuais"""
        # Limpa as linhas atuais
        self.tabela_itens.rows = []
        
        # Adiciona as compras à tabela
        for compra in self.itens_compra:
            self.tabela_itens.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(compra['data'])),
                        ft.DataCell(ft.Text(compra['fornecedor'])),
                        ft.DataCell(ft.Text(f"MZN {compra['valor_total']:.2f}")),
                        ft.DataCell(ft.Text(compra['usuario'])),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.icons.VISIBILITY,
                                        icon_color=ft.colors.BLUE_600,
                                        tooltip="Ver detalhes",
                                        on_click=lambda e, c=compra: self.ver_detalhes_compra(c)
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        icon_color=ft.colors.RED_600,
                                        tooltip="Excluir compra",
                                        on_click=lambda e, c=compra: self.confirmar_exclusao_compra(c)
                                    )
                                ]
                            )
                        )
                    ]
                )
            )
        
        # Atualiza a interface
        self.update()

    def adicionar_item_compra(self, e):
        """Adiciona um item à lista de compras"""
        try:
            # Validar campos obrigatórios
            if not self.codigo_field.value or not self.produto_field.value or not self.quantidade_field.value:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Preencha todos os campos obrigatórios"),
                    bgcolor=ft.colors.RED_400
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Criar dicionário com os dados do item
            item = {
                'codigo': self.codigo_field.value,
                'produto': self.produto_field.value,
                'categoria': self.categoria_field.value or "Sem Categoria",
                'quantidade': float(self.quantidade_field.value or 1),
                'preco_compra': float(self.preco_compra_field.value or 0) if self.preco_compra_field.value else 0,
                'preco_venda': float(self.preco_venda_field.value or 0) if self.preco_venda_field.value else 0,
            }
            
            # Adicionar à lista de itens
            self.itens_compra.append(item)
            
            # Atualizar a tabela
            self.atualizar_tabela_itens()
            
            # Limpar campos
            self.codigo_field.value = ""
            self.produto_field.value = ""
            self.quantidade_field.value = "1"
            self.preco_compra_field.value = ""
            self.preco_venda_field.value = ""
            
            # Atualizar a interface
            self.update()
            
            # Mostrar mensagem de sucesso
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Item adicionado com sucesso!"),
                bgcolor=ft.colors.GREEN_400
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao adicionar item: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao adicionar item: {str(e)}"),
                bgcolor=ft.colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def atualizar_tabela_itens(self):
        """Atualiza a tabela de itens com os itens atuais"""
        try:
            # Limpar linhas existentes
            self.tabela_itens.rows.clear()
            
            # Adicionar cada item à tabela
            for item in self.itens_compra:
                self.tabela_itens.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(item['codigo']))),
                            ft.DataCell(ft.Text(item['produto'])),
                            ft.DataCell(ft.Text(item['categoria'])),
                            ft.DataCell(ft.Text(str(item['quantidade']))),
                            ft.DataCell(ft.Text(f"MZN {item['preco_compra']:.2f}")),
                            ft.DataCell(ft.Text(f"MZN {item['preco_venda']:.2f}")),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        icon_color=ft.colors.RED,
                                        on_click=lambda e, item=item: self.remover_item_compra(item)
                                    )
                                ])
                            ),
                        ]
                    )
                )
            
            # Forçar atualização da interface
            self.update()
            
        except Exception as e:
            print(f"Erro ao atualizar tabela de itens: {e}")
    
    def remover_item_compra(self, item):
        """Remove um item da lista de compras"""
        try:
            if item in self.itens_compra:
                self.itens_compra.remove(item)
                self.atualizar_tabela_itens()
                
                # Mostrar mensagem de sucesso
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Item removido com sucesso!"),
                    bgcolor=ft.colors.GREEN_400
                )
                self.page.snack_bar.open = True
                self.page.update()
                
        except Exception as e:
            print(f"Erro ao remover item: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao remover item: {str(e)}"),
                bgcolor=ft.colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()

    def salvar_compra(self, e):
        """Salva a compra no banco de dados"""
        try:
            # Validar se existem itens na compra
            if not self.itens_compra:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Adicione itens à compra antes de salvar"),
                    bgcolor=ft.colors.ORANGE_400
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Validar fornecedor
            fornecedor = self.fornecedor_field.value.strip()
            if not fornecedor:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Informe o nome do fornecedor"),
                    bgcolor=ft.colors.RED_400
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Calcular totais
            total_compra = sum(item['quantidade'] * item['preco_compra'] for item in self.itens_compra)
            total_itens = len(self.itens_compra)
            
            # Obter observações
            observacoes = self.observacoes_field.value or ""
            
            # Inserir a compra no banco de dados
            db = Database()
            
            with db.conn:
                # Inserir cabeçalho da compra
                compra_id = db.inserir_compra(
                    fornecedor=fornecedor,
                    total=total_compra,
                    total_itens=total_itens,
                    observacoes=observacoes,
                    usuario_id=self.usuario_id
                )
                
                # Inserir itens da compra
                for item in self.itens_compra:
                    # Inserir produto se não existir
                    produto_id = db.obter_produto_por_codigo(item['codigo'])
                    if not produto_id:
                        produto_id = db.inserir_produto(
                            codigo=item['codigo'],
                            nome=item['produto'],
                            categoria=item['categoria'],
                            preco_compra=item['preco_compra'],
                            preco_venda=item['preco_venda'],
                            quantidade=item['quantidade'],
                            quantidade_minima=0,
                            ativo=True
                        )
                    
                    # Inserir item da compra
                    db.inserir_item_compra(
                        compra_id=compra_id,
                        produto_id=produto_id,
                        quantidade=item['quantidade'],
                        preco_unitario=item['preco_compra'],
                        preco_venda=item['preco_venda']
                    )
                    
                    # Atualizar estoque do produto
                    db.atualizar_estoque(
                        produto_id=produto_id,
                        quantidade=item['quantidade'],
                        operacao='entrada'
                    )
            
            # Limpar formulário após salvar
            self.itens_compra = []
            self.atualizar_tabela_itens()
            self.fornecedor_field.value = ""
            self.observacoes_field.value = ""
            
            # Atualizar a interface
            self.update()
            
            # Mostrar mensagem de sucesso
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Compra salva com sucesso! ID: {compra_id}"),
                bgcolor=ft.colors.GREEN_400
            )
            self.page.snack_bar.open = True
            self.page.update()
            
            # Atualizar a lista de compras
            self.carregar_compras_dia()
            
        except Exception as e:
            print(f"Erro ao salvar compra: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao salvar compra: {str(e)}"),
                bgcolor=ft.colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()


    def confirmar_exclusao_compra(self, compra):
        """Confirma a exclusão de uma compra"""
        try:
            # Exibe diálogo de confirmação
            dialog = ft.AlertDialog(
                title=ft.Text("Confirmar Exclusão"),
                content=ft.Text(f"Deseja realmente excluir a compra {compra['id']}?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: self.fechar_dialogo_exclusao(e)),
                    ft.TextButton("Excluir", on_click=lambda e: self.excluir_compra(e, compra['id']))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            # Mostra o diálogo
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao confirmar exclusão: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao confirmar exclusão: {str(e)}"),
                bgcolor=ft.colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def fechar_dialogo_exclusao(self, e):
        """Fecha o diálogo de confirmação de exclusão"""
        self.page.dialog.open = False
        self.page.update()
    
    def excluir_compra(self, e, compra_id):
        """Exclui uma compra do banco de dados"""
        try:
            # Fecha o diálogo de confirmação
            self.fechar_dialogo_exclusao(e)
            
            # Exclui a compra do banco de dados
            self.db.execute("DELETE FROM compras WHERE id = ?", (compra_id,))
            
            # Recarrega as compras do dia
            self.carregar_compras_dia()
            
            # Mostra mensagem de sucesso
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Compra excluída com sucesso!"),
                bgcolor=ft.colors.GREEN_400
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao excluir compra: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao excluir compra: {str(e)}"),
                bgcolor=ft.colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
