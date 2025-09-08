def remove_bom(input_file, output_file):
    # Lê o conteúdo do arquivo em modo binário para preservar o BOM
    with open(input_file, 'rb') as f:
        content = f.read()
    
    # Remove o BOM (se existir)
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]
    
    # Salva o conteúdo sem BOM
    with open(output_file, 'wb') as f:
        f.write(content)
    
    print(f"Arquivo sem BOM salvo como: {output_file}")

if __name__ == "__main__":
    input_file = r"c:\Users\saide\pdv3\database\database.py"
    output_file = r"c:\Users\saide\pdv3\database\database_fixed.py"
    
    print("Removendo BOM do arquivo...")
    remove_bom(input_file, output_file)
    
    # Substitui o arquivo original
    import shutil
    shutil.move(output_file, input_file)
    print("Arquivo original substituído com sucesso.")
