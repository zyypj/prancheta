import random

from config import DESAFIOS_PARA_OBJETIVO, DIFERENCA_FAVORITISMO, PREMIO_OBJETIVO
from liga.financas import lancar
from liga.tabela import saldo
from liga.temporada import (
    adversario_de,
    ajustar_confianca,
    clube_do_jogador,
    diferenca_de_forca,
    gols_do_clube,
    jogo_do_jogador,
    temporada_acabou,
)

DESAFIOS = {
    "vencer": {"texto": "Vencer o jogo", "premio": 1.5, "confianca": 2},
    "nao_perder": {"texto": "Não perder o jogo", "premio": 1.0, "confianca": 2},
    "sem_sofrer": {"texto": "Não sofrer gols", "premio": 1.2, "confianca": 2},
    "dois_gols": {"texto": "Marcar pelo menos 2 gols", "premio": 1.0, "confianca": 1},
    "golear": {"texto": "Vencer por 2 gols de diferença ou mais", "premio": 2.0, "confianca": 3},
    "posse": {"texto": "Ter mais posse de bola que o adversário", "premio": 0.6, "confianca": 1},
    "chutes": {"texto": "Finalizar pelo menos 12 vezes", "premio": 0.6, "confianca": 1},
    "disciplina": {"texto": "Terminar sem expulsões e com no máximo 10 faltas", "premio": 0.5, "confianca": 1},
    "jovem": {"texto": "Começar com um jogador de até 21 anos entre os titulares", "premio": 0.5, "confianca": 1},
}
DESAFIOS_POR_FAVORITISMO = {
    "azarao": ("nao_perder", "sem_sofrer", "posse", "disciplina", "jovem"),
    "equilibrado": ("vencer", "dois_gols", "sem_sofrer", "posse", "chutes", "disciplina", "jovem"),
    "favorito": ("golear", "dois_gols", "chutes", "vencer", "sem_sofrer"),
}
OBJETIVOS = {
    "artilheiro": "Ter um jogador com 5 gols ou mais na temporada",
    "sequencia": "Vencer 3 jogos seguidos",
    "semifinal": "Chegar à semifinal da copa",
    "desafios": f"Cumprir {DESAFIOS_PARA_OBJETIVO} desafios da diretoria",
    "saldo": "Terminar a liga com saldo de gols positivo",
}


def desafio_da_etapa(estado):
    """
    Devolve o desafio da diretoria para o jogo da etapa atual, sorteando um novo quando preciso.

    O desafio é sorteado uma vez por etapa e guardado no estado. A lista de onde ele sai depende do
    favoritismo: contra um adversário mais forte por mais de DIFERENCA_FAVORITISMO (5), a diretoria pede algo
    possível, como não perder; contra um mais fraco, pede goleada ou muitos gols. Se o clube não joga na
    etapa, não há desafio.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        dict | None: Desafio com identificador, texto, prêmio em milhões e confiança, ou None.
    """
    jogo = jogo_do_jogador(estado)
    if not jogo:
        return None
    atual = estado.get("desafio")
    if not atual or atual["etapa"] != estado["etapa"]:
        diferenca = diferenca_de_forca(estado, adversario_de(jogo, estado["clube_id"]))
        if diferenca < -DIFERENCA_FAVORITISMO:
            grupo = "azarao"
        elif diferenca > DIFERENCA_FAVORITISMO:
            grupo = "favorito"
        else:
            grupo = "equilibrado"
        atual = {"id": random.choice(DESAFIOS_POR_FAVORITISMO[grupo]), "etapa": estado["etapa"]}
        estado["desafio"] = atual
    return {**DESAFIOS[atual["id"]], **atual}


