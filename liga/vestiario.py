import random

from config import CHANCE_DISCUSSAO, CHANCE_DISCUSSAO_ELENCO, MULTA_DISCUSSAO
from elenco.escalacao import disponivel, rotulo
from liga.financas import lancar
from liga.temporada import ajustar_confianca, clube_do_jogador, gols_do_clube
from mercado.transferencias import dinheiro


def titulares_do_clube(clube):
    """
    Lista os titulares que ainda estão no elenco do clube.

    Args:
        clube (dict): Clube do técnico.

    Returns:
        list[dict]: Jogadores titulares.
    """
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    return [por_id[i] for i in clube["titulares"] if i in por_id]


def lider_do_elenco(clube, excluir=None):
    """
    Escolhe o líder do elenco: o titular de maior qualidade, sem contar quem foi excluído.

    Args:
        clube (dict): Clube do técnico.
        excluir (dict | None): Jogador que não pode ser escolhido. Padrão None.

    Returns:
        dict | None: Jogador escolhido, ou None se não houver ninguém.
    """
    candidatos = [jogador for jogador in titulares_do_clube(clube) if jogador is not excluir]
    return max(candidatos, key=lambda jogador: jogador["qualidade"], default=None)


def ocorrencias_do_clube(resultado, clube_id, tipo):
    """
    Filtra as ocorrências de um tipo que envolvem o clube no jogo.

    Args:
        resultado (dict | None): Resultado da partida do técnico.
        clube_id (str): Clube do técnico.
        tipo (str): Tipo da ocorrência, como "vermelho", "gol" ou "penalti_perdido".

    Returns:
        list[str]: Identificadores dos jogadores envolvidos.
    """
    if not resultado:
        return []
    return [o["jogador"] for o in resultado.get("ocorrencias", []) if o["tipo"] == tipo and o["time"] == clube_id]


def gatilhos_do_jogo(estado, resultado):
    """
    Procura no último jogo motivos para uma discussão entre jogadores.

    Pênalti perdido faz o melhor finalizador reclamar com o batedor; expulsão sem vitória faz o líder cobrar o
    expulso; goleada sofrida (3 gols de diferença ou mais) esquenta o vestiário; e uma vitória com gols de
    dois jogadores diferentes vira, em 35% das vezes, disputa de quem é o dono das bolas paradas.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict | None): Resultado da partida do técnico.

    Returns:
        list[dict]: Discussões possíveis, cada uma com tipo, os dois jogadores e o texto.
    """
    clube = clube_do_jogador(estado)
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    if not resultado:
        return []
    marcados, sofridos = gols_do_clube(clube["id"], resultado)
    gatilhos = []
    for batedor_id in ocorrencias_do_clube(resultado, clube["id"], "penalti_perdido")[:1]:
        batedor = por_id.get(batedor_id)
        outros = [j for j in titulares_do_clube(clube) if j is not batedor and j["pos"] != "GOL"]
        rival = max(outros, key=lambda j: j["fin"], default=None)
        if batedor and rival:
            texto = (
                f"No vestiário, {rotulo(rival)} disse que deveria ter batido o pênalti que {rotulo(batedor)} "
                "perdeu. Os dois discutiram feio."
            )
            gatilhos.append({"tipo": "penalti", "a": batedor, "b": rival, "texto": texto})
    for expulso_id in ocorrencias_do_clube(resultado, clube["id"], "vermelho")[:1]:
        expulso = por_id.get(expulso_id)
        lider = lider_do_elenco(clube, excluir=expulso)
        if expulso and lider and marcados <= sofridos:
            texto = f"{rotulo(lider)} cobrou {rotulo(expulso)} pela expulsão que complicou o jogo. O clima pesou."
            gatilhos.append({"tipo": "expulsao", "a": expulso, "b": lider, "texto": texto})
    if sofridos - marcados >= 3:
        lider = lider_do_elenco(clube)
        outros = [j for j in titulares_do_clube(clube) if j is not lider]
        if lider and outros:
            alvo = random.choice(outros)
            texto = (
                f"Depois da goleada, {rotulo(lider)} e {rotulo(alvo)} trocaram acusações no vestiário. "
                "Cada um culpa o outro pela derrota."
            )
            gatilhos.append({"tipo": "goleada", "a": alvo, "b": lider, "texto": texto})
    autores = list(dict.fromkeys(ocorrencias_do_clube(resultado, clube["id"], "gol")))
    vaidade = random.random() < 0.35
    if vaidade and marcados > sofridos and len(autores) >= 2 and autores[0] in por_id and autores[1] in por_id:
        a, b = por_id[autores[0]], por_id[autores[1]]
        texto = (
            f"Mesmo com a vitória, {rotulo(a)} e {rotulo(b)} discutiram no treino sobre quem é o dono das cobranças "
            "de falta e de pênalti."
        )
        gatilhos.append({"tipo": "vaidade", "a": a, "b": b, "texto": texto})
    return gatilhos


