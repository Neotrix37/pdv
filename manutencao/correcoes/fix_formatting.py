import re

def fix_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrigir quebras de linha
    content = content.replace('\r\n', '\n')
    
    # Padronizar aspas triplas
    content = re.sub(r'"""(.*?)"""', r'"""\1"""', content, flags=re.DOTALL)
    content = re.sub(r"'''(.*?)'''", r"'''\1'''", content, flags=re.DOTALL)
    
    # Corrigir strings quebradas em múltiplas linhas
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        single_quotes = line.count("'")
        double_quotes = line.count('"')
        
        # Se a linha tiver um número ímpar de aspas, verifique a próxima linha
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            # Tenta juntar com a próxima linha
            if i + 1 < len(lines):
                line = line + ' ' + lines[i+1]
                i += 1  # Pula a próxima linha
        
        fixed_lines.append(line)
        i += 1
    
    # Juntar tudo de volta
    fixed_content = '\n'.join(fixed_lines)
    
    # Salvar o arquivo corrigido
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Arquivo corrigido salvo como: {output_file}")

if __name__ == "__main__":
    input_file = r"c:\Users\saide\pdv3\database\database.py"
    output_file = r"c:\Users\saide\pdv3\database\database_fixed.py"
    
    print(f"Corrigindo formatação do arquivo: {input_file}")
    fix_file(input_file, output_file)
    print("Correção concluída.")
