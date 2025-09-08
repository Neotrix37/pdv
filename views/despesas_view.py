import flet as ft
from database.database import Database
from datetime import datetime, date
import locale
from utils.translation_mixin import TranslationMixin
from views.generic_table_style import apply_table_style

class DespesasView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        locale.setlocale(locale.LC_ALL, 'pt_PT.UTF-8')
        from utils.helpers import formatar_moeda
        
        # Referência para o texto do total geral
        self.total_geral_text = ft.Ref[ft.Text]()
        self.total_geral_text.current = ft.Text("MT 0,00")  # Inicializa com um valor padrão

        # Buscar categorias do banco de dados
        self.categorias = [
            categoria['nome'] for categoria in 
            self.db.fetchall("SELECT nome FROM categorias_despesa WHERE 1 ORDER BY nome")
        ]

        # Variável para controlar se está editando
        self.editando = False
        self.despesa_id = None
        
        # Botão de salvar/atualizar
        self.btn_salvar = ft.ElevatedButton(
            "Salvar",
            on_click=self.salvar_despesa,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.GREEN,
                color=ft.colors.WHITE
            )
        )
        
        # Botão de cancelar edição
        self.btn_cancelar = ft.OutlinedButton(
            "Cancelar",
            on_click=self.cancelar_edicao,
            visible=False,
            style=ft.ButtonStyle(
                color=ft.colors.BLUE_900
            )
        )
        
        # Campos do formulário com cores ajustadas
        self.tipo_despesa = ft.Dropdown(
            label="Tipo de Despesa",
            width=200,
            options=[
                ft.dropdown.Option("Fixa"),
                ft.dropdown.Option("Variável")
            ],
            value="Fixa"
        )

        self.categoria = ft.Dropdown(
            label="Categoria",
            width=200,
            options=[ft.dropdown.Option(cat) for cat in self.categorias]
        )

        self.descricao = ft.TextField(
            label="Descrição",
            width=400,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLUE_900),
            border_color=ft.colors.BLUE_900,
            focused_border_color=ft.colors.BLUE_900,
            cursor_color=ft.colors.BLUE_900
        )

        self.valor = ft.TextField(
            label="Valor",
            width=200,
            prefix_text="MT ",
            keyboard_type=ft.KeyboardType.NUMBER,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLUE_900),
            border_color=ft.colors.BLUE_900,
            focused_border_color=ft.colors.BLUE_900,
            cursor_color=ft.colors.BLUE_900
        )


        # Adicionar filtros
        self.filtro_tipo = ft.Dropdown(
            label="Filtrar por Tipo",
            width=200,
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Fixa"),
                ft.dropdown.Option("Variável")
            ],
            value="Todos",
            on_change=self.aplicar_filtros
        )

        # Tabela de despesas
        self.despesas_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Tipo", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Categoria", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Descrição", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Valor", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.GREY_900))
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=5,
            heading_row_color=ft.colors.BLUE_50,
            heading_row_height=40,
            data_row_height=50,
            horizontal_margin=10,
            column_spacing=20,
            divider_thickness=0.5
        )

        # Card para mostrar o total das despesas
        self.total_despesas_text = ft.Text(
            "MT 0,00", 
            size=24, 
            weight=ft.FontWeight.BOLD, 
            color=ft.colors.BLUE_900
        )
        # Botão de atualização
        self.btn_atualizar = ft.IconButton(
            icon=ft.icons.REFRESH,
            icon_color=ft.colors.GREEN_700,
            icon_size=24,
            tooltip="Atualizar totais",
            on_click=self.carregar_despesas,
            style=ft.ButtonStyle(
                color=ft.colors.GREEN_700,
                bgcolor=ft.colors.GREEN_50,
                overlay_color=ft.colors.GREEN_100,
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )
        
        self.total_despesas_card = ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET, color=ft.colors.BLUE_900, size=28),
                                ft.Column(
                                    [
                                        ft.Text("Total de Despesas", size=16, weight=ft.FontWeight.W_500),
                                        self.total_despesas_text
                                    ],
                                    spacing=0
                                )
                            ],
                            spacing=10
                        ),
                        self.btn_atualizar
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=15),
                border_radius=ft.border_radius.all(10),
                bgcolor=ft.colors.BLUE_50,
                border=ft.border.all(1, ft.colors.BLUE_100)
            ),
            elevation=2
        )
        
        # Inicializar o container da tabela com scroll
        self.tabela_container = ft.Container(
            content=ft.Column(
                [
                    self.despesas_table
                ],
                scroll=ft.ScrollMode.AUTO
            ),
            height=280,  # Altura ainda mais reduzida
            margin=ft.margin.only(top=10),
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            padding=10,
            border=ft.border.all(1, ft.colors.BLUE_200),
        )
        
        # Carregar despesas iniciais e total
        self.carregar_despesas()
        # Garantir que o total seja exibido ao carregar a página
        self.atualizar_total_despesas()

    def salvar_despesa(self, e):
        try:
            # Usar data atual para data_vencimento se não for fornecida
            data_atual = datetime.now().strftime("%Y-%m-%d")
            dados = {
                'tipo': self.tipo_despesa.value,
                'categoria': self.categoria.value,
                'descricao': self.descricao.value,
                'valor': float(self.valor.value.replace('MT ', '').replace(',', '.')),
                'status': 'Pago',
                'data_pagamento': data_atual,
                'data_vencimento': data_atual  # Usando a mesma data do pagamento como vencimento
            }
            
            if self.editando and self.despesa_id:
                self.atualizar_despesa(self.despesa_id, dados)
                return

            self.db.execute("""
                INSERT INTO despesas_recorrentes 
                (tipo, categoria, descricao, valor, status, data_pagamento, data_vencimento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                dados['tipo'],
                dados['categoria'],
                dados['descricao'],
                dados['valor'],
                dados['status'],
                dados['data_pagamento'],
                dados['data_vencimento']
            ))

            self.limpar_formulario()
            self.carregar_despesas()
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Despesa salva com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
        except Exception as e:
            print(f"Erro ao salvar despesa: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Erro ao salvar despesa!"))
            )

    def editar_despesa(self, e):
        try:
            despesa = e.control.data
            self.editando = True
            self.despesa_id = despesa['id']
            
            # Preencher formulário com dados da despesa
            self.tipo_despesa.value = despesa['tipo']
            self.categoria.value = despesa['categoria']
            self.descricao.value = despesa['descricao']
            self.valor.value = str(despesa['valor'])
            
            # Atualizar botões
            self.btn_salvar.text = "Atualizar"
            self.btn_cancelar.visible = True
            
            # Atualizar a UI
            self.update()
            
            # Rolar até o topo da página de forma segura
            try:
                if hasattr(self.page, 'scroll_to') and callable(self.page.scroll_to):
                    self.page.scroll_to(0, duration=300)
            except Exception as e:
                print(f"Aviso ao rolar a página: {e}")
            
        except Exception as e:
            print(f"Erro ao editar despesa: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Erro ao editar despesa!"))
            )

    def cancelar_edicao(self, e):
        self.limpar_formulario()
        self.editando = False
        self.despesa_id = None
        self.btn_salvar.text = "Salvar"
        self.btn_cancelar.visible = False
        self.update()
        
    def atualizar_total_despesas(self):
        """Atualiza o card com o total das despesas"""
        try:
            total = self.db.fetchone("""
                SELECT COALESCE(SUM(valor), 0) as total 
                FROM despesas_recorrentes
            """)
            
            if total and 'total' in total:
                valor_total = float(total['total'])
                if hasattr(self, 'total_despesas_text'):
                    self.total_despesas_text.value = f"MT {valor_total:,.2f}".replace('.', '#')\
                        .replace(',', '.').replace('#', ',')
                    self.update()
        except Exception as e:
            print(f"Erro ao atualizar total de despesas: {e}")

    def carregar_despesas(self, e=None):
        """Carrega as despesas do banco de dados e atualiza a tabela"""
        try:
            query = """
                SELECT id, tipo, categoria, descricao, valor
                FROM despesas_recorrentes 
                ORDER BY id DESC
            """
            print(f"Executando query: {query}")  # Log de depuração
            despesas = self.db.fetchall(query)
            print(f"\n=== DADOS DO BANCO ===")
            print(f"Total de despesas encontradas: {len(despesas) if despesas else 0}")
            if despesas:
                print(f"Primeira despesa: {despesas[0]}")
                print(f"Soma dos valores: {sum(float(d['valor']) for d in despesas if d and 'valor' in d)}")
            
            # Atualiza a tabela com as despesas
            print("\n=== ATUALIZANDO TABELA ===")
            print(f"Número de despesas a serem exibidas: {len(despesas) if despesas else 0}")
            if despesas:
                print(f"Soma dos valores a serem exibidos: {sum(float(d['valor']) for d in despesas if d and 'valor' in d)}")
            
            self.atualizar_tabela_despesas(despesas)
            
            print("\n=== APÓS ATUALIZAR TABELA ===")
            if hasattr(self, 'total_geral_text') and self.total_geral_text and hasattr(self.total_geral_text, 'current') and self.total_geral_text.current:
                print(f"Valor no card após atualização: {self.total_geral_text.current.value}")
            
            # Atualiza o total das despesas
            self.atualizar_total_despesas()
            
            # Se a página já estiver construída, força a atualização
            if hasattr(self, 'page') and self.page is not None:
                self.update()
                
        except Exception as e:
            import traceback
            print("\n=== ERRO ===")
            print(f"Erro ao carregar despesas: {e}")
            print("Traceback:")
            print(traceback.format_exc())
            
            # Tenta atualizar o total mesmo em caso de erro na tabela
            try:
                self.atualizar_total_despesas()
            except:
                pass
                
            if hasattr(self, 'page') and self.page is not None:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"Erro ao carregar despesas: {str(e)}"))
                )

    def atualizar_despesa(self, despesa_id, dados):
        try:
            self.db.execute("""
                UPDATE despesas_recorrentes 
                SET tipo = ?, categoria = ?, descricao = ?, 
                    valor = ?, status = ?, data_pagamento = ?, data_vencimento = ?
                WHERE id = ?
            """, (
                dados['tipo'],
                dados['categoria'],
                dados['descricao'],
                dados['valor'],
                dados['status'],
                dados['data_pagamento'],
                dados.get('data_vencimento', dados['data_pagamento']),  # Usa data_vencimento ou data_pagamento como fallback
                despesa_id
            ))
            
            # Reset form and UI state
            self.limpar_formulario()
            self.editando = False
            self.despesa_id = None
            self.btn_salvar.text = "Salvar"
            self.btn_cancelar.visible = False
            
            # Recarregar as despesas para garantir que a tabela e o total sejam atualizados
            self.carregar_despesas()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Despesa atualizada com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
        except Exception as e:
            print(f"Erro ao atualizar despesa: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Erro ao atualizar despesa!"))
            )

    def limpar_formulario(self):
        """Limpa todos os campos do formulário"""
        self.tipo_despesa.value = "Fixa"
        self.categoria.value = None
        self.descricao.value = ""
        self.valor.value = ""
        self.update()

    def confirmar_exclusao(self, e):
        try:
            despesa = e.control.data
            
            def excluir_despesa(e):
                try:
                    self.db.execute(
                        "DELETE FROM despesas_recorrentes WHERE id = ?",
                        (despesa['id'],)
                    )
                    
                    # Fechar diálogo e atualizar lista
                    dlg_modal.open = False
                    self.page.update()
                    self.carregar_despesas()
                    
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Despesa excluída com sucesso!"),
                            bgcolor=ft.colors.GREEN
                        )
                    )
                    
                except Exception as e:
                    print(f"Erro ao excluir despesa: {e}")
                    self.page.show_snack_bar(
                        ft.SnackBar(content=ft.Text("Erro ao excluir despesa!"))
                    )
            
            # Diálogo de confirmação
            dlg_modal = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar Exclusão"),
                content=ft.Text("Tem certeza que deseja excluir esta despesa?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda x: self.fechar_dialogo(dlg_modal)),
                    ft.TextButton("Excluir", on_click=excluir_despesa)
                ]
            )
            
            self.page.dialog = dlg_modal
            dlg_modal.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao confirmar exclusão: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Erro ao processar exclusão!"))
            )

    def fechar_dialogo(self, dlg):
        """Fecha um diálogo e atualiza a página"""
        dlg.open = False
        self.page.update()

    def aplicar_filtros(self, e):
        try:
            query = """
                SELECT * FROM despesas_recorrentes
                WHERE 1=1
            """
            params = []

            if self.filtro_tipo.value != "Todos":
                query += " AND tipo = ?"
                params.append(self.filtro_tipo.value)

            query += " ORDER BY id DESC"

            despesas = self.db.fetchall(query, tuple(params))
            self.atualizar_tabela_despesas(despesas)

        except Exception as e:
            print(f"Erro ao aplicar filtros: {e}")

    def formatar_moeda(self, valor):
        """Formata o valor para o formato monetário"""
        if isinstance(valor, str):
            try:
                valor = float(valor)
            except (ValueError, TypeError):
                return "MT 0,00"
        return f"MT {valor:,.2f}".replace('.', '|').replace(',', '.').replace('|', ',')


    def atualizar_tabela_despesas(self, despesas):
        self.despesas_table.rows.clear()
        total = 0.0
        
        for despesa in despesas:
            total += float(despesa['valor'])
            self.despesas_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(despesa['tipo'], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(despesa['categoria'], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(despesa['descricao'], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(self.formatar_moeda(despesa['valor']), color=ft.colors.GREY_900)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    icon_color=ft.colors.BLUE_600,
                                    tooltip="Editar",
                                    data=despesa,
                                    on_click=self.editar_despesa,
                                    style=ft.ButtonStyle(
                                        padding=5,
                                        overlay_color=ft.colors.BLUE_50
                                    )
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=ft.colors.RED_600,
                                    tooltip="Excluir",
                                    data=despesa,
                                    on_click=self.confirmar_exclusao,
                                    style=ft.ButtonStyle(
                                        padding=5,
                                        overlay_color=ft.colors.RED_50
                                    )
                                )
                            ],
                            spacing=5,
                            alignment=ft.MainAxisAlignment.CENTER,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True)
                        )
                    ],
                    color=ft.colors.WHITE,
                    selected=True,
                    on_select_changed=None
                )
            )
        
        # Atualizar o card de total
        self.atualizar_total_despesas()
        
        # Formatar o valor total
        total_formatado = self.formatar_moeda(total) if total else "MT 0,00"
        
        # Atualizar o texto do total no card lateral
        if hasattr(self, 'total_geral_text'):
            # Se a referência current existe, atualiza diretamente
            if hasattr(self.total_geral_text, 'current') and self.total_geral_text.current is not None:
                self.total_geral_text.current.value = total_formatado
                print(f"Atualizando total_geral_text.current para: {total_formatado}")
            
            # Se não encontrou a referência, tenta localizar o controle na árvore
            elif hasattr(self, 'page') and self.page is not None:
                print("Buscando controle na árvore...")
                for control in self.page.controls:
                    if hasattr(control, 'content'):
                        # Verifica se é um container com referência ao total_geral_text
                        if hasattr(control, 'ref') and control.ref == self.total_geral_text:
                            control.value = total_formatado
                            print(f"Atualizado controle direto: {control}")
                            break
                        
                        # Busca em controles aninhados
                        if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                            for c in control.content.controls:
                                if hasattr(c, 'ref') and c.ref == self.total_geral_text:
                                    c.value = total_formatado
                                    print(f"Atualizado controle aninhado: {c}")
                                    break
        
        # Forçar atualização da interface
        if hasattr(self, 'page') and self.page is not None:
            print("Atualizando página...")
            self.page.update()
            
            # Se ainda não estiver visível, tentar novamente após um pequeno atraso
            if hasattr(self, 'total_geral_text') and hasattr(self.total_geral_text, 'current') and \
               self.total_geral_text.current is not None and self.total_geral_text.current.value == "MT 0,00":
                
                def atualizar_com_atraso():
                    import time
                    time.sleep(1)  # Aguarda 1 segundo
                    if hasattr(self, 'total_geral_text') and hasattr(self.total_geral_text, 'current') and \
                       self.total_geral_text.current is not None:
                        print(f"Atualização atrasada para: {total_formatado}")
                        self.total_geral_text.current.value = total_formatado
                        self.page.update()
                
                import threading
                threading.Thread(target=atualizar_com_atraso).start()

    def build(self):
        # Criar a interface
        # Criar o layout principal
        layout = ft.Column(
            [
            # Cabeçalho com estilo igual às outras páginas
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/dashboard"),
                        icon_color=ft.colors.WHITE
                    ),
                    ft.Icon(
                        name=ft.icons.PAYMENTS,
                        size=30,
                        color=ft.colors.WHITE
                    ),
                    ft.Text(
                        "Gestão de Despesas",
                        size=20,
                        color=ft.colors.WHITE
                    )
                ], spacing=10),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
                ),
                padding=20,
                border_radius=10
            ),

            # Formulário com fundo branco para melhor contraste
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Nova Despesa",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900
                    ),
                    ft.Row([
                        # Coluna dos campos do formulário
                        ft.Column([
                            ft.Row([
                                self.tipo_despesa,
                                self.categoria,
                                self.valor
                            ]),
                            ft.Row([self.descricao])
                        ], expand=2),
                        
                        # Card informativo
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.BLUE_700, size=20),
                                    ft.Text("Resumo de Despesas", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                                    ft.Container(expand=True),
                                    self.btn_atualizar
                                ]),
                                ft.Divider(color=ft.colors.BLUE_100, height=10),
                                ft.Row([
                                    ft.Text("Total de Despesas:", size=12, weight=ft.FontWeight.W_500, color=ft.colors.BLUE_900),
                                    # Usando a referência diretamente
                                    ft.Text(
                                        value="MT 0,00", 
                                        size=14, 
                                        weight=ft.FontWeight.BOLD, 
                                        color=ft.colors.BLUE_900,
                                        ref=self.total_geral_text,
                                        key="total_geral_text"
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(color=ft.colors.BLUE_100, height=10),
                                ft.Text("• Clique em uma despesa para editar", size=10, color=ft.colors.GREY_600),
                                ft.Text("• Use os filtros para buscar despesas", size=10, color=ft.colors.GREY_600),
                            ], spacing=8),
                            padding=15,
                            margin=ft.margin.only(left=20),
                            bgcolor=ft.colors.BLUE_50,
                            border_radius=8,
                            border=ft.border.all(1, ft.colors.BLUE_100),
                            width=250,
                            key="card_total"
                        )
                    ]),
                    ft.Row([
                        self.btn_salvar,
                        self.btn_cancelar,
                        ft.OutlinedButton(
                            "Limpar",
                            on_click=lambda _: self.limpar_formulario(),
                            style=ft.ButtonStyle(
                                color=ft.colors.BLUE_900
                            )
                        ),
                        ft.ElevatedButton(
                            "Ver Histórico",
                            icon=ft.icons.HISTORY,
                            on_click=self._ver_historico,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.ORANGE_600,
                                color=ft.colors.WHITE
                            )
                        )
                    ])
                ]),
                padding=20,
                bgcolor=ft.colors.WHITE,
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color=ft.colors.with_opacity(0.25, ft.colors.BLACK)
                )
            ),

            # Tabela com fundo branco
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Despesas Cadastradas",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900
                    ),
                    # Container com scroll para a tabela
                    self.tabela_container
                ]),
                padding=20,
                bgcolor=ft.colors.WHITE,
                border_radius=10,
                width=1100,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color=ft.colors.with_opacity(0.25, ft.colors.BLACK)
                )
            )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Forçar o carregamento inicial das despesas após a construção do layout
        def on_build(e):
            self.carregar_despesas()
            self.page.update()
            
        # Configurar o evento de resize para garantir que o total seja atualizado
        if hasattr(self, 'page') and self.page is not None:
            self.page.on_resize = on_build

        return layout

    def _ver_historico(self, e):
        """Abre modal com histórico detalhado de despesas"""
        try:
            # Carregar histórico de despesas com informações do usuário
            historico = self._carregar_historico()
            
            # Converter SQLite Row para dicionário se necessário
            historico_dicts = []
            for row in historico:
                if hasattr(row, 'keys'):  # Se for um SQLite Row
                    row_dict = {}
                    for key in row.keys():
                        # Acessa o valor usando a chave e armazena no dicionário
                        row_dict[key] = row[key] if row[key] is not None else ''
                    historico_dicts.append(row_dict)
                else:
                    # Se já for um dicionário, apenas adiciona
                    historico_dicts.append(row)
            
            historico = historico_dicts
            
            # Criar tabela do histórico com larguras ajustadas usando Containers
            historico_table = ft.DataTable(
                columns=[
                    ft.DataColumn(
                        ft.Container(
                            ft.Text("#", weight=ft.FontWeight.BOLD),
                            width=50,
                            alignment=ft.alignment.center
                        ),
                        numeric=True,
                        tooltip="ID da despesa"
                    ),
                    ft.DataColumn(
                        ft.Container(
                            ft.Text("Data", weight=ft.FontWeight.BOLD),
                            width=120,
                            alignment=ft.alignment.center
                        ),
                        tooltip="Data da despesa"
                    ),
                    ft.DataColumn(
                        ft.Container(
                            ft.Text("Descrição", weight=ft.FontWeight.BOLD),
                            width=250
                        ),
                        tooltip="Descrição da despesa"
                    ),
                    ft.DataColumn(
                        ft.Container(
                            ft.Text("Categoria", weight=ft.FontWeight.BOLD),
                            width=150,
                            alignment=ft.alignment.center
                        ),
                        tooltip="Categoria da despesa"
                    ),
                    ft.DataColumn(
                        ft.Container(
                            ft.Text("Tipo", weight=ft.FontWeight.BOLD),
                            width=100,
                            alignment=ft.alignment.center
                        ),
                        tooltip="Tipo de despesa (Fixa/Variável)"
                    ),
                    ft.DataColumn(
                        ft.Container(
                            ft.Text("Valor", weight=ft.FontWeight.BOLD),
                            width=120,
                            alignment=ft.alignment.center_right
                        ),
                        numeric=True,
                        tooltip="Valor da despesa"
                    ),
                ],
                rows=[],
                column_spacing=10,
                heading_row_height=40,
                data_row_height=40,
                show_bottom_border=True,
                border_radius=8,
                border=ft.border.all(1, ft.colors.GREY_300),
                heading_row_color=ft.colors.BLUE_50,
            )

            # Adicionar dados à tabela
            for despesa in historico:
                # Formatar a data
                data_criacao = despesa.get('data_criacao', '')
                if isinstance(data_criacao, str):
                    try:
                        data_obj = datetime.strptime(data_criacao, '%Y-%m-%d %H:%M:%S')
                        data_formatada = data_obj.strftime('%d/%m/%Y %H:%M')
                    except (ValueError, AttributeError):
                        data_formatada = data_criacao
                else:
                    data_formatada = data_criacao.strftime('%d/%m/%Y %H:%M') if data_criacao else ''
                
                # Obter valor e formatar como número
                valor = despesa.get('valor', 0)
                try:
                    valor_formatado = f"MT {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                except (ValueError, TypeError):
                    valor_formatado = "MT 0,00"
                
                # Adicionar linha à tabela
                historico_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Container(
                                    ft.Text(str(despesa.get('id', '')), text_align=ft.TextAlign.CENTER),
                                    alignment=ft.alignment.center,
                                    width=50
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    ft.Text(data_formatada, text_align=ft.TextAlign.CENTER),
                                    alignment=ft.alignment.center,
                                    width=120
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    ft.Text(despesa.get('descricao', '')),
                                    padding=ft.padding.symmetric(horizontal=4)
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    ft.Text(despesa.get('categoria', ''), text_align=ft.TextAlign.CENTER),
                                    alignment=ft.alignment.center,
                                    width=150
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    ft.Container(
                                        ft.Text(
                                            despesa.get('tipo', ''),
                                            color=ft.colors.WHITE,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                        border_radius=8,
                                        bgcolor=ft.colors.BLUE_700 if despesa.get('tipo') == 'Fixa' else ft.colors.GREEN_700,
                                        alignment=ft.alignment.center
                                    ),
                                    alignment=ft.alignment.center,
                                    width=100
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    ft.Text(valor_formatado, text_align=ft.TextAlign.RIGHT),
                                    alignment=ft.alignment.center_right,
                                    width=120
                                )
                            ),
                        ]
                    )
                )
            
            # Campo de busca
            campo_busca = ft.TextField(
                label="Pesquisar...",
                on_change=lambda e: self._filtrar_historico(e, historico_table, historico),
                expand=True,
                border_color=ft.colors.BLUE_GREY_300,
                focused_border_color=ft.colors.BLUE_500,
                suffix_icon=ft.icons.SEARCH,
            )
            
            # Criar o modal
            modal = ft.AlertDialog(
                modal=True,
                title=ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.HISTORY, color=ft.colors.BLUE_700),
                            ft.Text("Histórico de Despesas", size=20, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_300)),
                ),
                content=ft.Container(
                    content=ft.Column(
                        [
                            # Campo de busca
                            ft.Row(
                                [campo_busca],
                                spacing=10,
                            ),
                            # Contador de itens
                            ft.Container(
                                content=ft.Text(
                                    f"Total: {len(historico)} itens",
                                    color=ft.colors.GREY_600,
                                    weight=ft.FontWeight.W_500
                                ),
                                alignment=ft.alignment.center_right,
                                padding=ft.padding.only(top=5, bottom=5)
                            ),
                            # Container da tabela com scroll
                            ft.Container(
                                content=ft.ListView(
                                    [historico_table],
                                    expand=True,
                                ),
                                height=400,
                                width=1000,
                                border_radius=10,
                                bgcolor=ft.colors.WHITE,
                                padding=10,
                                border=ft.border.all(1, ft.colors.BLUE_200),
                            ),
                        ],
                        spacing=10,
                        expand=True,
                    ),
                    padding=15,
                    expand=True,
                ),
                actions=[
                    ft.ElevatedButton(
                        "Fechar",
                        on_click=lambda _: self._fechar_modal(modal),
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_700,
                            color=ft.colors.WHITE,
                        ),
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            # Abrir o modal
            self.page.dialog = modal
            modal.open = True
            self.page.update()

        except Exception as e:
            print(f"Erro ao abrir histórico: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao carregar histórico: {str(e)}"),
                bgcolor=ft.colors.RED_500,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _carregar_historico(self):
        """Carrega o histórico de despesas do banco de dados"""
        try:
            # Tenta buscar com JOIN primeiro
            try:
                return self.db.fetchall("""
                    SELECT 
                        dr.id,
                        dr.tipo,
                        dr.categoria,
                        dr.descricao,
                        dr.valor,
                        dr.created_at as data_criacao,
                        'Ativa' as status,
                        COALESCE(u.nome, 'Sistema') as usuario_nome
                    FROM despesas_recorrentes dr
                    LEFT JOIN usuarios u ON dr.usuario_id = u.id
                    ORDER BY dr.created_at DESC
                """)
            except Exception:
                # Se falhar, tenta sem o JOIN
                return self.db.fetchall("""
                    SELECT 
                        id,
                        tipo,
                        categoria,
                        descricao,
                        valor,
                        created_at as data_criacao,
                        'Ativa' as status,
                        'Sistema' as usuario_nome
                    FROM despesas_recorrentes
                    ORDER BY created_at DESC
                """)
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            return []

    def _filtrar_historico(self, e, tabela, historico_completo):
        """Filtra o histórico de despesas"""
        try:
            termo = e.control.value.lower()
            
            # Limpar tabela
            tabela.rows.clear()
            
            # Filtrar dados
            historico_filtrado = [
                despesa for despesa in historico_completo
                if (termo in despesa.get('descricao', '').lower()) or
                   (termo in despesa.get('categoria', '').lower()) or
                   (termo in str(despesa.get('id', '')).lower()) or
                   (termo in (despesa.get('data_criacao', '')[:10] if despesa.get('data_criacao') else '')) or
                   (termo in despesa.get('tipo', '').lower())
            ]
            
            # Preencher tabela filtrada
            for despesa in historico_filtrado:
                data_criacao = despesa.get('data_criacao', '')
                if data_criacao:
                    try:
                        data_obj = datetime.strptime(str(data_criacao), '%Y-%m-%d %H:%M:%S')
                        data_formatada = data_obj.strftime('%d/%m/%Y')
                    except (ValueError, TypeError):
                        data_formatada = str(data_criacao)[:10]
                else:
                    data_formatada = ''
                
                valor = despesa.get('valor', 0)
                valor_formatado = f"MT {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                tabela.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Container(ft.Text(str(despesa.get('id', '')), text_align=ft.TextAlign.CENTER), 
                                                  alignment=ft.alignment.center, width=50)),
                            ft.DataCell(ft.Container(ft.Text(data_formatada, text_align=ft.TextAlign.CENTER), 
                                                  alignment=ft.alignment.center, width=120)),
                            ft.DataCell(ft.Container(ft.Text(despesa.get('descricao', '')), 
                                                  padding=ft.padding.symmetric(horizontal=4))),
                            ft.DataCell(ft.Container(ft.Text(despesa.get('categoria', ''), 
                                                  text_align=ft.TextAlign.CENTER), 
                                                  alignment=ft.alignment.center, width=150)),
                            ft.DataCell(ft.Container(
                                ft.Container(
                                    ft.Text(despesa.get('tipo', ''), 
                                          color=ft.colors.WHITE, 
                                          weight=ft.FontWeight.BOLD), 
                                    padding=ft.padding.symmetric(horizontal=8, vertical=2), 
                                    border_radius=8, 
                                    bgcolor=ft.colors.BLUE_700 if despesa.get('tipo') == 'Fixa' else ft.colors.GREEN_700, 
                                    alignment=ft.alignment.center
                                ), 
                                alignment=ft.alignment.center, 
                                width=100
                            )),
                            ft.DataCell(ft.Container(ft.Text(valor_formatado, text_align=ft.TextAlign.RIGHT), 
                                                  alignment=ft.alignment.center_right, width=120))
                        ]
                    )
                )
            
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao filtrar histórico: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao filtrar: {str(e)}"),
                bgcolor=ft.colors.RED_500,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _fechar_modal(self, modal):
        """Fecha o modal de histórico"""
        modal.open = False
        self.page.update()