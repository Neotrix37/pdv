from database.database import Database
from werkzeug.security import check_password_hash, generate_password_hash

class Usuario:
    def __init__(self):
        self.db = Database()
    
    def autenticar(self, usuario, senha):
        user = self.db.fetchone(
            "SELECT * FROM usuarios WHERE usuario = ? AND ativo = 1", 
            (usuario,)
        )
        if user and check_password_hash(user['senha'], senha):
            return dict(user)
        return None

    def criar(self, nome, usuario, senha, is_admin=False):
        return self.db.execute("""
            INSERT INTO usuarios (nome, usuario, senha, is_admin)
            VALUES (?, ?, ?, ?)
        """, (nome, usuario, generate_password_hash(senha), is_admin))
