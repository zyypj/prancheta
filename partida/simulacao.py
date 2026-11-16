import random

from elenco.escalacao import limitar, rotulo
from elenco.substituicoes import melhor_substituto, pode_substituir
from partida.jogo import jogar_partida
from partida.lances import CANTOS, FORCAS_PENALTI, criar_partida, fazer_substituicao, goleiro_de

SUBSTITUICOES_IA = 3


def escolher_ponderado(pesos):
    """
    Sorteia uma opção de acordo com os pesos informados.

    Pesos menores que 0,1, inclusive negativos, são tratados como 0,1, para que nenhuma opção fique
    impossível.

    Args:
        pesos (dict): Dicionário que associa cada opção ao seu peso.

    Returns:
        str: Opção sorteada.
    """
    opcoes = list(pesos)
    return random.choices(opcoes, weights=[max(0.1, pesos[opcao]) for opcao in opcoes])[0]


def ia_ataque(partida, time_id, zona, portador):
    """
    Decide a ação da inteligência artificial quando o time está com a bola.

    Sorteia a ação com pesos que dependem da zona e da ofensividade do plano. No campo de defesa, o time mais
    ofensivo conduz e lança mais; no meio-campo e na intermediária, enfia, dribla e lança mais, e toca menos;
    o estilo "jogo direto" aumenta o peso do lançamento. No ataque, o cruzamento fica bem mais provável quando
    a bola está pela ponta; na linha de fundo, o time cruza alto ou rasteiro para trás. Na área, o chute é a
    ação mais provável.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time que ataca.
        zona (str): Zona do campo onde está a bola, uma das chaves de ACOES.
        portador (dict): Jogador com a bola, não usado pela inteligência artificial.

    Returns:
        str: Ação escolhida. No meio-campo: "tocar", "enfiar", "driblar", "lancar" ou "abrir". No ataque:
            "tocar", "tabelar", "driblar", "cruzar" ou "chutar". Na área: "chutar", "driblar" ou "tocar".
    """
    plano = partida["times"][time_id]["plano"]
    ofensividade = plano["ofensividade"]
    direto = 2.5 if plano["estilo"] == "jogo direto" else 0
    if zona == "defesa":
        return escolher_ponderado(
            {
                "tocar": 6 - 0.5 * ofensividade,
                "conduzir": 1 + 0.3 * ofensividade,
                "lancar": 0.5 + 0.4 * ofensividade + direto,
                "inverter": 1.5,
            }
        )
    if zona == "intermediaria":
        return escolher_ponderado(
            {
                "tocar": 5 - 0.5 * ofensividade,
                "enfiar": 0.5 + 0.3 * ofensividade,
                "driblar": 0.5 * ofensividade,
                "abrir": 2,
                "chutar": 0.3 * ofensividade,
            }
        )
    if zona == "linha_de_fundo":
        return escolher_ponderado({"cruzar": 4, "rasteiro": 2.5, "driblar": 0.4 * ofensividade, "chutar": 0.3})
    if zona == "meio":
        return escolher_ponderado(
            {
                "tocar": 7 - ofensividade,
                "enfiar": 0.4 + 0.3 * ofensividade,
                "driblar": 0.6 * ofensividade,
                "lancar": 0.5 + 0.4 * ofensividade + direto,
                "abrir": 2,
            }
        )
    if zona == "ataque":
        na_ponta = partida["bola"]["faixa"] != 1
        return escolher_ponderado(
            {
                "tocar": 4.5 - ofensividade,
                "tabelar": 1.5,
                "driblar": 0.5 * ofensividade,
                "cruzar": 3.5 if na_ponta else 1,
                "chutar": 0.6 * ofensividade,
            }
        )
    return escolher_ponderado({"chutar": 2.5 + 0.6 * ofensividade, "driblar": 0.6 * ofensividade, "tocar": 1.2})


def ia_defesa(partida, time_id):
    """
    Decide a postura defensiva da inteligência artificial quando o adversário está com a bola.

    Sorteia a postura com pesos que dependem do plano: a intensidade aumenta o peso do bote e da pressão,
    ofensividade 4 ou mais também favorece a pressão, e quanto menor a ofensividade, mais o time recua. Fechar
    espaços tem peso fixo e a falta é rara.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time que defende.

    Returns:
        str: Postura escolhida: "bote", "pressao", "fechar", "recuar" ou "falta".
    """
    plano = partida["times"][time_id]["plano"]
    return escolher_ponderado(
        {
            "bote": plano["intensidade"],
            "pressao": 0.5 * plano["intensidade"] + (1 if plano["ofensividade"] >= 4 else 0),
            "fechar": 3,
            "recuar": 5 - plano["ofensividade"],
            "falta": 0.3,
        }
    )


