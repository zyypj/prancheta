from datetime import datetime

from config import PASTA_SAVES, VERSAO_SAVE
from persistencia.arquivos import gravar_json, ler_json


def nome_do_arquivo(tecnico):
    base = "".join(letra if letra.isalnum() else "_" for letra in tecnico.strip().lower())
    return base.strip("_") or "tecnico"


def caminho_do_save(tecnico):
    return PASTA_SAVES / f"{nome_do_arquivo(tecnico)}.json"


def salvar_jogo(estado):
    estado["salvo_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    return gravar_json(caminho_do_save(estado["tecnico"]), estado)


def listar_saves():
    try:
        arquivos = sorted(PASTA_SAVES.glob("*.json"), key=lambda caminho: caminho.stat().st_mtime, reverse=True)
    except OSError:
        return []
    saves = []
    for caminho in arquivos:
        estado = ler_json(caminho)
        if isinstance(estado, dict) and estado.get("versao") == VERSAO_SAVE:
            saves.append({
                "caminho": caminho,
                "tecnico": estado["tecnico"],
                "clube": estado["clubes"][estado["clube_id"]]["nome"],
                "rodada": estado["rodada"],
                "salvo_em": estado.get("salvo_em", "-"),
            })
    return saves


def carregar_jogo(caminho):
    estado = ler_json(caminho)
    if not isinstance(estado, dict) or estado.get("versao") != VERSAO_SAVE:
        return None
    try:
        estado["calendario"] = [[tuple(jogo) for jogo in rodada] for rodada in estado["calendario"]]
        confrontos = estado["copa"]["confrontos"]
        estado["copa"]["confrontos"] = {fase: [tuple(jogo) for jogo in jogos] for fase, jogos in confrontos.items()}
    except (KeyError, TypeError, AttributeError):
        return None
    return estado