def cumpriu_desafio(estado, desafio_id, resultado):
    """
    Confere se o clube do técnico cumpriu um desafio no jogo.

    Args:
        estado (dict): Estado atual da temporada.
        desafio_id (str): Chave do desafio em DESAFIOS.
        resultado (dict): Resultado da partida do técnico.

    Returns:
        bool: True se o desafio foi cumprido.
    """
    clube_id = estado["clube_id"]
    adversario = adversario_de((resultado["mandante"], resultado["visitante"]), clube_id)
    marcados, sofridos = gols_do_clube(clube_id, resultado)
    meus = resultado["estatisticas"][clube_id]
    deles = resultado["estatisticas"][adversario]
    vermelhos = resultado["vm"] if resultado["mandante"] == clube_id else resultado["vv"]
    clube = clube_do_jogador(estado)
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    regras = {
        "vencer": marcados > sofridos or resultado.get("vencedor") == clube_id and marcados == sofridos,
        "nao_perder": marcados >= sofridos,
        "sem_sofrer": sofridos == 0,
        "dois_gols": marcados >= 2,
        "golear": marcados - sofridos >= 2,
        "posse": meus["posse"] > deles["posse"],
        "chutes": meus["chutes"] >= 12,
        "disciplina": vermelhos == 0 and meus["faltas"] <= 10,
        "jovem": any(por_id[i].get("idade", 30) <= 21 for i in clube["titulares"] if i in por_id),
    }
    return regras[desafio_id]


def avaliar_desafio(estado, resultado):
    """
    Avalia o desafio da etapa depois do jogo do técnico e paga a recompensa se ele foi cumprido.

    Cumprido, o clube recebe o prêmio no caixa (categoria "Desafios da diretoria"), a confiança sobe e o
    contador de desafios cumpridos aumenta. O desafio só é avaliado uma vez.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict | None): Resultado da partida do técnico, ou None se ele não jogou.

    Returns:
        dict | None: Desafio avaliado, com a chave "cumpriu", ou None se não havia desafio.
    """
    if not resultado:
        return None
    desafio = desafio_da_etapa(estado)
    if not desafio or estado["desafio"].get("avaliado"):
        return None
    estado["desafio"]["avaliado"] = True
    desafio["cumpriu"] = cumpriu_desafio(estado, desafio["id"], resultado)
    if desafio["cumpriu"]:
        lancar(estado, estado["clube_id"], "Desafios da diretoria", desafio["premio"])
        ajustar_confianca(estado, desafio["confianca"])
        estado["desafios_cumpridos"] = estado.get("desafios_cumpridos", 0) + 1
    return desafio


def sequencia_atual(estado):
    """
    Conta quantas vitórias seguidas o clube tem nos resultados mais recentes.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        int: Tamanho da sequência de vitórias que termina no último jogo.
    """
    sequencia = 0
    for letra in reversed(estado["ultimos"]):
        if letra != "V":
            break
        sequencia += 1
    return sequencia


def objetivo_cumprido(estado, chave):
    """
    Confere se um objetivo da temporada já foi alcançado.

    O saldo de gols só conta quando a temporada termina; os outros objetivos podem ser alcançados a qualquer
    momento.

    Args:
        estado (dict): Estado atual da temporada.
        chave (str): Chave do objetivo em OBJETIVOS.

    Returns:
        bool: True se o objetivo foi alcançado.
    """
    clube = clube_do_jogador(estado)
    if chave == "artilheiro":
        return max((jogador["gols"] for jogador in clube["elenco"]), default=0) >= 5
    if chave == "sequencia":
        return sequencia_atual(estado) >= 3
    if chave == "semifinal":
        fases = estado["copa"]["confrontos"]
        return any(clube["id"] in jogo for fase in ("semifinal", "final") for jogo in fases.get(fase, []))
    if chave == "desafios":
        return estado.get("desafios_cumpridos", 0) >= DESAFIOS_PARA_OBJETIVO
    return temporada_acabou(estado) and saldo(estado["tabela"][clube["id"]]) > 0


def atualizar_objetivos(estado):
    """
    Marca os objetivos da temporada que acabaram de ser alcançados e paga o prêmio de cada um.

    Cada objetivo novo rende PREMIO_OBJETIVO (2 milhões) no caixa, na categoria "Objetivos da temporada", e
    entra na lista estado["objetivos"], que vale pontos no ranking.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        list[str]: Textos dos objetivos alcançados agora.
    """
    feitos = estado.setdefault("objetivos", [])
    novos = [chave for chave in OBJETIVOS if chave not in feitos and objetivo_cumprido(estado, chave)]
    for chave in novos:
        feitos.append(chave)
        lancar(estado, estado["clube_id"], "Objetivos da temporada", PREMIO_OBJETIVO)
    return [OBJETIVOS[chave] for chave in novos]
