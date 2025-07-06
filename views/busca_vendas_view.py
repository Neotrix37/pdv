import flet as ft
from database.database import Database
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import tempfile

class BuscaVendasView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.usuario = usuario
        self.db = Database()
        
        # Criar diretório para faturas se não existir
        self.faturas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faturas")
        if not os.path.exists(self.faturas_dir):
            os.makedirs(self.faturas_dir)
        
        # Campo de busca
        self.busca_field = ft.TextField(
            label="Buscar venda (código, data ou valor)",
            width=400,
            prefix_icon=ft.icons.SEARCH,
            on_change=self.filtrar_vendas,
            bgcolor=ft.colors.WHITE,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # DataTable para exibir resultados
        self.vendas_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Data", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Valor", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Forma Pagamento", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Vendedor", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.BLACK))
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.BLACK26),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.colors.BLACK26),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.BLACK26),
            heading_row_height=70
        )

    def build(self):
        # Header com gradiente azul
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/dashboard"),
                        icon_color=ft.colors.WHITE
                    ),
                    ft.Icon(
                        name=ft.icons.SEARCH_OUTLINED,
                        size=30,
                        color=ft.colors.WHITE
                    ),
                    ft.Text(
                        "Buscar Vendas",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE
                    ),
                    ft.Container(width=20),
                    ft.Text(
                        "Pesquise e gere PDFs das vendas",
                        size=16,
                        color=ft.colors.WHITE,
                        italic=True
                    ),
                    ft.IconButton(
                        icon=ft.icons.SETTINGS,
                        icon_color=ft.colors.WHITE,
                        tooltip="Configurar Dados da Empresa",
                        on_click=self.configurar_dados_empresa
                    )
                ],
                alignment=ft.MainAxisAlignment.START
            ),
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
        )

        # Container principal com sombra
        content = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(
                                name=ft.icons.SEARCH,
                                color=ft.colors.BLUE,
                                size=30
                            ),
                            self.busca_field
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=20),
                        ft.Container(
                            content=ft.Column(
                                [self.vendas_table],
                                scroll=ft.ScrollMode.AUTO
                            ),
                            height=400,
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
            ]),
            padding=20
        )

        return ft.Column(
            controls=[
                header,
                content
            ],
            spacing=0,
            expand=True
        )

    def filtrar_vendas(self, e):
        termo = e.control.value
        try:
            # Busca vendas no banco de dados
            vendas = self.db.fetchall("""
                SELECT 
                    v.id,
                    v.data_venda,
                    v.total,
                    v.forma_pagamento,
                    u.nome as vendedor
                FROM vendas v
                JOIN usuarios u ON v.usuario_id = u.id
                WHERE 
                    CAST(v.id as TEXT) LIKE ? OR
                    v.data_venda LIKE ? OR
                    CAST(v.total as TEXT) LIKE ?
                ORDER BY v.data_venda DESC
            """, (f"%{termo}%", f"%{termo}%", f"%{termo}%"))

            self.vendas_table.rows.clear()
            for venda in vendas:
                self.vendas_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(venda['id']), color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(venda['data_venda'], color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(f"MT {venda['total']:.2f}", color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(venda['forma_pagamento'], color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(venda['vendedor'], color=ft.colors.BLACK)),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.PICTURE_AS_PDF,
                                        icon_color=ft.colors.BLUE,
                                        tooltip="Gerar PDF",
                                        data=venda,
                                        on_click=self.mostrar_dialogo_fatura
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.VISIBILITY,
                                        icon_color=ft.colors.GREEN,
                                        tooltip="Visualizar Detalhes",
                                        data=venda,
                                        on_click=self.mostrar_detalhes
                                    )
                                ])
                            )
                        ]
                    )
                )
            self.update()
        except Exception as e:
            print(f"Erro ao filtrar vendas: {e}")

    def fechar_dialogo(self, e):
        self.page.dialog.open = False
        self.page.update()

    def mostrar_detalhes(self, e):
        try:
            venda = e.control.data
            # Buscar itens da venda
            itens = self.db.fetchall("""
                SELECT 
                    p.nome,
                    iv.quantidade,
                    iv.preco_unitario,
                    iv.subtotal
                FROM itens_venda iv
                JOIN produtos p ON iv.produto_id = p.id
                WHERE iv.venda_id = ?
            """, (venda['id'],))

            # Criar tabela de itens
            tabela_itens = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Produto", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Qtd", color=ft.colors.BLACK), numeric=True),
                    ft.DataColumn(ft.Text("Preço Unit.", color=ft.colors.BLACK), numeric=True),
                    ft.DataColumn(ft.Text("Subtotal", color=ft.colors.BLACK), numeric=True),
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(item['nome'], color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(str(item['quantidade']), color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(f"MT {item['preco_unitario']:.2f}", color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(f"MT {item['subtotal']:.2f}", color=ft.colors.BLACK)),
                        ],
                    ) for item in itens
                ],
            )

            # Diálogo
            dlg = ft.AlertDialog(
                title=ft.Text(
                    f"Detalhes da Venda #{venda['id']}",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLACK
                ),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Data: {venda['data_venda']}", color=ft.colors.BLACK),
                        ft.Text(f"Vendedor: {venda['vendedor']}", color=ft.colors.BLACK),
                        ft.Text(f"Forma de Pagamento: {venda['forma_pagamento']}", color=ft.colors.BLACK),
                        ft.Divider(),
                        ft.Text("Itens da Venda:", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                        tabela_itens,
                        ft.Divider(),
                        ft.Text(f"Total: MT {venda['total']:.2f}", 
                               size=18, 
                               weight=ft.FontWeight.BOLD,
                               color=ft.colors.BLACK)
                    ], scroll=ft.ScrollMode.AUTO),
                    bgcolor=ft.colors.WHITE,
                    padding=20
                ),
                actions=[
                    ft.ElevatedButton(
                        "Fechar",
                        on_click=self.fechar_dialogo
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )

            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

        except Exception as error:
            print(f"Erro ao mostrar detalhes: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao mostrar detalhes: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def mostrar_dialogo_fatura(self, e):
        try:
            venda = e.control.data
            
            # Buscar configurações da fatura
            config = self.db.get_printer_config()
            if not config:
                # Se não houver configurações, mostrar diálogo para configurar
                self.configurar_dados_empresa(e)
                return
            
            # Criar diálogo de confirmação
            dlg = ft.AlertDialog(
                title=ft.Text("Gerar PDF da Venda", color=ft.colors.BLACK),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Deseja gerar o PDF desta venda?",
                            color=ft.colors.BLACK
                        ),
                        ft.Text(
                            f"Venda #{venda['id']} - MT {venda['total']:.2f}",
                            color=ft.colors.BLACK,
                            weight=ft.FontWeight.BOLD
                        )
                    ]),
                    bgcolor=ft.colors.WHITE,
                    padding=20
                ),
                actions=[
                    ft.ElevatedButton(
                        "Cancelar",
                        on_click=self.fechar_dialogo
                    ),
                    ft.ElevatedButton(
                        "Gerar PDF",
                        on_click=lambda _: self.gerar_pdf(venda)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()
            
        except Exception as error:
            print(f"Erro ao mostrar diálogo: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao mostrar diálogo: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def gerar_pdf(self, venda):
        try:
            # Buscar configurações da empresa
            config = self.db.get_printer_config()
            print("Configurações recuperadas:", config)
            
            if not config:
                raise Exception("Configurações da fatura não encontradas")

            # Buscar itens da venda
            itens = self.db.fetchall("""
                SELECT 
                    p.nome as produto_nome,
                    p.codigo as produto_codigo,
                    iv.quantidade,
                    iv.preco_unitario,
                    iv.subtotal
                FROM itens_venda iv
                JOIN produtos p ON iv.produto_id = p.id
                WHERE iv.venda_id = ?
            """, (venda['id'],))

            # Criar arquivo temporário para o PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                pdf_path = tmp.name

            # Configurar o documento PDF
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            # Lista de elementos do PDF
            elements = []

            # Estilos
            styles = getSampleStyleSheet()
            header_style = ParagraphStyle(
                'HeaderStyle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Centralizado
            )
            normal_style = ParagraphStyle(
                'NormalStyle',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=10
            )

            # Cabeçalho com dados da empresa
            print("Adicionando dados da empresa ao PDF:")
            print(f"Nome da empresa: {config['empresa']}")
            elements.append(Paragraph(config['empresa'], header_style))
            
            if config['endereco']:
                print(f"Endereço: {config['endereco']}")
                elements.append(Paragraph(f"Endereço: {config['endereco']}", normal_style))
            
            if config['telefone']:
                print(f"Telefone: {config['telefone']}")
                elements.append(Paragraph(f"Telefone: {config['telefone']}", normal_style))
            
            if config['nuit']:
                print(f"NUIT: {config['nuit']}")
                elements.append(Paragraph(f"NUIT: {config['nuit']}", normal_style))

            elements.append(Spacer(1, 20))
            elements.append(HRFlowable(width="100%", thickness=1))
            elements.append(Spacer(1, 20))

            # Dados da venda
            elements.append(Paragraph(f"Fatura #{venda['id']}", header_style))
            elements.append(Paragraph(f"Data: {venda['data_venda']}", normal_style))
            elements.append(Paragraph(f"Vendedor: {venda['vendedor']}", normal_style))
            elements.append(Paragraph(f"Forma de Pagamento: {venda['forma_pagamento']}", normal_style))

            elements.append(Spacer(1, 20))

            # Tabela de itens
            table_data = [
                ['Produto', 'Código', 'Qtd', 'Preço Unit.', 'Subtotal']
            ]
            for item in itens:
                table_data.append([
                    item['produto_nome'],
                    item['produto_codigo'],
                    str(item['quantidade']),
                    f"MT {item['preco_unitario']:.2f}",
                    f"MT {item['subtotal']:.2f}"
                ])
            table_data.append(['', '', '', 'Total:', f"MT {venda['total']:.2f}"])

            # Estilo da tabela
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 10),
                ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])

            # Criar e adicionar a tabela
            table = Table(table_data, colWidths=[200, 80, 50, 80, 80])
            table.setStyle(table_style)
            elements.append(table)

            elements.append(Spacer(1, 30))
            elements.append(HRFlowable(width="100%", thickness=1))
            elements.append(Spacer(1, 10))

            # Rodapé
            if config['rodape']:
                elements.append(Paragraph(config['rodape'], normal_style))

            # Gerar o PDF
            doc.build(elements)

            # Abrir o PDF
            os.startfile(pdf_path)

            self.fechar_dialogo(None)
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ PDF gerado com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )

        except Exception as error:
            print(f"Erro ao gerar PDF: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao gerar PDF: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def configurar_dados_empresa(self, e):
        try:
            # Campos do formulário inicializados vazios
            empresa_field = ft.TextField(
                label="Nome da Empresa",
                value="",
                width=400,
                color=ft.colors.BLACK,
                label_style=ft.TextStyle(color=ft.colors.BLACK),
                hint_text="Digite o nome da empresa",
                border=ft.InputBorder.UNDERLINE,
                focused_border_color=ft.colors.BLUE,
                cursor_color=ft.colors.BLACK
            )
            
            endereco_field = ft.TextField(
                label="Endereço",
                value="",
                width=400,
                color=ft.colors.BLACK,
                label_style=ft.TextStyle(color=ft.colors.BLACK),
                hint_text="Digite o endereço",
                border=ft.InputBorder.UNDERLINE,
                focused_border_color=ft.colors.BLUE,
                cursor_color=ft.colors.BLACK
            )
            
            telefone_field = ft.TextField(
                label="Telefone",
                value="",
                width=400,
                color=ft.colors.BLACK,
                label_style=ft.TextStyle(color=ft.colors.BLACK),
                hint_text="Digite o telefone",
                border=ft.InputBorder.UNDERLINE,
                focused_border_color=ft.colors.BLUE,
                cursor_color=ft.colors.BLACK
            )
            
            nuit_field = ft.TextField(
                label="NUIT",
                value="",
                width=400,
                color=ft.colors.BLACK,
                label_style=ft.TextStyle(color=ft.colors.BLACK),
                hint_text="Digite o NUIT",
                border=ft.InputBorder.UNDERLINE,
                focused_border_color=ft.colors.BLUE,
                cursor_color=ft.colors.BLACK
            )
            
            rodape_field = ft.TextField(
                label="Texto do Rodapé",
                value="",
                width=400,
                color=ft.colors.BLACK,
                label_style=ft.TextStyle(color=ft.colors.BLACK),
                hint_text="Digite o texto do rodapé (opcional)",
                border=ft.InputBorder.UNDERLINE,
                focused_border_color=ft.colors.BLUE,
                cursor_color=ft.colors.BLACK
            )

            def salvar_config(e):
                try:
                    # Validar campo obrigatório
                    if not empresa_field.value:
                        raise Exception("O nome da empresa é obrigatório")

                    config_data = {
                        'empresa': empresa_field.value.strip(),
                        'endereco': endereco_field.value.strip(),
                        'telefone': telefone_field.value.strip(),
                        'nuit': nuit_field.value.strip(),
                        'rodape': rodape_field.value.strip() or 'Obrigado pela preferência!',
                        'impressora_padrao': '',
                        'imprimir_automatico': 0
                    }

                    print("Tentando salvar configurações:", config_data)
                    
                    if self.db.save_printer_config(config_data):
                        self.page.show_snack_bar(
                            ft.SnackBar(
                                content=ft.Text("✅ Configurações salvas com sucesso!"),
                                bgcolor=ft.colors.GREEN
                            )
                        )
                        self.fechar_dialogo(None)
                    else:
                        raise Exception("Não foi possível salvar as configurações. Verifique o console para mais detalhes.")
                        
                except Exception as error:
                    print(f"Erro ao salvar configurações: {error}")
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(f"❌ Erro ao salvar: {str(error)}"),
                            bgcolor=ft.colors.RED
                        )
                    )

            # Diálogo de configuração
            dlg = ft.AlertDialog(
                title=ft.Text("Configurar Dados da Empresa", color=ft.colors.BLACK),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Configure os dados que aparecerão nos PDFs gerados",
                            color=ft.colors.BLACK,
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        ft.Text(
                            "* Nome da empresa é obrigatório",
                            color=ft.colors.RED,
                            italic=True,
                            size=12
                        ),
                        ft.Container(height=20),
                        empresa_field,
                        endereco_field,
                        telefone_field,
                        nuit_field,
                        rodape_field
                    ]),
                    bgcolor=ft.colors.WHITE,
                    padding=30,
                    border_radius=10
                ),
                actions=[
                    ft.ElevatedButton(
                        "Cancelar",
                        on_click=self.fechar_dialogo,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.RED_400
                        )
                    ),
                    ft.ElevatedButton(
                        "Salvar",
                        on_click=salvar_config,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE_400
                        )
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()
            
        except Exception as error:
            print(f"Erro ao mostrar configurações: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao mostrar configurações: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            ) 