def gatilhos_do_elenco(estado):
    """
    Procura no elenco motivos para uma discussão que não dependem do último jogo.

    Um reserva disponível que é quase tão bom quanto um titular da mesma posição (no máximo 1 ponto abaixo,
    com qualidade 60 ou mais) briga pela vaga. A partir da quinta etapa, um atacante titular sem gols pode ser
    provocado pelo reserva da posição.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        list[dict]: Discussões possíveis, cada uma com tipo, os dois jogadores, o texto e se o reserva pode
            virar titular.
    """
    clube = clube_do_jogador(estado)
    titulares = titulares_do_clube(clube)
    reservas = [j for j in clube["elenco"] if j["id"] not in clube["titulares"] and disponivel(j)]
    gatilhos = []
    for reserva in reservas:
        rivais = [t for t in titulares if t["pos"] == reserva["pos"] and reserva["qualidade"] >= t["qualidade"] - 1]
        if rivais and reserva["qualidade"] >= 60:
            titular = min(rivais, key=lambda j: j["qualidade"])
            texto = (
                f"{rotulo(reserva)} acha que merece a vaga de {rotulo(titular)} e os dois bateram boca no treino. "
                "O elenco espera a sua decisão."
            )
            gatilhos.append({"tipo": "posicao", "a": titular, "b": reserva, "texto": texto, "troca": True})
            break
    if estado["etapa"] >= 4:
        secos = [t for t in titulares if t["pos"] == "ATA" and t["gols"] == 0]
        reservas_ata = [r for r in reservas if r["pos"] == "ATA"]
        if secos and reservas_ata:
            titular, reserva = secos[0], max(reservas_ata, key=lambda j: j["qualidade"])
            texto = (
                f'{rotulo(reserva)} provocou {rotulo(titular)} no treino: "quem não faz gol tem que dar lugar a '
                'quem faz". A conversa terminou em empurrão.'
            )
            gatilhos.append({"tipo": "seca", "a": titular, "b": reserva, "texto": texto, "troca": True})
    return gatilhos


