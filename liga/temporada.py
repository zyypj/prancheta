from datetime import datetime

from config import (
    BONUS_META,
    BONUS_TITULO,
    CONFIANCA_DERROTA,
    CONFIANCA_EMPATE,
    CONFIANCA_INICIAL,
    CONFIANCA_VITORIA,
    CONFIANCA_ZEBRA,
    DIFERENCA_FAVORITISMO,
    NIVEIS,
    TOTAL_RODADAS,
)
from elenco.escalacao import completar_titulares, escalar_automatico, gerar_elenco
from elenco.substituicoes import preparar_proxima_rodada
from liga.calendario import gerar_calendario, jogo_do_clube
from liga.tabela import criar_tabela, ordenar_tabela, posicao_do_clube, registrar_resultado, saldo
from partida.simulacao import simular_partida


def criar_estado_novo(tecnico, clube_id, clubes_base, banco_nomes):
    usados = set()
    clubes = {}
    for base in clubes_base:
        clube = dict(base)
        clube["plano"] = dict(base["plano"])
        clube["elenco"] = gerar_elenco(clube, banco_nomes, usados)
        clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
        clubes[clube["id"]] = clube
    ids = list(clubes)
    return {
        "versao": 1,
        "tecnico": tecnico,
        "clube_id": clube_id,
        "clubes": clubes,
        "calendario": gerar_calendario(ids),
        "rodada": 1,
        "tabela": criar_tabela(ids),
        "historico": [],
        "sumulas": {},
        "confianca": CONFIANCA_INICIAL,
        "ultimos": [],
        "demitido": False,
        "encerrado": False,
        "inicio": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def clube_do_jogador(estado):
    return estado["clubes"][estado["clube_id"]]


def jogos_da_rodada(estado, rodada=None):
    numero = rodada or estado["rodada"]
    return estado["calendario"][numero - 1]


def jogo_do_jogador(estado):
    return jogo_do_clube(jogos_da_rodada(estado), estado["clube_id"])


def adversario_de(jogo, clube_id):
    return jogo[1] if jogo[0] == clube_id else jogo[0]


def simular_outros_jogos(estado, frases):
    jogo = jogo_do_jogador(estado)
    return [
        simular_partida(estado["clubes"][casa], estado["clubes"][fora], frases)
        for casa, fora in jogos_da_rodada(estado)
        if (casa, fora) != jogo
    ]


def classificacao(estado):
    return ordenar_tabela(estado["tabela"], estado["historico"])


def posicao_atual(estado):
    return posicao_do_clube(classificacao(estado), estado["clube_id"])


def resultado_para(clube_id, resultado):
    feitos, sofridos = (resultado["gm"], resultado["gv"]) if resultado["mandante"] == clube_id else (resultado["gv"], resultado["gm"])
    if feitos > sofridos:
        return "V"
    if feitos == sofridos:
        return "E"
    return "D"


def variacao_de_confianca(estado, resultado):
    clube_id = estado["clube_id"]
    adversario = adversario_de((resultado["mandante"], resultado["visitante"]), clube_id)
    diferenca = estado["clubes"][clube_id]["forca"] - estado["clubes"][adversario]["forca"]
    letra = resultado_para(clube_id, resultado)
    variacao = {"V": CONFIANCA_VITORIA, "E": CONFIANCA_EMPATE, "D": CONFIANCA_DERROTA}[letra]
    if letra == "V" and diferenca < -DIFERENCA_FAVORITISMO:
        variacao += CONFIANCA_ZEBRA
    elif letra == "D" and diferenca > DIFERENCA_FAVORITISMO:
        variacao -= CONFIANCA_ZEBRA
    return letra, variacao


def ajustar_confianca(estado, variacao):
    estado["confianca"] = max(0, min(100, estado["confianca"] + variacao))
    if estado["confianca"] <= 0:
        estado["demitido"] = True


def fechar_rodada(estado, resultados):
    rodada = []
    for resultado in resultados:
        registrar_resultado(estado["tabela"], resultado)
        rodada.append({chave: resultado[chave] for chave in ("mandante", "visitante", "gm", "gv")})
    estado["historico"].append(rodada)
    do_jogador = next(resultado for resultado in resultados if estado["clube_id"] in (resultado["mandante"], resultado["visitante"]))
    letra, variacao = variacao_de_confianca(estado, do_jogador)
    estado["ultimos"] = (estado["ultimos"] + [letra])[-5:]
    ajustar_confianca(estado, variacao)
    trocados = []
    for clube in estado["clubes"].values():
        preparar_proxima_rodada(clube["elenco"])
        if clube["id"] == estado["clube_id"]:
            trocados = completar_titulares(clube)
        else:
            clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
    estado["rodada"] += 1
    if estado["rodada"] > TOTAL_RODADAS:
        estado["encerrado"] = True
    return {"letra": letra, "variacao": variacao, "trocados": trocados}


def temporada_acabou(estado):
    return estado["demitido"] or estado["encerrado"]


def meta_cumprida(estado, posicao):
    nivel = NIVEIS[clube_do_jogador(estado)["nivel"]]
    return posicao <= nivel["posicao_meta"]


def resumo_final(estado):
    clube = clube_do_jogador(estado)
    nivel = NIVEIS[clube["nivel"]]
    linha = estado["tabela"][clube["id"]]
    posicao = posicao_atual(estado)
    titulo = posicao == 1 and not estado["demitido"]
    cumpriu = meta_cumprida(estado, posicao) and not estado["demitido"]
    bonus = (BONUS_META if cumpriu else 0) + (BONUS_TITULO if titulo else 0)
    pontuacao = round((linha["pontos"] * 10 + saldo(linha) * 2 + bonus) * nivel["multiplicador"])
    if estado["demitido"]:
        desfecho = f"demitido na rodada {estado['rodada'] - 1}"
    elif titulo and clube["nivel"] != "grande":
        desfecho = "campeão (feito histórico)"
    elif titulo:
        desfecho = "campeão"
    elif cumpriu:
        desfecho = "meta cumprida"
    else:
        desfecho = "meta não cumprida"
    return {
        "tecnico": estado["tecnico"],
        "clube": clube["nome"],
        "posicao": posicao,
        "pontos": linha["pontos"],
        "saldo": saldo(linha),
        "pontuacao": max(0, pontuacao),
        "desfecho": desfecho,
        "venceu": cumpriu,
        "meta": nivel["meta"],
        "data": datetime.now().strftime("%d/%m/%Y"),
    }
