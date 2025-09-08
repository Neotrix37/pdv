#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corrigir a função de restauração no configuracoes_view.py
Torna a restauração mais robusta e compatível com o sistema simplificado
"""

def criar_funcao_restauracao_simplificada():
    """Cria uma versão simplificada e robusta da função de restauração"""
    
    funcao_nova = '''    def confirmar_restauracao_simplificada(self, backup_path):
        """
        Versão simplificada e robusta da restauração de backup.
        Compatível com o sistema de banco único (APPDATA).
        
        Args:
            backup_path (str): Caminho para o arquivo de backup a ser restaurado.
        """
        try:
            # Fechar diálogo se estiver aberto
            dlg = getattr(self, 'dialog', None)
            if dlg and dlg.open:
                dlg.open = False
            
            # Mostrar indicador de carregamento
            loading_snackbar = ft.SnackBar(
                content=ft.Row([
                    ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.colors.WHITE),
                    ft.Text(" Restaurando backup...", color=ft.colors.WHITE)
                ]),
                bgcolor=ft.colors.BLUE,
                duration=0
            )
            self.page.show_snack_bar(loading_snackbar)
            self.page.update()
            
            # Verificar se arquivo de backup existe
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_path}")
            
            backup_size = os.path.getsize(backup_path)
            if backup_size < 1000:  # Menos de 1KB é suspeito
                raise ValueError("Arquivo de backup muito pequeno ou corrompido")
            
            print(f"[RESTAURAÇÃO] Iniciando restauração de: {backup_path}")
            print(f"[RESTAURAÇÃO] Tamanho do backup: {backup_size / (1024*1024):.2f} MB")
            
            # Fazer backup de segurança do banco atual
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_restore_backup = os.path.join(self.backup_dir, f"pre_restore_{timestamp}.db")
            
            if os.path.exists(str(self.db.db_path)):
                shutil.copy2(str(self.db.db_path), pre_restore_backup)
                print(f"[BACKUP] Backup de segurança criado: {pre_restore_backup}")
            
            # Fechar conexão atual
            if hasattr(self.db, 'conn') and self.db.conn:
                self.db.conn.close()
                print("[RESTAURAÇÃO] Conexão fechada")
            
            # Aguardar liberação do arquivo
            import time
            time.sleep(1)
            
            # Remover banco atual
            if os.path.exists(str(self.db.db_path)):
                os.remove(str(self.db.db_path))
                print("[RESTAURAÇÃO] Banco atual removido")
            
            # Copiar backup para localização ativa
            shutil.copy2(backup_path, str(self.db.db_path))
            print(f"[RESTAURAÇÃO] Backup copiado para: {self.db.db_path}")
            
            # Verificar se cópia foi bem-sucedida
            if not os.path.exists(str(self.db.db_path)):
                raise Exception("Falha ao copiar arquivo de backup")
            
            # Resetar singleton e recriar conexão
            from database.database import Database
            Database._instance = None
            self.db = Database()
            
            # Verificar integridade do banco restaurado
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vendas")
            total_vendas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) FROM vendas")
            valor_total = cursor.fetchone()[0]
            
            print(f"[SUCESSO] Restauração concluída!")
            print(f"[SUCESSO] Vendas restauradas: {total_vendas}")
            print(f"[SUCESSO] Valor total: MT {valor_total:.2f}")
            
            # Verificar e corrigir esquema
            try:
                self.db.verificar_e_corrigir_esquema_pos_restauracao()
                print("[SUCESSO] Esquema verificado e corrigido")
            except Exception as e:
                print(f"[AVISO] Erro na verificação de esquema: {e}")
            
            # Mostrar mensagem de sucesso
            success_snackbar = ft.SnackBar(
                content=ft.Text(f"Backup restaurado com sucesso! {total_vendas} vendas, MT {valor_total:.2f}"),
                bgcolor=ft.colors.GREEN,
                duration=5000
            )
            self.page.show_snack_bar(success_snackbar)
            self.page.update()
            
            return True
            
        except Exception as e:
            print(f"[ERRO] Falha na restauração: {e}")
            
            # Tentar restaurar backup de segurança
            if 'pre_restore_backup' in locals() and os.path.exists(pre_restore_backup):
                try:
                    print("[RECUPERAÇÃO] Restaurando backup de segurança...")
                    if os.path.exists(str(self.db.db_path)):
                        os.remove(str(self.db.db_path))
                    shutil.copy2(pre_restore_backup, str(self.db.db_path))
                    
                    # Recriar conexão
                    from database.database import Database
                    Database._instance = None
                    self.db = Database()
                    
                    print("[RECUPERAÇÃO] Backup de segurança restaurado")
                except Exception as recovery_error:
                    print(f"[ERRO] Falha na recuperação: {recovery_error}")
            
            # Mostrar erro ao usuário
            error_snackbar = ft.SnackBar(
                content=ft.Text(f"Erro na restauração: {str(e)}"),
                bgcolor=ft.colors.RED,
                duration=5000
            )
            self.page.show_snack_bar(error_snackbar)
            self.page.update()
            
            return False'''
    
    return funcao_nova

def aplicar_correcao():
    """Aplica a correção no arquivo configuracoes_view.py"""
    
    print("CORREÇÃO DA FUNÇÃO DE RESTAURAÇÃO")
    print("=" * 50)
    
    arquivo_config = "views/configuracoes_view.py"
    
    try:
        # Ler arquivo atual
        with open(arquivo_config, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Criar backup
        import shutil
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{arquivo_config}.backup_restauracao_{timestamp}"
        shutil.copy2(arquivo_config, backup_file)
        print(f"[BACKUP] Backup criado: {backup_file}")
        
        # Adicionar nova função (não substituir a antiga ainda)
        funcao_nova = criar_funcao_restauracao_simplificada()
        
        # Encontrar local para inserir a nova função (após confirmar_restauracao)
        import re
        
        # Procurar o final da função confirmar_restauracao atual
        padrao = r'(def confirmar_restauracao\(self, backup_path\):.*?except Exception as e:.*?return False\s*)'
        
        if re.search(padrao, conteudo, re.DOTALL):
            # Adicionar nova função após a atual
            conteudo_novo = re.sub(
                padrao,
                r'\\1\\n\\n' + funcao_nova,
                conteudo,
                flags=re.DOTALL
            )
            
            # Salvar arquivo modificado
            with open(arquivo_config, 'w', encoding='utf-8') as f:
                f.write(conteudo_novo)
            
            print("[SUCESSO] Nova função de restauração adicionada!")
            print("A função 'confirmar_restauracao_simplificada' foi criada.")
            print("Você pode testar ela primeiro antes de substituir a original.")
            
            return True
        else:
            print("[ERRO] Não foi possível encontrar a função original para inserir a nova")
            return False
            
    except Exception as e:
        print(f"[ERRO] Falha ao aplicar correção: {e}")
        return False

if __name__ == "__main__":
    print("Este script criará uma versão melhorada da função de restauração.")
    print("A nova função será mais robusta e compatível com o sistema simplificado.")
    print()
    
    sucesso = aplicar_correcao()
    
    if sucesso:
        print("\\n[CONCLUÍDO] Correção aplicada com sucesso!")
        print("Nova função: confirmar_restauracao_simplificada()")
        print("Teste ela antes de substituir a função original.")
    else:
        print("\\n[FALHA] Não foi possível aplicar a correção.")
        print("Verifique os logs acima para mais detalhes.")
