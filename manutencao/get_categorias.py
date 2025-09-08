import sqlite3

def get_categorias():
    conn = sqlite3.connect('c:\\Users\\saide\\sinc\\pdv3\\database\\database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, descricao FROM categorias ORDER BY nome")
    categorias = cursor.fetchall()
    conn.close()
    return categorias

if __name__ == "__main__":
    categorias = get_categorias()
    if categorias:
        print("Categorias existentes:")
        for cat_id, nome, descricao in categorias:
            print(f"ID: {cat_id}, Nome: {nome}, Descrição: {descricao if descricao else 'N/A'}")
    else:
        print("Nenhuma categoria encontrada.")