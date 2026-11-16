import random


def gerar_calendario(ids):
    """
    Gera o calendário da liga em turno único, no sistema de todos contra todos.

    Embaralha os clubes e aplica o método do círculo: o primeiro clube fica fixo e os demais giram a cada rodada. Com número ímpar de clubes, um espaço vazio é incluído e quem cair contra ele folga na rodada. O mando de campo alterna conforme a soma do número da rodada com a posição do confronto.

    Args:
        ids (Iterable[str]): Identificadores dos clubes participantes.

    Returns:
        list[list[tuple[str, str]]]: Lista de rodadas, cada uma com os jogos no formato (mandante, visitante).
    """
    times = list(ids)
    random.shuffle(times)
    if len(times) % 2:
        times.append(None)
    quantidade = len(times)
    turno = []
    for numero in range(quantidade - 1):
        jogos = []
        for indice in range(quantidade // 2):
            casa, fora = times[indice], times[quantidade - 1 - indice]
            if casa is None or fora is None:
                continue
            jogos.append((casa, fora) if (numero + indice) % 2 == 0 else (fora, casa))
        turno.append(jogos)
        times = [times[0], times[-1]] + times[1:-1]
    return turno


def jogo_do_clube(rodada, clube_id):
    """
    Procura, dentro de uma rodada, o jogo em que o clube informado atua.

    Args:
        rodada (list[tuple[str, str]]): Jogos da rodada no formato (mandante, visitante).
        clube_id (str): Identificador do clube procurado.

    Returns:
        tuple[str, str] | None: Jogo do clube ou None se ele não joga nessa rodada.
    """
    for jogo in rodada:
        if clube_id in jogo:
            return jogo
    return None
