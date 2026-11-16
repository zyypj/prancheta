import random

from config import (
    CLUBES_DO_EXTERIOR,
    CONFIANCA_NEGOCIACAO_FRACASSADA,
    CONFIANCA_SEGURAR,
    CONFIANCA_VENDA,
    FAIXA_OFERTA_EXTERIOR,
    FAIXA_TETO_EXTERIOR,
    QUEDA_QUALIDADE_GAROTO,
)
from elenco.escalacao import criar_jogador, limitar, rotulo, sortear_nome, valor_de_mercado, valor_para_escalar
from liga.financas import lancar, vitorias_recentes
from liga.temporada import ajustar_confianca, clube_do_jogador
from mercado.transferencias import dinheiro


def sortear_evento(eventos):
    """
    Sorteia um evento da semana, respeitando o peso de cada um.

    Args:
        eventos (list[dict]): Eventos disponíveis, cada um com o campo "peso".

    Returns:
        dict: Evento sorteado.
    """
    return random.choices(eventos, weights=[evento["peso"] for evento in eventos])[0]


def escolher_alvo(clube, alvo):
    """
    Escolhe o jogador envolvido em um evento.

    Com o alvo "titular", sorteia um dos titulares que ainda estão no elenco; com o alvo "melhor", pega o
    jogador de linha (sem goleiros) de maior qualidade; com o alvo "jovem", pega o reserva de linha de até 21
    anos de maior qualidade. Qualquer outro alvo não envolve jogador.

    Args:
        clube (dict): Clube do jogador.
        alvo (str): Tipo de alvo do evento ("titular", "melhor", "jovem" ou outro valor).

    Returns:
        dict | None: Jogador escolhido ou None se não houver alvo ou candidato.
    """
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    if alvo == "titular":
        candidatos = [por_id[identificador] for identificador in clube["titulares"] if identificador in por_id]
        return random.choice(candidatos) if candidatos else None
    if alvo == "melhor":
        linha = [jogador for jogador in clube["elenco"] if jogador["pos"] != "GOL"]
        return max(linha, key=lambda jogador: jogador["qualidade"]) if linha else None
    if alvo == "jovem":
        jovens = [
            jogador
            for jogador in clube["elenco"]
            if jogador.get("idade", 30) <= 21 and jogador["id"] not in clube["titulares"] and jogador["pos"] != "GOL"
        ]
        return max(jovens, key=lambda jogador: jogador["qualidade"]) if jovens else None
    return None


def escolher_evento(eventos, clube, recentes=()):
    """
    Sorteia e prepara o evento da semana, garantindo que o jogador alvo exista.

    Eventos que aconteceram nas últimas semanas (recentes) e eventos que precisam de um jogador (alvo
    diferente de "nenhum") quando o clube não tem ninguém que sirva são sorteados de novo, até 10 tentativas;
    depois disso, a semana fica tranquila.

    Args:
        eventos (list[dict]): Eventos lidos de eventos.json.
        clube (dict): Clube do técnico.
        recentes (Iterable[str]): Identificadores dos eventos das últimas semanas. Padrão vazio.

    Returns:
        dict: Evento preparado, como em preparar_evento.
    """
    for _ in range(10):
        evento = sortear_evento(eventos)
        if evento["id"] in recentes:
            continue
        preparado = preparar_evento(evento, clube)
        if evento.get("alvo", "nenhum") == "nenhum" or preparado["jogador_id"]:
            return preparado
    tranquila = next(evento for evento in eventos if evento["id"] == "tranquila")
    return preparar_evento(tranquila, clube)


