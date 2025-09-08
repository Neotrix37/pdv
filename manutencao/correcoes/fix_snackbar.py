import re
import sys

def fix_snackbar_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove todas as linhas que contêm shape=ft.RoundedRectangleBorder(radius=8)
    pattern = r',\s*shape=ft\.RoundedRectangleBorder\(radius=8\)'
    new_content = re.sub(pattern, '', content)
    
    # Salva as alterações no arquivo
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print(f"Arquivo {file_path} atualizado com sucesso!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = r"c:\Users\saide\pdv3\views\relatorios_view.py"
    
    fix_snackbar_file(file_path)
