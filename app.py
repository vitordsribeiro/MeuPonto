"""
Registrador de Ponto - app.py

Este é o arquivo principal do Flask: define as ROTAS (as URLs que existem
no site) e chama funções que você vai implementar em services/ e auth.py.

Você não precisa mexer muito aqui — a ideia é que este arquivo já funcione
"de graça" assim que as funções em auth.py e services/sheets.py estiverem
implementadas.
"""

from flask import Flask, render_template, request, redirect, url_for, session
from datetime import date, datetime
import bcrypt
import os

from auth import login_required, verify_login, get_current_user
from services import sheets
from services import horas

app = Flask(__name__, static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "chave-de-desenvolvimento-troque-em-producao")


@app.template_filter("data_br")
def data_br(valor):
    """Formata uma data 'AAAA-MM-DD' (como é guardada na planilha) para 'DD/MM/AAAA'."""
    if not valor:
        return valor
    try:
        return date.fromisoformat(valor).strftime("%d/%m/%Y")
    except ValueError:
        return valor


@app.route("/")
@login_required
def dashboard():
    usuario = get_current_user()

    # TODO (você vai implementar em services/sheets.py):
    # busca o registro de hoje desse usuário na planilha
    registro_hoje = sheets.get_today_record(usuario["id"])

    # TODO (você vai implementar em services/horas.py):
    # soma as horas trabalhadas hoje e no mês, a partir dos registros
    horas_hoje = horas.calcular_horas_dia(registro_hoje)
    horas_mes = horas.calcular_horas_mes(sheets.get_month_records(usuario["id"]))

    return render_template(
        "dashboard.html",
        usuario=usuario,
        registro=registro_hoje,
        horas_hoje=horas_hoje,
        horas_mes=horas_mes,
    )


@app.route("/bater-ponto", methods=["POST"])
@login_required
def bater_ponto():
    """
    Chamado quando o usuário clica em um dos botões:
    Entrada, Saída Almoço, Volta Almoço ou Saída.

    O botão que foi clicado vem no campo 'tipo' do formulário,
    com um desses valores: entrada, saida_almoco, volta_almoco, saida
    """
    usuario = get_current_user()
    tipo = request.form.get("tipo")

    # TODO (services/sheets.py):
    # gravar (ou atualizar, se já existir a linha de hoje) o horário
    # atual na coluna correspondente a `tipo`
    sheets.registrar_ponto(usuario_id=usuario["id"], tipo=tipo)

    return redirect(url_for("dashboard"))