def preparar_evento(evento, clube):
    """
    Monta o evento que será mostrado ao jogador.

    Escolhe o jogador alvo e troca a marcação {jogador} pelo nome dele, com a posição, no texto do evento e no
    texto de cada opção.

    Args:
        evento (dict): Evento sorteado, como lido de eventos.json.
        clube (dict): Clube do jogador.

    Returns:
        dict: Evento com identificador, texto pronto, identificador do jogador alvo (ou None), efeito direto e
            opções de escolha.
    """
    jogador = escolher_alvo(clube, evento.get("alvo", "nenhum"))
    nome = rotulo(jogador) if jogador else ""
    opcoes = evento.get("opcoes", [])
    vende = jogador is not None and any(opcao["efeito"] == "vender" for opcao in opcoes)
    return {
        "id": evento["id"],
        "texto": evento["texto"].replace("{jogador}", nome),
        "jogador_id": jogador["id"] if jogador else None,
        "efeito": evento.get("efeito"),
        "opcoes": [{"texto": opcao["texto"].replace("{jogador}", nome), "efeito": opcao["efeito"]} for opcao in opcoes],
        "negociacao": criar_negociacao(jogador) if vende else None,
    }


def criar_negociacao(jogador):
    """
    Cria a proposta de um clube do exterior por um jogador.

    O clube interessado é sorteado em CLUBES_DO_EXTERIOR. A primeira oferta fica entre 110% e 140% do valor de
    mercado (FAIXA_OFERTA_EXTERIOR), e o teto, o máximo que o clube aceita pagar, fica entre 100% e 130% da
    primeira oferta (FAIXA_TETO_EXTERIOR). O teto não aparece na tela: o técnico só descobre pedindo mais, e
    às vezes a primeira oferta já é a última.

    Args:
        jogador (dict): Jogador que recebeu a proposta.

    Returns:
        dict: Negociação com clube interessado, valor de mercado, oferta atual, teto, número de
            contrapropostas e valor acertado (None enquanto não há acordo).
    """
    valor = valor_de_mercado(jogador)
    oferta = round(max(valor, 0.5) * random.uniform(*FAIXA_OFERTA_EXTERIOR), 1)
    return {
        "clube": random.choice(CLUBES_DO_EXTERIOR),
        "valor": valor,
        "oferta": oferta,
        "teto": round(oferta * random.uniform(*FAIXA_TETO_EXTERIOR), 1),
        "contrapropostas": 0,
        "acordo": None,
    }


def aceitar_oferta(negociacao):
    """
    Fecha a venda pelo valor da oferta atual.

    Args:
        negociacao (dict): Negociação em andamento.

    Returns:
        float: Valor acertado, em milhões.
    """
    negociacao["acordo"] = negociacao["oferta"]
    return negociacao["acordo"]


def responder_contraproposta(negociacao, pedido):
    """
    Decide a resposta do clube do exterior a um pedido maior que a oferta.

    Se o pedido couber no teto, o clube aceita e o valor vira o acordo. Se passar do teto, o clube pode
    desistir: a chance começa em 25%, cresce 1,5 ponto para cada 1% acima do teto e mais 15 pontos a cada
    contraproposta já feita, até 90%. Se não desistir, sobe a oferta, cobrindo 60% da distância até o teto; se
    a oferta já estiver no teto, mantém o valor.

    Args:
        negociacao (dict): Negociação em andamento; a oferta, o contador e o acordo são atualizados.
        pedido (float): Valor pedido pelo técnico, em milhões.

    Returns:
        str: "aceita", "sobe", "mantem" ou "desiste".
    """
    negociacao["contrapropostas"] += 1
    if pedido <= negociacao["teto"]:
        negociacao["acordo"] = pedido
        return "aceita"
    excesso = pedido / negociacao["teto"] - 1
    chance_de_desistir = min(0.9, 0.25 + excesso * 1.5 + 0.15 * (negociacao["contrapropostas"] - 1))
    if random.random() < chance_de_desistir:
        return "desiste"
    nova_oferta = round(negociacao["oferta"] + (negociacao["teto"] - negociacao["oferta"]) * 0.6, 1)
    if nova_oferta <= negociacao["oferta"]:
        return "mantem"
    negociacao["oferta"] = nova_oferta
    return "sobe"


def qualidade_do_garoto(jogador):
    """
    Calcula a qualidade do garoto da base que sobe quando um jogador é vendido.

    Args:
        jogador (dict): Jogador vendido.

    Returns:
        int: Qualidade do jogador vendido menos QUEDA_QUALIDADE_GAROTO (12), entre 40 e 92.
    """
    return limitar(jogador["qualidade"] - QUEDA_QUALIDADE_GAROTO, 40, 92)


