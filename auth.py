python
import bcrypt
from database import cursor, conn

# =========================================
# CRIAR USUÁRIO
# =========================================

def criar_usuario(usuario, senha):

    senha_hash = bcrypt.hashpw(
        senha.encode(),
        bcrypt.gensalt()
    )

    cursor.execute(
        "INSERT INTO usuarios(usuario, senha) VALUES (?, ?)",
        (usuario, senha_hash)
    )

    conn.commit()

# =========================================
# LOGIN
# =========================================

def login(usuario, senha):

    cursor.execute(
        "SELECT senha FROM usuarios WHERE usuario=?",
        (usuario,)
    )

    resultado = cursor.fetchone()

    if resultado:

        senha_hash = resultado[0]

        return bcrypt.checkpw(
            senha.encode(),
            senha_hash
        )

    return False


---