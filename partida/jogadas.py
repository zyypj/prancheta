import random

from elenco.escalacao import atributo_efetivo, limitar, rotulo
from partida.lances import (
    PESOS_MARCADOR,
    PESOS_PORTADOR,
    PESOS_REBOTE,
    amarelar,
    cara_a_cara,
    cartao_na_falta,
    cobrar_escanteio,
    cobrar_falta,
    cobrar_penalti,
    cometer_falta,
    cruzamento,
    entregar_bola,
    escolher_chute,
    escolher_jogador,
    finalizar,
    goleiro_de,
    jogar_posse,
    melhor_batedor,
    mover_bola,
    outro,
    perguntar,
    registrar,
    revisar_penalti,
)

CHANCE_JOGADA_ESPECIAL = 0.24
PESOS_JOGADAS = {
    "tiro_de_meta": 3,
    "lateral_no_ataque": 3,
    "superioridade": 3,
    "falta_lateral": 2,
    "falta_de_longe": 2,
    "sobra_na_entrada": 3,
    "erro_na_saida": 2,
    "arrancada": 3,
    "pressao_na_saida": 2,
    "escanteio_conquistado": 2,
    "bola_alta": 2,
}
CHANCES_ACONTECIMENTOS = {
    "reclamacao": 0.012,
    "confusao": 0.006,
    "paralisacao": 0.01,
    "chuva_comeca": 0.006,
    "beira_do_campo": 0.025,
}
PESOS_ATACANTE = {"ATA": 6, "MEI": 2}


def marcador_de(partida, time_id, zona):
    """
    Sorteia o jogador do adversário que marca a jogada numa zona.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a bola.
        zona (str): Zona do lance, uma das chaves de PESOS_MARCADOR.

    Returns:
        dict: Jogador do time adversário.
    """
    return escolher_jogador(partida["times"][outro(partida, time_id)], PESOS_MARCADOR[zona])


def contra_golpe(partida, time_id, zona, chance):
    """
    Decide se a perda da bola numa jogada especial vira contra-ataque do adversário.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que perdeu a bola.
        zona (str): Zona onde a bola foi perdida.
        chance (float): Chance de o adversário puxar o contra-ataque.

    Returns:
        tuple | None: (adversário, jogador que puxa o contra-ataque) ou None.
    """
    if random.random() < chance:
        return outro(partida, time_id), marcador_de(partida, time_id, zona)
    return None


def tiro_de_meta(partida, time_id, portador):
    """
    O goleiro tem a bola e escolhe como repor.

    Sair jogando curto começa uma posse normal no meio. O lançamento no centroavante vira uma disputa no alto
    entre o físico do atacante e o desarme do zagueiro (45% de base): ganhando, a posse começa no ataque.
    Lançar na ponta dá certo em 55% das vezes. Perder a disputa entrega a bola ao adversário.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que repõe a bola.
        portador (dict): Jogador que ganhou a bola no lance, usado se não houver goleiro.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver, como em jogar_posse.
    """
    time = partida["times"][time_id]
    goleiro = goleiro_de(time) or portador
    entregar_bola(partida, time_id, "saida", 1, goleiro)
    registrar(partida, "tiro_de_meta", {"goleiro": rotulo(goleiro), "time": time["nome"]}, time_id=time_id)
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(goleiro)} vai repor a bola. Como?",
        [("curto", "Sair jogando curto", 4), ("longo", "Lançar no centroavante", 3), ("ponta", "Lançar na ponta", 2)],
    )
    if escolha == "curto":
        mover_bola(partida, time_id, "defesa", 1)
        registrar(partida, "saida_curta", {"time": time["nome"]}, time_id=time_id)
        return jogar_posse(partida, time_id, zona_inicial="meio")
    alvo = escolher_jogador(time, PESOS_ATACANTE)
    zagueiro = marcador_de(partida, time_id, "ataque")
    dados = {"jogador": rotulo(alvo), "marcador": rotulo(zagueiro), "goleiro": rotulo(goleiro)}
    if escolha == "longo":
        chance = 0.45 + (atributo_efetivo(alvo, "fis") - atributo_efetivo(zagueiro, "des")) * 0.006
    else:
        chance = 0.55
    if random.random() < limitar(chance, 0.15, 0.8):
        registrar(partida, f"lancamento_{escolha}_ok", dados, time_id=time_id)
        return jogar_posse(partida, time_id, portador=alvo, zona_inicial="ataque")
    registrar(partida, "lancamento_perdido", dados, tipo="perda", time_id=time_id)
    return contra_golpe(partida, time_id, "meio", 0.15)