def nomes_em_uso(estado):
    """
    Reúne os nomes de todos os jogadores dos elencos da temporada.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        set[str]: Nomes já usados por algum jogador.
    """
    return {jogador["nome"] for clube in estado["clubes"].values() for jogador in clube["elenco"]}


def novo_garoto(estado, clube, banco, qualidade, posicao):
    """
    Cria um jogador vindo das categorias de base.

    O identificador usa o prefixo do clube e o maior número já usado com esse prefixo mais um, olhando todos
    os elencos, os jogadores sem clube e o contador do clube. Assim um garoto nunca herda o identificador de
    um jogador vendido ou transferido. O contador fica guardado no clube, e o nome é sorteado entre os que
    ainda não estão em uso. O jogador é criado, mas não é adicionado ao elenco.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube que recebe o jogador.
        banco (dict): Banco de nomes usado no sorteio.
        qualidade (int): Qualidade do novo jogador.
        posicao (str): Posição do novo jogador.

    Returns:
        dict: Jogador criado.
    """
    prefixo = f"{clube['id']}-"
    todos = [jogador for outro in estado["clubes"].values() for jogador in outro["elenco"]] + estado.get("livres", [])
    usados = [int(jogador["id"][len(prefixo) :]) for jogador in todos if jogador["id"].startswith(prefixo)]
    numero = max(usados + [clube.get("ultimo_id", 0)]) + 1
    clube["ultimo_id"] = numero
    nome = sortear_nome(banco, nomes_em_uso(estado))
    return criar_jogador(f"{clube['id']}-{numero:02d}", nome, posicao, qualidade)