def sortear_discussao(estado, resultado):
    """
    Decide se há uma discussão entre jogadores nesta semana e monta a tela dela.

    Os motivos ligados ao último jogo têm prioridade e geram discussão com CHANCE_DISCUSSAO (55%); sem eles,
    os motivos do elenco geram discussão com CHANCE_DISCUSSAO_ELENCO (20%). As opções são ficar do lado de
    cada jogador, reunir o grupo ou multar os dois; numa briga por posição, ficar do lado do reserva também dá
    a vaga a ele.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict | None): Resultado da partida do técnico, ou None se ele não jogou.

    Returns:
        dict | None: Discussão no formato de evento (texto, opções e jogadores), ou None.
    """
    gatilhos = gatilhos_do_jogo(estado, resultado)
    chance = CHANCE_DISCUSSAO
    if not gatilhos:
        gatilhos = gatilhos_do_elenco(estado)
        chance = CHANCE_DISCUSSAO_ELENCO
    if not gatilhos or random.random() >= chance:
        return None
    escolhido = random.choice(gatilhos)
    a, b = escolhido["a"], escolhido["b"]
    lado_b = f"Ficar do lado de {rotulo(b)}" + (" e dar a vaga a ele" if escolhido.get("troca") else "")
    return {
        "id": "discussao",
        "tipo": escolhido["tipo"],
        "texto": escolhido["texto"],
        "jogador_id": a["id"],
        "outro_id": b["id"],
        "troca": escolhido.get("troca", False),
        "efeito": None,
        "negociacao": None,
        "opcoes": [
            {"texto": f"Ficar do lado de {rotulo(a)}", "efeito": "lado_a"},
            {"texto": lado_b, "efeito": "lado_b"},
            {"texto": "Reunir o grupo e pedir união", "efeito": "unir"},
            {"texto": f"Multar os dois ({dinheiro(MULTA_DISCUSSAO)} para o clube)", "efeito": "multar"},
        ],
    }


def resolver_discussao(estado, discussao, efeito):
    """
    Aplica a decisão do técnico sobre uma discussão entre jogadores.

    Quem recebe apoio fica motivado por 1 rodada e o outro fica insatisfeito por 2; numa briga por posição, o
    reserva apoiado assume a vaga do titular. Reunir o grupo dá certo em 60% das vezes (os dois motivados e
    confiança +1); se não der, os dois ficam insatisfeitos por 1 rodada. Multar rende MULTA_DISCUSSAO ao caixa
    e 2 de confiança, mas deixa os dois insatisfeitos por 1 rodada.

    Args:
        estado (dict): Estado atual da temporada.
        discussao (dict): Discussão montada por sortear_discussao.
        efeito (str): Opção escolhida: "lado_a", "lado_b", "unir" ou "multar".

    Returns:
        str: Mensagem descrevendo o que mudou.
    """
    clube = clube_do_jogador(estado)
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    a, b = por_id.get(discussao["jogador_id"]), por_id.get(discussao["outro_id"])
    if not a or not b:
        return "Os dois já não estão no elenco. Nada mudou."
    if efeito in ("lado_a", "lado_b"):
        apoiado, contrariado = (a, b) if efeito == "lado_a" else (b, a)
        apoiado["fase"] = max(apoiado["fase"], 1)
        contrariado["insatisfeito"] = max(contrariado.get("insatisfeito", 0), 2)
        texto = f"{rotulo(apoiado)} se sente prestigiado. {rotulo(contrariado)} fica insatisfeito por 2 rodadas."
        if efeito == "lado_b" and discussao.get("troca") and a["id"] in clube["titulares"]:
            clube["titulares"][clube["titulares"].index(a["id"])] = b["id"]
            texto += f" {rotulo(b)} assume a vaga de titular."
        return texto
    if efeito == "unir":
        if random.random() < 0.6:
            for jogador in (a, b):
                jogador["fase"] = max(jogador["fase"], 1)
            ajustar_confianca(estado, 1)
            return f"A conversa funcionou: {rotulo(a)} e {rotulo(b)} se acertam e chegam motivados. Confiança +1."
        for jogador in (a, b):
            jogador["insatisfeito"] = max(jogador.get("insatisfeito", 0), 1)
        return f"A reunião não resolveu: {rotulo(a)} e {rotulo(b)} seguem de cara fechada na próxima rodada."
    lancar(estado, clube["id"], "Multas aplicadas", MULTA_DISCUSSAO)
    ajustar_confianca(estado, 2)
    for jogador in (a, b):
        jogador["insatisfeito"] = max(jogador.get("insatisfeito", 0), 1)
    return (
        f"Os dois são multados ({dinheiro(MULTA_DISCUSSAO)} para o clube). A diretoria aprova a disciplina "
        "(confiança +2), mas eles ficam insatisfeitos na próxima rodada."
    )
