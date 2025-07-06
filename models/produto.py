from database.database import Database

class Produto:
    def __init__(self):
        self.db = Database()
    
    def criar(self, codigo, nome, descricao, preco_custo, preco_venda, estoque, estoque_minimo):
        return self.db.execute("""
            INSERT INTO produtos (codigo, nome, descricao, preco_custo, preco_venda, 
                                estoque, estoque_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (codigo, nome, descricao, preco_custo, preco_venda, estoque, estoque_minimo))

    def atualizar_estoque(self, produto_id, quantidade):
        return self.db.execute("""
            UPDATE produtos 
            SET estoque = estoque + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (quantidade, produto_id))
