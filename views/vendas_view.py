def ver_detalhes_venda(self, e):
    venda = e.control.data
    
    try:
        # Busca os itens da venda
        itens = self.db.fetchall("""
            SELECT 
                i.quantidade,
                i.preco_unitario,
                i.subtotal,
                p.nome as produto_nome,
                p.codigo as produto_codigo
            FROM itens_venda i
            JOIN produtos p ON p.id = i.produto_id
            WHERE i.venda_id = ?
        """, (venda['id'],))
        
        # Cria a tabela de itens
        itens_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Produto")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Preço Unit.")),
                ft.DataColumn(ft.Text("Subtotal"))
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"{i['produto_nome']} ({i['produto_codigo']})")),
                        ft.DataCell(ft.Text(f"{i['quantidade']:.2f}")),
                        ft.DataCell(ft.Text(f"MT {i['preco_unitario']:.2f}")),
                        ft.DataCell(ft.Text(f"MT {i['subtotal']:.2f}"))
                    ]
                ) for i in itens
            ]
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("Detalhes da Venda"),
            content=ft.Column([
                ft.Text("Informações da Venda:", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"Data: {venda['data_venda'].split()[0]}"),
                ft.Text(f"Vendedor: {venda['vendedor']}"),
                ft.Text(f"Forma de Pagamento: {venda['forma_pagamento']}"),
                ft.Text(f"Status: {venda.get('status', 'Ativa')}"),
                ft.Divider(),
                ft.Text("Itens da Venda:", size=16, weight=ft.FontWeight.BOLD),
                itens_table,
                ft.Divider(),
                ft.Text(f"Total da Venda: MT {venda['total']:.2f}"),
                ft.Text(f"Valor Recebido: MT {venda['valor_recebido']:.2f}"),
                ft.Text(f"Troco: MT {venda['troco']:.2f}"),
                ft.Text(f"Motivo Alteração: {venda.get('motivo_alteracao', 'N/A')}") if venda.get('status') == 'Anulada' else ft.Container(),
            ], scroll=ft.ScrollMode.AUTO, height=400),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: close_dlg(e))
            ]
        )
        
        def close_dlg(e):
            dialog.open = False
            self.page.update()
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        
    except Exception as error:
        print(f"Erro ao carregar detalhes da venda: {error}")
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"❌ Erro ao carregar detalhes: {str(error)}"),
                bgcolor=ft.colors.RED
            )
        ) 