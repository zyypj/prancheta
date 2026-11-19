import random

from config import (
    CLASSIFICADOS_DIRETO_COPA,
    FASES_COPA,
    NOMES_FASES,
    PREMIO_FASE_COPA,
    PREMIO_TITULO_COPA,
    VAGAS_SERIE_B_COPA,
)
from liga.financas import lancar

CAMPOS_DO_RESUMO = ("mandante", "visitante", "gm", "gv", "penaltis", "vencedor")


def montar_confrontos(ids):
    """
    Sorteia os confrontos de uma fase da copa.

    Embaralha os clubes e forma os pares na ordem do sorteio; o primeiro de cada par é o mandante. Se a
    quantidade for ímpar, o último clube sorteado fica sem confronto.

    Args:
        ids (Iterable[str]): Identificadores dos clubes que entram no sorteio.

    Returns:
        list[tuple[str, str]]: Confrontos no formato (mandante, visitante).
    """
    sorteados = list(ids)
    random.shuffle(sorteados)
    return [(sorteados[indice], sorteados[indice + 1]) for indice in range(0, len(sorteados) - 1, 2)]


def ordem_por_forca(clubes):
    """
    Ordena os clubes de cada divisão pela força, do mais forte para o mais fraco.

    É a ordem usada para montar a copa na primeira temporada, quando ainda não há classificação anterior.

    Args:
        clubes (dict): Clubes da temporada, indexados pelo identificador.

    Returns:
        dict: Para cada divisão (1 e 2), a lista de identificadores na ordem.
    """
    ordem = {1: [], 2: []}
    for clube in sorted(clubes.values(), key=lambda clube: clube["forca"], reverse=True):
        ordem[clube.get("divisao", 1)].append(clube["id"])
    return ordem


def criar_copa(clubes, ordem=None):
    """
    Cria a estrutura inicial da copa.

    Jogam a copa os clubes da Série A e os VAGAS_SERIE_B_COPA (2) primeiros da Série B na ordem recebida. Os
    CLASSIFICADOS_DIRETO_COPA (4) primeiros da Série A vão direto às quartas de final; só os piores colocados
    da Série A e os clubes da Série B disputam a fase preliminar, com confrontos sorteados. A ordem é a
    classificação da temporada anterior ou, na primeira temporada, a força dos clubes.

    Args:
        clubes (dict): Clubes da temporada, indexados pelo identificador.
        ordem (dict | None): Para cada divisão, os identificadores do melhor para o pior. Padrão None, que usa
            a força.

    Returns:
        dict: Copa com os participantes, os classificados diretos, os confrontos da fase preliminar, os
            resultados vazios, o campeão e a fase de eliminação do jogador ainda indefinidos.
    """
    ordem = ordem or ordem_por_forca(clubes)
    serie_a = [clube_id for clube_id in ordem[1] if clube_id in clubes]
    serie_b = [clube_id for clube_id in ordem.get(2, []) if clube_id in clubes][:VAGAS_SERIE_B_COPA]
    diretos = serie_a[:CLASSIFICADOS_DIRETO_COPA]
    preliminar = serie_a[CLASSIFICADOS_DIRETO_COPA:] + serie_b
    return {
        "participantes": diretos + preliminar,
        "classificados": diretos,
        "confrontos": {"preliminar": montar_confrontos(preliminar)},
        "resultados": {},
        "campeao": None,
        "eliminado_em": None,
    }


def fase_da_etapa(valor):
    """
    Separa o valor de uma etapa da copa na fase e na perna do confronto.

    Args:
        valor (str): Valor da etapa, como "final", "quartas_ida" ou "quartas_volta".

    Returns:
        tuple[str, int]: Nome da fase e perna: 0 para jogo único, 1 para ida e 2 para volta.
    """
    for sufixo, perna in (("_ida", 1), ("_volta", 2)):
        if valor.endswith(sufixo):
            return valor[: -len(sufixo)], perna
    return valor, 0


def preparar_fase(copa, fase):
    """
    Define os confrontos de uma fase da copa, caso ainda não existam.

    Se a fase já tem confrontos, eles são devolvidos sem alteração. Nas quartas de final os classificados são
    sorteados; na semifinal e na final os pares seguem a ordem dos classificados, de modo que o vencedor de um
    jogo enfrenta o vencedor do jogo seguinte. Os confrontos gerados ficam gravados na copa.

    Args:
        copa (dict): Estrutura da copa na temporada.
        fase (str): Nome da fase, como definido em FASES_COPA.

    Returns:
        list[tuple[str, str]]: Confrontos da fase no formato (mandante, visitante).
    """
    if fase in copa["confrontos"]:
        return copa["confrontos"][fase]
    if fase == "quartas":
        confrontos = montar_confrontos(copa["classificados"])
    else:
        vivos = copa["classificados"]
        confrontos = [(vivos[indice], vivos[indice + 1]) for indice in range(0, len(vivos) - 1, 2)]
    copa["confrontos"][fase] = confrontos
    return confrontos


def confrontos_da_perna(copa, fase, perna):
    """
    Lista os jogos de uma perna da fase, invertendo os mandos na volta.

    Args:
        copa (dict): Estrutura da copa na temporada.
        fase (str): Nome da fase.
        perna (int): 0 para jogo único, 1 para ida e 2 para volta.

    Returns:
        list[tuple[str, str]]: Jogos no formato (mandante, visitante).
    """
    confrontos = preparar_fase(copa, fase)
    return [(fora, casa) for casa, fora in confrontos] if perna == 2 else confrontos


def jogo_de_ida(copa, fase, time_a, time_b):
    """
    Procura o resultado da ida entre dois clubes.

    Args:
        copa (dict): Estrutura da copa na temporada.
        fase (str): Nome da fase.
        time_a (str): Identificador de um clube.
        time_b (str): Identificador do outro clube.

    Returns:
        dict | None: Resumo da ida, ou None se ela não existe.
    """
    idas = copa.get("idas", {}).get(fase, [])
    return next((jogo for jogo in idas if {jogo["mandante"], jogo["visitante"]} == {time_a, time_b}), None)


def registrar_ida(estado, fase, resultados):
    """
    Guarda os resultados da ida de uma fase, sem definir quem avança.

    Args:
        estado (dict): Estado atual da temporada.
        fase (str): Nome da fase.
        resultados (list[dict]): Resultados dos jogos de ida.

    Returns:
        dict | None: Resultado do jogo do clube do jogador ou None se ele não disputou a fase.
    """
    estado["copa"].setdefault("idas", {})[fase] = [
        {campo: resultado.get(campo) for campo in CAMPOS_DO_RESUMO} for resultado in resultados
    ]
    return next((r for r in resultados if estado["clube_id"] in (r["mandante"], r["visitante"])), None)


def resumo_do_confronto(copa, fase, resultado):
    """
    Resume um confronto decidido, somando a ida quando a fase tem dois jogos.

    No resumo de ida e volta, mandante e visitante seguem a ordem da ida e os gols são os do agregado.

    Args:
        copa (dict): Estrutura da copa na temporada.
        fase (str): Nome da fase.
        resultado (dict): Resultado do jogo único ou da volta.

    Returns:
        dict: Mandante, visitante, gols, pênaltis e vencedor do confronto.
    """
    resumo = {campo: resultado.get(campo) for campo in CAMPOS_DO_RESUMO}
    ida = jogo_de_ida(copa, fase, resultado["mandante"], resultado["visitante"])
    if ida:
        resumo.update(
            {
                "mandante": ida["mandante"],
                "visitante": ida["visitante"],
                "gm": ida["gm"] + resultado["gv"],
                "gv": ida["gv"] + resultado["gm"],
            }
        )
    return resumo


