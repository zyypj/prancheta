from datetime import datetime

from config import (
    AGENDA,
    BONUS_COPA,
    BONUS_META,
    BONUS_TITULO,
    CONFIANCA_AVANCO_COPA,
    CONFIANCA_DERROTA,
    CONFIANCA_EMPATE,
    CONFIANCA_INICIAL,
    CONFIANCA_QUEDA_COPA,
    CONFIANCA_TITULO_COPA,
    CONFIANCA_VITORIA,
    CONFIANCA_ZEBRA,
    DIFERENCA_FAVORITISMO,
    FASES_COPA,
    NIVEIS,
    NOMES_FASES,
    PREMIO_EMPATE,
    PREMIO_VITORIA,
    TOTAL_RODADAS,
    VERSAO_SAVE,
)
from elenco.escalacao import completar_titulares, escalar_automatico, gerar_elenco
from elenco.substituicoes import preparar_proxima_rodada
from liga.calendario import gerar_calendario, jogo_do_clube
from liga.copa import criar_copa, fase_neutra, preparar_fase, registrar_fase
from liga.tabela import criar_tabela, ordenar_tabela, posicao_do_clube, registrar_resultado, saldo
from mercado.transferencias import gerar_agentes_livres
from partida.simulacao import simular_partida


def criar_estado_novo(tecnico, clube_id, clubes_base, banco_nomes):
    usados = set()
    clubes = {}
    for base in clubes_base:
        clube = dict(base)
        clube["plano"] = dict(base["plano"])
        clube["caixa"] = NIVEIS[clube["nivel"]]["caixa"]
        clube["elenco"] = gerar_elenco(clube, banco_nomes, usados)
        clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
        clubes[clube["id"]] = clube
    ids = list(clubes)
    return {
        "versao": VERSAO_SAVE,
        "tecnico": tecnico,
        "clube_id": clube_id,
        "clubes": clubes,
        "calendario": gerar_calendario(ids),
        "copa": criar_copa(clubes),
        "livres": gerar_agentes_livres(banco_nomes, usados),
        "etapa": 0,
        "rodada": 1,
        "tabela": criar_tabela(ids),
        "historico": [],
        "sumulas": {},
        "noticias": [],
        "confianca": CONFIANCA_INICIAL,
        "ultimos": [],
        "demitido": False,
        "encerrado": False,
        "inicio": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def clube_do_jogador(estado):
    return estado["clubes"][estado["clube_id"]]


def etapa_atual(estado):
    if estado["etapa"] >= len(AGENDA):
        return None
    return AGENDA[estado["etapa"]]


def descricao_etapa(etapa):
    competicao, valor = etapa
    if competicao == "liga":
        return f"Liga — rodada {valor}/{TOTAL_RODADAS}"
    return f"Copa — {NOMES_FASES[valor]}"


def jogos_da_rodada(estado, rodada=None):
    numero = rodada or estado["rodada"]
    return estado["calendario"][numero - 1]


def jogos_da_etapa(estado):
    competicao, valor = etapa_atual(estado)
    if competicao == "liga":
        return jogos_da_rodada(estado, valor)
    return preparar_fase(estado["copa"], valor)


def jogo_neutro(estado):
    competicao, valor = etapa_atual(estado)
    return competicao == "copa" and fase_neutra(valor)


def mata_mata(estado):
    return etapa_atual(estado)[0] == "copa"


def jogo_do_jogador(estado):
    return jogo_do_clube(jogos_da_etapa(estado), estado["clube_id"])


def adversario_de(jogo, clube_id):
    return jogo[1] if jogo[0] == clube_id else jogo[0]


def simular_outros_jogos(estado, frases):
    jogo = jogo_do_jogador(estado)
    return [
        simular_partida(estado["clubes"][casa], estado["clubes"][fora], frases, jogo_neutro(estado), mata_mata(estado))
        for casa, fora in jogos_da_etapa(estado)
        if (casa, fora) != jogo
    ]


def classificacao(estado):
    return ordenar_tabela(estado["tabela"], estado["historico"])


def posicao_atual(estado):
    return posicao_do_clube(classificacao(estado), estado["clube_id"])


def gols_do_clube(clube_id, resultado):
    if resultado["mandante"] == clube_id:
        return resultado["gm"], resultado["gv"]
    return resultado["gv"], resultado["gm"]


def resultado_para(clube_id, resultado):
    feitos, sofridos = gols_do_clube(clube_id, resultado)
    if feitos > sofridos:
        return "V"
    if feitos == sofridos:
        return "E"
    return "D"


def ultimos_resultados(estado, clube_id, quantidade=5):
    letras = []
    for rodada in estado["historico"]:
        for jogo in rodada:
            if clube_id in (jogo["mandante"], jogo["visitante"]):
                letras.append(resultado_para(clube_id, jogo))
    return letras[-quantidade:]


def diferenca_de_forca(estado, adversario_id):
    return clube_do_jogador(estado)["forca"] - estado["clubes"][adversario_id]["forca"]


def variacao_de_confianca(estado, resultado):
    clube_id = estado["clube_id"]
    adversario = adversario_de((resultado["mandante"], resultado["visitante"]), clube_id)
    diferenca = diferenca_de_forca(estado, adversario)
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


def pagar_premios(estado, resultado):
    for clube_id in (resultado["mandante"], resultado["visitante"]):
        letra = resultado_para(clube_id, resultado)
        premio = PREMIO_VITORIA if letra == "V" else (PREMIO_EMPATE if letra == "E" else 0)
        clube = estado["clubes"][clube_id]
        clube["caixa"] = round(clube.get("caixa", 0) + premio, 1)


def preparar_elencos(estado):
    trocados = []
    for clube in estado["clubes"].values():
        preparar_proxima_rodada(clube["elenco"])
        if clube["id"] == estado["clube_id"]:
            trocados = completar_titulares(clube)
        else:
            clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
    return trocados


def fechar_rodada(estado, resultados):
    rodada = []
    for resultado in resultados:
        registrar_resultado(estado["tabela"], resultado)
        pagar_premios(estado, resultado)
        rodada.append({chave: resultado[chave] for chave in ("mandante", "visitante", "gm", "gv")})
    estado["historico"].append(rodada)
    do_jogador = next(
        resultado for resultado in resultados if estado["clube_id"] in (resultado["mandante"], resultado["visitante"]))
    letra, variacao = variacao_de_confianca(estado, do_jogador)
    estado["ultimos"] = (estado["ultimos"] + [letra])[-5:]
    ajustar_confianca(estado, variacao)
    trocados = preparar_elencos(estado)
    estado["rodada"] += 1
    return {"letra": letra, "variacao": variacao, "trocados": trocados}


def fechar_fase_copa(estado, resultados):
    fase = etapa_atual(estado)[1]
    jogo = registrar_fase(estado, fase, resultados)
    variacao = 0
    letra = None
    if jogo:
        passou = jogo["vencedor"] == estado["clube_id"]
        letra = "V" if passou else "D"
        if passou:
            variacao = CONFIANCA_TITULO_COPA if fase == FASES_COPA[-1] else CONFIANCA_AVANCO_COPA
        else:
            adversario = adversario_de((jogo["mandante"], jogo["visitante"]), estado["clube_id"])
            variacao = CONFIANCA_QUEDA_COPA
            if diferenca_de_forca(estado, adversario) > DIFERENCA_FAVORITISMO:
                variacao -= CONFIANCA_ZEBRA
        estado["ultimos"] = (estado["ultimos"] + [letra])[-5:]
        ajustar_confianca(estado, variacao)
    trocados = preparar_elencos(estado)
    return {"letra": letra, "variacao": variacao, "trocados": trocados, "jogo": jogo}


def avancar_etapa(estado):
    estado["etapa"] += 1
    proxima = etapa_atual(estado)
    if proxima is None:
        estado["encerrado"] = True
    elif proxima[0] == "copa":
        preparar_fase(estado["copa"], proxima[1])


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
    copa = estado["copa"]["campeao"] == clube["id"]
    cumpriu = meta_cumprida(estado, posicao) and not estado["demitido"]
    bonus = (BONUS_META if cumpriu else 0) + (BONUS_TITULO if titulo else 0) + (BONUS_COPA if copa else 0)
    pontuacao = round((linha["pontos"] * 10 + saldo(linha) * 2 + bonus) * nivel["multiplicador"])
    if estado["demitido"]:
        desfecho = f"demitido ({descricao_etapa(AGENDA[max(0, estado['etapa'] - 1)])})"
    elif titulo and clube["nivel"] != "grande":
        desfecho = "campeão (feito histórico)"
    elif titulo:
        desfecho = "campeão"
    elif cumpriu:
        desfecho = "meta cumprida"
    else:
        desfecho = "meta não cumprida"
    if copa:
        desfecho += " + campeão da copa"
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
        "copa": copa,
        "data": datetime.now().strftime("%d/%m/%Y"),
    }
