import os
import winshell
from win32com.client import Dispatch
import sys

def create_shortcut():
    # Obtém o caminho do desktop
    desktop = winshell.desktop()
    
    # Caminho do executável
    path = os.path.join(os.getcwd(), "dist", "PDV", "PDV.exe")
    
    # Caminho do atalho
    shortcut_path = os.path.join(desktop, "PDV.lnk")
    
    # Cria o atalho
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = path
    shortcut.WorkingDirectory = os.path.dirname(path)
    shortcut.IconLocation = path
    shortcut.save()
    
    print(f"Atalho criado com sucesso em: {shortcut_path}")

if __name__ == "__main__":
    try:
        create_shortcut()
    except Exception as e:
        print(f"Erro ao criar atalho: {e}")
        input("Pressione Enter para sair...") 