def lateral_no_ataque(partida, time_id, portador):
    """
    Lateral a favor perto da área adversária.

    O lateral longo vira um cruzamento na área em 50% das vezes, com mais chance para quem tem físico alto; o
    curto começa uma posse já na entrada da área; recuar recomeça a jogada no meio.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que cobra o lateral.
        portador (dict): Jogador que vai cobrar.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    faixa = random.choice((0, 2))
    entregar_bola(partida, time_id, "ataque", faixa, portador)
    registrar(partida, "lateral", {"time": time["nome"], "jogador": rotulo(portador)}, time_id=time_id)
    escolha = perguntar(
        partida,
        time_id,
        f"Lateral no ataque com {rotulo(portador)}. Como cobrar?",
        [
            ("longo", "Lateral longo na área", 2),
            ("curto", "Curto, para tabelar", 4),
            ("recuar", "Recuar e recomeçar", 2),
        ],
    )
    if escolha == "longo":
        if random.random() < 0.5 + (atributo_efetivo(portador, "fis") - 70) * 0.005:
            registrar(partida, "lateral_longo", {"jogador": rotulo(portador)}, time_id=time_id)
            cruzamento(partida, time_id, portador, -0.04, "fechar")
            return None
        registrar(partida, "lateral_afastado", tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.1)
    if escolha == "curto":
        return jogar_posse(partida, time_id, portador=portador, zona_inicial="ataque")
    registrar(partida, "lateral_recuado", {"time": time["nome"]}, time_id=time_id)
    return jogar_posse(partida, time_id, zona_inicial="meio")


def superioridade(partida, time_id, portador):
    """
    Contra-ataque com três atacantes contra dois defensores.

    Tocar para o centroavante deixa ele cara a cara em 60% das vezes (mais com bom passe). Abrir para o ponta
    dá certo em 70% e vira cruzamento. Conduzir e chutar é uma finalização com bônus, de fora ou de dentro da
    área. Errar o passe pode devolver o contra-ataque.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que contra-ataca.
        portador (dict): Jogador que conduz a bola.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    entregar_bola(partida, time_id, "ataque", 1, portador)
    registrar(partida, "superioridade", {"time": time["nome"], "jogador": rotulo(portador)}, time_id=time_id)
    escolha = perguntar(
        partida,
        time_id,
        f"Três contra dois! {rotulo(portador)} conduz. O que fazer?",
        [
            ("centro", "Tocar para o centroavante", 4),
            ("ponta", "Abrir para o ponta", 3),
            ("conduzir", "Conduzir e chutar", 3),
        ],
    )
    if escolha == "centro":
        centroavante = escolher_jogador(time, PESOS_ATACANTE, excluir=portador)
        if random.random() < 0.6 + (atributo_efetivo(portador, "pas") - 70) * 0.004:
            cara_a_cara(partida, time_id, centroavante, 0.04, "recuar")
            return None
        registrar(partida, "passe_cortado", {"jogador": rotulo(portador)}, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.2)
    if escolha == "ponta":
        ponta = escolher_jogador(time, {"ATA": 4, "MEI": 4}, excluir=portador)
        if random.random() < 0.7:
            entregar_bola(partida, time_id, "ataque", random.choice((0, 2)), ponta)
            registrar(partida, "abriu_ponta", {"jogador": rotulo(ponta)}, time_id=time_id)
            cruzamento(partida, time_id, ponta, 0.03, "recuar")
            return None
        registrar(partida, "passe_cortado", {"jogador": rotulo(portador)}, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.2)
    local = random.choice(("longe", "area"))
    finalizar(partida, time_id, portador, local, escolher_chute(partida, time_id, portador, local), 0.04, "recuar")
    return None


