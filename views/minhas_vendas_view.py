import flet as ft
from database.database import Database
import locale
from datetime import datetime, timedelta
from utils.translation_mixin import TranslationMixin
from views.generic_table_style import apply_table_style
from pathlib import Path

class MinhasVendasView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.BLUE_50  # Define cor de fundo
        self.usuario = usuario
        self.db = Database()
        locale.setlocale(locale.LC_ALL, 'pt_PT.UTF-8')
        
        # Inicializar o texto de total
        self.total_text = ft.Text(
            "Total do Período: MT 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_900
        )
        
        # Data atual e 7 dias atrás
        self.data_atual = datetime.now()
        self.data_7_dias = self.data_atual - timedelta(days=7)
        
        # Campo de busca e filtros
        self.data_inicial = ft.TextField(
            label="Data Inicial",
            width=200,
            height=50,
            value=datetime.now().strftime("%Y-%m-%d"),
            color=ft.colors.GREY_900,
            bgcolor=ft.colors.WHITE
        )
        self.data_final = ft.TextField(
            label=self.t("end_date"),
            width=200,
            height=50,
            value=self.data_atual.strftime("%Y-%m-%d"),
            color=ft.colors.GREY_900,
            bgcolor=ft.colors.WHITE,
            read_only=not self.usuario.get('is_admin')  # Somente admin pode alterar
        )
        
        # Tabela de vendas
        self.vendas_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Data")),
                ft.DataColumn(ft.Text("Hora")),
                ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("Forma Pagamento")),
                ft.DataColumn(ft.Text("Itens"))
            ],
            rows=[]
        )
        apply_table_style(self.vendas_table)
        
        # Carregar vendas iniciais
        self.carregar_vendas()

    def carregar_vendas(self, e=None):
        try:
            vendas = self.db.fetchall("""
                SELECT 
                    v.id,
                    DATE(v.data_venda) as data,
                    TIME(v.data_venda) as hora,
                    v.total,
                    v.forma_pagamento,
                    v.status,
                    GROUP_CONCAT(
                        p.nome || ' (' || iv.quantidade || 'x - MT ' || 
                        printf('%.2f', iv.preco_unitario) || ')'
                    ) as itens
                FROM vendas v
                JOIN itens_venda iv ON iv.venda_id = v.id
                JOIN produtos p ON p.id = iv.produto_id
                WHERE v.usuario_id = ?
                AND DATE(v.data_venda) BETWEEN ? AND ?
                AND (v.status IS NULL OR v.status != 'Anulada')
                GROUP BY v.id
                ORDER BY v.data_venda DESC
            """, (self.usuario['id'], self.data_inicial.value, self.data_final.value))

            # Calcular total do período
            total_periodo = sum(v['total'] for v in vendas)

            self.vendas_table.rows.clear()
            for v in vendas:
                cor = ft.colors.RED if v['status'] == 'Fechada' else ft.colors.GREY_900
                
                self.vendas_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(v['id']), color=cor)),
                            ft.DataCell(ft.Text(v['data'], color=cor)),
                            ft.DataCell(ft.Text(v['hora'], color=cor)),
                            ft.DataCell(ft.Text(f"MT {v['total']:.2f}", color=cor)),
                            ft.DataCell(ft.Text(v['forma_pagamento'], color=cor)),
                            ft.DataCell(ft.Text(v['itens'], color=cor))
                        ]
                    )
                )

            self.total_text.value = f"Total do Período: MT {total_periodo:.2f}"
            self.update()

        except Exception as error:
            print(f"Erro ao carregar vendas: {error}")

    def mostrar_fechamento_caixa(self, e):
        try:
            # Primeiro, vamos verificar se há vendas do dia
            vendas_hoje = self.db.fetchall("""
                SELECT COUNT(*) as total
                FROM vendas 
                WHERE usuario_id = ?
                AND DATE(data_venda) = DATE('now')
                AND (status IS NULL OR status != 'Anulada')
                AND status != 'Fechada'
            """, (self.usuario['id'],))
            
            print(f"Total de vendas hoje: {vendas_hoje[0]['total']}")  # Debug

            # Buscar vendas do dia atual não fechadas
            vendas_por_forma = self.db.fetchall("""
                SELECT 
                    forma_pagamento,
                    COUNT(*) as quantidade,
                    SUM(total) as total,
                    GROUP_CONCAT(id) as venda_ids
                FROM vendas 
                WHERE usuario_id = ?
                AND DATE(data_venda) = DATE('now')
                AND (status IS NULL OR status != 'Anulada')
                AND status != 'Fechada'
                GROUP BY forma_pagamento
                HAVING total > 0
            """, (self.usuario['id'],))
            
            print(f"Vendas por forma encontradas: {len(vendas_por_forma)}")  # Debug
            for v in vendas_por_forma:
                print(f"Forma: {v['forma_pagamento']}, Quantidade: {v['quantidade']}, Total: {v['total']}")  # Debug
            
            # Se não encontrou vendas para fechar
            if not vendas_por_forma:
                # Verificar se todas as vendas já foram fechadas
                vendas_fechadas = self.db.fetchall("""
                    SELECT COUNT(*) as total
                    FROM vendas
                    WHERE usuario_id = ?
                    AND DATE(data_venda) = DATE('now')
                    AND status = 'Fechada'
                """, (self.usuario['id'],))
                
                if vendas_fechadas[0]['total'] > 0:
                    mensagem = "Todas as vendas de hoje já foram fechadas!"
                else:
                    mensagem = "Não há vendas para fechar!"
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(mensagem),
                        bgcolor=ft.colors.ORANGE
                    )
                )
                return

            # Criar conteúdo do diálogo
            content = ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.POINT_OF_SALE, size=30, color=ft.colors.BLUE),
                    ft.Text(
                        "Fechamento de Caixa",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text(
                    f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    color=ft.colors.GREY_700
                ),
                ft.Text(
                    f"Funcionário: {self.usuario['nome']}",
                    color=ft.colors.GREY_700
                ),
                ft.Divider(),
            ], scroll=ft.ScrollMode.AUTO)

            total_sistema = 0
            campos_valores = {}
            
            # Adicionar resumo por forma de pagamento
            for v in vendas_por_forma:
                total_sistema += v['total']
                campo = ft.TextField(
                    label=f"Valor em {v['forma_pagamento']}",
                    value=str(v['total']),
                    prefix_text="MT ",
                    helper_text=f"{v['quantidade']} venda(s) - Sistema: MT {v['total']:.2f}",
                    color=ft.colors.BLACK,
                    border_color=ft.colors.BLUE,
                    on_change=lambda e, forma=v['forma_pagamento']: self.atualizar_diferenca(forma)
                )
                
                # Container para mostrar diferença
                diferenca_text = ft.Text(
                    "Diferença: MT 0.00",
                    color=ft.colors.GREY_700,
                    size=12
                )
                
                campos_valores[v['forma_pagamento']] = {
                    'campo': campo,
                    'sistema': v['total'],
                    'quantidade': v['quantidade'],
                    'venda_ids': v['venda_ids'],
                    'diferenca_text': diferenca_text
                }
                
                content.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(
                                    ft.icons.PAYMENTS,
                                    color=ft.colors.BLUE,
                                    size=20
                                ),
                                ft.Text(
                                    v['forma_pagamento'],
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLUE,
                                    size=16
                                )
                            ]),
                            campo,
                            ft.Text(
                                f"Total no sistema: MT {v['total']:.2f}",
                                color=ft.colors.GREY_700,
                                size=12
                            ),
                            diferenca_text
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.colors.BLUE_100),
                        border_radius=10,
                        margin=ft.margin.only(bottom=10)
                    )
                )

            # Texto para mostrar diferença total
            diferenca_total_text = ft.Text(
                "Diferença Total: MT 0.00",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE
            )
            content.controls.append(diferenca_total_text)

            def atualizar_diferenca(self, forma_pagamento):
                try:
                    dados = campos_valores[forma_pagamento]
                    valor_informado = float(dados['campo'].value or 0)
                    diferenca = valor_informado - dados['sistema']
                    
                    # Atualizar texto da diferença individual
                    cor = ft.colors.RED if diferenca < 0 else ft.colors.GREEN if diferenca > 0 else ft.colors.GREY_700
                    dados['diferenca_text'].value = f"Diferença: MT {diferenca:.2f}"
                    dados['diferenca_text'].color = cor
                    
                    # Calcular e atualizar diferença total
                    total_informado = sum(float(d['campo'].value or 0) for d in campos_valores.values())
                    diferenca_total = total_informado - total_sistema
                    
                    cor_total = ft.colors.RED if diferenca_total < 0 else ft.colors.GREEN if diferenca_total > 0 else ft.colors.BLUE
                    diferenca_total_text.value = f"Diferença Total: MT {diferenca_total:.2f}"
                    diferenca_total_text.color = cor_total
                    
                    self.page.update()
                except ValueError:
                    pass

            # Campo de observações
            observacoes = ft.TextField(
                label="Observações",
                multiline=True,
                min_lines=2,
                max_lines=4,
                color=ft.colors.BLACK,
                border_color=ft.colors.BLUE
            )
            content.controls.append(
                ft.Container(
                    content=observacoes,
                    padding=10
                )
            )

            def confirmar_fechamento(self, e, dlg, campos_valores, total_sistema, observacoes):
                try:
                    dados_fechamento = {
                        'usuario_id': self.usuario['id'],
                        'data_fechamento': datetime.now(),
                        'valor_sistema': total_sistema,
                        'valor_informado': 0,
                        'diferenca': 0,
                        'observacoes': observacoes.value,
                        'formas_pagamento': []
                    }

                    total_informado = 0
                    for forma, dados in campos_valores.items():
                        valor_informado = float(dados['campo'].value or 0)
                        total_informado += valor_informado
                        diferenca = valor_informado - dados['sistema']
                        
                        dados_fechamento['formas_pagamento'].append({
                            'forma': forma,
                            'valor_sistema': dados['sistema'],
                            'valor_informado': valor_informado,
                            'diferenca': diferenca,
                            'quantidade_vendas': dados['quantidade']
                        })

                    dados_fechamento['valor_informado'] = total_informado
                    dados_fechamento['diferenca'] = total_informado - total_sistema

                    try:
                        # Registrar fechamento
                        fechamento_id = self.db.registrar_fechamento(dados_fechamento)
                        
                        # Atualizar status das vendas
                        self.db.execute("""
                            UPDATE vendas 
                            SET status = 'Fechada'
                            WHERE usuario_id = ? 
                            AND DATE(data_venda) = DATE('now')
                            AND (status IS NULL OR status != 'Anulada')
                            AND status != 'Fechada'
                        """, (self.usuario['id'],))
                        
                        # Gerar PDF
                        if self.gerar_pdf_fechamento(dados_fechamento, fechamento_id):
                            self.db.conn.commit()  # Commit somente se tudo der certo
                            dlg.open = False
                            self.page.update()

                            self.page.show_snack_bar(
                                ft.SnackBar(
                                    content=ft.Text("Fechamento realizado com sucesso! PDF gerado."),
                                    bgcolor=ft.colors.GREEN
                                )
                            )
                            
                            # Atualizar a lista de vendas
                            self.carregar_vendas()
                        else:
                            self.db.conn.rollback()  # Rollback se falhar ao gerar PDF
                            raise Exception("Erro ao gerar PDF")

                    except Exception as e:
                        self.db.conn.rollback()  # Rollback em caso de qualquer erro
                        raise e

                except ValueError:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Por favor, insira valores válidos!"),
                            bgcolor=ft.colors.RED
                        )
                    )
                except Exception as error:
                    print(f"Erro ao confirmar fechamento: {error}")
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Erro ao realizar fechamento!"),
                            bgcolor=ft.colors.RED
                        )
                    )

            # Adicionar botões de ação
            content.controls.append(
                ft.Row([
                    ft.ElevatedButton(
                        "Confirmar",
                        icon=ft.icons.CHECK,
                        on_click=lambda e: self._confirmar_fechamento(e, dlg, campos_valores, total_sistema, observacoes),
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.GREEN,
                            color=ft.colors.WHITE
                        )
                    ),
                    ft.OutlinedButton(
                        "Cancelar",
                        icon=ft.icons.CANCEL,
                        on_click=lambda e: self._cancelar_fechamento(e, dlg)
                    )
                ], alignment=ft.MainAxisAlignment.END)
            )

            # Criar e mostrar diálogo
            dlg = ft.AlertDialog(
                content=content,
                shape=ft.RoundedRectangleBorder(radius=10),
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

        except Exception as error:
            print(f"Erro ao mostrar fechamento: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao preparar fechamento!"),
                    bgcolor=ft.colors.RED
                )
            )

    def gerar_pdf_fechamento(self, dados_fechamento, fechamento_id):
        """Gera um PDF profissional do fechamento de caixa"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
            import os
            
            # Criar diretório para PDFs se não existir
            pdf_dir = Path("pdfs")
            pdf_dir.mkdir(exist_ok=True)
            
            # Nome do arquivo com timestamp
            filename = pdf_dir / f"fechamento_caixa_{fechamento_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Configurações do documento
            doc = SimpleDocTemplate(
                str(filename),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='TitleStyle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1a237e')  # Azul escuro
            ))
            
            styles.add(ParagraphStyle(
                name='SubtitleStyle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#283593')  # Azul médio
            ))
            
            styles.add(ParagraphStyle(
                name='InfoStyle',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=5,
                alignment=TA_LEFT,
                textColor=colors.HexColor('#424242')  # Cinza escuro
            ))
            
            elements = []

            # Logo da empresa (se existir)
            logo_path = "assets/logo.png"  # Ajuste o caminho conforme necessário
            if os.path.exists(logo_path):
                img = Image(logo_path)
                img.drawHeight = 1.5*inch
                img.drawWidth = 1.5*inch
                elements.append(img)
            
            # Título
            elements.append(Paragraph("FECHAMENTO DE CAIXA", styles['TitleStyle']))
            
            # Informações da empresa
            empresa_info = self.db.fetchone("SELECT * FROM printer_config LIMIT 1")
            if empresa_info:
                # Adicionar informações da empresa diretamente
                elements.append(Paragraph(f"<b>{empresa_info['empresa']}</b>", styles['InfoStyle']))
                if empresa_info['endereco']:
                    elements.append(Paragraph(f"{empresa_info['endereco']}", styles['InfoStyle']))
                if empresa_info['telefone']:
                    elements.append(Paragraph(f"Tel: {empresa_info['telefone']}", styles['InfoStyle']))
                if empresa_info['nuit']:
                    elements.append(Paragraph(f"NUIT: {empresa_info['nuit']}", styles['InfoStyle']))
            
            elements.append(Spacer(1, 20))
            
            # Informações do fechamento em uma tabela
            info_data = [
                ['Data do Fechamento:', dados_fechamento['data_fechamento'].strftime('%d/%m/%Y %H:%M')],
                ['Funcionário:', self.usuario['nome']],
                ['Nº do Fechamento:', str(fechamento_id)]
            ]
            
            info_table = Table(info_data, colWidths=[150, 300])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#424242')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 20))
            
            # Resumo das vendas
            elements.append(Paragraph("RESUMO DAS VENDAS", styles['SubtitleStyle']))
            
            # Tabela de formas de pagamento
            data = [['Forma de Pagamento', 'Qtd. Vendas', 'Sistema (MT)', 'Informado (MT)', 'Diferença (MT)']]
            total_vendas = 0
            total_sistema = 0
            
            for forma in dados_fechamento['formas_pagamento']:
                total_vendas += forma['quantidade_vendas']
                total_sistema += forma['valor_sistema']
                data.append([
                    forma['forma'],
                    str(forma['quantidade_vendas']),
                    f"{forma['valor_sistema']:.2f}",
                    "________________",  # Espaço para preenchimento manual
                    "________________"   # Espaço para preenchimento manual
                ])
            
            # Linha de total
            data.append([
                'TOTAL',
                str(total_vendas),
                f"{total_sistema:.2f}",
                "________________",  # Espaço para preenchimento manual
                "________________"   # Espaço para preenchimento manual
            ])

            col_widths = [150, 80, 100, 100, 100]
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                # Corpo da tabela
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#424242')),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
                # Linha de total
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
                # Estilo para as células de preenchimento manual
                ('LINEBELOW', (3, 1), (4, -1), 1, colors.black),  # Linha embaixo para preenchimento
                ('TEXTCOLOR', (3, 1), (4, -1), colors.white),     # Texto branco para não aparecer
            ]))
            elements.append(table)
            
            # Observações
            if dados_fechamento['observacoes']:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("OBSERVAÇÕES", styles['SubtitleStyle']))
                elements.append(Paragraph(dados_fechamento['observacoes'], styles['InfoStyle']))
            
            # Assinaturas
            elements.append(Spacer(1, 50))
            
            signatures = Table([
                ['_' * 30, '_' * 30],
                ['Assinatura do Funcionário', 'Assinatura do Supervisor'],
            ], colWidths=[250, 250])
            
            signatures.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('TOPPADDING', (0, 1), (-1, 1), 5),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#424242')),
            ]))
            elements.append(signatures)

            # Gerar o PDF
            doc.build(elements)
            print(f"PDF gerado com sucesso: {filename}")
            return True

        except Exception as error:
            print(f"Erro ao gerar PDF: {error}")
            import traceback
            traceback.print_exc()
            return False

    def _confirmar_fechamento(self, e, dlg, campos_valores, total_sistema, observacoes):
        """Confirma o fechamento de caixa e gera o PDF"""
        try:
            dados_fechamento = {
                'usuario_id': self.usuario['id'],
                'data_fechamento': datetime.now(),
                'valor_sistema': total_sistema,
                'valor_informado': 0,
                'diferenca': 0,
                'observacoes': observacoes.value,
                'formas_pagamento': []
            }

            total_informado = 0
            for forma, dados in campos_valores.items():
                valor_informado = float(dados['campo'].value or 0)
                total_informado += valor_informado
                diferenca = valor_informado - dados['sistema']
                
                dados_fechamento['formas_pagamento'].append({
                    'forma': forma,
                    'valor_sistema': dados['sistema'],
                    'valor_informado': valor_informado,
                    'diferenca': diferenca,
                    'quantidade_vendas': dados['quantidade']
                })

            dados_fechamento['valor_informado'] = total_informado
            dados_fechamento['diferenca'] = total_informado - total_sistema

            try:
                # Registrar fechamento
                fechamento_id = self.db.registrar_fechamento(dados_fechamento)
                
                # Atualizar status das vendas
                self.db.execute("""
                    UPDATE vendas 
                    SET status = 'Fechada'
                    WHERE usuario_id = ? 
                    AND DATE(data_venda) = DATE('now')
                    AND (status IS NULL OR status != 'Anulada')
                    AND status != 'Fechada'
                """, (self.usuario['id'],))
                
                # Gerar PDF
                if self.gerar_pdf_fechamento(dados_fechamento, fechamento_id):
                    self.db.conn.commit()  # Commit somente se tudo der certo
                    dlg.open = False
                    self.page.update()

                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Fechamento realizado com sucesso! PDF gerado."),
                            bgcolor=ft.colors.GREEN
                        )
                    )
                    
                    # Atualizar a lista de vendas
                    self.carregar_vendas()
                else:
                    self.db.conn.rollback()  # Rollback se falhar ao gerar PDF
                    raise Exception("Erro ao gerar PDF")

            except Exception as e:
                self.db.conn.rollback()  # Rollback em caso de qualquer erro
                raise e

        except ValueError:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Por favor, insira valores válidos!"),
                    bgcolor=ft.colors.RED
                )
            )
        except Exception as error:
            print(f"Erro ao confirmar fechamento: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao realizar fechamento!"),
                    bgcolor=ft.colors.RED
                )
            )

    def _cancelar_fechamento(self, e, dlg):
        """Fecha o diálogo de fechamento"""
        dlg.open = False
        self.page.update()

    def build(self):
        # Cabeçalho com botão de fechamento
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/dashboard")
                ),
                ft.Icon(
                    name=ft.icons.SHOPPING_CART,
                    size=30,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    self.t("my_sales"),
                    size=20,
                    color=ft.colors.WHITE
                ),
                ft.Container(expand=True),  # Espaçador flexível
                ft.ElevatedButton(
                    "Fechar Caixa",
                    icon=ft.icons.POINT_OF_SALE,
                    on_click=self.mostrar_fechamento_caixa,
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.GREEN
                    )
                )
            ]),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
            ),
            padding=20,
            border_radius=10
        )

        # Filtros
        filtros = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.data_inicial,
                    self.data_final,
                    ft.ElevatedButton(
                        "Atualizar",
                        icon=ft.icons.REFRESH,
                        on_click=self.carregar_vendas,
                        visible=self.usuario.get('is_admin')  # Botão visível apenas para admin
                    )
                ]),
                self.total_text
            ]),
            bgcolor=ft.colors.WHITE,
            padding=20,
            border_radius=10
        )

        # Container da tabela
        table_container = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Últimos 7 dias de vendas" if not self.usuario.get('is_admin') else "Vendas no período",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE
                ),
                ft.Container(
                    content=ft.Column(
                        [self.vendas_table],
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

        return ft.Column([
            header,
            ft.Container(height=20),
            filtros,
            ft.Container(height=20),
            table_container
        ]) 