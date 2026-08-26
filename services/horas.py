"""
services/horas.py — cálculo de horas trabalhadas

Esse módulo é o mais "Python puro" de todos: nenhuma dependência externa,
só datetime e timedelta. Bom lugar pra relembrar manipulação de tempo.
"""

from datetime import datetime, timedelta


def _string_para_hora(hhmm: str):
    """
    Já implementada — converte "08:02" em um objeto datetime.time
    (usamos uma data fixa qualquer, só nos importa a hora:minuto).
    """
    if not hhmm:
        return None
    return datetime.strptime(hhmm, "%H:%M")


def _formatar_timedelta(delta: timedelta) -> str:
    total_segundos = int(delta.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    return f"{horas}h {minutos}min"


def _tempo_trabalhado_dia(registro: dict):
    """
    Retorna um timedelta com o tempo trabalhado no dia, ou None
    se o dia ainda não tem entrada e saída registradas.
    """
    entrada = _string_para_hora(registro.get("entrada"))
    saida = _string_para_hora(registro.get("saida"))

    if entrada is None or saida is None:
        return None

    tempo_total = saida - entrada

    saida_almoco = _string_para_hora(registro.get("saida_almoco"))
    volta_almoco = _string_para_hora(registro.get("volta_almoco"))

    if saida_almoco is not None and volta_almoco is not None:
        tempo_total -= (volta_almoco - saida_almoco)

    return tempo_total


def calcular_horas_dia(registro: dict) -> str:
    tempo = _tempo_trabalhado_dia(registro)
    if tempo is None:
        return "--:--"
    return _formatar_timedelta(tempo)


def calcular_horas_mes(registros: list) -> str:
    total = timedelta()
    for registro in registros:
        tempo = _tempo_trabalhado_dia(registro)
        if tempo is not None:
            total += tempo
    return _formatar_timedelta(total)