def falta_lateral(partida, time_id, portador):
    """
    Falta a favor pelo lado do campo, perto da área.

    O adversário soma a falta e o autor pode levar amarelo (15%). O batedor escolhe cruzar fechado (o goleiro
    corta 15% das vezes e a bola pode entrar direto em 4%), aberto no segundo pau (35% de chance de a zaga
    afastar, mas com bônus), uma jogada ensaiada rasteira (metade das vezes alguém bate livre) ou bater
    direto, com pouca chance.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que sofreu a falta.
        portador (dict): Jogador que sofreu a falta.

    Returns:
        tuple | None: Sempre None; a jogada termina na cobrança.
    """
    defensor_id = outro(partida, time_id)
    time = partida["times"][time_id]
    autor = marcador_de(partida, time_id, "ataque")
    partida["times"][defensor_id]["faltas"] += 1
    batedor = melhor_batedor(time)
    entregar_bola(partida, time_id, "ataque", random.choice((0, 2)), batedor)
    registrar(
        partida,
        "falta_lateral",
        {"marcador": rotulo(autor), "jogador": rotulo(portador), "time": time["nome"]},
        tipo="bola_parada",
        time_id=time_id,
    )
    cartao_na_falta(partida, defensor_id, autor, 0.15)
    escolha = perguntar(
        partida,
        time_id,
        f"Falta pelo lado! {rotulo(batedor)} na bola. Como cobrar?",
        [
            ("fechado", "Cruzar fechado, na direção do gol", 3),
            ("aberto", "Cruzar aberto, no segundo pau", 3),
            ("ensaiada", "Jogada ensaiada rasteira", 2),
            ("direto", "Bater direto no gol", 1),
        ],
    )
    dados = {"jogador": rotulo(batedor)}
    if escolha == "fechado":
        sorteio = random.random()
        if sorteio < 0.04:
            registrar(partida, "cruzamento_direto_gol", dados, tipo="oportunidade", time_id=time_id)
            finalizar(partida, time_id, batedor, "falta", "colocado", 0.3, "fechar", rebote=False)
        elif sorteio < 0.19:
            registrar(partida, "goleiro_corta", dados, tipo="defesa", time_id=time_id)
        else:
            cruzamento(partida, time_id, batedor, 0.0, "fechar")
    elif escolha == "aberto":
        if random.random() < 0.35:
            registrar(partida, "escanteio_afastado", tipo="perda", time_id=time_id)
        else:
            cruzamento(partida, time_id, batedor, 0.04, "fechar")
    elif escolha == "ensaiada":
        if random.random() < 0.5:
            companheiro = escolher_jogador(time, PESOS_REBOTE, excluir=batedor)
            registrar(partida, "ensaiada_ok", {"jogador": rotulo(companheiro)}, time_id=time_id)
            finalizar(partida, time_id, companheiro, "area", "colocado", 0.05, "fechar")
        else:
            registrar(partida, "ensaiada_erro", dados, tipo="perda", time_id=time_id)
    else:
        finalizar(partida, time_id, batedor, "falta", "forte", -0.1, "fechar")
    return None


