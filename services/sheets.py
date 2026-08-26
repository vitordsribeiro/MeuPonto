"""
services/sheets.py — toda a comunicação com a planilha do Google

Usamos a biblioteca `gspread`, que é bem mais simples que a API oficial crua.
Instale com: pip install gspread google-auth

Estrutura esperada da planilha (Google Sheets):

Aba "Usuarios":
| id | nome  | email           | senha_hash |
|----|-------|-----------------|------------|
| 1  | Vitor | vitor@email.com | $2b$12...  |

Aba "RegistrosPonto":
| id | usuario_id | data       | entrada | saida_almoco | volta_almoco | saida |
|----|-----------|------------|---------|--------------|--------------|-------|
| 1  | 1         | 2026-08-25 | 08:02   | 12:00        | 13:01        |       |

Autenticação: você vai criar uma Service Account no Google Cloud Console,
baixar o JSON de credenciais, e compartilhar a planilha com o email
dela (com permissão de Editor).
"""

import gspread
import json
import os
from datetime import datetime, date

# Em produção (Vercel), as credenciais vêm da variável de ambiente
# GOOGLE_CREDENTIALS_JSON (o conteúdo inteiro do credentials.json, em uma linha).
# Em desenvolvimento local, se essa variável não existir, cai no arquivo local.
CREDENTIALS_FILE = "credentials.json"
SHEET_ID = os.environ.get("SHEET_ID", "1LiK2osZtp774QCERuRKrj4ZAK40M4wQ8WtvS3OBX_Fw")


def _get_client():
    credenciais_env = os.environ.get("GOOGLE_CREDENTIALS_JSON")

    if credenciais_env:
        # Produção: monta as credenciais a partir do JSON guardado na env var
        info = json.loads(credenciais_env)
        return gspread.service_account_from_dict(info)

    # Desenvolvimento local: usa o arquivo credentials.json na raiz do projeto
    return gspread.service_account(filename=CREDENTIALS_FILE)


def _get_worksheet(nome_aba: str):
    """
    Já implementada — pega uma aba específica da planilha pelo nome.
    """
    client = _get_client()
    sheet = client.open_by_key(SHEET_ID)
    return sheet.worksheet(nome_aba)


def _proximo_id_usuario(ws):
    valores = ws.get_all_values()
    ids = [int(l[0]) for l in valores[1:] if l and l[0].isdigit()]
    return max(ids, default=0) + 1


def create_user(nome: str, email: str, senha_hash: str):
    """
    Cria um novo usuário na aba "Usuarios". Retorna o dicionário do
    usuário criado (com o id já atribuído).
    """
    ws = _get_worksheet("Usuarios")
    novo_id = _proximo_id_usuario(ws)
    ws.append_row([novo_id, nome, email, senha_hash])
    return {"id": novo_id, "nome": nome, "email": email, "senha_hash": senha_hash}


def find_user_by_email(email: str):
    ws = _get_worksheet("Usuarios")
    usuarios = ws.get_all_records()
    for usuario in usuarios:
        if usuario.get("email") == email:
            return usuario
    return None


def find_user_by_id(usuario_id):
    ws = _get_worksheet("Usuarios")
    usuarios = ws.get_all_records()
    for usuario in usuarios:
        if str(usuario.get("id")) == str(usuario_id):
            return usuario
    return None


def _registro_vazio():
    return {"entrada": None, "saida_almoco": None, "volta_almoco": None, "saida": None}


def get_today_record(usuario_id):
    hoje = date.today().isoformat()  # "2026-08-25"
    ws = _get_worksheet("RegistrosPonto")
    registros = ws.get_all_records()

    for registro in registros:
        if str(registro.get("usuario_id")) == str(usuario_id) and registro.get("data") == hoje:
            return registro

    return _registro_vazio()


def get_month_records(usuario_id, ano=None, mes=None):
    hoje = date.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    prefixo = f"{ano:04d}-{mes:02d}"  # "2026-08"

    ws = _get_worksheet("RegistrosPonto")
    registros = ws.get_all_records()

    return [
        r for r in registros
        if str(r.get("usuario_id")) == str(usuario_id) and str(r.get("data", "")).startswith(prefixo)
    ]


# Ordem das colunas na aba RegistrosPonto (1 = coluna A)
_COLUNAS = {
    "id": 1,
    "usuario_id": 2,
    "data": 3,
    "entrada": 4,
    "saida_almoco": 5,
    "volta_almoco": 6,
    "saida": 7,
}


def _encontrar_linha(ws, usuario_id, data_str):
    """
    Percorre a planilha e retorna o número da linha (1-indexado, contando
    o cabeçalho) que bate com usuario_id + data. Retorna None se não achar.
    """
    valores = ws.get_all_values()  # lista de listas, valores[0] é o cabeçalho
    for i, linha in enumerate(valores[1:], start=2):  # começa na linha 2 (pula cabeçalho)
        if len(linha) < 3:
            continue
        if linha[_COLUNAS["usuario_id"] - 1] == str(usuario_id) and linha[_COLUNAS["data"] - 1] == data_str:
            return i
    return None


def _proximo_id(ws):
    valores = ws.get_all_values()
    ids = [int(l[0]) for l in valores[1:] if l and l[0].isdigit()]
    return max(ids, default=0) + 1


def registrar_ponto(usuario_id, tipo: str):
    hoje = date.today().isoformat()
    hora_atual = datetime.now().strftime("%H:%M")
    ws = _get_worksheet("RegistrosPonto")

    linha = _encontrar_linha(ws, usuario_id, hoje)

    if linha is None:
        novo_id = _proximo_id(ws)
        nova_linha = [""] * 7
        nova_linha[_COLUNAS["id"] - 1] = novo_id
        nova_linha[_COLUNAS["usuario_id"] - 1] = usuario_id
        nova_linha[_COLUNAS["data"] - 1] = hoje
        nova_linha[_COLUNAS[tipo] - 1] = hora_atual
        ws.append_row(nova_linha)
    else:
        coluna = _COLUNAS[tipo]
        ws.update_cell(linha, coluna, hora_atual)


def editar_registro(usuario_id, data: str, campo: str, novo_horario: str):
    ws = _get_worksheet("RegistrosPonto")
    linha = _encontrar_linha(ws, usuario_id, data)

    if linha is None:
        # não existia registro nesse dia ainda — cria um novo já com o valor editado
        novo_id = _proximo_id(ws)
        nova_linha = [""] * 7
        nova_linha[_COLUNAS["id"] - 1] = novo_id
        nova_linha[_COLUNAS["usuario_id"] - 1] = usuario_id
        nova_linha[_COLUNAS["data"] - 1] = data
        nova_linha[_COLUNAS[campo] - 1] = novo_horario
        ws.append_row(nova_linha)
    else:
        coluna = _COLUNAS[campo]
        ws.update_cell(linha, coluna, novo_horario)
