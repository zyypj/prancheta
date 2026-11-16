import random

from config import BONUS_GRANDE_FASE, COMPOSICAO_ELENCO, ENERGIA_SEM_PERDA, FORMACOES

ATRIBUTOS = ("fin", "pas", "des", "fis", "ref")
AJUSTES = {
    "GOL": {"fin": -40, "pas": -15, "des": -25, "fis": -5, "ref": 0},
    "DEF": {"fin": -18, "pas": -6, "des": 4, "fis": 2, "ref": -60},
    "MEI": {"fin": -6, "pas": 4, "des": -6, "fis": 0, "ref": -60},
    "ATA": {"fin": 4, "pas": -6, "des": -24, "fis": 0, "ref": -60},
}
TITULARES_POR_POSICAO = {"GOL": 1, "DEF": 4, "MEI": 4, "ATA": 2}


def limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def ler_banco_de_nomes(linhas):
    banco = {"N": [], "S": [], "A": []}
    for linha in linhas:
        tipo, separador, texto = linha.partition(":")
        tipo = tipo.strip().upper()
        if separador and tipo in banco and texto.strip():
            banco[tipo].append(texto.strip())
    return banco


def sortear_nome(banco, usados):
    for _ in range(80):
        if banco["A"] and random.random() < 0.25:
            nome = random.choice(banco["A"])
        else:
            nome = f"{random.choice(banco['N'])} {random.choice(banco['S'])}"
        if nome not in usados:
            usados.add(nome)
            return nome
    nome = f"{random.choice(banco['N'])} {len(usados) + 1}"
    usados.add(nome)
    return nome


def criar_jogador(identificador, nome, posicao, qualidade):
    jogador = {
        "id": identificador,
        "nome": nome,
        "pos": posicao,
        "qualidade": qualidade,
        "energia": 100,
        "amarelos": 0,
        "suspenso": 0,
        "lesao": 0,
        "fase": 0,
        "gols": 0,
        "desfalque": False,
    }
    for atributo in ATRIBUTOS:
        jogador[atributo] = limitar(qualidade + AJUSTES[posicao][atributo] + random.randint(-5, 5), 5, 99)
    return jogador


def sortear_qualidade(forca, titular):
    media = forca + 2 if titular else forca - 6
    return limitar(round(random.gauss(media, 4)), 40, 92)


def gerar_elenco(clube, banco, usados):
    elenco = []
    numero = 1
    for posicao, quantidade in COMPOSICAO_ELENCO.items():
        for indice in range(quantidade):
            titular = indice < TITULARES_POR_POSICAO[posicao]
            qualidade = sortear_qualidade(clube["forca"], titular)
            elenco.append(criar_jogador(f"{clube['id']}-{numero:02d}", sortear_nome(banco, usados), posicao, qualidade))
            numero += 1
    craque = random.choice([jogador for jogador in elenco if jogador["pos"] != "GOL"])
    craque["qualidade"] = limitar(craque["qualidade"] + 7, 40, 92)
    for atributo in ("fin", "pas", "des", "fis"):
        craque[atributo] = limitar(craque[atributo] + 7, 5, 99)
    return elenco


def disponivel(jogador):
    return jogador["lesao"] == 0 and jogador["suspenso"] == 0


def fator_energia(energia):
    if energia >= ENERGIA_SEM_PERDA:
        return 1.0
    return 0.7 + 0.3 * energia / ENERGIA_SEM_PERDA


def atributo_efetivo(jogador, atributo):
    bonus = BONUS_GRANDE_FASE if jogador["fase"] > 0 else 0
    return (jogador[atributo] + bonus) * fator_energia(jogador["energia"])


def valor_para_escalar(jogador):
    bonus = BONUS_GRANDE_FASE if jogador["fase"] > 0 else 0
    return (jogador["qualidade"] + bonus) * fator_energia(jogador["energia"])


def escalar_automatico(elenco, formacao):
    defensores, meias, atacantes = FORMACOES[formacao]
    vagas = {"GOL": 1, "DEF": defensores, "MEI": meias, "ATA": atacantes}
    livres = sorted([jogador for jogador in elenco if disponivel(jogador)], key=valor_para_escalar, reverse=True)
    escolhidos = []
    for posicao, quantidade in vagas.items():
        da_posicao = [jogador for jogador in livres if jogador["pos"] == posicao and jogador not in escolhidos]
        escolhidos.extend(da_posicao[:quantidade])
    restantes = [jogador for jogador in livres if jogador not in escolhidos and jogador["pos"] != "GOL"]
    while len(escolhidos) < 11 and restantes:
        escolhidos.append(restantes.pop(0))
    return [jogador["id"] for jogador in escolhidos]


def completar_titulares(clube):
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    validos = [identificador for identificador in clube["titulares"] if identificador in por_id and disponivel(por_id[identificador])]
    if len(validos) == 11:
        clube["titulares"] = validos
        return []
    sugestao = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
    trocados = [por_id[identificador]["nome"] for identificador in clube["titulares"] if identificador not in validos and identificador in por_id]
    for identificador in sugestao:
        if len(validos) >= 11:
            break
        if identificador not in validos:
            validos.append(identificador)
    clube["titulares"] = validos
    return trocados


def contar_posicoes(jogadores):
    contagem = {posicao: 0 for posicao in ("GOL", "DEF", "MEI", "ATA")}
    for jogador in jogadores:
        contagem[jogador["pos"]] += 1
    return contagem


def media(valores, padrao):
    return sum(valores) / len(valores) if valores else padrao


def forca_setores(em_campo):
    por_posicao = {posicao: [jogador for jogador in em_campo if jogador["pos"] == posicao] for posicao in ("GOL", "DEF", "MEI", "ATA")}
    contagem = contar_posicoes(em_campo)
    defesa = media([atributo_efetivo(j, "des") * 0.8 + atributo_efetivo(j, "fis") * 0.2 for j in por_posicao["DEF"]], 35)
    meio = media([atributo_efetivo(j, "pas") * 0.6 + atributo_efetivo(j, "des") * 0.2 + atributo_efetivo(j, "fis") * 0.2 for j in por_posicao["MEI"]], 35)
    ataque = media([atributo_efetivo(j, "fin") * 0.7 + atributo_efetivo(j, "fis") * 0.3 for j in por_posicao["ATA"]], 35)
    ataque = ataque * 0.75 + media([atributo_efetivo(j, "pas") for j in por_posicao["MEI"]], 35) * 0.25
    goleiro = max([atributo_efetivo(j, "ref") for j in por_posicao["GOL"]], default=30)
    defesa += (contagem["DEF"] - 4) * 2.5
    meio += (contagem["MEI"] - 4) * 2.5
    ataque += (contagem["ATA"] - 2) * 3
    falta = 11 - len(em_campo)
    return {
        "defesa": defesa - falta * 3,
        "meio": meio - falta * 3,
        "ataque": ataque - falta * 2,
        "goleiro": goleiro,
    }