def falta_de_longe(partida, time_id, portador):
    """
    Falta a favor a uns 30 metros do gol.

    O batedor pode bater direto (chute forte de longe), levantar na área (55% de chance de o cruzamento
    chegar), rolar curto para manter a posse na entrada da área ou rolar para um companheiro bater de
    primeira.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que sofreu a falta.
        portador (dict): Jogador que sofreu a falta.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    defensor_id = outro(partida, time_id)
    time = partida["times"][time_id]
    autor = marcador_de(partida, time_id, "meio")
    partida["times"][defensor_id]["faltas"] += 1
    batedor = melhor_batedor(time)
    entregar_bola(partida, time_id, "ataque", 1, batedor)
    registrar(
        partida,
        "falta_longe",
        {"marcador": rotulo(autor), "jogador": rotulo(portador), "time": time["nome"]},
        tipo="bola_parada",
        time_id=time_id,
    )
    cartao_na_falta(partida, defensor_id, autor, 0.12)
    escolha = perguntar(
        partida,
        time_id,
        f"Falta de longe! {rotulo(batedor)} ajeita a bola. O que fazer?",
        [
            ("direto", "Bater direto", 3),
            ("levantar", "Levantar na área", 3),
            ("curta", "Rolar curto e manter a posse", 3),
            ("rolar", "Rolar para um companheiro bater", 2),
        ],
    )
    if escolha == "direto":
        finalizar(partida, time_id, batedor, "longe", "forte", -0.02, "fechar")
    elif escolha == "levantar":
        if random.random() < 0.55:
            cruzamento(partida, time_id, batedor, -0.03, "fechar")
        else:
            registrar(partida, "escanteio_afastado", tipo="perda", time_id=time_id)
    elif escolha == "curta":
        return jogar_posse(partida, time_id, portador=batedor, zona_inicial="ataque")
    else:
        companheiro = escolher_jogador(time, PESOS_REBOTE, excluir=batedor)
        registrar(
            partida,
            "falta_rolada",
            {"jogador": rotulo(batedor), "companheiro": rotulo(companheiro)},
            time_id=time_id,
        )
        finalizar(partida, time_id, companheiro, "primeira", "forte", 0.03, "fechar")
    return None


def sobra_na_entrada(partida, time_id, portador):
    """
    A defesa afasta mal e a bola sobra na entrada da área.

    Bater de primeira é um chute forte com pouco controle; matar no peito perde a bola 30% das vezes, mas
    deixa escolher o chute; o lençol passa pelo marcador conforme o físico contra o desarme e deixa o jogador
    na área com bônus; tocar recomeça a jogada da entrada da área.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que fica com a sobra.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    jogador = escolher_jogador(time, PESOS_REBOTE)
    entregar_bola(partida, time_id, "ataque", random.randint(0, 2), jogador)
    registrar(
        partida, "sobra", {"jogador": rotulo(jogador), "time": time["nome"]}, tipo="oportunidade", time_id=time_id
    )
    escolha = perguntar(
        partida,
        time_id,
        f"A bola sobra para {rotulo(jogador)} na entrada da área!",
        [
            ("primeira", "Bater de primeira", 4),
            ("peito", "Matar no peito e bater", 3),
            ("lencol", "Dar um lençol no marcador", 1),
            ("tocar", "Tocar e reorganizar", 2),
        ],
    )
    if escolha == "primeira":
        finalizar(partida, time_id, jogador, "primeira", "forte", 0.02, "fechar")
        return None
    if escolha == "peito":
        if random.random() < 0.3:
            registrar(partida, "dominar_erro", {"jogador": rotulo(jogador)}, tipo="perda", time_id=time_id)
            return contra_golpe(partida, time_id, "ataque", 0.15)
        finalizar(partida, time_id, jogador, "longe", escolher_chute(partida, time_id, jogador, "longe"), 0.0, "fechar")
        return None
    if escolha == "lencol":
        marcador = marcador_de(partida, time_id, "ataque")
        dados = {"jogador": rotulo(jogador), "marcador": rotulo(marcador)}
        chance = 0.35 + (atributo_efetivo(jogador, "fis") - atributo_efetivo(marcador, "des")) * 0.005
        if random.random() < limitar(chance, 0.15, 0.6):
            registrar(partida, "lencol_ok", dados, time_id=time_id)
            finalizar(partida, time_id, jogador, "area", "colocado", 0.08, "fechar")
            return None
        registrar(partida, "lencol_erro", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.2)
    return jogar_posse(partida, time_id, portador=jogador, zona_inicial="ataque")


