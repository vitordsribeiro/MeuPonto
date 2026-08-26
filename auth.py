"""
auth.py — autenticação e controle de sessão

Aqui moram as funções relacionadas a login, senha e "quem é o usuário logado".

Bibliotecas que você vai usar aqui:
- bcrypt -> para conferir senha (nunca comparar senha em texto puro!)
- flask.session -> Flask já cuida do cookie de sessão pra você

Instale com: pip install bcrypt
"""

from functools import wraps
from flask import session, redirect, url_for
import bcrypt

from services import sheets


def verify_login(email: str, senha: str):
    usuario = sheets.find_user_by_email(email)
    if not usuario:
        return None

    hash_salvo = usuario.get("senha_hash", "")
    if not hash_salvo:
        return None

    if bcrypt.checkpw(senha.encode(), hash_salvo.encode()):
        return usuario

    return None


def get_current_user():
    """
    Retorna o usuário atualmente logado, usando o usuario_id
    guardado na sessão (session["usuario_id"]).

    Esta função já funciona — não precisa mexer, mas dá uma lida
    pra entender como ela se conecta com sheets.py.
    """
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return None
    return sheets.find_user_by_id(usuario_id)


def login_required(f):
    """
    Decorator que protege uma rota: se não tiver ninguém logado,
    redireciona pra tela de login.

    Já está pronto — é um bom exemplo de decorator em Python pra estudar.
    Repare como ele "embrulha" a função original.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated
