import random

from config import PONTOS_EMPATE, PONTOS_VITORIA


def criar_tabela(ids):
    """
    Cria a tabela de classificação da liga com todos os clubes zerados.

    Cada linha recebe também um número sorteado, usado como último critério de desempate.

    Args:
        ids (Iterable[str]): Identificadores dos clubes.

    Returns:
        dict: Linhas da tabela indexadas pelo identificador do clube.
    """
    return {
        identificador: {
            "id": identificador,
            "pontos": 0,
            "jogos": 0,
            "vitorias": 0,
            "empates": 0,
            "derrotas": 0,
            "gp": 0,
            "gc": 0,
            "vermelhos": 0,
            "sorteio": random.random(),
        }
        for identificador in ids
    }


def saldo(linha):
    """
    Calcula o saldo de gols de um clube.

    Args:
        linha (dict): Linha do clube na tabela.

    Returns:
        int: Gols marcados menos gols sofridos.
    """
    return linha["gp"] - linha["gc"]


def aplicar_placar(linha, feitos, sofridos, vermelhos):
    """
    Atualiza a linha de um clube na tabela com o placar de um jogo.

    Soma o jogo, os gols marcados e sofridos e os cartões vermelhos, e conta vitória (PONTOS_VITORIA pontos), empate (PONTOS_EMPATE ponto) ou derrota (nenhum ponto).

    Args:
        linha (dict): Linha do clube na tabela.
        feitos (int): Gols marcados pelo clube.
        sofridos (int): Gols sofridos pelo clube.
        vermelhos (int): Cartões vermelhos recebidos pelo clube no jogo.
    """
    linha["jogos"] += 1
    linha["gp"] += feitos
    linha["gc"] += sofridos
    linha["vermelhos"] += vermelhos
    if feitos > sofridos:
        linha["vitorias"] += 1
        linha["pontos"] += PONTOS_VITORIA
    elif feitos == sofridos:
        linha["empates"] += 1
        linha["pontos"] += PONTOS_EMPATE
    else:
        linha["derrotas"] += 1


def registrar_resultado(tabela, resultado):
    """
    Registra o resultado de um jogo na tabela, atualizando mandante e visitante.

    Args:
        tabela (dict): Tabela de classificação da liga.
        resultado (dict): Resultado da partida, com placar e, se houver, os vermelhos de cada lado (zero quando ausentes).
    """
    aplicar_placar(tabela[resultado["mandante"]], resultado["gm"], resultado["gv"], resultado.get("vm", 0))
    aplicar_placar(tabela[resultado["visitante"]], resultado["gv"], resultado["gm"], resultado.get("vv", 0))


def criterio_principal(linha):
    """
    Monta a chave dos critérios principais de classificação.

    A ordem é: pontos, vitórias, saldo de gols e gols marcados.

    Args:
        linha (dict): Linha do clube na tabela.

    Returns:
        tuple[int, int, int, int]: Pontos, vitórias, saldo e gols marcados.
    """
    return linha["pontos"], linha["vitorias"], saldo(linha), linha["gp"]


def pontos_no_confronto(historico, grupo):
    """
    Calcula os pontos de cada clube apenas nos jogos entre os clubes do grupo.

    Usado no desempate por confronto direto: só contam os jogos do histórico em que mandante e visitante pertencem ao grupo.

    Args:
        historico (list[list[dict]]): Resultados da liga, rodada a rodada.
        grupo (set[str]): Identificadores dos clubes empatados.

    Returns:
        dict: Pontos de cada clube do grupo, indexados pelo identificador.
    """
    pontos = {identificador: 0 for identificador in grupo}
    for rodada in historico:
        for jogo in rodada:
            casa, fora = jogo["mandante"], jogo["visitante"]
            if casa not in grupo or fora not in grupo:
                continue
            if jogo["gm"] > jogo["gv"]:
                pontos[casa] += PONTOS_VITORIA
            elif jogo["gm"] < jogo["gv"]:
                pontos[fora] += PONTOS_VITORIA
            else:
                pontos[casa] += PONTOS_EMPATE
                pontos[fora] += PONTOS_EMPATE
    return pontos


def ordenar_tabela(tabela, historico):
    """
    Ordena a tabela de classificação da liga.

    Ordena por pontos, vitórias, saldo e gols marcados. Clubes que empatam em todos esses critérios são desempatados, nessa ordem, pelos pontos no confronto direto entre eles, pelo menor número de cartões vermelhos e pelo número sorteado na criação da tabela.

    Args:
        tabela (dict): Tabela de classificação da liga.
        historico (list[list[dict]]): Resultados da liga, rodada a rodada.

    Returns:
        list[dict]: Linhas da tabela do primeiro ao último colocado.
    """
    linhas = sorted(tabela.values(), key=criterio_principal, reverse=True)
    ordenada = []
    inicio = 0
    while inicio < len(linhas):
        fim = inicio
        while fim < len(linhas) and criterio_principal(linhas[fim]) == criterio_principal(linhas[inicio]):
            fim += 1
        grupo = linhas[inicio:fim]
        if len(grupo) > 1:
            confronto = pontos_no_confronto(historico, {linha["id"] for linha in grupo})
            grupo.sort(key=lambda linha: (confronto[linha["id"]], -linha["vermelhos"], linha["sorteio"]), reverse=True)
        ordenada.extend(grupo)
        inicio = fim
    return ordenada


def posicao_do_clube(ordenada, clube_id):
    """
    Informa a posição de um clube na tabela já ordenada.

    Args:
        ordenada (list[dict]): Linhas da tabela em ordem de classificação.
        clube_id (str): Identificador do clube.

    Returns:
        int: Posição do clube, começando em 1, ou a última posição se ele não for encontrado.
    """
    for posicao, linha in enumerate(ordenada, start=1):
        if linha["id"] == clube_id:
            return posicao
    return len(ordenada)