def erro_na_saida(partida, time_id, portador):
    """
    O adversário erra o passe na saída de bola e o atacante rouba perto da área.

    Chutar logo é uma finalização da área com bônus pequeno; avançar deixa o atacante cara a cara em 55% das
    vezes (mais com bom físico), senão o zagueiro chega no carrinho e pode fazer pênalti; tocar para o
    companheiro livre dá certo em 65% das vezes e vira uma finalização com bônus.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que roubou a bola.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Sempre None; a jogada termina no ataque.
    """
    time = partida["times"][time_id]
    errou = marcador_de(partida, time_id, "area")
    ladrao = escolher_jogador(time, PESOS_ATACANTE)
    entregar_bola(partida, time_id, "area", 1, ladrao)
    registrar(
        partida,
        "erro_saida",
        {"marcador": rotulo(errou), "jogador": rotulo(ladrao)},
        tipo="oportunidade",
        time_id=time_id,
    )
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(ladrao)} rouba a bola na saída! O que fazer?",
        [
            ("chutar", "Chutar logo", 3),
            ("avancar", "Avançar para o cara a cara", 3),
            ("tocar", "Tocar para o companheiro livre", 3),
        ],
    )
    if escolha == "chutar":
        finalizar(partida, time_id, ladrao, "area", escolher_chute(partida, time_id, ladrao, "area"), 0.02, "recuar")
    elif escolha == "avancar":
        if random.random() < 0.55 + (atributo_efetivo(ladrao, "fis") - 70) * 0.004:
            cara_a_cara(partida, time_id, ladrao, 0.03, "recuar")
            return None
        zagueiro = marcador_de(partida, time_id, "area")
        if random.random() < 0.2:
            cometer_falta(partida, time_id, "area", ladrao, zagueiro, "bote")
            if revisar_penalti(partida, time_id):
                cobrar_penalti(partida, time_id)
        else:
            registrar(partida, "carrinho_salvador", {"marcador": rotulo(zagueiro)}, tipo="defesa", time_id=time_id)
    elif random.random() < 0.65:
        companheiro = escolher_jogador(time, PESOS_REBOTE, excluir=ladrao)
        registrar(
            partida, "tocou_livre", {"jogador": rotulo(ladrao), "companheiro": rotulo(companheiro)}, time_id=time_id
        )
        finalizar(partida, time_id, companheiro, "area", "colocado", 0.06, "recuar")
    else:
        registrar(partida, "passe_cortado", {"jogador": rotulo(ladrao)}, tipo="perda", time_id=time_id)
    return None