def ia_escolha(partida, time_id, pergunta, opcoes):
    """
    Responde pela inteligência artificial a uma decisão de lance.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time que decide.
        pergunta (str): Texto da decisão, não usado pela inteligência artificial.
        opcoes (list[tuple]): Opções no formato (chave, texto, peso) ou (chave, texto, peso, chance).

    Returns:
        str: Chave da opção sorteada, com chance proporcional ao peso.
    """
    return random.choices([opcao[0] for opcao in opcoes], weights=[opcao[2] for opcao in opcoes])[0]


def ia_bater_penalti(partida, time_id, batedor, goleiro):
    """
    Escolhe pela inteligência artificial o canto e a força de uma cobrança de pênalti.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time que cobra.
        batedor (dict): Jogador que cobra, não usado pela inteligência artificial.
        goleiro (dict): Goleiro adversário, não usado pela inteligência artificial.

    Returns:
        tuple: Par (canto, força). O canto é "esquerda" ou "direita" com 42% de chance cada e "meio" com 16%;
            a força é "colocado" ou "forte", com a mesma chance.
    """
    return random.choices(CANTOS, weights=(0.42, 0.16, 0.42))[0], random.choices(
        FORCAS_PENALTI, weights=(0.45, 0.35, 0.2)
    )[0]


def ia_defender_penalti(partida, time_id, batedor, goleiro):
    """
    Escolhe pela inteligência artificial o canto para onde o goleiro pula no pênalti.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time que defende.
        batedor (dict): Jogador que cobra, não usado pela inteligência artificial.
        goleiro (dict): Goleiro que defende, não usado pela inteligência artificial.

    Returns:
        str: Canto escolhido: "esquerda" ou "direita" com 45% de chance cada, e "meio" com 10%.
    """
    return random.choices(CANTOS, weights=(0.45, 0.10, 0.45))[0]


def ia_lesao(partida, time_id, lesionado):
    """
    Repõe pela inteligência artificial um jogador que deixou o campo machucado.

    Se o time ainda puder substituir, coloca em campo o melhor reserva para a posição do lesionado,
    registrando a troca com o nome dele. Sem reserva adequado ou sem substituições, o time segue com um a
    menos.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time que perdeu o jogador.
        lesionado (dict): Jogador que saiu de campo.
    """
    time = partida["times"][time_id]
    if pode_substituir(time):
        entra = melhor_substituto(time, lesionado["pos"])
        if entra:
            fazer_substituicao(partida, time_id, None, entra["id"], rotulo(lesionado))


def ajustar_ofensividade(partida, time_id):
    """
    Ajusta a ofensividade do time conforme o placar.

    Partindo da ofensividade original do plano, o time que está perdendo sobe um nível, até no máximo 5. O que
    está ganhando a partir dos 75 minutos desce um nível, até no mínimo 1. Nos demais casos, volta à
    ofensividade original.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time ajustado.
    """
    time = partida["times"][time_id]
    adversario = partida["times"][partida["fora"] if time_id == partida["casa"] else partida["casa"]]
    diferenca = time["gols"] - adversario["gols"]
    base = time["ofensividade_base"]
    if diferenca < 0:
        time["plano"]["ofensividade"] = min(5, base + 1)
    elif diferenca > 0 and partida["minuto"] >= 75:
        time["plano"]["ofensividade"] = max(1, base - 1)
    else:
        time["plano"]["ofensividade"] = base


def trocar_cansados(partida, time_id, limite_energia, quantidade):
    """
    Substitui os jogadores de linha mais cansados do time.

    Seleciona os jogadores de linha com energia abaixo do limite, do mais cansado para o menos, e troca até a
    quantidade pedida pelo melhor reserva de cada posição. Para antes se o time atingir o limite de
    substituições da inteligência artificial ou não puder mais substituir.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time.
        limite_energia (float): Energia abaixo da qual o jogador é considerado cansado.
        quantidade (int): Número máximo de jogadores a avaliar para troca.
    """
    time = partida["times"][time_id]
    cansados = sorted(
        [j for j in time["em_campo"] if j["pos"] != "GOL" and j["energia"] < limite_energia], key=lambda j: j["energia"]
    )
    for jogador in cansados[:quantidade]:
        if time["subs"] >= SUBSTITUICOES_IA or not pode_substituir(time):
            return
        entra = melhor_substituto(time, jogador["pos"])
        if entra:
            fazer_substituicao(partida, time_id, jogador["id"], entra["id"])


