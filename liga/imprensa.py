import random

from config import CHANCE_BOATO, DURACAO_BOATO, FONTES_DA_IMPRENSA
from liga.carreira import clubes_melhores
from liga.tabela import posicao_do_clube
from liga.temporada import classificacao, clube_do_jogador, meta_cumprida, posicao_atual
from mercado.transferencias import noticia

TEXTOS_DO_BOATO = {
    "pressao": (
        "{fonte}: a diretoria do {clube} já discute a demissão de {tecnico}.",
        "{fonte}: {tecnico} balança no {clube} e pode cair a qualquer momento.",
        "{fonte}: dirigentes do {clube} procuram um substituto para {tecnico}.",
    ),
    "interesse": (
        "{fonte}: o {clube} está de olho em {tecnico} para a próxima mudança no comando.",
        "{fonte}: {tecnico} entrou na lista de desejos do {clube}.",
        "{fonte}: emissários do {clube} teriam sondado {tecnico}.",
    ),
    "rival": (
        "{fonte}: o técnico do {clube} está com os dias contados.",
        "{fonte}: o vestiário do {clube} rachou e o técnico pode cair.",
        "{fonte}: a diretoria do {clube} já avalia trocar de técnico.",
    ),
}
DESFECHOS_DO_BOATO = {
    ("pressao", True): "A diretoria do {clube} segurou {tecnico} por enquanto. {fonte} mantém a informação.",
    ("pressao", False): "O {clube} desmentiu: {tecnico} segue com apoio da diretoria. {fonte} errou.",
    ("interesse", True): "A conversa entre o {clube} e {tecnico} esfriou, segundo {fonte}.",
    ("interesse", False): "O {clube} negou interesse em {tecnico}. {fonte} errou.",
    ("rival", True): "O {clube} demitiu o técnico, como {fonte} havia adiantado.",
    ("rival", False): "O {clube} confirmou o técnico no cargo. {fonte} errou.",
}


def pesos_dos_boatos(estado):
    """
    Define a frequência de cada tipo de boato conforme o momento do técnico.

    Args:
        estado (dict): Estado da carreira.

    Returns:
        dict: Peso de "pressao", "interesse" e "rival".
    """
    na_meta = meta_cumprida(estado, posicao_atual(estado))
    return {"pressao": 1 if na_meta else 3, "interesse": 3 if na_meta else 1, "rival": 2}


def clube_em_crise(estado):
    """
    Sorteia um clube da metade de baixo da sua divisão, sem contar o do técnico.

    Args:
        estado (dict): Estado da carreira.

    Returns:
        dict: Clube sorteado.
    """
    candidatos = []
    for clube in estado["clubes"].values():
        tabela = classificacao(estado, clube.get("divisao", 1))
        if clube["id"] != estado["clube_id"] and posicao_do_clube(tabela, clube["id"]) > len(tabela) / 2:
            candidatos.append(clube)
    return random.choice(candidatos)


def criar_boato(estado):
    """
    Sorteia um novo boato da imprensa, se não houver outro em andamento.

    A chance é CHANCE_BOATO (30%) por etapa. A veracidade depende da fonte, de FONTES_DA_IMPRENSA, e fica
    escondida do técnico. A pressão sobre o cargo só é verdadeira com o clube fora da meta, e o interesse só é
    verdadeiro se vier de um clube melhor que o atual. O boato vale por DURACAO_BOATO (3) etapas.

    Args:
        estado (dict): Estado da carreira.

    Returns:
        str | None: Texto da notícia, ou None se não surgiu boato.
    """
    if "boato" in estado or random.random() >= CHANCE_BOATO:
        return None
    pesos = pesos_dos_boatos(estado)
    tipo = random.choices(list(pesos), list(pesos.values()))[0]
    fonte, confiabilidade = random.choice(FONTES_DA_IMPRENSA)
    verdadeiro = random.random() < confiabilidade
    atual = clube_do_jogador(estado)
    if tipo == "pressao":
        clube = atual
        verdadeiro = verdadeiro and not meta_cumprida(estado, posicao_atual(estado))
    elif tipo == "rival":
        clube = clube_em_crise(estado)
    else:
        melhores = clubes_melhores(estado)
        verdadeiro = verdadeiro and bool(melhores)
        outros = [c for c in estado["clubes"].values() if c["id"] != atual["id"]]
        clube = random.choice(melhores if verdadeiro else outros)
    estado["boato"] = {
        "tipo": tipo,
        "fonte": fonte,
        "clube_id": clube["id"],
        "verdadeiro": verdadeiro,
        "expira": estado["etapa"] + DURACAO_BOATO,
    }
    modelo = random.choice(TEXTOS_DO_BOATO[tipo])
    return modelo.format(fonte=fonte, clube=clube["nome"], tecnico=estado["tecnico"])


def encerrar_boato(estado):
    """
    Encerra o boato cujo prazo acabou e informa o que aconteceu.

    Quando o boato verdadeiro sobre outro clube se confirma, a demissão vira notícia e, se esse clube for melhor
    que o atual e o técnico estiver dentro da meta, ele oferece o cargo.

    Args:
        estado (dict): Estado da carreira.

    Returns:
        dict | None: Texto do desfecho e propostas de emprego, ou None se nada terminou.
    """
    boato = estado.get("boato")
    if not boato or estado["etapa"] < boato["expira"]:
        return None
    del estado["boato"]
    clube = estado["clubes"][boato["clube_id"]]
    modelo = DESFECHOS_DO_BOATO[(boato["tipo"], boato["verdadeiro"])]
    texto = modelo.format(fonte=boato["fonte"], clube=clube["nome"], tecnico=estado["tecnico"])
    propostas = []
    if boato["tipo"] == "rival" and boato["verdadeiro"]:
        noticia(estado, texto)
        ids_melhores = [c["id"] for c in clubes_melhores(estado)]
        if clube["id"] in ids_melhores and meta_cumprida(estado, posicao_atual(estado)):
            propostas = [{"clube_id": clube["id"], "motivo": "demitiu o técnico"}]
    return {"texto": texto, "propostas": propostas}