def aplicar_efeito(estado, efeito, jogador_id, banco, valor_venda=None):
    """
    Aplica o efeito de um evento ao clube do jogador.

    Cada efeito altera o estado de um jeito: "grande_fase" dá ao alvo 2 rodadas de bônus de qualidade;
    "lesao_treino" deixa o alvo lesionado por 1 a 3 rodadas; "reuniao" soma 2 de confiança; "afastar" suspende
    o alvo por pelo menos 1 rodada e soma 5 de confiança; "vender" tira o alvo do elenco, credita no caixa o
    valor negociado (ou 1,2 vez o valor de mercado, se não houve negociação), sobe da base um garoto da mesma
    posição com 12 de qualidade a menos (entre 40 e 92) e soma 6 de confiança; "segurar" dá ao alvo pelo menos
    1 rodada de bônus e tira 3 de confiança; "negociacao_fracassou" mantém o alvo e tira 2 de confiança;
    "base" troca o jogador de linha com menor valor para escalar por um garoto da mesma posição, com qualidade
    sorteada entre 6 abaixo e 4 acima da força do clube (entre 40 e 92); "protesto" tira 5 de confiança;
    "descanso" recupera 15 de energia de todo o elenco, até 100. Os demais efeitos (patrocínio, amistoso,
    camisas, investidor, aumento, treinos, folga, loja, multa, chance para a base, festa e palestra) ficam em
    EFEITOS_DA_SEMANA, uma função para cada. Os efeitos que dependem de alvo não fazem nada se ele não
    existir.

    Args:
        estado (dict): Estado atual da temporada.
        efeito (str | None): Nome do efeito escolhido.
        jogador_id (str | None): Identificador do jogador alvo do evento.
        banco (dict): Banco de nomes usado para criar garotos da base.
        valor_venda (float | None): Valor acertado na negociação com o clube do exterior. Padrão None.

    Returns:
        str: Mensagem descrevendo o que mudou.
    """
    clube = clube_do_jogador(estado)
    jogador = next((j for j in clube["elenco"] if j["id"] == jogador_id), None)
    if efeito == "grande_fase" and jogador:
        jogador["fase"] = 2
        return f"{rotulo(jogador)} ganha +5 de qualidade nas próximas 2 rodadas."
    if efeito == "lesao_treino" and jogador:
        jogador["lesao"] = random.randint(1, 3)
        return f"{rotulo(jogador)} fica fora por {jogador['lesao']} rodada(s)."
    if efeito == "reuniao":
        ajustar_confianca(estado, 2)
        return "O grupo se acertou. Confiança da diretoria +2."
    if efeito == "afastar" and jogador:
        jogador["suspenso"] = max(jogador["suspenso"], 1)
        ajustar_confianca(estado, 5)
        return f"{rotulo(jogador)} fica fora da próxima rodada. A diretoria aprovou a firmeza: confiança +5."
    if efeito == "vender" and jogador:
        clube["elenco"].remove(jogador)
        if jogador["id"] in clube["titulares"]:
            clube["titulares"].remove(jogador["id"])
        garoto = novo_garoto(estado, clube, banco, qualidade_do_garoto(jogador), jogador["pos"])
        clube["elenco"].append(garoto)
        valor = valor_venda if valor_venda else round(valor_de_mercado(jogador) * 1.2, 1)
        lancar(estado, clube["id"], "Venda ao exterior", valor)
        ajustar_confianca(estado, CONFIANCA_VENDA)
        return (
            f"{rotulo(jogador)} foi vendido por {dinheiro(valor)}. "
            f"{rotulo(garoto)} sobe da base no lugar. Confiança +{CONFIANCA_VENDA}."
        )
    if efeito == "segurar" and jogador:
        jogador["fase"] = max(jogador["fase"], 1)
        ajustar_confianca(estado, CONFIANCA_SEGURAR)
        return (
            f"{rotulo(jogador)} fica e joga motivado na próxima rodada. "
            f"A diretoria não gostou: confiança {CONFIANCA_SEGURAR}."
        )
    if efeito == "negociacao_fracassou" and jogador:
        ajustar_confianca(estado, CONFIANCA_NEGOCIACAO_FRACASSADA)
        return (
            f"O clube do exterior desistiu e {rotulo(jogador)} fica. "
            f"A diretoria lamentou o dinheiro perdido: confiança {CONFIANCA_NEGOCIACAO_FRACASSADA}."
        )
    if efeito == "base":
        linha = [j for j in clube["elenco"] if j["pos"] != "GOL"]
        pior = min(linha, key=valor_para_escalar)
        qualidade = limitar(clube["forca"] + random.randint(-6, 4), 40, 92)
        garoto = novo_garoto(estado, clube, banco, qualidade, pior["pos"])
        clube["elenco"].remove(pior)
        if pior["id"] in clube["titulares"]:
            clube["titulares"].remove(pior["id"])
        clube["elenco"].append(garoto)
        return f"{rotulo(garoto)} (qualidade {garoto['qualidade']}) entra no lugar de {rotulo(pior)}."
    if efeito == "protesto":
        ajustar_confianca(estado, -5)
        return "A pressão aumentou. Confiança da diretoria -5."
    if efeito == "descanso":
        for j in clube["elenco"]:
            j["energia"] = min(100, j["energia"] + 15)
        return "Todo o elenco recupera +15 de energia."
    funcao = EFEITOS_DA_SEMANA.get(efeito)
    if funcao:
        return funcao(estado, clube, jogador)
    return "Nada mudou."


def mudar_energia(clube, quantidade):
    """
    Soma ou tira energia de todo o elenco, mantendo cada jogador entre 0 e 100.

    Args:
        clube (dict): Clube do técnico.
        quantidade (int): Energia a somar; negativa para cansar o elenco.
    """
    for jogador in clube["elenco"]:
        jogador["energia"] = max(0, min(100, jogador["energia"] + quantidade))


def pagar(estado, clube, categoria, custo):
    """
    Tira dinheiro do caixa do clube se ele tiver o suficiente.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        categoria (str): Nome da despesa no extrato.
        custo (float): Valor em milhões.

    Returns:
        bool: True se o pagamento foi feito, False se faltou dinheiro.
    """
    if clube.get("caixa", 0) < custo:
        return False
    lancar(estado, clube["id"], categoria, -custo)
    return True