def ia_pausa(partida, time_id, motivo):
    """
    Toma as decisões da inteligência artificial numa pausa da partida.

    Após uma expulsão que deixou o time sem goleiro, se ainda puder substituir e houver goleiro no banco, tira
    o jogador de linha de menor qualidade e coloca o goleiro reserva. No intervalo, troca até dois jogadores
    com energia abaixo de 60 e ajusta a ofensividade conforme o placar.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time.
        motivo (str): Motivo da pausa ("expulsao" ou "intervalo").
    """
    time = partida["times"][time_id]
    if motivo == "expulsao" and goleiro_de(time) is None and pode_substituir(time):
        reserva = next((j for j in time["banco"] if j["pos"] == "GOL"), None)
        linha = [j for j in time["em_campo"] if j["pos"] != "GOL"]
        if reserva and linha:
            fazer_substituicao(partida, time_id, min(linha, key=lambda j: j["qualidade"])["id"], reserva["id"])
    if motivo == "intervalo":
        trocar_cansados(partida, time_id, 60, 2)
        ajustar_ofensividade(partida, time_id)


def ia_ajuste(partida, time_id):
    """
    Faz os ajustes da inteligência artificial a cada lance.

    A partir dos 60 minutos, troca um jogador com energia abaixo de 45, se houver. A partir dos 70 minutos,
    ajusta a ofensividade conforme o placar.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time.
    """
    if partida["minuto"] >= 60:
        trocar_cansados(partida, time_id, 45, 1)
    if partida["minuto"] >= 70:
        ajustar_ofensividade(partida, time_id)


def ia_minijogo(partida, time_id, tipo, detalhe):
    """
    Responde pela inteligência artificial ao convite de minijogo, que só existe para o jogador humano.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do time.
        tipo (str): Tipo de minijogo.
        detalhe (str | None): Detalhe da jogada.

    Returns:
        float: Sempre 0.0, sem efeito na jogada.
    """
    return 0.0


CONTROLE_IA = {
    "ataque": ia_ataque,
    "defesa": ia_defesa,
    "escolha": ia_escolha,
    "bater_penalti": ia_bater_penalti,
    "defender_penalti": ia_defender_penalti,
    "lesao": ia_lesao,
    "pausa": ia_pausa,
    "ajuste": ia_ajuste,
    "minijogo": ia_minijogo,
}


def plano_ia(clube, adversario, em_casa):
    """
    Monta o plano tático de um clube controlado pela inteligência artificial.

    Copia o plano do clube e ajusta a ofensividade: sobe um nível jogando em casa e outro se a força do clube
    superar a do adversário em mais de 8 pontos, e desce um nível se for mais fraco por mais de 8. O resultado
    fica entre 1 e 5.

    Args:
        clube (dict): Clube que receberá o plano.
        adversario (dict): Clube adversário.
        em_casa (bool): Se o clube joga com mando de campo.

    Returns:
        dict: Cópia do plano do clube com a ofensividade ajustada.
    """
    plano = dict(clube["plano"])
    diferenca = clube["forca"] - adversario["forca"]
    ofensividade = (
        plano["ofensividade"] + (1 if em_casa else 0) + (1 if diferenca > 8 else 0) - (1 if diferenca < -8 else 0)
    )
    plano["ofensividade"] = int(limitar(ofensividade, 1, 5))
    return plano


def simular_partida(clube_casa, clube_fora, frases, neutro=False, mata_mata=False):
    """
    Simula uma partida inteira entre dois clubes controlados pela inteligência artificial.

    Monta os planos dos dois clubes, considerando o mandante como time da casa apenas se o jogo não for em
    campo neutro, cria a partida e a joga até o fim com os controles da inteligência artificial para os dois
    lados.

    Args:
        clube_casa (dict): Clube mandante.
        clube_fora (dict): Clube visitante.
        frases (dict): Frases de narração agrupadas por chave.
        neutro (bool): Se o jogo é em campo neutro. Padrão False.
        mata_mata (bool): Se a partida é de mata-mata, com disputa de pênaltis em caso de empate. Padrão
            False.

    Returns:
        dict: Resultado da partida, com mandante, visitante, placar, cartões vermelhos, vencedor, pênaltis,
            súmula e estatísticas.
    """
    partida = criar_partida(
        clube_casa,
        clube_fora,
        frases,
        plano_ia(clube_casa, clube_fora, not neutro),
        plano_ia(clube_fora, clube_casa, False),
        neutro,
    )
    return jogar_partida(partida, {clube_casa["id"]: CONTROLE_IA, clube_fora["id"]: CONTROLE_IA}, mata_mata=mata_mata)