@app.route("/editar", methods=["GET", "POST"])
@login_required
def editar():
    usuario = get_current_user()

    if request.method == "POST":
        try:
            data_iso = datetime.strptime(request.form.get("data", ""), "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            registros = sheets.get_month_records(usuario["id"])
            return render_template("editar.html", registros=registros, erro="Data inválida. Use o formato DD/MM/AAAA.")

        # TODO (services/sheets.py):
        # atualizar manualmente um horário específico de um dia específico
        sheets.editar_registro(
            usuario_id=usuario["id"],
            data=data_iso,
            campo=request.form.get("campo"),
            novo_horario=request.form.get("novo_horario"),
        )
        return redirect(url_for("editar"))

    registros = sheets.get_month_records(usuario["id"])
    return render_template("editar.html", registros=registros)


MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def _mes_escolhido():
    """Lê ?mes=AAAA-MM da URL. Se não vier (ou vier inválido), usa o mês atual."""
    try:
        escolhido = datetime.strptime(request.args.get("mes", ""), "%Y-%m")
        return escolhido.year, escolhido.month
    except ValueError:
        hoje = sheets._hoje()
        return hoje.year, hoje.month


@app.route("/atendimentos")
@login_required
def atendimentos():
    usuario = get_current_user()
    return render_template(
        "atendimentos.html",
        aberto=sheets.get_atendimento_aberto(usuario["id"]),
        ultimos=sheets.get_ultimos_atendimentos(usuario["id"]),
        duracao=horas.formatar_duracao_atendimento,
    )


@app.route("/atendimentos/iniciar", methods=["POST"])
@login_required
def iniciar_atendimento():
    sheets.iniciar_atendimento(get_current_user()["id"])
    return redirect(url_for("atendimentos"))


@app.route("/atendimentos/finalizar", methods=["POST"])
@login_required
def finalizar_atendimento():
    usuario = get_current_user()
    observacao = request.form.get("observacao", "").strip()

    # O botão já fica desabilitado sem observação, mas conferimos aqui também
    if not observacao:
        return render_template(
            "atendimentos.html",
            aberto=sheets.get_atendimento_aberto(usuario["id"]),
            ultimos=sheets.get_ultimos_atendimentos(usuario["id"]),
            duracao=horas.formatar_duracao_atendimento,
            erro="Preencha a observação para finalizar o atendimento.",
        )

    sheets.finalizar_atendimento(usuario["id"], observacao)
    return redirect(url_for("atendimentos"))


@app.route("/atendimentos/editar", methods=["GET", "POST"])
@login_required
def editar_atendimentos():
    usuario = get_current_user()
    erro = None
    form = {}

    if request.method == "POST":
        form = request.form
        campos = [form.get(c, "").strip() for c in ("data_inicio", "hora_inicio", "data_fim", "hora_fim", "observacao")]
        data_inicio, hora_inicio, data_fim, hora_fim, observacao = campos

        if not all(campos):
            erro = "Preencha todos os campos."
        elif horas.duracao_atendimento(dict(zip(
                ("data_inicio", "hora_inicio", "data_fim", "hora_fim"), campos))) is None:
            erro = "O fim precisa ser depois do início."
        else:
            sheets.salvar_atendimento(usuario["id"], form.get("id"), *campos)
            return redirect(url_for("editar_atendimentos", mes=data_inicio[:7]))

    ano, mes = _mes_escolhido()
    editando = None
    if request.args.get("id"):
        editando = sheets.get_atendimento(usuario["id"], request.args["id"])

    return render_template(
        "editar_atendimentos.html",
        atendimentos=sheets.get_atendimentos_mes(usuario["id"], ano, mes),
        mes=f"{ano:04d}-{mes:02d}",
        editando=editando,
        form=form or editando or {},
        erro=erro,
    )


@app.route("/atendimentos/excluir", methods=["POST"])
@login_required
def excluir_atendimento():
    sheets.excluir_atendimento(get_current_user()["id"], request.form.get("id"))
    return redirect(url_for("editar_atendimentos", mes=request.form.get("mes")))


@app.route("/relatorio")
@login_required
def relatorio():
    usuario = get_current_user()
    ano, mes = _mes_escolhido()
    lista = sheets.get_atendimentos_mes(usuario["id"], ano, mes)
    return render_template(
        "relatorio.html",
        usuario=usuario,
        atendimentos=lista,
        mes=f"{ano:04d}-{mes:02d}",
        periodo=f"{MESES[mes - 1]}/{ano}",
        total=horas.total_atendimentos(lista),
        duracao=horas.formatar_duracao_atendimento,
        gerado_em=sheets._agora().strftime("%d/%m/%Y %H:%M"),
    )


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not nome or not email or not senha:
            return render_template("cadastro.html", erro="Preencha todos os campos.")

        if senha != confirmar_senha:
            return render_template("cadastro.html", erro="As senhas não coincidem.")

        if len(senha) < 6:
            return render_template("cadastro.html", erro="A senha precisa ter pelo menos 6 caracteres.")

        if sheets.find_user_by_email(email):
            return render_template("cadastro.html", erro="Já existe uma conta com esse email.")

        senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
        usuario = sheets.create_user(nome=nome, email=email, senha_hash=senha_hash)

        session["usuario_id"] = usuario["id"]
        return redirect(url_for("dashboard"))

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        # TODO (auth.py):
        # verificar email/senha contra a planilha de usuários
        usuario = verify_login(email, senha)

        if usuario:
            session["usuario_id"] = usuario["id"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", erro="Email ou senha inválidos")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
