import flet as ft

def create_header(page: ft.Page, title: str, icon: str, subtitle: str = None):
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    icon_color=ft.colors.BLACK,
                    on_click=lambda _: page.go("/dashboard"),
                    tooltip="Voltar para Dashboard"
                ),
                ft.Icon(
                    name=icon, 
                    size=30, 
                    color=ft.colors.BLACK
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            title, 
                            size=20, 
                            color=ft.colors.BLACK
                        ),
                        ft.Text(
                            subtitle if subtitle else "", 
                            color=ft.colors.BLACK, 
                            size=14
                        ) if subtitle else ft.Container()
                    ]
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_900, ft.colors.PURPLE_900]
        ),
        padding=20,
        border_radius=10
    ) 