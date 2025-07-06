import flet as ft

def apply_table_style(table: ft.DataTable):
    """Aplica um estilo consistente para todas as tabelas do sistema"""
    # Estilo para o cabeçalho
    for column in table.columns:
        if isinstance(column.label, ft.Text):
            column.label.color = ft.colors.GREY_900
            column.label.weight = ft.FontWeight.BOLD
            column.label.size = 14

    # Estilo para as linhas
    for row in table.rows:
        for cell in row.cells:
            if isinstance(cell.content, ft.Text):
                cell.content.color = ft.colors.GREY_900
                cell.content.size = 14

    # Configurações gerais da tabela
    table.bgcolor = ft.colors.WHITE
    table.heading_row_color = ft.colors.WHITE
    table.data_row_color = ft.colors.WHITE
    table.heading_text_style = ft.TextStyle(
        color=ft.colors.GREY_900,
        weight=ft.FontWeight.BOLD,
        size=14
    )
    table.data_text_style = ft.TextStyle(
        color=ft.colors.GREY_900,
        size=14
    ) 