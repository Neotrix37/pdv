import flet as ft
from database.database import Database
from datetime import datetime, timedelta
import locale
from views.generic_header import create_header
import os
from pathlib import Path
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

class RelatorioFinanceiroView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.BLUE_50
        self.usuario = usuario
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

        # Diretórios para relatórios
        self.relatorios_dir = Path("relatorios")
        self.relatorios_dir.mkdir(exist_ok=True)
        self.pdf_dir = self.relatorios_dir / "pdf"
        self.excel_dir = self.relatorios_dir / "excel"
        self.pdf_dir.mkdir(exist_ok=True)
        self.excel_dir.mkdir(exist_ok=True)

        # Campos de data com estilo melhorado
        data_final = datetime.now()
        data_inicial = data_final.replace(day=1)
        
        self.data_inicial = ft.TextField(
            label="Data Inicial",
            width=200,
            value=data_inicial.strftime("%Y-%m-%d"),
            bgcolor=ft.colors.WHITE,
            border=ft.InputBorder.UNDERLINE,
            label_style=ft.TextStyle(color=ft.colors.BLUE),
            text_size=14
        )
        
        self.data_final = ft.TextField(
            label="Data Final",
            width=200,
            value=data_final.strftime("%Y-%m-%d"),
            bgcolor=ft.colors.WHITE,
            border=ft.InputBorder.UNDERLINE,
            label_style=ft.TextStyle(color=ft.colors.BLUE),
            text_size=14
        )

        # Containers para métricas
        self.vendas_container = ft.Container(
            content=ft.Column([]),
            bgcolor=ft.colors.WHITE,
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=4,
                color=ft.colors.with_opacity(0.25, ft.colors.BLACK)
            )
        )
        
        self.custos_container = ft.Container(
            content=ft.Column([]),
            bgcolor=ft.colors.WHITE,
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=4,
                color=ft.colors.with_opacity(0.25, ft.colors.BLACK)
            )
        )
        
        self.despesas_container = ft.Container(
            content=ft.Column([]),
            bgcolor=ft.colors.WHITE,
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=4,
                color=ft.colors.with_opacity(0.25, ft.colors.BLACK)
            )
        )

    def build(self):
        return ft.Column([
            # Header padrão
            create_header(
                self.page,
                "Relatório Financeiro",
                ft.icons.ANALYTICS,
                "Análise financeira consolidada"
            ),
            ft.Container(height=20),

            # Filtros e botões
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Filtros e Exportação",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900
                    ),
                    ft.Container(height=10),
                    ft.Row([
                        self.data_inicial,
                        ft.Container(width=20),
                        self.data_final,
                        ft.Container(width=20),
                        ft.ElevatedButton(
                            "Gerar Relatório",
                            icon=ft.icons.REFRESH,
                            on_click=self.gerar_relatorio,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.BLUE,
                                color=ft.colors.WHITE
                            )
                        ),
                        ft.Container(width=20),
                        ft.ElevatedButton(
                            "Exportar PDF",
                            icon=ft.icons.PICTURE_AS_PDF,
                            on_click=self.exportar_pdf,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.RED,
                                color=ft.colors.WHITE
                            )
                        ),
                        ft.Container(width=20),
                        ft.ElevatedButton(
                            "Exportar Excel",
                            icon=ft.icons.TABLE_CHART,
                            on_click=self.exportar_excel,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.GREEN,
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

            ft.Container(height=20),

            # Métricas em Grid
            ft.ResponsiveRow([
                # Vendas
                ft.Column([
                    ft.Text(
                        "Vendas e Receitas",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900
                    ),
                    self.vendas_container
                ], col={"sm": 12, "md": 6, "xl": 4}),

                # Custos
                ft.Column([
                    ft.Text(
                        "Custos e Margens",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900
                    ),
                    self.custos_container
                ], col={"sm": 12, "md": 6, "xl": 4}),

                # Despesas
                ft.Column([
                    ft.Text(
                        "Despesas",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900
                    ),
                    self.despesas_container
                ], col={"sm": 12, "md": 6, "xl": 4})
            ])
        ], scroll=ft.ScrollMode.AUTO)

    def criar_card_metrica(self, titulo, valor, icone, cor=ft.colors.BLUE):
        return ft.Container(
            content=ft.Column([
                ft.Icon(name=icone, size=24, color=cor),
                ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD),
                ft.Text(valor, size=16, color=cor)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=160,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.BLACK12),
            border_radius=8,
            padding=10,
            margin=3
        )

    def calcular_metricas(self):
        try:
            data_inicial = self.data_inicial.value
            data_final = self.data_final.value

            # Valor total em estoque
            valor_estoque = self.db.get_valor_estoque()
            valor_venda_estoque = self.db.get_valor_venda_estoque()

            # Cálculo de vendas e lucro
            vendas_query = """
                SELECT 
                    v.forma_pagamento,
                    COUNT(DISTINCT v.id) as num_vendas,
                    SUM(v.total) as total,
                    SUM(
                        CASE
                            WHEN v.status = 'Anulada' THEN 0
                            ELSE (
                                CASE
                                    WHEN iv.status = 'Removido' THEN 0
                                    ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                                END
                            )
                        END
                    ) as lucro
                FROM vendas v
                LEFT JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
                    AND (v.status IS NULL OR v.status != 'Anulada')
                GROUP BY v.forma_pagamento
            """
            
            vendas = self.db.fetchall(vendas_query, (data_inicial, data_final), dictionary=True)

            formas_pagamento = {
                v['forma_pagamento']: v['total'] if v['total'] is not None else 0
                for v in vendas
            }

            total_vendas = sum(v['total'] if v['total'] is not None else 0 for v in vendas) if vendas else 0
            lucro_total = sum(v['lucro'] if v['lucro'] is not None else 0 for v in vendas) if vendas else 0
            num_vendas = sum(v['num_vendas'] if v['num_vendas'] is not None else 0 for v in vendas) if vendas else 0
            receita_bruta = total_vendas
            ticket_medio = receita_bruta / num_vendas if num_vendas > 0 else 0

            # Cálculo de custos dos produtos vendidos
            custos = self.db.fetchone("""
                SELECT 
                    COALESCE(SUM(
                        CASE
                            WHEN v.status = 'Anulada' THEN 0
                            ELSE (
                                CASE
                                    WHEN iv.status = 'Removido' THEN 0
                                    ELSE (iv.preco_custo_unitario * iv.quantidade)
                                END
                            )
                        END
                    ), 0) as total
                FROM vendas v
                LEFT JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
                    AND (v.status IS NULL OR v.status != 'Anulada')
            """, (data_inicial, data_final), dictionary=True)

            custo_produtos = custos['total'] if custos and custos['total'] is not None else 0
            lucro_bruto = receita_bruta - custo_produtos
            margem_bruta = (lucro_bruto / receita_bruta * 100) if receita_bruta > 0 else 0

            # Cálculo de despesas (despesas recorrentes + salários)
            despesas_recorrentes = self.db.fetchone("""
                SELECT COALESCE(SUM(valor), 0) as total
                FROM despesas_recorrentes 
                WHERE DATE(data_vencimento) BETWEEN ? AND ?
                    AND status = 'Pago'
            """, (data_inicial, data_final), dictionary=True)

            # Buscar salários dos funcionários ativos
            salarios = self.db.fetchone("""
                SELECT COALESCE(SUM(salario), 0) as total
                FROM usuarios 
                WHERE ativo = 1
            """, dictionary=True)

            total_despesas_recorrentes = despesas_recorrentes['total'] if despesas_recorrentes and despesas_recorrentes['total'] is not None else 0
            total_salarios = salarios['total'] if salarios and salarios['total'] is not None else 0
            total_despesas = total_despesas_recorrentes + total_salarios

            # Detalhamento das despesas
            despesas_detalhadas = []
            
            # Primeiro, ver todas as despesas, independente do status
            print("\n=== TODAS AS DESPESAS CADASTRADAS ===")
            todas_despesas = self.db.fetchall("""
                SELECT 
                    id,
                    data_vencimento,
                    tipo,
                    categoria,
                    descricao, 
                    valor,
                    status
                FROM despesas_recorrentes
                ORDER BY data_vencimento DESC
            """, dictionary=True)
            
            if todas_despesas:
                print(f"\nTotal de despesas cadastradas: {len(todas_despesas)}")
                print("\nÚltimas 5 despesas:")
                for i, despesa in enumerate(todas_despesas[:5], 1):
                    print(f"{i}. ID: {despesa['id']} | Data: {despesa['data_vencimento']} | "
                          f"Tipo: {despesa['tipo']} | Categoria: {despesa['categoria']} | "
                          f"Valor: MT {despesa['valor']} | Status: {despesa['status']} | "
                          f"Descrição: {despesa['descricao']}")
            else:
                print("Nenhuma despesa encontrada no banco de dados!")
            
            # Agora busca as despesas para o relatório (apenas pagas no período)
            print(f"\n=== BUSCANDO DESPESAS PARA O RELATÓRIO ===")
            print(f"Período: {data_inicial} até {data_final} | Status: Pago")
            
            despesas_recorrentes_detail = self.db.fetchall("""
                SELECT 
                    id,
                    data_vencimento,
                    tipo,
                    categoria,
                    descricao, 
                    valor,
                    status
                FROM despesas_recorrentes
                WHERE DATE(data_vencimento) BETWEEN ? AND ?
                    AND status = 'Pago'
                ORDER BY data_vencimento DESC, valor DESC
            """, (data_inicial, data_final), dictionary=True)
            
            print(f"\nTotal de despesas encontradas para o relatório: {len(despesas_recorrentes_detail)}")
            if despesas_recorrentes_detail:
                print("\nDetalhes das despesas encontradas:")
                for i, despesa in enumerate(despesas_recorrentes_detail, 1):
                    print(f"{i}. ID: {despesa['id']} | Data: {despesa['data_vencimento']} | "
                          f"Tipo: {despesa['tipo']} | Categoria: {despesa['categoria']} | "
                          f"Valor: MT {despesa['valor']} | Status: {despesa['status']}")
            
            print("\n=== FIM DA CONSULTA DE DESPESAS ===\n")
            despesas_detalhadas.extend(despesas_recorrentes_detail)

            # Adicionar total de salários como uma despesa
            if total_salarios > 0:
                despesas_detalhadas.append({
                    'descricao': 'Salários Funcionários',
                    'valor': total_salarios
                })

            # Cálculo de lucro líquido
            lucro_liquido = (lucro_bruto if lucro_bruto is not None else 0) - (total_despesas if total_despesas is not None else 0)
            margem_liquida = (lucro_liquido / receita_bruta * 100) if receita_bruta > 0 else 0

            # Análise de produtos mais vendidos
            produtos_vendidos = self.db.fetchall("""
                SELECT 
                    p.nome as produto,
                    SUM(
                        CASE
                            WHEN v.status = 'Anulada' THEN 0
                            ELSE (
                                CASE
                                    WHEN iv.status = 'Removido' THEN 0
                                    ELSE iv.quantidade
                                END
                            )
                        END
                    ) as quantidade,
                    SUM(
                        CASE
                            WHEN v.status = 'Anulada' THEN 0
                            ELSE (
                                CASE
                                    WHEN iv.status = 'Removido' THEN 0
                                    ELSE iv.subtotal
                                END
                            )
                        END
                    ) as total_vendas,
                    SUM(
                        CASE
                            WHEN v.status = 'Anulada' THEN 0
                            ELSE (
                                CASE
                                    WHEN iv.status = 'Removido' THEN 0
                                    ELSE (iv.preco_custo_unitario * iv.quantidade)
                                END
                            )
                        END
                    ) as total_custos,
                    SUM(
                        CASE
                            WHEN v.status = 'Anulada' THEN 0
                            ELSE (
                                CASE
                                    WHEN iv.status = 'Removido' THEN 0
                                    ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                                END
                            )
                        END
                    ) as lucro
                FROM itens_venda iv
                JOIN vendas v ON v.id = iv.venda_id
                JOIN produtos p ON p.id = iv.produto_id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
                    AND (v.status IS NULL OR v.status != 'Anulada')
                GROUP BY p.id, p.nome
                ORDER BY quantidade DESC
                LIMIT 10
            """, (data_inicial, data_final), dictionary=True)

            # Estrutura final dos dados
            return {
                'vendas': {
                    'por_pagamento': formas_pagamento,
                    'total_vendas': total_vendas,
                    'num_vendas': num_vendas,
                    'receita_bruta': receita_bruta,
                    'ticket_medio': ticket_medio
                },
                'custos': {
                    'custo_produtos': custo_produtos,
                    'lucro_bruto': lucro_bruto,
                    'margem_bruta': margem_bruta
                },
                'despesas': {
                    'total': total_despesas,
                    'salarios': total_salarios,
                    'recorrentes': total_despesas_recorrentes,
                    'detalhadas': despesas_detalhadas,
                    'categorias': {d['categoria']: sum(d2['valor'] for d2 in despesas_detalhadas if d2.get('categoria') == d['categoria']) 
                                 for d in despesas_detalhadas if 'categoria' in d}
                },
                'resultados': {
                    'lucro_liquido': lucro_liquido,
                    'margem_liquida': margem_liquida
                },
                'estoque': {
                    'valor_custo': valor_estoque,
                    'valor_venda': valor_venda_estoque,
                    'margem_potencial': ((valor_venda_estoque - valor_estoque) / valor_estoque * 100) if valor_estoque > 0 else 0
                },
                'produtos_mais_vendidos': [
                    {
                        'produto': p['produto'],
                        'quantidade': p['quantidade'] if p['quantidade'] is not None else 0,
                        'vendas': p['total_vendas'] if p['total_vendas'] is not None else 0,
                        'custos': p['total_custos'] if p['total_custos'] is not None else 0,
                        'lucro': p['lucro'] if p['lucro'] is not None else 0
                    } for p in produtos_vendidos
                ] if produtos_vendidos else [],
                'tendencia_mensal': self.calcular_tendencia_mensal(data_final)
            }

        except Exception as e:
            print(f"Erro ao calcular métricas: {e}")
            return None

    def calcular_tendencia_mensal(self, data_final):
        try:
            tendencia = self.db.fetchall("""
                SELECT 
                    strftime('%Y-%m', data_venda) as mes,
                    COUNT(*) as num_vendas,
                    SUM(total) as total_vendas,
                    AVG(total) as ticket_medio,
                    SUM(
                        CASE
                            WHEN status = 'Anulada' THEN 0
                            ELSE (
                                SELECT SUM(
                                    CASE
                                        WHEN iv.status = 'Removido' THEN 0
                                        ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                                    END
                                )
                                FROM itens_venda iv
                                WHERE iv.venda_id = vendas.id
                            )
                        END
                    ) as lucro
                FROM vendas
                WHERE data_venda >= date(?, '-3 months')
                    AND data_venda <= ?
                    AND status != 'Anulada'
                GROUP BY strftime('%Y-%m', data_venda)
                ORDER BY mes
            """, (data_final, data_final))

            return [
                {
                    'mes': t['mes'],
                    'num_vendas': t['num_vendas'] if t['num_vendas'] is not None else 0,
                    'total': t['total_vendas'] if t['total_vendas'] is not None else 0,
                    'ticket_medio': t['ticket_medio'] if t['ticket_medio'] is not None else 0,
                    'lucro': t['lucro'] if t['lucro'] is not None else 0
                } for t in tendencia
            ] if tendencia else []

        except Exception as e:
            print(f"Erro ao calcular tendência mensal: {e}")
            return []

    def atualizar_metricas(self, dados):
        try:
            # Atualizar container de vendas
            self.vendas_container.content = ft.Column([
                ft.Row([
                    self.criar_card_metrica(
                        "Total de Vendas",
                        f"MT {dados['vendas']['total_vendas']:.2f}",
                        ft.icons.SHOPPING_CART
                    ),
                    self.criar_card_metrica(
                        "Receita Bruta",
                        f"MT {dados['vendas']['receita_bruta']:.2f}",
                        ft.icons.ATTACH_MONEY,
                        ft.colors.GREEN
                    )
                ]),
                ft.Container(height=10),
                ft.Row([
                    self.criar_card_metrica(
                        "Ticket Médio",
                        f"MT {dados['vendas']['ticket_medio']:.2f}",
                        ft.icons.RECEIPT_LONG
                    ),
                    self.criar_card_metrica(
                        "Valor em Estoque",
                        f"MT {dados['estoque']['valor_custo']:.2f}",
                        ft.icons.INVENTORY,
                        ft.colors.BLUE
                    )
                ])
            ])

            # Atualizar container de custos
            self.custos_container.content = ft.Column([
                ft.Row([
                    self.criar_card_metrica(
                        "Custo dos Produtos",
                        f"MT {dados['custos']['custo_produtos']:.2f}",
                        ft.icons.INVENTORY,
                        ft.colors.RED
                    ),
                    self.criar_card_metrica(
                        "Lucro Bruto",
                        f"MT {dados['custos']['lucro_bruto']:.2f}",
                        ft.icons.TRENDING_UP,
                        ft.colors.GREEN
                    )
                ]),
                ft.Container(height=10),
                ft.Row([
                    self.criar_card_metrica(
                        "Margem Bruta",
                        f"{dados['custos']['margem_bruta']:.1f}%",
                        ft.icons.PERCENT
                    ),
                    self.criar_card_metrica(
                        "Margem Potencial",
                        f"{dados['estoque']['margem_potencial']:.1f}%",
                        ft.icons.TRENDING_UP,
                        ft.colors.BLUE
                    )
                ])
            ])

            # Criar linhas da tabela de despesas detalhadas
            linhas_despesas = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(d['descricao'][:30] + ('...' if len(d['descricao']) > 30 else ''))),
                        ft.DataCell(ft.Text(d.get('categoria', 'N/A'))),
                        ft.DataCell(ft.Text(f"MT {d['valor']:.2f}", text_align=ft.TextAlign.RIGHT)),
                    ]
                ) for d in dados['despesas'].get('detalhadas', [])[:5]  # Mostrar até 5 despesas
            ]

            # Adicionar linha de total
            linhas_despesas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("Total", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text("", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(
                            f"MT {dados['despesas']['total']:.2f}", 
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.RIGHT
                        )),
                    ],
                    color=ft.colors.GREY_200
                )
            )

            # Atualizar container de despesas
            self.despesas_container.content = ft.Column([
                ft.Row([
                    self.criar_card_metrica(
                        "Total de Despesas",
                        f"MT {dados['despesas']['total']:.2f}",
                        ft.icons.MONEY_OFF,
                        ft.colors.RED
                    ),
                    self.criar_card_metrica(
                        "Salários",
                        f"MT {dados['despesas']['salarios']:.2f}",
                        ft.icons.PEOPLE,
                        ft.colors.ORANGE
                    )
                ]),
                ft.Container(height=10),
                # Tabela de despesas detalhadas
                ft.Text("Despesas Detalhadas", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.ListView(
                        [
                            ft.DataTable(
                                columns=[
                                    ft.DataColumn(ft.Text("Descrição")),
                                    ft.DataColumn(ft.Text("Categoria")),
                                    ft.DataColumn(ft.Text("Valor"), numeric=True),
                                ],
                                rows=linhas_despesas,
                                border=ft.border.all(1, ft.colors.GREY_300),
                                border_radius=5,
                                heading_row_color=ft.colors.BLUE_50,
                                heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                                horizontal_margin=10,
                                column_spacing=20,
                                show_bottom_border=True,
                            )
                        ],
                        height=min(300, max(100, len(linhas_despesas) * 40)),
                    ),
                    margin=ft.margin.only(top=5, bottom=10),
                ),
                ft.Row([
                    self.criar_card_metrica(
                        "Lucro Líquido",
                        f"MT {dados['resultados']['lucro_liquido']:.2f}",
                        ft.icons.SAVINGS,
                        ft.colors.GREEN if dados['resultados']['lucro_liquido'] > 0 else ft.colors.RED
                    ),
                    self.criar_card_metrica(
                        "Margem Líquida",
                        f"{dados['resultados']['margem_liquida']:.1f}%",
                        ft.icons.PERCENT,
                        ft.colors.GREEN if dados['resultados']['margem_liquida'] > 0 else ft.colors.RED
                    )
                ])
            ])

            self.update()

        except Exception as e:
            print(f"Erro ao atualizar métricas: {e}")
            raise e

    def gerar_relatorio(self, e=None):
        try:
            dados = self.calcular_metricas()
            if dados:
                self.atualizar_metricas(dados)
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Relatório gerado com sucesso!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            else:
                raise Exception("Erro ao calcular métricas")
        except Exception as e:
            print(f"Erro ao gerar relatório: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao gerar relatório!"),
                    bgcolor=ft.colors.RED
                )
            )

    def calcular_vendas_por_categoria(self):
        """Calcula o total de vendas por categoria de produto"""
        try:
            vendas = self.db.fetchall("""
                SELECT 
                    c.nome as categoria,
                    SUM(iv.quantidade * iv.preco_unitario) as total,
                    COUNT(DISTINCT v.id) as num_vendas
                FROM itens_venda iv
                JOIN produtos p ON p.id = iv.produto_id
                JOIN categorias c ON c.id = p.categoria_id
                JOIN vendas v ON v.id = iv.venda_id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
                    AND v.status = 'Concluída'
                GROUP BY c.nome
                ORDER BY total DESC
            """, (self.data_inicial.value, self.data_final.value))
            
            return {v['categoria']: {
                'total': v['total'],
                'num_vendas': v['num_vendas']
            } for v in vendas}
        except Exception as e:
            print(f"Erro ao calcular vendas por categoria: {e}")
            return {}

    def calcular_custos_operacionais(self):
        """Calcula custos operacionais do período"""
        try:
            custos = self.db.fetchall("""
                SELECT 
                    tipo_custo,
                    SUM(valor) as total
                FROM custos_operacionais
                WHERE DATE(data) BETWEEN ? AND ?
                GROUP BY tipo_custo
            """, (self.data_inicial.value, self.data_final.value))
            
            return {c['tipo_custo']: c['total'] for c in custos}
        except Exception as e:
            print(f"Erro ao calcular custos operacionais: {e}")
            return {}

    def calcular_despesas_fixas(self):
        """Calcula total de despesas fixas"""
        try:
            despesas = self.db.fetchone("""
                SELECT SUM(valor) as total
                FROM despesas
                WHERE tipo = 'Fixa'
                    AND DATE(data_vencimento) BETWEEN ? AND ?
                    AND status = 'Pago'
            """, (self.data_inicial.value, self.data_final.value))
            
            return despesas['total'] if despesas['total'] else 0
        except Exception as e:
            print(f"Erro ao calcular despesas fixas: {e}")
            return 0

    def calcular_despesas_variaveis(self):
        """Calcula total de despesas variáveis"""
        try:
            despesas = self.db.fetchone("""
                SELECT SUM(valor) as total
                FROM despesas
                WHERE tipo = 'Variável'
                    AND DATE(data_vencimento) BETWEEN ? AND ?
                    AND status = 'Pago'
            """, (self.data_inicial.value, self.data_final.value))
            
            return despesas['total'] if despesas['total'] else 0
        except Exception as e:
            print(f"Erro ao calcular despesas variáveis: {e}")
            return 0

    def calcular_roi(self):
        """Calcula o ROI (Return on Investment)"""
        try:
            # Obter lucro líquido
            lucro = self.db.fetchone("""
                SELECT 
                    (SELECT SUM(total) FROM vendas 
                     WHERE DATE(data_venda) BETWEEN ? AND ?
                     AND status = 'Concluída') -
                    (SELECT SUM(valor) FROM despesas 
                     WHERE DATE(data_vencimento) BETWEEN ? AND ?
                     AND status = 'Pago') as lucro
            """, (self.data_inicial.value, self.data_final.value,
                 self.data_inicial.value, self.data_final.value))

            # Obter investimento total (custos + despesas)
            investimento = self.db.fetchone("""
                SELECT 
                    (SELECT SUM(valor) FROM despesas 
                     WHERE DATE(data_vencimento) BETWEEN ? AND ?) +
                    (SELECT SUM(preco_custo * quantidade) FROM itens_venda iv
                     JOIN vendas v ON v.id = iv.venda_id
                     WHERE DATE(v.data_venda) BETWEEN ? AND ?) as total
            """, (self.data_inicial.value, self.data_final.value,
                 self.data_inicial.value, self.data_final.value))

            if investimento['total'] and investimento['total'] > 0:
                return (lucro['lucro'] / investimento['total']) * 100
            return 0
        except Exception as e:
            print(f"Erro ao calcular ROI: {e}")
            return 0

    def calcular_ponto_equilibrio(self):
        """Calcula o ponto de equilíbrio"""
        try:
            # Custos fixos
            custos_fixos = self.calcular_despesas_fixas()
            
            # Margem de contribuição média
            dados = self.db.fetchone("""
                SELECT 
                    AVG((iv.preco_unitario - p.preco_custo) / iv.preco_unitario) as margem_media
                FROM itens_venda iv
                JOIN produtos p ON p.id = iv.produto_id
                JOIN vendas v ON v.id = iv.venda_id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
            """, (self.data_inicial.value, self.data_final.value))

            if dados['margem_media'] and dados['margem_media'] > 0:
                return custos_fixos / dados['margem_media']
            return 0
        except Exception as e:
            print(f"Erro ao calcular ponto de equilíbrio: {e}")
            return 0

    def gerar_projecao_vendas(self):
        """Gera projeção de vendas para o próximo mês"""
        try:
            # Média dos últimos 3 meses
            media = self.db.fetchone("""
                SELECT 
                    AVG(total_mes) as media,
                    AVG(crescimento) as tendencia
                FROM (
                    SELECT 
                        strftime('%Y-%m', data_venda) as mes,
                        SUM(total) as total_mes,
                        (SUM(total) - LAG(SUM(total)) OVER (ORDER BY strftime('%Y-%m', data_venda))) / 
                        LAG(SUM(total)) OVER (ORDER BY strftime('%Y-%m', data_venda)) * 100 as crescimento
                    FROM vendas
                    WHERE data_venda >= date('now', '-3 months')
                    GROUP BY mes
                )
            """)
            
            return {
                'media_vendas': media['media'],
                'tendencia_crescimento': media['tendencia'],
                'projecao': media['media'] * (1 + (media['tendencia'] or 0) / 100)
            }
        except Exception as e:
            print(f"Erro ao gerar projeção: {e}")
            return {}

    def gerar_analise_desempenho(self, dados):
        """Gera mensagens de análise baseadas nos dados financeiros"""
        try:
            mensagens = []
            
            # Análise de vendas
            if dados['vendas']['total_vendas'] > 0:
                if dados['vendas']['num_vendas'] > 10:
                    mensagens.append(
                        ("Volume de Vendas", "POSITIVO", 
                         f"Bom volume de vendas com {dados['vendas']['num_vendas']} transações realizadas.")
                    )
                else:
                    mensagens.append(
                        ("Volume de Vendas", "ATENÇÃO",
                         "Volume de vendas baixo. Considere estratégias para aumentar o número de clientes.")
                    )

            # Análise de margens
            margem_bruta = dados['custos']['margem_bruta']
            if margem_bruta >= 30:
                mensagens.append(
                    ("Margem Bruta", "POSITIVO",
                     f"Excelente margem bruta de {margem_bruta:.1f}%. Produtos bem precificados.")
                )
            elif margem_bruta >= 20:
                mensagens.append(
                    ("Margem Bruta", "ATENÇÃO",
                     f"Margem bruta de {margem_bruta:.1f}%. Considere revisar os preços ou custos.")
                )
            else:
                mensagens.append(
                    ("Margem Bruta", "CRÍTICO",
                     f"Margem bruta baixa ({margem_bruta:.1f}%). Urgente revisar preços e custos.")
                )

            # Análise de lucro
            if dados['resultados']['lucro_liquido'] > 0:
                margem_liquida = dados['resultados']['margem_liquida']
                if margem_liquida >= 15:
                    mensagens.append(
                        ("Lucro Líquido", "POSITIVO",
                         f"Ótimo resultado com margem líquida de {margem_liquida:.1f}%.")
                    )
                elif margem_liquida >= 8:
                    mensagens.append(
                        ("Lucro Líquido", "ATENÇÃO",
                         f"Resultado positivo, mas margem líquida de {margem_liquida:.1f}% pode melhorar.")
                    )
                else:
                    mensagens.append(
                        ("Lucro Líquido", "ATENÇÃO",
                         f"Margem líquida baixa ({margem_liquida:.1f}%). Analise custos e despesas.")
                    )
            else:
                mensagens.append(
                    ("Lucro Líquido", "CRÍTICO",
                     "Prejuízo no período. Necessária ação imediata para reverter resultado.")
                )

            # Análise de despesas
            peso_despesas = (dados['despesas']['total'] / dados['vendas']['total_vendas'] * 100) if dados['vendas']['total_vendas'] > 0 else 0
            if peso_despesas > 30:
                mensagens.append(
                    ("Despesas", "CRÍTICO",
                     f"Despesas representam {peso_despesas:.1f}% das vendas. Muito elevado!")
                )
            elif peso_despesas > 20:
                mensagens.append(
                    ("Despesas", "ATENÇÃO",
                     f"Despesas em {peso_despesas:.1f}% das vendas. Busque reduzir custos.")
                )
            else:
                mensagens.append(
                    ("Despesas", "POSITIVO",
                     f"Boa gestão de despesas ({peso_despesas:.1f}% das vendas).")
                )

            return mensagens

        except Exception as e:
            print(f"Erro ao gerar análise: {e}")
            return []

    def exportar_pdf(self, e):
        try:
            print("\n=== Debug exportar_pdf ===")
            dados = self.calcular_metricas()
            if not dados:
                raise Exception("Sem dados para exportar")

            # Configuração do documento com margens menores
            filename = os.path.join(self.pdf_dir, f"relatorio_financeiro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            os.makedirs(self.pdf_dir, exist_ok=True)
            
            # Definir estilos mais compactos
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=styles['Title'],
                fontSize=20,
                spaceAfter=10,
                textColor=colors.HexColor('#1a237e')
            ))
            styles.add(ParagraphStyle(
                name='CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=10,
                textColor=colors.HexColor('#283593')
            ))
            
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )
            
            elementos_relatorio = []

            # Cabeçalho mais compacto
            elementos_relatorio.extend([
                Paragraph("Relatório Financeiro", styles['CustomTitle']),
                Paragraph(
                    f"Período: {self.data_inicial.value} até {self.data_final.value}",
                    ParagraphStyle(
                        'Period',
                        parent=styles['Normal'],
                        fontSize=10,
                        spaceAfter=5
                    )
                ),
                HRFlowable(
                    width="100%",
                    thickness=1,
                    color=colors.HexColor('#e0e0e0'),
                    spaceBefore=5,
                    spaceAfter=10
                )
            ])

            # Layout em duas colunas para Resumo e Análise
            dados_coluna1 = [
                ["Indicador", "Valor"],
                ["Vendas Totais", f"MT {dados['vendas']['total_vendas']:,.2f}"],
                ["Nº Vendas", str(dados['vendas']['num_vendas'])],
                ["Lucro Bruto", f"MT {dados['custos']['lucro_bruto']:,.2f}"],
                ["Lucro Líquido", f"MT {dados['resultados']['lucro_liquido']:,.2f}"]
            ]

            dados_coluna2 = [
                ["Indicador", "Valor"],
                ["Margem Bruta", f"{dados['custos']['margem_bruta']:.1f}%"],
                ["Margem Líquida", f"{dados['resultados']['margem_liquida']:.1f}%"],
                ["Ticket Médio", f"MT {dados['vendas']['ticket_medio']:,.2f}"],
                ["Total Despesas", f"MT {dados['despesas']['total']:,.2f}"]
            ]

            tabela_coluna1 = Table(dados_coluna1, colWidths=[100, 100])
            tabela_coluna2 = Table(dados_coluna2, colWidths=[100, 100])

            estilo_tabela_resumo = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ])

            tabela_coluna1.setStyle(estilo_tabela_resumo)
            tabela_coluna2.setStyle(estilo_tabela_resumo)

            # Tabela com duas colunas lado a lado
            tabela_resumo = Table([[tabela_coluna1, tabela_coluna2]], colWidths=[220, 220])
            tabela_resumo.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10)
            ]))

            elementos_relatorio.extend([
                Paragraph("Resumo Financeiro", styles['CustomHeading']),
                tabela_resumo,
                Spacer(1, 10)
            ])

            # Adicionar seção de despesas detalhadas após o resumo financeiro
            dados_despesas = [["Data", "Tipo", "Categoria", "Descrição", "Valor"]]
            
            if dados['despesas']['detalhadas']:
                for despesa in dados['despesas']['detalhadas']:
                    # Formatar a data de vencimento para o padrão brasileiro
                    data_formatada = datetime.strptime(despesa['data_vencimento'], '%Y-%m-%d').strftime('%d/%m/%Y') if 'data_vencimento' in despesa and despesa['data_vencimento'] else 'N/D'
                    
                    dados_despesas.append([
                        data_formatada,
                        despesa.get('tipo', 'N/D'),
                        despesa.get('categoria', 'N/D'),
                        despesa['descricao'],
                        f"MT {despesa['valor']:,.2f}"
                    ])
            
            dados_despesas.append([
                "Total Despesas",
                f"MT {dados['despesas']['total']:,.2f}"
            ])

            # Ajustar larguras das colunas para acomodar os novos campos
            tabela_despesas = Table(dados_despesas, colWidths=[70, 70, 100, 150, 80])
            tabela_despesas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),
                ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f5f5f5')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('SPAN', (0, -1), (3, -1)),
                ('ALIGN', (0, -1), (3, -1), 'RIGHT')
            ]))

            # Inserir a tabela de despesas após o resumo financeiro
            elementos_relatorio.extend([
                Paragraph("Detalhamento de Despesas", styles['CustomHeading']),
                tabela_despesas,
                Spacer(1, 10)
            ])

            # Análise de Desempenho mais compacta
            analises = self.gerar_analise_desempenho(dados)
            dados_analise = [["Indicador", "Status", "Análise"]]
            dados_analise.extend(analises)

            tabela_analise = Table(dados_analise, colWidths=[80, 70, 310])
            tabela_analise.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                *[('TEXTCOLOR', (1, i), (1, i), {
                    "POSITIVO": colors.HexColor('#4CAF50'),
                    "ATENÇÃO": colors.HexColor('#FFA726'),
                    "CRÍTICO": colors.HexColor('#F44336')
                }.get(status, colors.black))
                  for i, (_, status, _) in enumerate(analises, start=1)],
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0'))
            ]))

            elementos_relatorio.extend([
                Paragraph("Análise de Desempenho", styles['CustomHeading']),
                tabela_analise,
                Spacer(1, 10)
            ])

            # Top Produtos em formato mais compacto
            if dados['produtos_mais_vendidos']:
                dados_produtos = [["Produto", "Qtd", "Vendas", "Lucro", "Margem"]]
                for produto in dados['produtos_mais_vendidos'][:5]:
                    vendas = produto['vendas']
                    lucro = produto['lucro']
                    margem = (lucro / vendas * 100) if vendas > 0 else 0
                    dados_produtos.append([
                        produto['produto'][:20],
                        str(produto['quantidade']),
                        f"MT {produto['vendas']:,.0f}",
                        f"MT {lucro:,.0f}",
                        f"{margem:.1f}%"
                    ])

                tabela_produtos = Table(dados_produtos, colWidths=[160, 50, 80, 80, 60])
                tabela_produtos.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0'))
                ]))

                elementos_relatorio.extend([
                    Paragraph("Top 5 Produtos", styles['CustomHeading']),
                    tabela_produtos
                ])

            # Rodapé compacto
            elementos_relatorio.extend([
                Spacer(1, 10),
                HRFlowable(
                    width="100%",
                    thickness=1,
                    color=colors.HexColor('#e0e0e0'),
                    spaceBefore=5,
                    spaceAfter=5
                ),
                Paragraph(
                    f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    ParagraphStyle(
                        'Footer',
                        parent=styles['Normal'],
                        fontSize=8,
                        textColor=colors.grey,
                        alignment=TA_RIGHT
                    )
                )
            ])

            # Gerar PDF
            doc.build(elementos_relatorio)
            os.startfile(filename)

            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("PDF gerado com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )

        except Exception as e:
            print(f"Erro ao exportar PDF: {e}")
            import traceback
            traceback.print_exc()
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao gerar relatório PDF: {str(e)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def exportar_excel(self, e):
        try:
            print("\n=== Debug exportar_excel ===")
            dados = self.calcular_metricas()
            if not dados:
                raise Exception("Sem dados para exportar")

            print("Dados calculados com sucesso")
            print(f"Diretório Excel: {self.excel_dir}")
            
            # Garantir que o diretório existe
            os.makedirs(self.excel_dir, exist_ok=True)
            
            filename = os.path.join(self.excel_dir, f"relatorio_financeiro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            print(f"Arquivo a ser gerado: {filename}")

            print("Criando DataFrames...")
            
            # DataFrame de Vendas
            vendas_data = [
                ['Total de Vendas', dados['vendas']['total_vendas']],
                ['Número de Vendas', dados['vendas']['num_vendas']],
                ['Ticket Médio', dados['vendas']['ticket_medio']]
            ]
            for forma, valor in dados['vendas']['por_pagamento'].items():
                vendas_data.append([f'Total {forma}', valor])
            df_vendas = pd.DataFrame(vendas_data, columns=['Indicador', 'Valor'])

            # DataFrame de Resultados
            df_resultados = pd.DataFrame([
                ['Receita Bruta', dados['vendas']['receita_bruta']],
                ['Custo dos Produtos', dados['custos']['custo_produtos']],
                ['Lucro Bruto', dados['custos']['lucro_bruto']],
                ['Margem Bruta %', dados['custos']['margem_bruta']],
                ['Total Despesas', dados['despesas']['total']],
                ['Lucro Líquido', dados['resultados']['lucro_liquido']],
                ['Margem Líquida %', dados['resultados']['margem_liquida']]
            ], columns=['Indicador', 'Valor'])

            # DataFrame de Produtos
            df_produtos = pd.DataFrame(dados['produtos_mais_vendidos'])

            # DataFrame de Despesas Detalhadas
            despesas_data = []
            for despesa in dados['despesas']['detalhadas']:
                despesas_data.append({
                    'Data': despesa.get('data_vencimento', 'N/D'),
                    'Tipo': despesa.get('tipo', 'N/D'),
                    'Categoria': despesa.get('categoria', 'N/D'),
                    'Descrição': despesa.get('descricao', ''),
                    'Valor': despesa.get('valor', 0),
                    'Status': despesa.get('status', 'N/D')
                })
            
            # Adicionar linha de total
            if despesas_data:
                despesas_data.append({
                    'Data': 'TOTAL',
                    'Tipo': '',
                    'Categoria': '',
                    'Descrição': '',
                    'Valor': dados['despesas']['total'],
                    'Status': ''
                })
            
            df_despesas = pd.DataFrame(despesas_data)

            print("Salvando Excel...")
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df_vendas.to_excel(writer, sheet_name='Vendas', index=False)
                df_resultados.to_excel(writer, sheet_name='Resultados', index=False)
                if not df_produtos.empty:
                    df_produtos.to_excel(writer, sheet_name='Produtos Mais Vendidos', index=False)
                if not df_despesas.empty:
                    df_despesas.to_excel(writer, sheet_name='Despesas Detalhadas', index=False)

            print(f"Excel gerado com sucesso: {filename}")
            os.startfile(filename)

            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Excel gerado com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )

        except Exception as e:
            print(f"Erro ao exportar Excel: {e}")
            import traceback
            traceback.print_exc()
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao exportar Excel: {str(e)}"),
                    bgcolor=ft.colors.RED
                )
            )