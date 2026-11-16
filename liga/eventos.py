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
    jogador de linha (sem goleiros) de maior qualidade. Qualquer outro alvo não envolve jogador.

    Args:
        clube (dict): Clube do jogador.
        alvo (str): Tipo de alvo do evento ("titular", "melhor" ou outro valor).

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
    return None


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
    primeira oferta (FAIXA_TETO_EXTERIOR). O teto não aparece na tela: o técnico só descobre pedindo mais, e às
    vezes a primeira oferta já é a última.

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
    1 rodada de bônus e tira 3 de confiança; "negociacao_fracassou" mantém o alvo e tira 2 de confiança; "base"
    troca o jogador de linha com menor valor para escalar por um garoto da mesma posição, com qualidade
    sorteada entre 6 abaixo e 4 acima da força do clube (entre 40 e 92); "protesto" tira 5 de confiança;
    "descanso" recupera 15 de energia de todo o elenco, até 100. Os efeitos que dependem de alvo não fazem
    nada se ele não existir.

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
        clube["caixa"] = round(clube.get("caixa", 0) + valor, 1)
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
    return "Nada mudou."