def efeito_patrocinio(estado, clube, jogador):
    """
    Recebe R$ 3 mi de patrocínio e cansa o elenco em 10 de energia.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    lancar(estado, clube["id"], "Patrocínio", 3.0)
    mudar_energia(clube, -10)
    return f"Ação de marketing feita: {dinheiro(3.0)} no caixa, mas o elenco perde 10 de energia."


def efeito_amistoso(estado, clube, jogador):
    """
    Recebe R$ 4 mi pelo amistoso e cansa o elenco em 20 de energia.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    lancar(estado, clube["id"], "Amistosos", 4.0)
    mudar_energia(clube, -20)
    return f"O time joga o amistoso: {dinheiro(4.0)} no caixa e o elenco perde 20 de energia."


def efeito_camisas(estado, clube, jogador):
    """
    Recebe a venda de camisas: R$ 1 mi mais R$ 0,4 mi por vitória nos últimos 5 jogos da liga.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    valor = lancar(estado, clube["id"], "Venda de camisas", 1.0 + 0.4 * vitorias_recentes(estado, clube["id"]))
    return f"A camisa nova rendeu {dinheiro(valor)} para o clube."


def efeito_investidor(estado, clube, jogador):
    """
    Recebe R$ 6 mi do investidor, e a diretoria perde 4 de confiança.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    lancar(estado, clube["id"], "Investidor", 6.0)
    ajustar_confianca(estado, -4)
    return f"O investidor aporta {dinheiro(6.0)}. A diretoria não gostou de dividir o poder: confiança -4."


def efeito_pagar_aumento(estado, clube, jogador):
    """
    Paga R$ 1 mi de aumento e deixa o jogador motivado por 2 rodadas.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Jogador que pediu aumento.

    Returns:
        str: Mensagem do resultado.
    """
    if not jogador or not pagar(estado, clube, "Salários extras", 1.0):
        return "O clube não tem caixa para o aumento. Nada mudou."
    jogador["fase"] = max(jogador["fase"], 2)
    return f"{rotulo(jogador)} recebe o aumento e fica motivado nas próximas 2 rodadas."


def efeito_renovar(estado, clube, jogador):
    """
    Paga R$ 2 mi pela renovação e deixa o jogador motivado por 2 rodadas.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Jogador que renova.

    Returns:
        str: Mensagem do resultado.
    """
    if not jogador or not pagar(estado, clube, "Salários extras", 2.0):
        return "O clube não tem caixa para a renovação. Nada mudou."
    jogador["fase"] = max(jogador["fase"], 2)
    return f"{rotulo(jogador)} renova o contrato e fica motivado nas próximas 2 rodadas."


def efeito_negar_aumento(estado, clube, jogador):
    """
    Nega o pedido e deixa o jogador insatisfeito por 2 rodadas.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Jogador que teve o pedido negado.

    Returns:
        str: Mensagem do resultado.
    """
    if not jogador:
        return "Nada mudou."
    jogador["insatisfeito"] = max(jogador.get("insatisfeito", 0), 2)
    return f"{rotulo(jogador)} não gostou da resposta e fica insatisfeito por 2 rodadas."


def efeito_treino_finalizacao(estado, clube, jogador):
    """
    Paga R$ 1 mi e dá +2 de finalização a meias e atacantes, até 99.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    if not pagar(estado, clube, "Treinos especiais", 1.0):
        return "O clube não tem caixa para o treino especial. Nada mudou."
    for atleta in clube["elenco"]:
        if atleta["pos"] in ("MEI", "ATA"):
            atleta["fin"] = min(99, atleta["fin"] + 2)
    return "Semana de finalização: meias e atacantes ganham +2 de finalização."


def efeito_treino_defesa(estado, clube, jogador):
    """
    Paga R$ 1 mi e dá +2 de desarme aos defensores, até 99.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    if not pagar(estado, clube, "Treinos especiais", 1.0):
        return "O clube não tem caixa para o treino especial. Nada mudou."
    for atleta in clube["elenco"]:
        if atleta["pos"] == "DEF":
            atleta["des"] = min(99, atleta["des"] + 2)
    return "Semana de marcação: os defensores ganham +2 de desarme."