def arrancada(partida, time_id, portador):
    """
    O jogador mais forte e técnico do meio para frente arranca com a bola dominada.

    Arrancar em velocidade compara o físico dele com o desarme do marcador (45% de base): passando, finaliza
    da área; parado, pode sofrer falta perigosa (30%). Driblar dois marcadores é mais difícil (25% de base),
    mas termina cara a cara. Soltar a bola no ponto futuro começa uma posse na entrada da área.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a bola.
        portador (dict): Jogador usado se o time não tiver meias nem atacantes em campo.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    candidatos = [j for j in time["em_campo"] if j["pos"] in ("MEI", "ATA")]
    craque = max(candidatos, key=lambda j: atributo_efetivo(j, "fis") + atributo_efetivo(j, "fin"), default=portador)
    entregar_bola(partida, time_id, "meio", 1, craque)
    registrar(partida, "arrancada", {"jogador": rotulo(craque), "time": time["nome"]}, time_id=time_id)
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(craque)} arranca com a bola dominada! E agora?",
        [
            ("velocidade", "Arrancar em velocidade", 4),
            ("driblar_dois", "Driblar dois marcadores", 2),
            ("soltar", "Soltar a bola no ponto futuro", 3),
        ],
    )
    marcador = marcador_de(partida, time_id, "ataque")
    dados = {"jogador": rotulo(craque), "marcador": rotulo(marcador)}
    if escolha == "velocidade":
        chance = 0.45 + (atributo_efetivo(craque, "fis") - atributo_efetivo(marcador, "des")) * 0.005
        if random.random() < limitar(chance, 0.2, 0.75):
            entregar_bola(partida, time_id, "area", 1, craque)
            registrar(partida, "arrancada_ok", dados, time_id=time_id)
            finalizar(
                partida, time_id, craque, "area", escolher_chute(partida, time_id, craque, "area"), 0.03, "fechar"
            )
            return None
        if random.random() < 0.3:
            cometer_falta(partida, time_id, "ataque", craque, marcador, "bote")
            cobrar_falta(partida, time_id, "fechar")
            return None
        registrar(partida, "arrancada_parada", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "meio", 0.15)
    if escolha == "driblar_dois":
        tecnica = (atributo_efetivo(craque, "fin") + atributo_efetivo(craque, "fis")) / 2
        if random.random() < limitar(0.25 + (tecnica - atributo_efetivo(marcador, "des")) * 0.005, 0.1, 0.5):
            registrar(partida, "driblou_dois", dados, tipo="oportunidade", time_id=time_id)
            cara_a_cara(partida, time_id, craque, 0.08, "fechar")
            return None
        registrar(partida, "driblar_erro", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "meio", 0.25)
    companheiro = escolher_jogador(time, PESOS_PORTADOR["ataque"], excluir=craque)
    registrar(partida, "ponto_futuro", {"jogador": rotulo(craque), "companheiro": rotulo(companheiro)}, time_id=time_id)
    return jogar_posse(partida, time_id, portador=companheiro, zona_inicial="ataque")


def pressao_na_saida(partida, time_id, portador):
    """
    O adversário tenta sair jogando de trás e o time escolhe como pressionar.

    Pressionar o goleiro rouba a bola na área em 30% das vezes, força um chutão em 15% e, no resto, a pressão
    é furada e o adversário pode sair em contra-ataque (55%). Fechar as linhas de passe recupera a bola no
    ataque em 45% das vezes. Esperar no meio deixa o adversário com a posse.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que pressiona.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque de algum dos times, quando houver.
    """
    time = partida["times"][time_id]
    adversario_id = outro(partida, time_id)
    adversario = partida["times"][adversario_id]
    goleiro = goleiro_de(adversario)
    nome_goleiro = rotulo(goleiro) if goleiro else "o zagueiro"
    mover_bola(partida, adversario_id, "saida", 1)
    registrar(partida, "pressao_saida", {"time": adversario["nome"], "goleiro": nome_goleiro}, time_id=adversario_id)
    escolha = perguntar(
        partida,
        time_id,
        f"O {adversario['nome']} quer sair jogando de trás. Como o {time['nome']} pressiona?",
        [
            ("pressionar", "Pressionar o goleiro", 3),
            ("linhas", "Fechar as linhas de passe", 3),
            ("esperar", "Esperar no meio", 2),
        ],
    )
    if escolha == "pressionar":
        sorteio = random.random()
        if sorteio < 0.3:
            ladrao = escolher_jogador(time, PESOS_ATACANTE)
            entregar_bola(partida, time_id, "area", 1, ladrao)
            registrar(
                partida,
                "roubou_na_saida",
                {"jogador": rotulo(ladrao), "goleiro": nome_goleiro},
                tipo="oportunidade",
                time_id=time_id,
            )
            finalizar(partida, time_id, ladrao, "area", "colocado", 0.06, "recuar")
            return None
        if sorteio < 0.45:
            registrar(partida, "chutao", {"goleiro": nome_goleiro}, time_id=adversario_id)
            return None
        registrar(partida, "pressao_furada", {"time": adversario["nome"]}, tipo="perda", time_id=adversario_id)
        return contra_golpe(partida, time_id, "meio", 0.55)
    if escolha == "linhas":
        if random.random() < 0.45:
            jogador = escolher_jogador(time, PESOS_PORTADOR["ataque"])
            registrar(partida, "recuperou_alto", {"jogador": rotulo(jogador), "time": time["nome"]}, time_id=time_id)
            return jogar_posse(partida, time_id, portador=jogador, zona_inicial="ataque")
        registrar(partida, "adversario_escapa", {"time": adversario["nome"]}, time_id=adversario_id)
        return None
    registrar(partida, "time_espera", {"time": time["nome"]}, time_id=time_id)
    return jogar_posse(partida, adversario_id)


def escanteio_conquistado(partida, time_id, portador):
    """
    O ataque força um escanteio logo de cara.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que ganhou o escanteio.
        portador (dict): Jogador que forçou o escanteio.

    Returns:
        tuple | None: Sempre None; a jogada termina na cobrança.
    """
    registrar(
        partida,
        "escanteio_conquistado",
        {"jogador": rotulo(portador), "time": partida["times"][time_id]["nome"]},
        time_id=time_id,
    )
    cobrar_escanteio(partida, time_id, "fechar")
    return None


def bola_alta(partida, time_id, portador):
    """
    Uma bola longa chega pelo alto e o jogador escolhe como dominar.

    Ganhar de cabeça depende do físico contra o do marcador (50% de base) e leva a posse para a entrada da
    área; dominar no peito depende do passe (60% de base) e mantém a posse no meio; deixar quicar é cara ou
    coroa.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que disputa a bola.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque de algum dos times, quando houver.
    """
    time = partida["times"][time_id]
    jogador = escolher_jogador(time, {"ATA": 4, "MEI": 3, "DEF": 2})
    marcador = marcador_de(partida, time_id, "meio")
    dados = {"jogador": rotulo(jogador), "marcador": rotulo(marcador)}
    entregar_bola(partida, time_id, "meio", random.randint(0, 2), jogador)
    registrar(partida, "bola_alta", dados, time_id=time_id)
    escolha = perguntar(
        partida,
        time_id,
        f"A bola vem pelo alto para {rotulo(jogador)}. Como dominar?",
        [("cabeca", "Ganhar de cabeça e escorar", 3), ("peito", "Dominar no peito", 3), ("deixar", "Deixar quicar", 1)],
    )
    if escolha == "cabeca":
        chance = 0.5 + (atributo_efetivo(jogador, "fis") - atributo_efetivo(marcador, "fis")) * 0.006
        if random.random() < limitar(chance, 0.2, 0.8):
            registrar(partida, "escorou_alto", dados, time_id=time_id)
            return jogar_posse(partida, time_id, zona_inicial="ataque")
        registrar(partida, "perdeu_alto", dados, tipo="perda", time_id=time_id)
        return None
    if escolha == "peito":
        if random.random() < 0.6 + (atributo_efetivo(jogador, "pas") - 70) * 0.004:
            registrar(partida, "dominou_alto", dados, time_id=time_id)
            return jogar_posse(partida, time_id, portador=jogador, zona_inicial="meio")
        registrar(partida, "dominar_erro", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "meio", 0.1)
    if random.random() < 0.5:
        registrar(partida, "quicou_bem", dados, time_id=time_id)
        return jogar_posse(partida, time_id, portador=jogador, zona_inicial="meio")
    registrar(partida, "quicou_mal", dados, tipo="perda", time_id=time_id)
    return None


def reclamacao(partida):
    """
    Um jogador reclama demais com o árbitro e leva amarelo.

    Args:
        partida (dict): Estado da partida.
    """
    time_id = random.choice((partida["casa"], partida["fora"]))
    jogador = escolher_jogador(partida["times"][time_id], {"DEF": 2, "MEI": 2, "ATA": 2})
    registrar(partida, "reclamacao", {"jogador": rotulo(jogador)}, tipo="falta", time_id=time_id)
    amarelar(partida, time_id, jogador)


def confusao(partida):
    """
    Começa um empurra-empurra entre os jogadores; cada time tem 40% de chance de levar um amarelo.

    Args:
        partida (dict): Estado da partida.
    """
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    registrar(partida, "confusao", {"time_casa": casa["nome"], "time_fora": fora["nome"]}, tipo="falta")
    for time_id in (partida["casa"], partida["fora"]):
        if random.random() < 0.4:
            jogador = escolher_jogador(partida["times"][time_id], {"DEF": 3, "MEI": 2, "ATA": 2})
            amarelar(partida, time_id, jogador)


def paralisacao(partida):
    """
    O jogo para por alguns minutos, e o árbitro aumenta os acréscimos em 1 ou 2 minutos.

    Args:
        partida (dict): Estado da partida.
    """
    registrar(partida, "paralisacao", tipo="evento")
    partida["limite"] = partida.get("limite", 45) + random.randint(1, 2)


def chuva_comeca(partida):
    """
    Começa a chover durante o jogo, o que deixa passes e cruzamentos mais difíceis dali em diante.

    Args:
        partida (dict): Estado da partida.
    """
    if partida["chuva"]:
        return
    partida["chuva"] = True
    registrar(partida, "chuva_comeca", tipo="evento")


def beira_do_campo(partida):
    """
    Narra algo que acontece fora das quatro linhas, sem efeito no jogo.

    Args:
        partida (dict): Estado da partida.
    """
    time_id = random.choice((partida["casa"], partida["fora"]))
    registrar(partida, "beira_do_campo", {"time": partida["times"][time_id]["nome"]}, tipo="evento", time_id=time_id)


FUNCOES_JOGADAS = {
    "tiro_de_meta": tiro_de_meta,
    "lateral_no_ataque": lateral_no_ataque,
    "superioridade": superioridade,
    "falta_lateral": falta_lateral,
    "falta_de_longe": falta_de_longe,
    "sobra_na_entrada": sobra_na_entrada,
    "erro_na_saida": erro_na_saida,
    "arrancada": arrancada,
    "pressao_na_saida": pressao_na_saida,
    "escanteio_conquistado": escanteio_conquistado,
    "bola_alta": bola_alta,
}
FUNCOES_ACONTECIMENTOS = {
    "reclamacao": reclamacao,
    "confusao": confusao,
    "paralisacao": paralisacao,
    "chuva_comeca": chuva_comeca,
    "beira_do_campo": beira_do_campo,
}


def jogada_especial(partida, time_id, portador):
    """
    Sorteia e joga uma das jogadas especiais para o time que ganhou a bola.

    A jogada é sorteada com os pesos de PESOS_JOGADAS e executada pela função correspondente em
    FUNCOES_JOGADAS.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que ganhou a bola.
        portador (dict): Jogador que ganhou a bola.

    Returns:
        tuple | None: Contra-ataque de algum dos times, quando houver, como em jogar_posse.
    """
    tipo = random.choices(list(PESOS_JOGADAS), weights=list(PESOS_JOGADAS.values()))[0]
    return FUNCOES_JOGADAS[tipo](partida, time_id, portador)


def sortear_acontecimento(partida):
    """
    Sorteia no máximo um acontecimento extra antes do lance, como reclamação, confusão ou paralisação.

    Cada acontecimento tem a sua chance em CHANCES_ACONTECIMENTOS; o primeiro sorteado é executado.

    Args:
        partida (dict): Estado da partida.
    """
    for tipo, chance in CHANCES_ACONTECIMENTOS.items():
        if random.random() < chance:
            FUNCOES_ACONTECIMENTOS[tipo](partida)
            return
