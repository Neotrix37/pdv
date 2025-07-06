import flet as ft
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from database.database import Database
from views.generic_header import create_header
from datetime import datetime, timedelta

class GraficosView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        
        # Campos de filtro
        self.data_inicial = ft.TextField(
            label="Data Inicial",
            width=200,
            height=50,
            value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        self.data_final = ft.TextField(
            label="Data Final",
            width=200,
            height=50,
            value=datetime.now().strftime("%Y-%m-%d"),
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Containers para os gráficos
        self.grafico_vendas = ft.Container(
            content=ft.Text("Carregando gráfico de vendas..."),
            height=500,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            padding=20,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.1, ft.colors.BLACK)
            )
        )
        
        self.grafico_produtos = ft.Container(
            content=ft.Text("Carregando gráfico de produtos..."),
            height=500,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            padding=20,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.1, ft.colors.BLACK)
            )
        )

    def build(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    create_header(
                        self.page,
                        "Análise de Vendas",
                        ft.icons.BAR_CHART,
                        "Gráficos de vendas e produtos mais vendidos"
                    ),
                    
                    # Filtros
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.data_inicial,
                                self.data_final,
                                ft.ElevatedButton(
                                    "Atualizar Gráficos",
                                    icon=ft.icons.REFRESH,
                                    on_click=self.atualizar_graficos
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND
                        ),
                        padding=20,
                        bgcolor=ft.colors.WHITE,
                        border_radius=10,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.colors.with_opacity(0.1, ft.colors.BLACK)
                        ),
                        margin=ft.margin.only(top=20)
                    ),
                    
                    # Gráficos
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            "Vendas por Dia",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.BLACK
                                        ),
                                        self.grafico_vendas
                                    ],
                                    expand=True,
                                    alignment=ft.MainAxisAlignment.START
                                ),
                                
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            "Produtos Mais Vendidos",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.BLACK
                                        ),
                                        self.grafico_produtos
                                    ],
                                    expand=True,
                                    alignment=ft.MainAxisAlignment.START
                                )
                            ],
                            spacing=20,
                            expand=True
                        ),
                        margin=ft.margin.only(top=20)
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=20,
            bgcolor=ft.colors.WHITE
        )

    def atualizar_graficos(self, e):
        try:
            print("=== Iniciando atualização de gráficos ===")
            
            # Carregar dados de vendas
            print("Carregando dados de vendas...")
            vendas = self.db.fetchall("""
                SELECT 
                    DATE(v.data_venda) as data,
                    SUM(v.total) as total
                FROM vendas v
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
                GROUP BY DATE(v.data_venda)
                ORDER BY data
            """, (self.data_inicial.value, self.data_final.value), dictionary=True)
            
            print(f"Dados de vendas carregados: {vendas}")
            
            # Criar DataFrame para vendas
            df_vendas = pd.DataFrame(vendas)
            print(f"DataFrame de vendas criado: {df_vendas}")
            
            # Criar gráfico de vendas
            fig_vendas = go.Figure()
            
            if not df_vendas.empty:
                fig_vendas.add_trace(go.Scatter(
                    x=df_vendas['data'],
                    y=df_vendas['total'],
                    mode='lines+markers',
                    name='Vendas',
                    line=dict(color='#2196F3', width=2),
                    marker=dict(size=8)
                ))
            else:
                # Adicionar mensagem quando não há dados
                fig_vendas.add_annotation(
                    text="Não há dados de vendas no período selecionado",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="black")
                )
                # Adicionar um ponto invisível para garantir que o gráfico seja renderizado
                fig_vendas.add_trace(go.Scatter(
                    x=[0],
                    y=[0],
                    mode='markers',
                    marker=dict(size=0),
                    showlegend=False
                ))
            
            fig_vendas.update_layout(
                title='Vendas por Dia',
                xaxis_title='Data',
                yaxis_title='Valor (MT)',
                template='plotly_white',
                margin=dict(l=40, r=40, t=40, b=40),
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(showgrid=True, gridcolor='lightgray'),
                yaxis=dict(showgrid=True, gridcolor='lightgray')
            )
            
            # Carregar dados de produtos
            print("Carregando dados de produtos...")
            produtos = self.db.fetchall("""
                SELECT 
                    p.nome,
                    SUM(iv.quantidade) as quantidade
                FROM itens_venda iv
                JOIN produtos p ON p.id = iv.produto_id
                JOIN vendas v ON v.id = iv.venda_id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
                GROUP BY p.nome
                ORDER BY quantidade DESC
                LIMIT 10
            """, (self.data_inicial.value, self.data_final.value), dictionary=True)
            
            print(f"Dados de produtos carregados: {produtos}")
            
            # Criar DataFrame para produtos
            df_produtos = pd.DataFrame(produtos)
            print(f"DataFrame de produtos criado: {df_produtos}")
            
            # Criar gráfico de produtos
            fig_produtos = go.Figure()
            
            if not df_produtos.empty:
                fig_produtos.add_trace(go.Bar(
                    x=df_produtos['nome'],
                    y=df_produtos['quantidade'],
                    name='Quantidade',
                    marker_color='#4CAF50'
                ))
            else:
                # Adicionar mensagem quando não há dados
                fig_produtos.add_annotation(
                    text="Não há dados de produtos no período selecionado",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="black")
                )
                # Adicionar uma barra invisível para garantir que o gráfico seja renderizado
                fig_produtos.add_trace(go.Bar(
                    x=[0],
                    y=[0],
                    marker_color='rgba(0,0,0,0)',
                    showlegend=False
                ))
            
            fig_produtos.update_layout(
                title='Top 10 Produtos Mais Vendidos',
                xaxis_title='Produto',
                yaxis_title='Quantidade',
                template='plotly_white',
                margin=dict(l=40, r=40, t=40, b=40),
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(showgrid=True, gridcolor='lightgray'),
                yaxis=dict(showgrid=True, gridcolor='lightgray')
            )
            
            # Atualizar containers com os gráficos
            print("Atualizando containers com os gráficos...")
            
            # Converter os gráficos para imagens PNG
            img_vendas = fig_vendas.to_image(format="png")
            img_produtos = fig_produtos.to_image(format="png")
            
            # Converter para base64
            import base64
            img_vendas_base64 = base64.b64encode(img_vendas).decode('utf-8')
            img_produtos_base64 = base64.b64encode(img_produtos).decode('utf-8')
            
            # Atualizar os containers
            self.grafico_vendas.content = ft.Image(
                src_base64=img_vendas_base64,
                fit=ft.ImageFit.CONTAIN,
                width=800,
                height=500
            )
            
            self.grafico_produtos.content = ft.Image(
                src_base64=img_produtos_base64,
                fit=ft.ImageFit.CONTAIN,
                width=800,
                height=500
            )
            
            self.update()
            print("=== Atualização de gráficos concluída ===")
            
        except Exception as error:
            print(f"Erro ao atualizar gráficos: {error}")
            import traceback
            print(f"Traceback completo: {traceback.format_exc()}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao atualizar gráficos!"),
                    bgcolor=ft.colors.RED
                )
            )

    def did_mount(self):
        self.atualizar_graficos(None) 