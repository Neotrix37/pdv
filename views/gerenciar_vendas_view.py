import flet as ft
from database.database import Database
from repositories.venda_repository import VendaRepository
from datetime import datetime, timedelta
from utils.translation_mixin import TranslationMixin
from utils.helpers import formatar_moeda
from views.generic_table_style import apply_table_style
import logging

class GerenciarVendasView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        # Registrar início da operação para diagnóstico de desempenho
        inicio_inicializacao = datetime.now()
        print(f"[DESEMPENHO] Iniciando inicialização da página Gerenciar Vendas em {inicio_inicializacao.strftime('%H:%M:%S.%f')}")
        
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        self.venda_repo = VendaRepository()
        
        # Configurações de paginação
        self.pagina_atual = 1
        self.itens_por_pagina = 50
        self.total_vendas = 0
        
        # Log de acesso à página
        logging.info(f"[ACESSO] Usuário {self.usuario['nome']} (ID: {self.usuario['id']}) acessou a página Gerenciar Vendas em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"[ACESSO] Usuário {self.usuario['nome']} (ID: {self.usuario['id']}) acessou a página Gerenciar Vendas em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Inicializar a referência do total_text
        self.total_text = ft.Ref[ft.Text]()
        
        # Inicializar campos de busca
        print(f"[DESEMPENHO] Inicializando campos de busca...")
        self.init_search_fields()
        
        # Inicializar tabela
        print(f"[DESEMPENHO] Inicializando tabela...")
        self.init_table()
        
        # Inicializar diálogos
        print(f"[DESEMPENHO] Inicializando diálogos...")
        self.init_dialogs()
        
        # Registrar tempo antes de carregar vendas
        antes_carregar = datetime.now()
        tempo_inicializacao = (antes_carregar - inicio_inicializacao).total_seconds()
        print(f"[DESEMPENHO] Inicialização de componentes completada em {tempo_inicializacao:.2f} segundos. Iniciando carregamento de vendas...")
        
        # Carregar vendas iniciais (limitado para melhorar desempenho)
        self.carregar_vendas()
        
        # Registrar tempo total da inicialização
        fim_inicializacao = datetime.now()
        tempo_total = (fim_inicializacao - inicio_inicializacao).total_seconds()
        print(f"[DESEMPENHO] Inicialização total da página completada em {tempo_total:.2f} segundos.")

    def init_search_fields(self):
        # Data inicial (30 dias atrás)
        self.data_inicio = ft.TextField(
            label="Data Inicial",
            value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Data final (hoje)
        self.data_fim = ft.TextField(
            label="Data Final",
            value=datetime.now().strftime("%Y-%m-%d"),
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Campo de busca
        self.busca_field = ft.TextField(
            label="Buscar por ID, vendedor ou forma de pagamento",
            width=350,
            height=50,
            prefix_icon=ft.icons.SEARCH,
            on_change=self.filtrar_vendas,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )

    def init_table(self):
        # Indicador de carregamento
        self.loading_indicator = ft.ProgressBar(width=500, visible=False)
        
        # Controles de paginação
        self.pagina_anterior_btn = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            on_click=self.pagina_anterior,
            disabled=True
        )
        
        self.pagina_proxima_btn = ft.IconButton(
            icon=ft.icons.ARROW_FORWARD,
            on_click=self.pagina_proxima
        )
        
        self.pagina_info = ft.Text("Página 1")
        
        self.vendas_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nº Venda", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Data/Hora", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Vendedor", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Total", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Forma Pgto.", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Status", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.GREY_900))
            ],
            rows=[]
        )
        apply_table_style(self.vendas_table)

    def init_dialogs(self):
        # Diálogo de anulação
        self.motivo_anulacao = ft.TextField(
            label="Motivo da anulação",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=400,
            value="",
            hint_text="Informe o motivo da anulação",
            text_style=ft.TextStyle(color=ft.colors.BLACK),
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )

        self.dialog_anulacao = ft.AlertDialog(
            modal=True,
            title=ft.Text("Anular Venda", color=ft.colors.BLACK),
            content=ft.Column([
                ft.Text(
                    "Tem certeza que deseja anular esta venda?",
                    color=ft.colors.BLACK
                ),
                self.motivo_anulacao
            ], spacing=20),
            actions=[
                ft.ElevatedButton(
                    "Cancelar",
                    icon=ft.icons.CANCEL,
                    bgcolor=ft.colors.BLUE_400,
                    color=ft.colors.WHITE,
                    on_click=self.fechar_dialog
                ),
                ft.ElevatedButton(
                    "Confirmar",
                    icon=ft.icons.CHECK_CIRCLE,
                    bgcolor=ft.colors.RED_400,
                    color=ft.colors.WHITE,
                    on_click=self.confirmar_anulacao
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        # Diálogo de detalhes da venda
        self.dialog_detalhes = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalhes da Venda", color=ft.colors.BLACK),
            content=ft.Column([
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Produto", color=ft.colors.BLACK)),
                        ft.DataColumn(ft.Text("Qtd", color=ft.colors.BLACK)),
                        ft.DataColumn(ft.Text("Preço", color=ft.colors.BLACK)),
                        ft.DataColumn(ft.Text("Subtotal", color=ft.colors.BLACK))
                    ],
                    rows=[]
                )
            ]),
            actions=[
                ft.ElevatedButton(
                    "Fechar",
                    icon=ft.icons.CLOSE,
                    bgcolor=ft.colors.BLUE_400,
                    color=ft.colors.WHITE,
                    on_click=self.fechar_dialog
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        # Campo de busca de produtos para adicionar
        self.busca_produto_field = ft.TextField(
            label="Buscar produto para adicionar",
            width=300,
            height=50,
            prefix_icon=ft.icons.SEARCH,
            on_change=self.filtrar_produtos_edicao,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )

        # Tabela de produtos disponíveis
        self.produtos_edicao_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Produto")),
                ft.DataColumn(ft.Text("Preço")),
                ft.DataColumn(ft.Text("Estoque")),
                ft.DataColumn(ft.Text("Ações"))
            ],
            rows=[],
            visible=True  # Garantir que a tabela está visível
        )

        # Tabela de itens da venda
        self.itens_edicao_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Produto")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Preço")),
                ft.DataColumn(ft.Text("Subtotal")),
                ft.DataColumn(ft.Text("Ações"))
            ],
            rows=[]
        )

        # Campo para quantidade
        self.quantidade_field = ft.TextField(
            label="Quantidade",
            width=100,
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER
        )

        # Criar o texto do total com a referência
        self.total_text = ft.Ref[ft.Text]()
        total_text = ft.Text(
            "MT 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            ref=self.total_text
        )

        # Diálogo de edição
        self.dialog_edicao = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Venda"),
            content=ft.Column([
                ft.Text("Adicionar Produtos", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.busca_produto_field,
                    self.quantidade_field
                ]),
                self.produtos_edicao_table,
                ft.Divider(),
                ft.Text("Itens da Venda", size=16, weight=ft.FontWeight.BOLD),
                self.itens_edicao_table,
                ft.Text("Total da Venda:", size=16, weight=ft.FontWeight.BOLD),
                total_text
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            actions=[
                ft.ElevatedButton(
                    "Cancelar",
                    icon=ft.icons.CANCEL,
                    bgcolor=ft.colors.RED_400,
                    color=ft.colors.WHITE,
                    on_click=self.fechar_dialog
                ),
                ft.ElevatedButton(
                    "Salvar",
                    icon=ft.icons.SAVE,
                    bgcolor=ft.colors.GREEN_400,
                    color=ft.colors.WHITE,
                    on_click=self.confirmar_edicao
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        # Diálogo de confirmação para deletar venda
        self.dialog_deletar = ft.AlertDialog(
            modal=True,
            title=ft.Text("Deletar Venda", size=16, color=ft.colors.BLACK),
            content=ft.Text(
                "Tem certeza que deseja deletar esta venda?",
                color=ft.colors.BLACK,
                size=14
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=self.fechar_dialog
                ),
                ft.TextButton(
                    "Deletar",
                    style=ft.ButtonStyle(color=ft.colors.RED),
                    on_click=self.confirmar_deletar
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        # Diálogo de confirmação para deletar múltiplas vendas
        self.dialog_deletar_multiplas = ft.AlertDialog(
            modal=True,
            title=ft.Text("Deletar Vendas", size=16, color=ft.colors.BLACK),
            content=ft.Text(
                "Tem certeza que deseja deletar todas as vendas filtradas?",
                color=ft.colors.BLACK,
                size=14
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=self.fechar_dialog
                ),
                ft.TextButton(
                    "Deletar Todas",
                    style=ft.ButtonStyle(color=ft.colors.RED),
                    on_click=self.confirmar_deletar_multiplas
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def voltar_dashboard(self, e):
        # Mostrar indicador de carregamento
        self.loading_indicator.visible = True
        self.update()
        
        # Registrar início da operação para diagnóstico de desempenho
        inicio_saida = datetime.now()
        print(f"[DESEMPENHO] Iniciando saída da página em {inicio_saida.strftime('%H:%M:%S.%f')}")
        
        # Log de saída da página
        logging.info(f"[SAÍDA] Usuário {self.usuario['nome']} (ID: {self.usuario['id']}) saiu da página Gerenciar Vendas em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"[SAÍDA] Usuário {self.usuario['nome']} (ID: {self.usuario['id']}) saiu da página Gerenciar Vendas em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Limpar dados para liberar memória antes de sair da página
        self.vendas_table.rows.clear()
        
        # Registrar tempo total da operação
        fim_saida = datetime.now()
        tempo_saida = (fim_saida - inicio_saida).total_seconds()
        print(f"[DESEMPENHO] Saída da página completada em {tempo_saida:.2f} segundos.")
        
        # Navegar para o dashboard
        self.page.go("/dashboard")
            
    def pagina_anterior(self, e):
        if self.pagina_atual > 1:
            # Mostrar indicador de carregamento
            self.loading_indicator.visible = True
            self.update()
            
            self.pagina_atual -= 1
            self.carregar_vendas()
    
    def pagina_proxima(self, e):
        # Calcular total de páginas
        total_paginas = (self.total_vendas + self.itens_por_pagina - 1) // self.itens_por_pagina
        
        if self.pagina_atual < total_paginas:
            # Mostrar indicador de carregamento
            self.loading_indicator.visible = True
            self.update()
            
            self.pagina_atual += 1
            self.carregar_vendas()
    
    def build(self):
        return ft.Column([
            # Header
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=self.voltar_dashboard,
                        icon_color=ft.colors.WHITE
                    ),
                    ft.Icon(
                        name=ft.icons.EDIT_NOTE,
                        size=30,
                        color=ft.colors.WHITE
                    ),
                    ft.Text(
                        "Gerenciar Vendas",
                        size=20,
                        color=ft.colors.WHITE
                    )
                ]),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
                ),
                padding=20,
                border_radius=10
            ),
            ft.Container(height=20),
            
            # Filtros
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        self.data_inicio,
                        self.data_fim,
                        self.busca_field,
                        ft.ElevatedButton(
                            "Filtrar",
                            icon=ft.icons.FILTER_ALT,
                            on_click=self.carregar_vendas
                        ),
                        ft.ElevatedButton(
                            "Deletar Vendas Filtradas",
                            icon=ft.icons.DELETE_SWEEP,
                            bgcolor=ft.colors.RED_400,
                            color=ft.colors.WHITE,
                            on_click=self.mostrar_dialog_deletar_multiplas
                        )
                    ])
                ]),
                bgcolor=ft.colors.WHITE,
                padding=20,
                border_radius=10
            ),
            ft.Container(height=20),
            
            # Indicador de carregamento
            ft.Container(
                content=self.loading_indicator,
                bgcolor=ft.colors.WHITE,
                padding=ft.padding.only(left=20, right=20),
                border_radius=10
            ),
            
            # Tabela de vendas
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Column(
                            [self.vendas_table],
                            scroll=ft.ScrollMode.AUTO
                        ),
                        height=500,
                        border=ft.border.all(1, ft.colors.BLACK26),
                        border_radius=10,
                        padding=10
                    ),
                    # Controles de paginação
                    ft.Row(
                        [
                            self.pagina_anterior_btn,
                            self.pagina_info,
                            self.pagina_proxima_btn
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ]),
                bgcolor=ft.colors.WHITE,
                padding=20,
                border_radius=10
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    def carregar_vendas(self, e=None):
        try:
            # Mostrar indicador de carregamento
            self.loading_indicator.visible = True
            self.update()
            
            # Registrar início da operação para diagnóstico de desempenho
            inicio_operacao = datetime.now()
            print(f"[DESEMPENHO] Iniciando carregamento de vendas em {inicio_operacao.strftime('%H:%M:%S.%f')}")
            
            # Verificar se a coluna status existe
            colunas = self.db.fetchall("PRAGMA table_info(vendas)")
            tem_status = any(col['name'] == 'status' for col in colunas)
            
            # Ajustar a query baseado na existência da coluna status
            if tem_status:
                status_sql = "COALESCE(v.status, 'Ativa') as status"
            else:
                status_sql = "'Ativa' as status"
            
            # Calcular o offset para paginação
            offset = (self.pagina_atual - 1) * self.itens_por_pagina
            
            # Usar repositório híbrido para buscar vendas
            print(f"🔍 Buscando vendas híbridas para período {self.data_inicio.value} a {self.data_fim.value}")
            
            # Obter total de vendas para paginação
            self.total_vendas = self.venda_repo.count_vendas_periodo(
                self.data_inicio.value, 
                self.data_fim.value
            )
            total_paginas = (self.total_vendas + self.itens_por_pagina - 1) // self.itens_por_pagina
            
            # Buscar vendas com paginação usando repositório híbrido
            vendas = self.venda_repo.get_vendas_com_detalhes(
                data_inicio=self.data_inicio.value,
                data_fim=self.data_fim.value,
                limit=self.itens_por_pagina,
                offset=offset
            )
            
            # Registrar tempo após consulta
            apos_consulta = datetime.now()
            tempo_consulta = (apos_consulta - inicio_operacao).total_seconds()
            print(f"[DESEMPENHO] Consulta SQL completada em {tempo_consulta:.2f} segundos. Encontradas {len(vendas)} vendas.")

            self.vendas_table.rows.clear()
            for v in vendas:
                try:
                    data_formatada = datetime.strptime(v['data_venda'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                except:
                    # Fallback caso a data esteja em um formato diferente
                    data_formatada = v['data_venda']

                # Criar botões de ação com base no status da venda
                acoes = []
                
                # Sempre adicionar o botão de visualizar detalhes
                acoes.append(
                    ft.IconButton(
                        icon=ft.icons.VISIBILITY,
                        icon_color=ft.colors.BLUE,
                        tooltip="Ver Detalhes",
                        data=v,
                        on_click=self.ver_detalhes
                    )
                )
                
                # Se a venda estiver ativa, adicionar os outros botões
                if v['status'].lower() == "ativa":
                    acoes.append(
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            icon_color=ft.colors.ORANGE,
                            tooltip="Editar Venda",
                            data=v,
                            on_click=self.mostrar_dialog_edicao
                        )
                    )
                    acoes.append(
                        ft.IconButton(
                            icon=ft.icons.CANCEL,
                            icon_color=ft.colors.RED,
                            tooltip="Anular Venda",
                            data=v,
                            on_click=self.mostrar_dialog_anulacao
                        )
                    )
                
                # Sempre adicionar o botão de deletar
                acoes.append(
                    ft.IconButton(
                        icon=ft.icons.DELETE_FOREVER,
                        icon_color=ft.colors.RED_700,
                        tooltip="Deletar venda",
                        data=v,
                        on_click=self.mostrar_dialog_deletar
                    )
                )
                
                self.vendas_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(v['id']))),
                            ft.DataCell(ft.Text(data_formatada)),
                            ft.DataCell(ft.Text(v['vendedor'] or "N/A")),
                            ft.DataCell(ft.Text(f"MT {v['total']:.2f}" if v['total'] is not None else "MT 0.00")),
                            ft.DataCell(ft.Text(v['forma_pagamento'] or "N/A")),
                            ft.DataCell(ft.Text(v['status'] or "N/A")),
                            ft.DataCell(ft.Row(acoes))
                        ]
                    )
                )
            
            # Atualizar informações de paginação
            total_paginas = (self.total_vendas + self.itens_por_pagina - 1) // self.itens_por_pagina
            self.pagina_info.value = f"Página {self.pagina_atual} de {total_paginas} (Total: {self.total_vendas} vendas)"
            
            # Atualizar estado dos botões de paginação
            self.pagina_anterior_btn.disabled = self.pagina_atual <= 1
            self.pagina_proxima_btn.disabled = self.pagina_atual >= total_paginas
            
            # Esconder indicador de carregamento
            self.loading_indicator.visible = False
            self.update()
            
            # Registrar tempo total da operação
            fim_operacao = datetime.now()
            tempo_total = (fim_operacao - inicio_operacao).total_seconds()
            print(f"[DESEMPENHO] Carregamento total de vendas completado em {tempo_total:.2f} segundos. Exibindo página {self.pagina_atual} de {total_paginas}.")
        except Exception as e:
            # Esconder indicador de carregamento em caso de erro
            self.loading_indicator.visible = False
            self.update()
            print(f"Erro ao carregar vendas: {e}")
            self.mostrar_erro("Erro ao carregar vendas!")

    def ver_detalhes(self, e):
        try:
            venda = e.control.data
            
            # Buscar informações adicionais da venda
            venda_info = self.db.fetchone("""
                SELECT origem, valor_original_divida, desconto_aplicado_divida 
                FROM vendas WHERE id = ?
            """, (venda['id'],))
            
            # Criar a tabela de detalhes
            self.detalhes_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Produto", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Qtd", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Preço", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Subtotal", color=ft.colors.BLACK))
                ],
                rows=[]
            )

            # Query atualizada para considerar apenas itens não removidos
            itens = self.db.fetchall("""
                SELECT 
                    p.nome as produto,
                    iv.quantidade,
                    iv.preco_unitario,
                    iv.subtotal
                FROM itens_venda iv
                JOIN produtos p ON iv.produto_id = p.id
                WHERE iv.venda_id = ?
                AND (iv.status IS NULL OR iv.status != 'Removido')
            """, (venda['id'],))

            for i in itens:
                self.detalhes_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(i['produto'])),
                            ft.DataCell(ft.Text(f"{i['quantidade']:.2f}")),
                            ft.DataCell(ft.Text(f"MT {i['preco_unitario']:.2f}")),
                            ft.DataCell(ft.Text(f"MT {i['subtotal']:.2f}"))
                        ]
                    )
                )

            # Preparar conteúdo do diálogo
            conteudo_dialogo = [
                ft.Text("Detalhes da Venda", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                self.detalhes_table
            ]
            
            # Adicionar informações de desconto se for dívida quitada
            if venda_info and venda_info['origem'] == 'divida_quitada' and venda_info['valor_original_divida'] > 0:
                conteudo_dialogo.extend([
                    ft.Divider(),
                    ft.Text("Informações da Dívida Original:", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
                    ft.Text(f"Valor Original: MT {venda_info['valor_original_divida']:.2f}", color=ft.colors.BLUE),
                    ft.Text(f"Desconto Aplicado: MT {venda_info['desconto_aplicado_divida']:.2f}", color=ft.colors.GREEN),
                    ft.Text(f"Valor Final: MT {venda_info['valor_original_divida'] - venda_info['desconto_aplicado_divida']:.2f}", color=ft.colors.BLACK, weight=ft.FontWeight.BOLD)
                ])
            
            # Atualizar o conteúdo do diálogo
            self.dialog_detalhes.content = ft.Column(conteudo_dialogo, scroll=ft.ScrollMode.AUTO)
            
            self.page.dialog = self.dialog_detalhes
            self.dialog_detalhes.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao carregar detalhes: {e}")
            self.mostrar_erro("Erro ao carregar detalhes da venda!")

    def mostrar_dialog_anulacao(self, e):
        self.venda_em_anulacao = e.control.data
        self.dialog_anulacao.content.controls[1].value = ""  # Limpa o campo de motivo
        self.page.dialog = self.dialog_anulacao
        self.dialog_anulacao.open = True
        self.page.update()

    def confirmar_anulacao(self, e):
        try:
            print("\n=== Iniciando processo de anulação ===")
            if not self.venda_em_anulacao:
                print("Erro: Nenhuma venda selecionada para anulação")
                return
            
            if not self.motivo_anulacao.value:
                self.mostrar_erro("Informe o motivo da anulação!")
                return
            
            venda_id = self.venda_em_anulacao['id']
            print(f"Anulando venda ID: {venda_id}")
            
            # Verificar se a venda tem origem de dívida quitada
            venda_info = self.db.fetchone("""
                SELECT origem, valor_original_divida, desconto_aplicado_divida 
                FROM vendas WHERE id = ?
            """, (venda_id,))
            
            is_divida_quitada = venda_info and venda_info['origem'] == 'divida_quitada'
            
            if is_divida_quitada:
                print("AVISO: Esta venda tem origem 'divida_quitada'. Não devolveremos estoque.")
            
            # Iniciar transação
            self.db.execute("BEGIN TRANSACTION")
            
            # Buscar itens ativos da venda (não removidos)
            itens_query = """
                SELECT 
                    iv.produto_id,
                    iv.quantidade,
                    p.venda_por_peso,
                    p.nome,
                    p.estoque as estoque_atual
                FROM itens_venda iv
                JOIN produtos p ON p.id = iv.produto_id
                WHERE iv.venda_id = ?
                AND (iv.status IS NULL OR iv.status != 'Removido')
            """
            
            print("\n--- Buscando itens da venda ---")
            itens = self.db.fetchall(itens_query, (venda_id,))
            
            if not itens:
                print("Aviso: Nenhum item ativo encontrado para esta venda")
            
            # Devolver estoque para itens ativos
            # Se for dívida quitada, NÃO devolver estoque (pois o estoque já foi devolvido quando a dívida foi criada)
            # Se for venda normal, devolver estoque normalmente
            # NOTA: Se você quiser devolver estoque mesmo para dívidas quitadas, remova a condição 'if not is_divida_quitada:'
            if not is_divida_quitada:
                for item in itens:
                    print(f"\nProcessando item: {item['nome']}")
                    print(f"Quantidade vendida: {item['quantidade']}")
                    print(f"Estoque atual: {item['estoque_atual']}")
                    print(f"Venda por peso: {'Sim' if item['venda_por_peso'] else 'Não'}")
                    print(f"Origem da venda: {'Dívida quitada' if is_divida_quitada else 'Venda normal'}")
                    
                    # A quantidade já está correta, seja por peso ou por unidade
                    novo_estoque = item['estoque_atual'] + item['quantidade']
                    print(f"Novo estoque após devolução: {novo_estoque}")
                    
                    self.db.execute("""
                        UPDATE produtos 
                        SET estoque = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (novo_estoque, item['produto_id']))
                    
                    # Verificar se a atualização foi bem sucedida
                    estoque_atual = self.db.fetchone("""
                        SELECT estoque FROM produtos WHERE id = ?
                    """, (item['produto_id'],))
                    
                    print(f"Estoque após atualização: {estoque_atual['estoque']}")
                
                print("Estoque devolvido - venda normal anulada")
            else:
                print("AVISO: Venda originada de dívida quitada - estoque NÃO será devolvido")
                print("O estoque já foi devolvido quando a dívida foi criada")
                if venda_info['valor_original_divida'] > 0:
                    print(f"Valor original da dívida: MT {venda_info['valor_original_divida']:.2f}")
                    print(f"Desconto aplicado: MT {venda_info['desconto_aplicado_divida']:.2f}")
                    print(f"Valor com desconto: MT {venda_info['valor_original_divida'] - venda_info['desconto_aplicado_divida']:.2f}")
            
            # Atualizar status da venda
            print("\n--- Atualizando status da venda ---")
            self.db.execute("""
                UPDATE vendas 
                SET status = 'Anulada',
                    motivo_alteracao = ?,
                    data_alteracao = CURRENT_TIMESTAMP,
                    alterado_por = ?
                WHERE id = ?
            """, (
                self.motivo_anulacao.value,
                self.usuario['id'],
                venda_id
            ))
            
            # Commit da transação
            print("\n--- Finalizando transação ---")
            self.db.conn.commit()
            print("Transação concluída com sucesso")
            
            # Fechar diálogo
            self.dialog_anulacao.open = False
            self.page.update()
            
            # Atualizar dashboard se existir
            if hasattr(self.page, 'dashboard_view') and self.page.dashboard_view:
                self.page.dashboard_view.atualizar_valores()
            
            # Recarregar vendas
            self.carregar_vendas()
            
            # Mostrar mensagem de sucesso
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Venda anulada com sucesso!"),
                    bgcolor=ft.colors.GREEN_700
                )
            )
            print("=== Processo de anulação concluído ===\n")
            
        except Exception as error:
            print(f"\nERRO ao anular venda: {error}")
            print("Detalhes do erro:", error.__class__.__name__)
            if self.db.conn:
                self.db.conn.rollback()
                print("Transação revertida")
            self.mostrar_erro("Erro ao anular venda!")

    def fechar_dialog(self, e):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def filtrar_vendas(self, e):
        termo = e.control.value.lower()
        try:
            vendas = self.db.fetchall("""
                SELECT 
                    v.id,
                    v.data_venda,
                    u.nome as vendedor,
                    v.total,
                    v.forma_pagamento,
                    v.status
                FROM vendas v
                JOIN usuarios u ON v.usuario_id = u.id
                WHERE (
                    LOWER(CAST(v.id AS TEXT)) LIKE ? OR
                    LOWER(u.nome) LIKE ? OR
                    LOWER(COALESCE(v.forma_pagamento, '')) LIKE ?
                )
                AND DATE(v.data_venda) BETWEEN ? AND ?
                ORDER BY v.data_venda DESC
            """, (f"%{termo}%", f"%{termo}%", f"%{termo}%", self.data_inicio.value, self.data_fim.value))
            
            self.atualizar_tabela_vendas(vendas)
            
        except Exception as e:
            print(f"Erro ao filtrar vendas: {e}")
            self.mostrar_erro("Erro ao filtrar vendas!")

    def atualizar_tabela_vendas(self, vendas):
        self.vendas_table.rows.clear()
        for venda in vendas:
            # Criar botões de ação
            botoes_acao = ft.Row([
                ft.IconButton(
                    icon=ft.icons.VISIBILITY,
                    icon_color=ft.colors.BLUE_400,
                    tooltip="Ver detalhes",
                    data=venda['id'],
                    on_click=self.ver_detalhes
                ),
                ft.IconButton(
                    icon=ft.icons.EDIT,
                    icon_color=ft.colors.ORANGE_400,
                    tooltip="Editar venda",
                    data=venda['id'],
                    on_click=self.mostrar_dialog_edicao
                ),
                ft.IconButton(
                    icon=ft.icons.CANCEL,
                    icon_color=ft.colors.RED_400,
                    tooltip="Anular venda",
                    data=venda['id'],
                    on_click=self.mostrar_dialog_anulacao
                ),
                ft.IconButton(
                    icon=ft.icons.DELETE_FOREVER,
                    icon_color=ft.colors.RED_700,
                    tooltip="Deletar venda",
                    data=venda['id'],
                    on_click=self.mostrar_dialog_deletar
                )
            ])

            self.vendas_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(venda['id']))),
                        ft.DataCell(ft.Text(venda['data_venda'] or "N/A")),
                        ft.DataCell(ft.Text(venda['vendedor'] or "N/A")),
                        ft.DataCell(ft.Text(f"MT {venda['total']:.2f}" if venda['total'] is not None else "MT 0.00")),
                        ft.DataCell(ft.Text(venda['forma_pagamento'] or "N/A")),
                        ft.DataCell(ft.Text(venda['status'] or "N/A")),
                        ft.DataCell(botoes_acao)
                    ]
                )
            )
        self.update()

    def voltar_dashboard(self, e):
        """Registra o log de saída e volta para o dashboard"""
        logging.info(f"[SAÍDA] Usuário {self.usuario['nome']} (ID: {self.usuario['id']}) saiu da página Gerenciar Vendas em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"[SAÍDA] Usuário {self.usuario['nome']} (ID: {self.usuario['id']}) saiu da página Gerenciar Vendas em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.page.go("/dashboard")
        
    def mostrar_erro(self, mensagem):
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(mensagem),
                bgcolor=ft.colors.RED_700
            )
        )

    def mostrar_dialog_edicao(self, e):
        try:
            print("\n=== Debug mostrar_dialog_edicao ===")
            venda = e.control.data
            self.venda_em_edicao = dict(venda)
            
            # Buscar itens da venda e agrupar por produto
            itens = self.db.fetchall("""
                SELECT 
                    p.id as produto_id,
                    p.nome as produto,
                    SUM(iv.quantidade) as quantidade,
                    iv.preco_unitario,
                    SUM(iv.subtotal) as subtotal,
                    p.preco_custo as preco_custo_unitario,
                    p.estoque as estoque_disponivel
                FROM itens_venda iv
                JOIN produtos p ON p.id = iv.produto_id
                WHERE iv.venda_id = ? AND (iv.status IS NULL OR iv.status != 'Removido')
                GROUP BY p.id, p.nome, iv.preco_unitario, p.preco_custo, p.estoque
            """, (self.venda_em_edicao['id'],))
            
            # Limpar tabelas
            self.itens_edicao_table.rows.clear()
            self.produtos_edicao_table.rows.clear()
            
            total_venda = 0
            
            # Preencher tabela de itens da venda
            for item in itens:
                item_dict = dict(item)
                total_venda += item_dict['subtotal']
                
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item_dict['produto'])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
                                    icon_color=ft.colors.BLACK,
                                    tooltip="Diminuir quantidade",
                                    data=item_dict,
                                    on_click=lambda e: self.ajustar_quantidade(e, -1)
                                ),
                                ft.Text(
                                    str(item_dict['quantidade']), 
                                    size=16,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.IconButton(
                                    icon=ft.icons.ADD_CIRCLE_OUTLINE,
                                    icon_color=ft.colors.BLACK,
                                    tooltip="Aumentar quantidade",
                                    data=item_dict,
                                    on_click=lambda e: self.ajustar_quantidade(e, 1)
                                ),
                            ], alignment=ft.MainAxisAlignment.CENTER)
                        ),
                        ft.DataCell(ft.Text(f"MT {item_dict['preco_unitario']:.2f}")),
                        ft.DataCell(ft.Text(f"MT {item_dict['subtotal']:.2f}")),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color=ft.colors.RED,
                                tooltip="Remover item",
                                data=item_dict,
                                on_click=self.remover_item_temp
                            )
                        )
                    ],
                    data=item_dict
                )
                self.itens_edicao_table.rows.append(row)
            
            # Atualizar o total
            if self.total_text.current:
                self.total_text.current.value = f"MT {total_venda:.2f}"
            
            # Limpar campos de busca e quantidade
            self.busca_produto_field.value = ""
            self.quantidade_field.value = "1"
            
            # Carregar produtos iniciais
            self.carregar_produtos_edicao()
            
            # Mostrar o diálogo
            self.page.dialog = self.dialog_edicao
            self.dialog_edicao.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao mostrar diálogo de edição: {e}")
            self.mostrar_erro("Erro ao carregar edição da venda!")

    def carregar_produtos_edicao(self):
        """Carrega a lista inicial de produtos para o diálogo de edição"""
        try:
            produtos = self.db.fetchall("""
                SELECT 
                    id, 
                    codigo, 
                    nome, 
                    preco_venda, 
                    preco_custo,
                    estoque,
                    estoque_minimo,
                    CASE 
                        WHEN estoque = 0 THEN 'sem_estoque'
                        WHEN estoque <= estoque_minimo THEN 'baixo_estoque'
                        ELSE 'estoque_normal'
                    END as status_estoque
                FROM produtos 
                WHERE ativo = 1
                ORDER BY 
                    CASE 
                        WHEN estoque = 0 THEN 2
                        WHEN estoque <= estoque_minimo THEN 1
                        ELSE 0
                    END,
                    nome
                LIMIT 100
            """)
            
            self.atualizar_tabela_produtos(produtos)
            
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")
            self.mostrar_erro("Erro ao carregar lista de produtos!")

    def atualizar_tabela_produtos(self, produtos):
        """Atualiza a tabela de produtos com os resultados fornecidos"""
        try:
            self.produtos_edicao_table.rows.clear()
            
            if not produtos:
                self.produtos_edicao_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("Nenhum produto encontrado")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text(""))
                        ]
                    )
                )
                return
            
            for p in produtos:
                # Definir cores e ícones baseados no status do estoque
                if p['status_estoque'] == 'sem_estoque':
                    cor_fundo = ft.colors.RED_50
                    cor_texto = ft.colors.RED_900
                    icone_estoque = ft.icons.ERROR_OUTLINE
                    cor_icone = ft.colors.RED
                    tooltip = "Sem estoque"
                elif p['status_estoque'] == 'baixo_estoque':
                    cor_fundo = ft.colors.AMBER_50
                    cor_texto = ft.colors.ORANGE_900
                    icone_estoque = ft.icons.WARNING_AMBER_ROUNDED
                    cor_icone = ft.colors.ORANGE
                    tooltip = f"Estoque baixo ({p['estoque']} un.)"
                else:
                    cor_fundo = None
                    cor_texto = ft.colors.BLACK
                    icone_estoque = ft.icons.INVENTORY_2_ROUNDED
                    cor_icone = ft.colors.GREEN
                    tooltip = f"Estoque: {p['estoque']} un."

                self.produtos_edicao_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(p['codigo'], color=cor_texto)),
                            ft.DataCell(
                                ft.Row([
                                    ft.Text(p['nome'], color=cor_texto),
                                    ft.Icon(
                                        name=icone_estoque,
                                        color=cor_icone,
                                        size=20,
                                        tooltip=tooltip
                                    )
                                ])
                            ),
                            ft.DataCell(ft.Text(f"MT {p['preco_venda']:.2f}", color=cor_texto)),
                            ft.DataCell(
                                ft.Row([
                                    ft.Icon(
                                        name=icone_estoque,
                                        color=cor_icone,
                                        size=20
                                    ),
                                    ft.Text(str(p['estoque']), color=cor_texto)
                                ])
                            ),
                            ft.DataCell(
                                ft.IconButton(
                                    icon=ft.icons.ADD_SHOPPING_CART,
                                    icon_color=ft.colors.BLUE if p['estoque'] > 0 else ft.colors.GREY_400,
                                    tooltip="Adicionar ao carrinho" if p['estoque'] > 0 else "Sem estoque disponível",
                                    data=p,
                                    on_click=self.adicionar_produto if p['estoque'] > 0 else None,
                                    disabled=p['estoque'] <= 0
                                )
                            )
                        ],
                        color=cor_fundo
                    )
                )
            
            self.update()
            
        except Exception as e:
            print(f"Erro ao atualizar tabela de produtos: {e}")
            self.mostrar_erro("Erro ao atualizar lista de produtos!")

    def filtrar_produtos_edicao(self, e):
        try:
            print("\n=== Debug filtrar_produtos_edicao ===")
            termo = e.control.value.lower().strip()
            print(f"Termo de busca: {termo}")
            
            # Query base
            query = """
                SELECT 
                    p.id,
                    p.codigo,
                    p.nome,
                    p.preco_venda,
                    p.preco_custo,
                    p.estoque,
                    p.estoque_minimo
                FROM produtos p
                WHERE p.ativo = 1
            """
            params = []
            
            # Adicionar filtro de busca se houver termo
            if termo:
                query += """ 
                    AND (
                        LOWER(p.nome) LIKE ? 
                        OR LOWER(p.codigo) LIKE ?
                    )
                """
                termo_busca = f"%{termo}%"
                params.extend([termo_busca, termo_busca])
            
            # Ordenação
            query += " ORDER BY p.nome COLLATE NOCASE LIMIT 50"
            
            print(f"Query: {query}")
            print(f"Params: {params}")
            
            # Executar busca
            produtos = self.db.fetchall(query, tuple(params))
            print(f"Produtos encontrados: {len(produtos)}")
            
            # Limpar tabela atual
            self.produtos_edicao_table.rows.clear()
            
            if not produtos:
                self.produtos_edicao_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("Nenhum produto encontrado")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text(""))
                        ]
                    )
                )
            else:
                for p in produtos:
                    # Definir estilo baseado no estoque
                    if p['estoque'] <= 0:
                        cor_fundo = ft.colors.RED_50
                        cor_texto = ft.colors.RED
                        icone = ft.icons.ERROR_OUTLINE
                        cor_icone = ft.colors.RED
                        tooltip = "Sem estoque"
                    elif p['estoque'] <= p['estoque_minimo']:
                        cor_fundo = ft.colors.AMBER_50
                        cor_texto = ft.colors.ORANGE
                        icone = ft.icons.WARNING_AMBER_ROUNDED
                        cor_icone = ft.colors.ORANGE
                        tooltip = f"Estoque baixo ({p['estoque']} un.)"
                    else:
                        cor_fundo = None
                        cor_texto = ft.colors.BLACK
                        icone = ft.icons.CHECK_CIRCLE
                        cor_icone = ft.colors.GREEN
                        tooltip = f"Estoque: {p['estoque']} un."
                    
                    self.produtos_edicao_table.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(p['codigo'], color=cor_texto)),
                                ft.DataCell(ft.Text(p['nome'], color=cor_texto)),
                                ft.DataCell(ft.Text(f"MT {p['preco_venda']:.2f}", color=cor_texto)),
                                ft.DataCell(
                                    ft.Row([
                                        ft.Icon(
                                            name=icone,
                                            color=cor_icone,
                                            size=20,
                                            tooltip=tooltip
                                        ),
                                        ft.Text(str(p['estoque']), color=cor_texto)
                                    ])
                                ),
                                ft.DataCell(
                                    ft.IconButton(
                                        icon=ft.icons.ADD_SHOPPING_CART,
                                        icon_color=ft.colors.BLUE if p['estoque'] > 0 else ft.colors.GREY_400,
                                        tooltip="Adicionar ao carrinho" if p['estoque'] > 0 else "Sem estoque disponível",
                                        data=p,
                                        on_click=self.adicionar_produto if p['estoque'] > 0 else None,
                                        disabled=p['estoque'] <= 0
                                    )
                                )
                            ],
                            color=cor_fundo
                        )
                    )
            
            # Atualizar a tabela e o diálogo
            self.produtos_edicao_table.update()
            self.dialog_edicao.update()
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao filtrar produtos: {e}")
            self.mostrar_erro("Erro ao buscar produtos!")

    def adicionar_produto(self, e):
        try:
            produto = e.control.data
            quantidade = float(self.quantidade_field.value)
            
            if quantidade <= 0:
                self.mostrar_erro("Quantidade deve ser maior que zero!")
                return
            
            if quantidade > produto['estoque']:
                self.mostrar_erro(f"Quantidade maior que o estoque disponível ({produto['estoque']} un.)!")
                return
            
            # Verificar se o produto já existe na tabela
            produto_existente = None
            for row in self.itens_edicao_table.rows:
                if row.cells[0].content.value == produto['nome']:
                    produto_existente = row
                    break
            
            if produto_existente:
                # Obter dados do item existente
                qtd_atual = float(produto_existente.cells[1].content.controls[1].value)
                nova_qtd = qtd_atual + quantidade
                
                # Verificar estoque para a quantidade total
                if nova_qtd > produto['estoque']:
                    self.mostrar_erro(f"Quantidade total ({nova_qtd}) maior que o estoque disponível ({produto['estoque']} un.)!")
                    return
                
                # Atualizar quantidade e subtotal
                subtotal = nova_qtd * produto['preco_venda']
                
                # Atualizar a linha existente
                produto_existente.cells[1].content.controls[1].value = str(nova_qtd)
                produto_existente.cells[3].content.value = f"MT {subtotal:.2f}"
                
                # Atualizar os dados do item para uso posterior
                produto_existente.data = {
                    'produto_id': produto['id'],
                    'produto': produto['nome'],
                    'quantidade': nova_qtd,
                    'preco_unitario': produto['preco_venda'],
                    'preco_custo_unitario': produto['preco_custo'],
                    'subtotal': subtotal,
                    'status': 'modificado',
                    'estoque_disponivel': produto['estoque']
                }
                
                # Destacar a linha atualizada
                produto_existente.color = ft.colors.BLUE_50
                
                # Mostrar mensagem específica
                mensagem = "Quantidade atualizada! Clique em 'Salvar' para confirmar as alterações."
                
            else:
                # Criar novo item
                subtotal = quantidade * produto['preco_venda']
                novo_item = {
                    'produto_id': produto['id'],
                    'produto': produto['nome'],
                    'quantidade': quantidade,
                    'preco_unitario': produto['preco_venda'],
                    'preco_custo_unitario': produto['preco_custo'],
                    'subtotal': subtotal,
                    'status': 'novo',
                    'estoque_disponivel': produto['estoque']
                }
                
                # Adicionar nova linha
                nova_linha = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(novo_item['produto'], color=ft.colors.BLUE_900)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
                                    icon_color=ft.colors.BLUE_900,
                                    tooltip="Diminuir quantidade",
                                    data=novo_item,
                                    on_click=lambda e: self.ajustar_quantidade(e, -1)
                                ),
                                ft.Text(
                                    str(novo_item['quantidade']), 
                                    color=ft.colors.BLUE_900,
                                    size=16,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.IconButton(
                                    icon=ft.icons.ADD_CIRCLE_OUTLINE,
                                    icon_color=ft.colors.BLUE_900,
                                    tooltip="Aumentar quantidade",
                                    data=novo_item,
                                    on_click=lambda e: self.ajustar_quantidade(e, 1)
                                ),
                            ], alignment=ft.MainAxisAlignment.CENTER)
                        ),
                        ft.DataCell(ft.Text(f"MT {novo_item['preco_unitario']:.2f}", color=ft.colors.BLUE_900)),
                        ft.DataCell(ft.Text(f"MT {novo_item['subtotal']:.2f}", color=ft.colors.BLUE_900)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color=ft.colors.RED,
                                tooltip="Remover item",
                                data=novo_item,
                                on_click=self.remover_item_temp
                            )
                        )
                    ],
                    color=ft.colors.BLUE_50,
                    data=novo_item
                )
                
                self.itens_edicao_table.rows.append(nova_linha)
                mensagem = "Produto adicionado! Clique em 'Salvar' para confirmar as alterações."
            
            # Atualizar total
            self.atualizar_total_venda()
            
            # Limpar campo de quantidade
            self.quantidade_field.value = "1"
            self.page.update()
            
            # Mostrar mensagem de feedback
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(mensagem),
                    bgcolor=ft.colors.BLUE_700,
                    duration=3000
                )
            )
            
        except ValueError:
            self.mostrar_erro("Quantidade inválida!")
        except Exception as e:
            print(f"Erro ao adicionar produto: {e}")
            self.mostrar_erro("Erro ao adicionar produto!")

    def ajustar_quantidade(self, e, delta):
        try:
            item = e.control.data
            nova_qtd = item['quantidade'] + delta
            
            # Validar quantidade mínima
            if nova_qtd <= 0:
                self.mostrar_erro("Quantidade deve ser maior que zero!")
                return
            
            # Validar estoque disponível
            if delta > 0 and nova_qtd > item['estoque_disponivel']:
                self.mostrar_erro(f"Quantidade maior que o estoque disponível ({item['estoque_disponivel']} un.)!")
                return
            
            # Atualizar quantidade e subtotal
            item['quantidade'] = nova_qtd
            item['subtotal'] = item['preco_unitario'] * nova_qtd
            item['status'] = 'modificado'
            
            # Atualizar a linha na tabela
            for row in self.itens_edicao_table.rows:
                if row.cells[0].content.value == item['produto']:
                    # Atualizar quantidade
                    row.cells[1].content.controls[1].value = str(nova_qtd)
                    # Atualizar subtotal
                    row.cells[3].content.value = f"MT {item['subtotal']:.2f}"
                    break
            
            # Atualizar total
            self.atualizar_total_venda()
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao ajustar quantidade: {e}")
            self.mostrar_erro("Erro ao ajustar quantidade!")

    def remover_item_temp(self, e):
        try:
            item = e.control.data
            
            # Remover item da tabela
            nova_lista = [
                row for row in self.itens_edicao_table.rows 
                if row.cells[0].content.value != item['produto']
            ]
            self.itens_edicao_table.rows = nova_lista
            
            # Atualizar total
            self.atualizar_total_venda()
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao remover item: {e}")
            self.mostrar_erro("Erro ao remover item!")

    def atualizar_total_venda(self):
        try:
            total = 0
            for row in self.itens_edicao_table.rows:
                # Extrair valor do subtotal da célula
                subtotal_text = row.cells[3].content.value
                subtotal = float(subtotal_text.replace("MT ", ""))
                total += subtotal
            
            if self.total_text.current:
                self.total_text.current.value = f"MT {total:.2f}"
            
        except Exception as e:
            print(f"Erro ao atualizar total: {e}")

    def remover_item(self, e):
        try:
            item = e.control.data
            
            # Remover item da tabela
            nova_lista = [
                row for row in self.itens_edicao_table.rows 
                if row.cells[0].content.value != item['produto']
            ]
            self.itens_edicao_table.rows = nova_lista
            
            # Atualizar total
            self.atualizar_total_venda()
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao remover item: {e}")
            self.mostrar_erro("Erro ao remover item!")

    def atualizar_itens_venda(self):
        try:
            itens = self.db.fetchall("""
                SELECT 
                    iv.id, p.nome as produto,
                    iv.quantidade, iv.preco_unitario,
                    iv.subtotal, p.id as produto_id
                FROM itens_venda iv
                JOIN produtos p ON p.id = iv.produto_id
                WHERE iv.venda_id = ? AND iv.status IS NULL
            """, (self.venda_em_edicao['id'],))
            
            self.itens_edicao_table.rows.clear()
            total = 0
            
            for item in itens:
                total += item['subtotal']
                self.itens_edicao_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(item['produto'])),
                            ft.DataCell(ft.Text(str(item['quantidade']))),
                            ft.DataCell(ft.Text(f"MT {item['preco_unitario']:.2f}")),
                            ft.DataCell(ft.Text(f"MT {item['subtotal']:.2f}")),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.REMOVE,
                                        icon_color=ft.colors.RED,
                                        tooltip="Remover",
                                        data=item,
                                        on_click=self.remover_item
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.EDIT,
                                        icon_color=ft.colors.BLUE,
                                        tooltip="Editar Quantidade",
                                        data=item,
                                        on_click=self.editar_quantidade
                                    )
                                ])
                            )
                        ]
                    )
                )
            
            self.total_text.current.value = f"MT {total:.2f}"
            self.update()
            
        except Exception as e:
            print(f"Erro ao atualizar itens: {e}") 

    def confirmar_edicao(self, e):
        try:
            # Verificar se a venda tem origem de dívida quitada
            venda_info = self.db.fetchone("""
                SELECT origem, valor_original_divida, desconto_aplicado_divida 
                FROM vendas WHERE id = ?
            """, (self.venda_em_edicao['id'],))
            
            is_divida_quitada = venda_info and venda_info['origem'] == 'divida_quitada'
            
            if is_divida_quitada:
                print("AVISO: Esta venda tem origem 'divida_quitada'. Não afetaremos estoque.")
            
            # Iniciar transação
            self.db.execute("BEGIN TRANSACTION")
            
            # Primeiro, marcar todos os itens existentes como removidos
            self.db.execute("""
                UPDATE itens_venda 
                SET status = 'Removido',
                    data_alteracao = CURRENT_TIMESTAMP,
                    alterado_por = ?
                WHERE venda_id = ? AND (status IS NULL OR status != 'Removido')
            """, (self.usuario['id'], self.venda_em_edicao['id']))
            
            total_venda = 0
            
            # Processar cada item da tabela
            for row in self.itens_edicao_table.rows:
                item_data = row.data
                quantidade = float(row.cells[1].content.controls[1].value)
                preco_unitario = float(row.cells[2].content.value.replace("MT ", ""))
                subtotal = quantidade * preco_unitario
                
                # Inserir novo item
                self.db.execute("""
                    INSERT INTO itens_venda (
                        venda_id, produto_id, quantidade, 
                        preco_unitario, preco_custo_unitario, subtotal,
                        data_alteracao, alterado_por
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (
                    self.venda_em_edicao['id'],
                    item_data['produto_id'],
                    quantidade,
                    preco_unitario,
                    item_data['preco_custo_unitario'],
                    subtotal,
                    self.usuario['id']
                ))
                
                # Atualizar estoque apenas se NÃO for dívida quitada
                if not is_divida_quitada:
                    self.db.execute("""
                        UPDATE produtos 
                        SET estoque = estoque - ?,
                            updated_at = CURRENT_TIMESTAMP,
                            synced = 0
                        WHERE id = ?
                    """, (quantidade, item_data['produto_id']))
                else:
                    print(f"AVISO: Não afetando estoque para produto {item_data['produto_id']} - venda originada de dívida quitada")
                
                total_venda += subtotal
            
            # Atualizar total da venda
            self.db.execute("""
                UPDATE vendas 
                SET total = ?,
                    data_alteracao = CURRENT_TIMESTAMP,
                    alterado_por = ?
                WHERE id = ?
            """, (total_venda, self.usuario['id'], self.venda_em_edicao['id']))
            
            # Commit da transação
            self.db.conn.commit()
            
            # Fechar diálogo e atualizar interface
            self.dialog_edicao.open = False
            self.page.update()
            
            # Recarregar vendas
            self.carregar_vendas()
            
            # Mostrar mensagem de sucesso
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Venda atualizada com sucesso!"),
                    bgcolor=ft.colors.GREEN_700,
                    duration=2000
                )
            )
            
        except Exception as e:
            print(f"Erro ao confirmar edição: {e}")
            if self.db.conn:
                self.db.conn.rollback()
            self.mostrar_erro("Erro ao salvar alterações!") 

    def mostrar_dialog_deletar(self, e):
        """Mostra o diálogo de confirmação para deletar uma venda"""
        venda = e.control.data
        self.venda_id_para_deletar = venda['id']
        self.page.dialog = self.dialog_deletar
        self.dialog_deletar.open = True
        self.page.update()

    def mostrar_dialog_deletar_multiplas(self, e):
        """Mostra o diálogo de confirmação para deletar múltiplas vendas"""
        self.page.dialog = self.dialog_deletar_multiplas
        self.dialog_deletar_multiplas.open = True
        self.page.update()

    def confirmar_deletar(self, e):
        """Anula uma venda específica e devolve o estoque"""
        try:
            # Verificar se a venda já está anulada
            venda_status = self.db.fetchone("""
                SELECT status FROM vendas WHERE id = ?
            """, (self.venda_id_para_deletar,))
            
            if venda_status and venda_status['status'] == 'Anulada':
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Esta venda já foi anulada anteriormente!"),
                        bgcolor=ft.colors.ORANGE
                    )
                )
                self.fechar_dialog(e)
                return
            
            # Iniciar transação
            self.db.execute("BEGIN TRANSACTION")
            
            # Buscar os itens da venda para devolver o estoque
            itens_venda = self.db.fetchall("""
                SELECT iv.produto_id, iv.quantidade, p.nome
                FROM itens_venda iv
                JOIN produtos p ON iv.produto_id = p.id
                WHERE iv.venda_id = ?
            """, (self.venda_id_para_deletar,))
            
            # Devolver estoque para cada item
            for item in itens_venda:
                self.db.execute("""
                    UPDATE produtos 
                    SET estoque = estoque + ? 
                    WHERE id = ?
                """, (item['quantidade'], item['produto_id']))
                print(f"Devolvido estoque: {item['quantidade']} unidades de {item['nome']}")
            
            # Marcar a venda como anulada em vez de deletar
            motivo = self.motivo_anulacao.value or "Venda anulada via gerenciamento"
            self.db.execute("""
                UPDATE vendas 
                SET status = 'Anulada',
                    motivo_alteracao = ?,
                    data_alteracao = CURRENT_TIMESTAMP,
                    alterado_por = ?
                WHERE id = ?
            """, (f"ANULADA: {motivo}", self.usuario['id'], self.venda_id_para_deletar))
            
            # Commit da transação
            self.db.conn.commit()
            
            # Fechar o diálogo e recarregar as vendas
            self.fechar_dialog(e)
            self.carregar_vendas()
            
            # Mostrar mensagem de sucesso
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Venda anulada e estoque devolvido com sucesso!"),
                    bgcolor=ft.colors.GREEN_700
                )
            )
        except Exception as error:
            # Rollback em caso de erro
            self.db.conn.rollback()
            print(f"Erro ao anular venda: {error}")
            self.mostrar_erro(f"Erro ao anular venda: {str(error)}")

    def confirmar_deletar_multiplas(self, e):
        """Anula múltiplas vendas e devolve o estoque"""
        try:
            # Construir a query base
            query_base = """
                SELECT id FROM vendas v
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
            """
            params = [self.data_inicio.value, self.data_fim.value]
            
            # Adicionar filtro de busca se houver
            if self.busca_field.value:
                query_base += " AND (v.id LIKE ? OR v.forma_pagamento LIKE ?)"
                busca = f"%{self.busca_field.value}%"
                params.extend([busca, busca])
            
            # Obter IDs das vendas filtradas
            vendas_ids = self.db.fetchall(query_base, tuple(params))
            
            if vendas_ids:
                # Iniciar transação
                self.db.execute("BEGIN TRANSACTION")
                
                vendas_anuladas = 0
                for venda in vendas_ids:
                    venda_id = venda['id']
                    
                    # Verificar se a venda já está anulada
                    venda_status = self.db.fetchone("""
                        SELECT status FROM vendas WHERE id = ?
                    """, (venda_id,))
                    
                    if venda_status and venda_status['status'] == 'Anulada':
                        print(f"Venda {venda_id} já estava anulada, pulando...")
                        continue
                    
                    # Buscar os itens da venda para devolver o estoque
                    itens_venda = self.db.fetchall("""
                        SELECT iv.produto_id, iv.quantidade, p.nome
                        FROM itens_venda iv
                        JOIN produtos p ON iv.produto_id = p.id
                        WHERE iv.venda_id = ?
                    """, (venda_id,))
                    
                    # Devolver estoque para cada item
                    for item in itens_venda:
                        self.db.execute("""
                            UPDATE produtos 
                            SET estoque = estoque + ? 
                            WHERE id = ?
                        """, (item['quantidade'], item['produto_id']))
                        print(f"Devolvido estoque: {item['quantidade']} unidades de {item['nome']} (Venda {venda_id})")
                    
                    # Marcar a venda como anulada
                    self.db.execute("""
                        UPDATE vendas 
                        SET status = 'Anulada',
                            motivo_alteracao = 'ANULADA: Anulação em lote via gerenciamento',
                            data_alteracao = CURRENT_TIMESTAMP,
                            alterado_por = ?
                        WHERE id = ?
                    """, (self.usuario['id'], venda_id))
                    
                    vendas_anuladas += 1
                
                # Commit da transação
                self.db.conn.commit()
                
                # Fechar o diálogo e recarregar as vendas
                self.fechar_dialog(e)
                self.carregar_vendas()
                
                # Mostrar mensagem de sucesso
                if vendas_anuladas > 0:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(f"{vendas_anuladas} vendas anuladas e estoque devolvido com sucesso!"),
                            bgcolor=ft.colors.GREEN_700
                        )
                    )
                else:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Todas as vendas selecionadas já estavam anuladas!"),
                            bgcolor=ft.colors.ORANGE
                        )
                    )
            else:
                self.mostrar_erro("Nenhuma venda encontrada para anular")
                
        except Exception as error:
            # Rollback em caso de erro
            self.db.conn.rollback()
            print(f"Erro ao anular vendas: {error}")
            self.mostrar_erro(f"Erro ao anular vendas: {str(error)}")