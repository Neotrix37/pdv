import flet as ft
import os
import shutil
from datetime import datetime
from database.database import Database

def resetar_vendas_mes(page, db, backup_dir):
    """Abre modal para confirmar reset das vendas do mês atual"""
    
    # Obter dados do mês atual
    try:
        mes_atual = datetime.now().strftime("%Y-%m")
        
        # Contar vendas do mês
        vendas_mes = db.fetchone("""
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as valor_total
            FROM vendas 
            WHERE strftime('%Y-%m', data_venda) = ?
            AND status != 'Anulada'
        """, (mes_atual,))
        
        if not vendas_mes or vendas_mes['total'] == 0:
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("ℹ️ Não há vendas no mês atual para resetar"),
                    bgcolor=ft.colors.BLUE
                )
            )
            return
        
    except Exception as error:
        print(f"Erro ao consultar vendas do mês: {error}")
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"❌ Erro ao consultar vendas: {str(error)}"),
                bgcolor=ft.colors.RED
            )
        )
        return
    
    # Campo de confirmação
    confirmacao_field = ft.TextField(
        hint_text="Digite CONFIRMO em maiúsculas",
        width=300,
        height=50,
        color=ft.colors.BLACK
    )
    
    def executar_reset_mes(e):
        if confirmacao_field.value != "CONFIRMO":
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Digite 'CONFIRMO' para prosseguir"),
                    bgcolor=ft.colors.RED
                )
            )
            return
            
        try:
            # Fazer backup antes do reset
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"pre_reset_mes_{timestamp}.db")
            shutil.copy2(db.db_path, backup_file)
            
            # Resetar vendas do mês
            db.execute("""
                DELETE FROM vendas 
                WHERE strftime('%Y-%m', data_venda) = ?
            """, (mes_atual,))
            
            # Resetar itens das vendas do mês
            db.execute("""
                DELETE FROM itens_venda 
                WHERE venda_id NOT IN (SELECT id FROM vendas)
            """)
            
            # Resetar movimentação de caixa do mês
            db.execute("""
                DELETE FROM movimentacao_caixa 
                WHERE strftime('%Y-%m', data_movimento) = ?
                AND descricao LIKE 'Venda #%'
            """, (mes_atual,))
            
            db.conn.commit()
            
            # Fechar modal
            dlg_reset_mes.open = False
            page.update()
            
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"✅ Vendas do mês resetadas! Backup: pre_reset_mes_{timestamp}.db"),
                    bgcolor=ft.colors.GREEN,
                    duration=5000
                )
            )
            
        except Exception as error:
            print(f"Erro ao resetar vendas do mês: {error}")
            dlg_reset_mes.open = False
            page.update()
            
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao resetar vendas: {str(error)}"),
                    bgcolor=ft.colors.RED,
                    duration=5000
                )
            )
    
    def fechar_modal(e):
        dlg_reset_mes.open = False
        page.update()
    
    # Modal de confirmação
    dlg_reset_mes = ft.AlertDialog(
        modal=True,
        title=ft.Text("⚠️ Resetar Vendas do Mês", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.RED),
        content=ft.Column([
            ft.Text(
                f"Você está prestes a DELETAR todas as vendas do mês atual ({datetime.now().strftime('%m/%Y')})!",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.RED
            ),
            ft.Container(height=10),
            ft.Text(f"📊 Vendas encontradas: {vendas_mes['total']}", size=14),
            ft.Text(f"💰 Valor total: MT {vendas_mes['valor_total']:.2f}", size=14),
            ft.Container(height=10),
            ft.Text(
                "⚠️ ATENÇÃO: Esta ação NÃO pode ser desfeita!",
                size=14,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.RED
            ),
            ft.Text(
                "✅ Um backup será criado automaticamente antes do reset.",
                size=12,
                color=ft.colors.GREEN
            ),
            ft.Container(height=10),
            ft.Text(
                "Digite 'CONFIRMO' para prosseguir:",
                size=14,
                weight=ft.FontWeight.BOLD
            ),
            confirmacao_field
        ], tight=True, spacing=5),
        actions=[
            ft.TextButton(
                "Cancelar",
                icon=ft.icons.CANCEL,
                on_click=fechar_modal
            ),
            ft.ElevatedButton(
                "RESETAR VENDAS DO MÊS",
                icon=ft.icons.DELETE_FOREVER,
                bgcolor=ft.colors.RED,
                color=ft.colors.WHITE,
                on_click=executar_reset_mes
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.dialog = dlg_reset_mes
    dlg_reset_mes.open = True
    page.update()

def resetar_vendas_hoje(page, db, backup_dir):
    """Abre modal para confirmar reset das vendas de hoje"""
    
    # Obter dados de hoje
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        # Contar vendas de hoje
        vendas_hoje = db.fetchone("""
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as valor_total
            FROM vendas 
            WHERE DATE(data_venda) = ?
            AND status != 'Anulada'
        """, (hoje,))
        
        if not vendas_hoje or vendas_hoje['total'] == 0:
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("ℹ️ Não há vendas hoje para resetar"),
                    bgcolor=ft.colors.BLUE
                )
            )
            return
        
    except Exception as error:
        print(f"Erro ao consultar vendas de hoje: {error}")
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"❌ Erro ao consultar vendas: {str(error)}"),
                bgcolor=ft.colors.RED
            )
        )
        return
    
    # Campo de confirmação
    confirmacao_field = ft.TextField(
        hint_text="Digite CONFIRMO em maiúsculas",
        width=300,
        height=50,
        color=ft.colors.BLACK
    )
    
    def executar_reset_hoje(e):
        if confirmacao_field.value != "CONFIRMO":
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Digite 'CONFIRMO' para prosseguir"),
                    bgcolor=ft.colors.RED
                )
            )
            return
            
        try:
            # Fazer backup antes do reset
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"pre_reset_hoje_{timestamp}.db")
            shutil.copy2(db.db_path, backup_file)
            
            # Resetar vendas de hoje
            db.execute("""
                DELETE FROM vendas 
                WHERE DATE(data_venda) = ?
            """, (hoje,))
            
            # Resetar itens das vendas de hoje
            db.execute("""
                DELETE FROM itens_venda 
                WHERE venda_id NOT IN (SELECT id FROM vendas)
            """)
            
            # Resetar movimentação de caixa de hoje
            db.execute("""
                DELETE FROM movimentacao_caixa 
                WHERE DATE(data_movimento) = ?
                AND descricao LIKE 'Venda #%'
            """, (hoje,))
            
            db.conn.commit()
            
            # Fechar modal
            dlg_reset_hoje.open = False
            page.update()
            
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"✅ Vendas de hoje resetadas! Backup: pre_reset_hoje_{timestamp}.db"),
                    bgcolor=ft.colors.GREEN,
                    duration=5000
                )
            )
            
        except Exception as error:
            print(f"Erro ao resetar vendas de hoje: {error}")
            dlg_reset_hoje.open = False
            page.update()
            
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao resetar vendas: {str(error)}"),
                    bgcolor=ft.colors.RED,
                    duration=5000
                )
            )
    
    def fechar_modal(e):
        dlg_reset_hoje.open = False
        page.update()
    
    # Modal de confirmação
    dlg_reset_hoje = ft.AlertDialog(
        modal=True,
        title=ft.Text("⚠️ Zerar Vendas de Hoje", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE),
        content=ft.Column([
            ft.Text(
                f"Você está prestes a DELETAR todas as vendas de hoje ({datetime.now().strftime('%d/%m/%Y')})!",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.ORANGE
            ),
            ft.Container(height=10),
            ft.Text(f"📊 Vendas encontradas: {vendas_hoje['total']}", size=14),
            ft.Text(f"💰 Valor total: MT {vendas_hoje['valor_total']:.2f}", size=14),
            ft.Container(height=10),
            ft.Text(
                "⚠️ ATENÇÃO: Esta ação NÃO pode ser desfeita!",
                size=14,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.RED
            ),
            ft.Text(
                "✅ Um backup será criado automaticamente antes do reset.",
                size=12,
                color=ft.colors.GREEN
            ),
            ft.Container(height=10),
            ft.Text(
                "Digite 'CONFIRMO' para prosseguir:",
                size=14,
                weight=ft.FontWeight.BOLD
            ),
            confirmacao_field
        ], tight=True, spacing=5),
        actions=[
            ft.TextButton(
                "Cancelar",
                icon=ft.icons.CANCEL,
                on_click=fechar_modal
            ),
            ft.ElevatedButton(
                "ZERAR VENDAS DE HOJE",
                icon=ft.icons.DELETE_SWEEP,
                bgcolor=ft.colors.ORANGE,
                color=ft.colors.WHITE,
                on_click=executar_reset_hoje
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.dialog = dlg_reset_hoje
    dlg_reset_hoje.open = True
    page.update()
