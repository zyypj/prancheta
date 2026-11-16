from datetime import datetime

from config import PASTA_SAVES, VERSAO_SAVE
from persistencia.arquivos import gravar_json, ler_json


def nome_do_arquivo(tecnico):
    """
    Gera um nome de arquivo seguro a partir do nome do técnico.

    Converte o nome para minúsculas, troca todo caractere que não seja letra ou número por "_" e remove os "_"
    das pontas. Se nada sobrar, usa "tecnico".

    Args:
        tecnico (str): Nome do técnico.

    Returns:
        str: Nome base do arquivo, sem extensão.
    """
    base = "".join(letra if letra.isalnum() else "_" for letra in tecnico.strip().lower())
    return base.strip("_") or "tecnico"


def caminho_do_save(tecnico):
    """
    Monta o caminho do arquivo de save de um técnico.

    Args:
        tecnico (str): Nome do técnico.

    Returns:
        Path: Caminho do arquivo JSON dentro de PASTA_SAVES (dados/saves).
    """
    return PASTA_SAVES / f"{nome_do_arquivo(tecnico)}.json"


def salvar_jogo(estado):
    """
    Salva o estado da temporada em arquivo JSON.

    Registra a data e a hora do salvamento no campo "salvo_em" (formato dd/mm/aaaa hh:mm) e grava o estado
    inteiro no arquivo do técnico, sobrescrevendo o save anterior.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        bool: True se o save foi gravado, False em caso de erro.
    """
    estado["salvo_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    return gravar_json(caminho_do_save(estado["tecnico"]), estado)


def listar_saves():
    """
    Lista os jogos salvos disponíveis para carregar.

    Percorre os arquivos JSON de PASTA_SAVES, do modificado mais recentemente para o mais antigo, e ignora os
    que não são um dicionário, que têm versão diferente de VERSAO_SAVE ou que estão sem algum dado do resumo
    (técnico, clube ou rodada), sem derrubar a lista. Se a pasta não puder ser lida, o erro é capturado por
    try/except e a função devolve uma lista vazia.

    Returns:
        list: Dicionários com caminho, técnico, nome do clube, rodada e data do salvamento de cada save
            válido.
    """
    try:
        arquivos = sorted(PASTA_SAVES.glob("*.json"), key=lambda caminho: caminho.stat().st_mtime, reverse=True)
    except OSError:
        return []
    saves = []
    for caminho in arquivos:
        estado = ler_json(caminho)
        if not isinstance(estado, dict) or estado.get("versao") != VERSAO_SAVE:
            continue
        try:
            saves.append(
                {
                    "caminho": caminho,
                    "tecnico": estado["tecnico"],
                    "clube": estado["clubes"][estado["clube_id"]]["nome"],
                    "rodada": estado["rodada"],
                    "salvo_em": estado.get("salvo_em", "-"),
                }
            )
        except (KeyError, TypeError):
            continue
    return saves


def carregar_jogo(caminho):
    """
    Carrega uma temporada salva a partir do arquivo JSON.

    Rejeita o arquivo se ele não for um dicionário ou tiver versão diferente de VERSAO_SAVE. Como o JSON
    guarda tuplas como listas, os jogos do calendário e os confrontos de cada fase da copa são convertidos de
    volta para tuplas. Se essa estrutura estiver incompleta ou malformada, o erro é capturado por try/except e
    o save é rejeitado.

    Args:
        caminho (str | Path): Caminho do arquivo de save.

    Returns:
        dict | None: Estado da temporada restaurado ou None se o save for inválido.
    """
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