def jogo_na_fase(copa, fase, clube_id):
    """
    Procura o confronto de um clube em uma fase da copa.

    Args:
        copa (dict): Estrutura da copa na temporada.
        fase (str): Nome da fase.
        clube_id (str): Identificador do clube procurado.

    Returns:
        tuple[str, str] | None: Confronto do clube ou None se ele não joga nessa fase ou a fase ainda não foi
            montada.
    """
    return next((jogo for jogo in copa["confrontos"].get(fase, []) if clube_id in jogo), None)


def fase_neutra(fase):
    """
    Indica se a fase da copa é disputada em campo neutro, o que acontece apenas na final.

    Args:
        fase (str): Nome da fase.

    Returns:
        bool: True se a fase for a final, False caso contrário.
    """
    return fase == "final"


def registrar_fase(estado, fase, resultados):
    """
    Registra os resultados de uma fase da copa e atualiza os classificados.

    Guarda um resumo de cada confronto (com o placar agregado, se houve ida e volta), soma PREMIO_FASE_COPA ao
    caixa de cada vencedor e atualiza a lista de
    classificados: na fase preliminar os vencedores se juntam aos classificados diretos; nas demais fases os
    vencedores passam a ser os classificados, na ordem dos confrontos. Na final, define o campeão e soma
    também PREMIO_TITULO_COPA ao caixa dele. Se o clube do jogador perdeu, anota a fase em que foi eliminado.

    Args:
        estado (dict): Estado atual da temporada.
        fase (str): Nome da fase disputada.
        resultados (list[dict]): Resultados dos jogos únicos ou das voltas da fase.

    Returns:
        dict | None: Resultado do jogo do clube do jogador ou None se ele não disputou a fase.
    """
    copa = estado["copa"]
    resumos = [resumo_do_confronto(copa, fase, resultado) for resultado in resultados]
    copa["resultados"][fase] = resumos
    vencedores = [resumo["vencedor"] for resumo in resumos]
    for clube_id in vencedores:
        lancar(estado, clube_id, "Premiação da copa", PREMIO_FASE_COPA)
    if fase == "preliminar":
        copa["classificados"] = copa["classificados"] + vencedores
    else:
        ordem = list(copa["confrontos"][fase])
        por_jogo = {(r["mandante"], r["visitante"]): r["vencedor"] for r in resumos}
        copa["classificados"] = [por_jogo[jogo] for jogo in ordem]
    if fase == FASES_COPA[-1]:
        copa["campeao"] = vencedores[0]
        campeao = estado["clubes"][copa["campeao"]]
        lancar(estado, campeao["id"], "Premiação da copa", PREMIO_TITULO_COPA)
    jogo = next((r for r in resultados if estado["clube_id"] in (r["mandante"], r["visitante"])), None)
    if jogo and jogo["vencedor"] != estado["clube_id"]:
        copa["eliminado_em"] = fase
    return jogo


def situacao_do_clube(copa, clube_id):
    """
    Descreve a situação de um clube na copa.

    Clubes que não entraram na copa aparecem como fora dela. Para os outros, verifica primeiro se o clube é
    o campeão; depois procura, nos resultados registrados, um jogo em que ele tenha perdido.

    Args:
        copa (dict): Estrutura da copa na temporada.
        clube_id (str): Identificador do clube.

    Returns:
        str: "fora da copa", "campeão", "eliminado na <fase>" ou "na disputa".
    """
    if clube_id not in copa.get("participantes", [clube_id]):
        return "fora da copa"
    if copa["campeao"] == clube_id:
        return "campeão"
    for fase, resultados in copa["resultados"].items():
        for resultado in resultados:
            if clube_id in (resultado["mandante"], resultado["visitante"]) and resultado["vencedor"] != clube_id:
                return f"eliminado na {NOMES_FASES[fase].lower()}"
    return "na disputa"
