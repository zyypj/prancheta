import random


def gerar_calendario(ids):
    """
    Gera o calendário da liga em turno único, no sistema de todos contra todos.

    Embaralha os clubes e aplica o método do círculo: o primeiro clube fica fixo e os demais giram a cada
    rodada. Com número ímpar de clubes, um espaço vazio é incluído e quem cair contra ele folga na rodada. Em
    cada confronto, manda o jogo quem jogou menos vezes em casa até ali; no empate, quem jogou fora na rodada
    anterior, e depois sorteio. Assim cada clube joga de 4 a 6 vezes em casa e nunca passa de 4 jogos seguidos
    com o mesmo mando.

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
    jogos_em_casa = {time: 0 for time in times if time}
    ultimo_mando = {}
    turno = []
    for _ in range(quantidade - 1):
        jogos = []
        for indice in range(quantidade // 2):
            um, outro = times[indice], times[quantidade - 1 - indice]
            if um is None or outro is None:
                continue
            casa, fora = sorted(
                (um, outro), key=lambda time: (jogos_em_casa[time], ultimo_mando.get(time) == "casa", random.random())
            )
            jogos_em_casa[casa] += 1
            ultimo_mando[casa], ultimo_mando[fora] = "casa", "fora"
            jogos.append((casa, fora))
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
