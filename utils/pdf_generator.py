from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        # Criar estilo personalizado para o título
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        ))
        
    def gerar_pdf_fechamento(self, detalhes, caminho_pdf):
        doc = SimpleDocTemplate(
            caminho_pdf,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Lista de elementos do PDF
        elements = []
        
        # Título
        elements.append(Paragraph(
            "Relatório de Fechamento de Caixa",
            self.styles['CustomTitle']
        ))
        
        # Informações Gerais
        fechamento = detalhes['fechamento']
        try:
            data = datetime.strptime(fechamento['data_fechamento'].split('.')[0], '%Y-%m-%d %H:%M:%S')
        except:
            data = datetime.strptime(fechamento['data_fechamento'], '%Y-%m-%d %H:%M:%S')
        
        info_geral = [
            ["Data:", data.strftime('%d/%m/%Y %H:%M')],
            ["Operador:", fechamento['usuario_nome']],
            ["Status:", fechamento['status']],
            ["Total Sistema:", f"MT {fechamento['valor_sistema']:.2f}"],
            ["Total Informado:", f"MT {fechamento['valor_informado']:.2f}"],
            ["Diferença:", f"MT {fechamento['diferenca']:.2f}"]
        ]
        
        t_info = Table(info_geral, colWidths=[100, 300])
        t_info.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 20))
        
        # Detalhes por Forma de Pagamento
        elements.append(Paragraph(
            "Detalhamento por Forma de Pagamento",
            self.styles['Heading2']
        ))
        elements.append(Spacer(1, 10))
        
        formas_header = ['Forma', 'Sistema', 'Informado', 'Diferença']
        formas_data = [formas_header]
        
        for forma in detalhes['formas_pagamento']:
            formas_data.append([
                forma['forma_pagamento'],
                f"MT {forma['valor_sistema']:.2f}",
                f"MT {forma['valor_informado']:.2f}",
                f"MT {forma['diferenca']:.2f}"
            ])
            
        t_formas = Table(formas_data, colWidths=[100, 100, 100, 100])
        t_formas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_formas)
        elements.append(Spacer(1, 20))
        
        # Lista de Vendas
        elements.append(Paragraph(
            "Vendas Incluídas no Fechamento",
            self.styles['Heading2']
        ))
        elements.append(Spacer(1, 10))
        
        vendas_header = ['#', 'Valor', 'Forma Pagamento', 'Itens']
        vendas_data = [vendas_header]
        
        for venda in detalhes['vendas']:
            vendas_data.append([
                str(venda['id']),
                f"MT {venda['total']:.2f}",
                venda['forma_pagamento'],
                venda['itens']
            ])
            
        t_vendas = Table(vendas_data, colWidths=[50, 80, 100, 270])
        t_vendas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_vendas)
        
        # Observações
        if fechamento.get('observacoes'):
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(
                "Observações:",
                self.styles['Heading2']
            ))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                fechamento['observacoes'],
                self.styles['Normal']
            ))
        
        # Gerar PDF
        doc.build(elements) 