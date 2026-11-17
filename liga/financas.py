from config import BILHETERIA, COTA_TV, FATOR_RECEITA_SERIE_B


def lancar(estado, clube_id, categoria, valor):
    """
    Lança uma entrada ou saída de dinheiro no caixa de um clube.

    Soma o valor ao caixa, arredondado em uma casa. Quando o clube é o do técnico, o lançamento também vai
    para o extrato da temporada (estado["financas"], somado por categoria) e para o extrato da semana
    (estado["extrato_etapa"]), mostrado na tela de resultados.

    Args:
        estado (dict): Estado atual da temporada.
        clube_id (str): Clube que recebe ou paga.
        categoria (str): Nome da receita ou despesa, como "Bilheteria" ou "Compras".
        valor (float): Valor em milhões; negativo para despesas.

    Returns:
        float: Valor lançado, já arredondado.
    """
    valor = round(valor, 1)
    clube = estado["clubes"][clube_id]
    clube["caixa"] = round(clube.get("caixa", 0) + valor, 1)
    if clube_id == estado["clube_id"] and valor:
        financas = estado.setdefault("financas", {})
        financas[categoria] = round(financas.get(categoria, 0) + valor, 1)
        estado.setdefault("extrato_etapa", []).append((categoria, valor))
    return valor


def fator_da_divisao(clube):
    """
    Indica quanto da receita normal um clube recebe pela divisão em que joga.

    Args:
        clube (dict): Clube avaliado.

    Returns:
        float: 1 na Série A e FATOR_RECEITA_SERIE_B (0,6) na Série B.
    """
    return FATOR_RECEITA_SERIE_B if clube.get("divisao", 1) == 2 else 1.0


def vitorias_recentes(estado, clube_id, quantidade=5):
    """
    Conta as vitórias de um clube nos últimos jogos da liga.

    Args:
        estado (dict): Estado atual da temporada.
        clube_id (str): Clube avaliado.
        quantidade (int): Quantos jogos recentes considerar. Padrão 5.

    Returns:
        int: Número de vitórias nesses jogos.
    """
    jogos = [
        jogo for rodada in estado["historico"] for jogo in rodada if clube_id in (jogo["mandante"], jogo["visitante"])
    ]
    vitorias = 0
    for jogo in jogos[-quantidade:]:
        marcados, sofridos = (jogo["gm"], jogo["gv"]) if jogo["mandante"] == clube_id else (jogo["gv"], jogo["gm"])
        vitorias += marcados > sofridos
    return vitorias


def fator_torcida(estado, clube_id):
    """
    Calcula quanto a fase do clube enche o estádio.

    Parte de 0,7 e soma 0,1 por vitória nos últimos 5 jogos da liga, indo de 0,7 a 1,2.

    Args:
        estado (dict): Estado atual da temporada.
        clube_id (str): Clube mandante.

    Returns:
        float: Multiplicador da bilheteria.
    """
    return 0.7 + 0.1 * vitorias_recentes(estado, clube_id)


def receber_bilheteria(estado, resultado, neutro=False):
    """
    Paga a bilheteria de um jogo.

    O mandante recebe o valor de BILHETERIA do seu nível multiplicado pelo fator da torcida. Em campo neutro,
    a renda é dividida: cada clube recebe metade do valor do seu nível. Clubes da Série B recebem só
    FATOR_RECEITA_SERIE_B (60%) desses valores.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict): Resultado da partida.
        neutro (bool): Se o jogo foi em campo neutro. Padrão False.
    """
    if neutro:
        for clube_id in (resultado["mandante"], resultado["visitante"]):
            clube = estado["clubes"][clube_id]
            lancar(estado, clube_id, "Bilheteria", BILHETERIA[clube["nivel"]] / 2 * fator_da_divisao(clube))
        return
    mandante = resultado["mandante"]
    clube = estado["clubes"][mandante]
    valor = BILHETERIA[clube["nivel"]] * fator_torcida(estado, mandante) * fator_da_divisao(clube)
    lancar(estado, mandante, "Bilheteria", valor)


def receber_cota_tv(estado):
    """
    Paga a cota de TV da rodada da liga a todos os clubes, conforme o nível de cada um (COTA_TV). Na Série
    B, a cota é FATOR_RECEITA_SERIE_B (60%) do valor.

    Args:
        estado (dict): Estado atual da temporada.
    """
    for clube_id, clube in estado["clubes"].items():
        lancar(estado, clube_id, "Cota de TV", COTA_TV[clube["nivel"]] * fator_da_divisao(clube))


def extrato(estado):
    """
    Lista as receitas e despesas do clube do técnico na temporada, das maiores entradas para as maiores
    saídas.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        list[tuple]: Pares (categoria, valor em milhões).
    """
    return sorted(estado.get("financas", {}).items(), key=lambda item: item[1], reverse=True)