def efeito_dar_folga(estado, clube, jogador):
    """
    Dá folga: o elenco recupera 20 de energia e a diretoria perde 1 de confiança.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    mudar_energia(clube, 20)
    ajustar_confianca(estado, -1)
    return "Folga dada: o elenco recupera 20 de energia, mas a diretoria torceu o nariz (confiança -1)."


def efeito_negar_folga(estado, clube, jogador):
    """
    Nega a folga: a diretoria ganha 1 de confiança e o elenco perde 5 de energia.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    mudar_energia(clube, -5)
    ajustar_confianca(estado, 1)
    return "Sem folga: a diretoria aprova (confiança +1), mas o elenco perde 5 de energia."


def efeito_loja(estado, clube, jogador):
    """
    Recebe R$ 1,5 mi da loja do clube.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    lancar(estado, clube["id"], "Loja do clube", 1.5)
    return f"A loja rendeu {dinheiro(1.5)} na semana."


def efeito_multa(estado, clube, jogador):
    """
    Paga R$ 1 mi de multa à federação, mesmo que o caixa fique negativo.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    lancar(estado, clube["id"], "Multas", -1.0)
    return f"O clube paga {dinheiro(1.0)} de multa."


def efeito_dar_chance(estado, clube, jogador):
    """
    Coloca o jovem no time titular, no lugar do titular mais fraco da mesma posição, e o deixa motivado.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Jovem que pediu a chance.

    Returns:
        str: Mensagem do resultado.
    """
    if not jogador:
        return "Nada mudou."
    por_id = {atleta["id"]: atleta for atleta in clube["elenco"]}
    mesma_posicao = [por_id[i] for i in clube["titulares"] if i in por_id and por_id[i]["pos"] == jogador["pos"]]
    jogador["fase"] = max(jogador["fase"], 2)
    if not mesma_posicao:
        return f"{rotulo(jogador)} fica motivado, mas não há vaga na posição dele."
    sai = min(mesma_posicao, key=valor_para_escalar)
    clube["titulares"][clube["titulares"].index(sai["id"])] = jogador["id"]
    return f"{rotulo(jogador)} entra no time titular no lugar de {rotulo(sai)} e chega motivado."


def efeito_esperar_chance(estado, clube, jogador):
    """
    Pede paciência ao jovem, que fica insatisfeito por 1 rodada.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Jovem que pediu a chance.

    Returns:
        str: Mensagem do resultado.
    """
    if not jogador:
        return "Nada mudou."
    jogador["insatisfeito"] = max(jogador.get("insatisfeito", 0), 1)
    return f"{rotulo(jogador)} aceita esperar, mas fica insatisfeito na próxima rodada."


def efeito_festa_torcida(estado, clube, jogador):
    """
    A festa da torcida anima a diretoria: confiança +2.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    ajustar_confianca(estado, 2)
    return "Clima de festa no clube. Confiança da diretoria +2."


def efeito_palestra(estado, clube, jogador):
    """
    Dois titulares sorteados saem motivados da palestra, em grande fase por 1 rodada.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube do técnico.
        jogador (dict | None): Não usado.

    Returns:
        str: Mensagem do resultado.
    """
    por_id = {atleta["id"]: atleta for atleta in clube["elenco"]}
    titulares = [por_id[i] for i in clube["titulares"] if i in por_id]
    escolhidos = random.sample(titulares, min(2, len(titulares)))
    for atleta in escolhidos:
        atleta["fase"] = max(atleta["fase"], 1)
    nomes = " e ".join(rotulo(atleta) for atleta in escolhidos)
    return f"{nomes} saíram inspirados da palestra e estão em grande fase na próxima rodada."


EFEITOS_DA_SEMANA = {
    "patrocinio": efeito_patrocinio,
    "amistoso": efeito_amistoso,
    "camisas": efeito_camisas,
    "investidor": efeito_investidor,
    "pagar_aumento": efeito_pagar_aumento,
    "renovar": efeito_renovar,
    "negar_aumento": efeito_negar_aumento,
    "treino_finalizacao": efeito_treino_finalizacao,
    "treino_defesa": efeito_treino_defesa,
    "dar_folga": efeito_dar_folga,
    "negar_folga": efeito_negar_folga,
    "loja": efeito_loja,
    "multa": efeito_multa,
    "dar_chance": efeito_dar_chance,
    "esperar_chance": efeito_esperar_chance,
    "festa_torcida": efeito_festa_torcida,
    "palestra": efeito_palestra,
}
