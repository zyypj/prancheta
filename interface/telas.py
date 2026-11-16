from rich.panel import Panel
from rich.table import Table

from config import ESTILOS, FORMACOES, NIVEIS, NOME_JOGO, NOMES_ESTILOS, TOTAL_RODADAS, VERSAO, ZONA_G4, ZONA_REBAIXAMENTO
from elenco.escalacao import disponivel, escalar_automatico
from interface.campo import barra
from interface.entrada import console, ler_opcao, limpar, pausar
from liga.tabela import saldo
from liga.temporada import adversario_de, classificacao, clube_do_jogador, jogo_do_jogador, jogos_da_rodada, posicao_atual

OPCOES_MENU = ("Novo jogo", "Carregar", "Ranking", "Sair")
CORES_RESULTADO = {"V": "green", "E": "yellow", "D": "red"}


def titulo(texto):
    limpar()
    console.print(Panel.fit(f"[bold]{texto}[/]", border_style="green"))


def nivel_de_forca(forca):
    quantidade = max(1, min(5, (forca - 50) // 7))
    return f"[green]{'█' * quantidade}[/][dim]{'░' * (5 - quantidade)}[/]"


def mostrar_menu_inicial():
    limpar()
    console.print(Panel.fit(f"[bold green]{' '.join(NOME_JOGO)}[/]  [dim]v{VERSAO}[/]", border_style="green"))
    for numero, opcao in enumerate(OPCOES_MENU, start=1):
        console.print(f" {numero} - {opcao}")
    return ler_opcao(1, len(OPCOES_MENU))


def escolher_clube(clubes_base):
    titulo("ESCOLHA SEU CLUBE")
    tabela = Table(header_style="bold")
    for coluna in ("#", "Clube", "Nível", "Força", "Meta da diretoria"):
        tabela.add_column(coluna)
    for numero, clube in enumerate(clubes_base, start=1):
        nivel = NIVEIS[clube["nivel"]]
        tabela.add_row(str(numero), f"[bold {clube['cor']}]{clube['nome']}[/]", nivel["nome"], f"{nivel_de_forca(clube['forca'])} {clube['forca']}", nivel["meta"])
    console.print(tabela)
    console.print(" [dim]Clubes menores pontuam mais no ranking (médio x1,3, pequeno x1,6).[/]")
    console.print(" [bold]0[/] Voltar")
    escolha = ler_opcao(0, len(clubes_base))
    return clubes_base[escolha - 1]["id"] if escolha else None


def texto_jogo(estado, jogo):
    casa = estado["clubes"][jogo[0]]
    fora = estado["clubes"][jogo[1]]
    return f"[bold {casa['cor']}]{casa['nome']}[/] x [bold {fora['cor']}]{fora['nome']}[/]"


def mostrar_central(estado):
    clube = clube_do_jogador(estado)
    nivel = NIVEIS[clube["nivel"]]
    titulo(f"CENTRAL DO CLUBE — {clube['nome'].upper()}")
    ultimos = " ".join(f"[{CORES_RESULTADO[letra]}]{letra}[/]" for letra in estado["ultimos"]) or "-"
    console.print(f" Técnico: [bold]{estado['tecnico']}[/]   Meta: [bold]{nivel['meta']}[/]   Posição: [bold]{posicao_atual(estado)}º[/]")
    console.print(f" Rodada [bold]{estado['rodada']}/{TOTAL_RODADAS}[/]   Últimos jogos: {ultimos}")
    console.print(f" Confiança da diretoria: {barra(estado['confianca'], 20)}")
    jogo = jogo_do_jogador(estado)
    local = "em casa" if jogo[0] == clube["id"] else "fora de casa"
    adversario = estado["clubes"][adversario_de(jogo, clube["id"])]
    console.print(f"\n Próximo jogo ({local}): {texto_jogo(estado, jogo)}  [dim]força {adversario['forca']}[/]\n")
    opcoes = ("Próxima partida", "Elenco", "Plano de jogo", "Classificação", "Rodadas e histórico", "Salvar", "Voltar ao menu")
    for numero, opcao in enumerate(opcoes, start=1):
        console.print(f" {numero} - {opcao}")
    return ler_opcao(1, len(opcoes))


def status_jogador(jogador, titulares):
    partes = []
    if jogador["id"] in titulares:
        partes.append("[green]titular[/]")
    if jogador["lesao"]:
        partes.append(f"[red]lesionado ({jogador['lesao']})[/]")
    if jogador["suspenso"]:
        partes.append("[red]suspenso[/]")
    if jogador["fase"]:
        partes.append("[cyan]grande fase[/]")
    if jogador["amarelos"]:
        partes.append(f"[yellow]{jogador['amarelos']} amarelo(s)[/]")
    return " ".join(partes)


def tabela_elenco(clube):
    tabela = Table(header_style="bold")
    for coluna in ("#", "Jogador", "Pos", "Qual", "Fin", "Pas", "Des", "Fís", "Ref", "Energia", "Gols", "Situação"):
        tabela.add_column(coluna)
    ordem = {"GOL": 0, "DEF": 1, "MEI": 2, "ATA": 3}
    jogadores = sorted(clube["elenco"], key=lambda j: (ordem[j["pos"]], -j["qualidade"]))
    for numero, jogador in enumerate(jogadores, start=1):
        referencia = str(jogador["ref"]) if jogador["pos"] == "GOL" else "-"
        tabela.add_row(
            str(numero), jogador["nome"], jogador["pos"], str(jogador["qualidade"]),
            str(jogador["fin"]), str(jogador["pas"]), str(jogador["des"]), str(jogador["fis"]), referencia,
            barra(jogador["energia"], 6), str(jogador["gols"]), status_jogador(jogador, clube["titulares"]),
        )
    return tabela, jogadores


def mostrar_elenco(clube):
    titulo(f"ELENCO — {clube['nome'].upper()}")
    tabela, _ = tabela_elenco(clube)
    console.print(tabela)
    pausar()


def trocar_titular(clube):
    limpar()
    tabela, jogadores = tabela_elenco(clube)
    console.print(tabela)
    console.print(" [bold]0[/] Cancelar")
    sai = ler_opcao(0, len(jogadores), " Número do titular que sai > ")
    if not sai or jogadores[sai - 1]["id"] not in clube["titulares"]:
        return "Escolha um jogador que seja titular."
    entra = ler_opcao(0, len(jogadores), " Número do reserva que entra > ")
    if not entra:
        return ""
    reserva = jogadores[entra - 1]
    if reserva["id"] in clube["titulares"] or not disponivel(reserva):
        return "Esse jogador já é titular ou não está disponível."
    indice = clube["titulares"].index(jogadores[sai - 1]["id"])
    clube["titulares"][indice] = reserva["id"]
    return f"{reserva['nome']} entra no time titular."


def editar_plano(clube):
    mensagem = ""
    while True:
        titulo("PLANO DE JOGO")
        plano = clube["plano"]
        console.print(f" Formação: [bold]{plano['formacao']}[/]   Estilo: [bold]{NOMES_ESTILOS[plano['estilo']]}[/]")
        console.print(f" Ofensividade: [bold]{plano['ofensividade']}[/]/5   Intensidade: [bold]{plano['intensidade']}[/]/5")
        titulares = [j for j in clube["elenco"] if j["id"] in clube["titulares"]]
        console.print(" Titulares: " + ", ".join(f"{j['nome']} ({j['pos']})" for j in titulares))
        if mensagem:
            console.print(f" [yellow]{mensagem}[/]")
        console.print("\n 1 - Formação  2 - Estilo  3 - Ofensividade  4 - Intensidade  5 - Escalação automática  6 - Trocar titular  0 - Voltar")
        escolha = ler_opcao(0, 6)
        mensagem = ""
        if escolha == 0:
            return
        if escolha == 1:
            nomes = list(FORMACOES)
            console.print(" " + "   ".join(f"[bold]{n}[/] {f}" for n, f in enumerate(nomes, start=1)) + "   [bold]0[/] Voltar")
            nova = ler_opcao(0, len(nomes))
            if nova:
                plano["formacao"] = nomes[nova - 1]
                clube["titulares"] = escalar_automatico(clube["elenco"], plano["formacao"])
                mensagem = "Time reescalado para a nova formação."
        elif escolha == 2:
            console.print(" " + "   ".join(f"[bold]{n}[/] {NOMES_ESTILOS[e]}" for n, e in enumerate(ESTILOS, start=1)) + "   [bold]0[/] Voltar")
            novo = ler_opcao(0, len(ESTILOS))
            if novo:
                plano["estilo"] = ESTILOS[novo - 1]
        elif escolha == 3:
            plano["ofensividade"] = ler_opcao(0, 5, " Ofensividade (1 retranca a 5 tudo ao ataque, 0 mantém) > ") or plano["ofensividade"]
        elif escolha == 4:
            plano["intensidade"] = ler_opcao(0, 5, " Intensidade (1 a 5, mais alta cansa mais, 0 mantém) > ") or plano["intensidade"]
        elif escolha == 5:
            clube["titulares"] = escalar_automatico(clube["elenco"], plano["formacao"])
            mensagem = "Escalados os melhores disponíveis."
        else:
            mensagem = trocar_titular(clube)


def mostrar_classificacao(estado):
    titulo("CLASSIFICAÇÃO")
    tabela = Table(header_style="bold")
    for coluna in ("#", "Clube", "P", "J", "V", "E", "D", "GP", "GC", "SG"):
        tabela.add_column(coluna, justify="right" if coluna not in ("Clube",) else "left")
    ordenada = classificacao(estado)
    for posicao, linha in enumerate(ordenada, start=1):
        clube = estado["clubes"][linha["id"]]
        if linha["id"] == estado["clube_id"]:
            estilo = "bold yellow"
        elif posicao == 1:
            estilo = "green"
        elif posicao <= ZONA_G4:
            estilo = "blue"
        elif posicao > len(ordenada) - ZONA_REBAIXAMENTO:
            estilo = "red"
        else:
            estilo = ""
        tabela.add_row(
            str(posicao), clube["nome"], str(linha["pontos"]), str(linha["jogos"]), str(linha["vitorias"]),
            str(linha["empates"]), str(linha["derrotas"]), str(linha["gp"]), str(linha["gc"]), f"{saldo(linha):+d}",
            style=estilo,
        )
    console.print(tabela)
    console.print(" [green]■[/] campeão  [blue]■[/] G4  [red]■[/] rebaixamento  [bold yellow]■[/] seu clube")
    console.print(" [dim]Desempate: pontos, vitórias, saldo, gols marcados, confronto direto, menos vermelhos, sorteio.[/]")
    pausar()


def mostrar_sumula(linhas):
    for linha in linhas or ["Sem lances registrados."]:
        console.print(f"  {linha}")


def mostrar_rodadas(estado):
    while True:
        titulo("RODADAS E HISTÓRICO")
        console.print(f" Rodada atual: {estado['rodada']}/{TOTAL_RODADAS}")
        numero = ler_opcao(0, TOTAL_RODADAS, " Qual rodada ver? (0 volta) > ")
        if numero == 0:
            return
        titulo(f"RODADA {numero}")
        jogada = numero <= len(estado["historico"])
        if jogada:
            for jogo in estado["historico"][numero - 1]:
                destaque = " [yellow]◄[/]" if estado["clube_id"] in (jogo["mandante"], jogo["visitante"]) else ""
                casa = estado["clubes"][jogo["mandante"]]
                fora = estado["clubes"][jogo["visitante"]]
                console.print(f" {casa['nome']:>22} [bold]{jogo['gm']} x {jogo['gv']}[/] {fora['nome']}{destaque}")
            console.print("\n [bold]Súmula do seu jogo:[/]")
            mostrar_sumula(estado["sumulas"].get(str(numero)))
        else:
            for jogo in jogos_da_rodada(estado, numero):
                destaque = " [yellow]◄[/]" if estado["clube_id"] in jogo else ""
                console.print(f" {estado['clubes'][jogo[0]]['nome']:>22}   x   {estado['clubes'][jogo[1]]['nome']}{destaque}")
        pausar()


def pre_jogo(estado):
    clube = clube_do_jogador(estado)
    jogo = jogo_do_jogador(estado)
    adversario = estado["clubes"][adversario_de(jogo, clube["id"])]
    titulo(f"PRÉ-JOGO — RODADA {estado['rodada']}")
    console.print(f" {texto_jogo(estado, jogo)}")
    console.print(f" Força: {clube['nome']} {clube['forca']}  x  {adversario['nome']} {adversario['forca']}")
    plano = clube["plano"]
    console.print(f" Seu plano: {plano['formacao']} · {NOMES_ESTILOS[plano['estilo']]} · Ofensividade {plano['ofensividade']} · Intensidade {plano['intensidade']}")
    titulares = [j for j in clube["elenco"] if j["id"] in clube["titulares"]]
    cansados = [j["nome"] for j in titulares if j["energia"] < 50]
    if cansados:
        console.print(f" [yellow]Titulares cansados: {', '.join(cansados)}[/]")
    console.print("\n 1 - Jogar lance a lance  2 - Simular (normal)  3 - Simular (rápido)  4 - Ajustar plano  0 - Voltar")
    return ler_opcao(0, 4)


def mostrar_fim_de_jogo(estado, resultado):
    casa = estado["clubes"][resultado["mandante"]]
    fora = estado["clubes"][resultado["visitante"]]
    titulo("FIM DE JOGO")
    console.print(f" [bold {casa['cor']}]{casa['nome']}[/] [bold]{resultado['gm']} x {resultado['gv']}[/] [bold {fora['cor']}]{fora['nome']}[/]\n")
    estatisticas = resultado["estatisticas"]
    tabela = Table(header_style="bold")
    tabela.add_column("")
    tabela.add_column(casa["sigla"], justify="center")
    tabela.add_column(fora["sigla"], justify="center")
    for chave, nome in (("posse", "Posse %"), ("chutes", "Finalizações"), ("no_alvo", "No alvo"), ("faltas", "Faltas")):
        tabela.add_row(nome, str(estatisticas[casa["id"]][chave]), str(estatisticas[fora["id"]][chave]))
    console.print(tabela)
    console.print(" [bold]Súmula:[/]")
    mostrar_sumula(resultado["sumula"])
    pausar("Enter para continuar...")


def mostrar_resultados_rodada(estado, resultados, informacao, numero):
    titulo(f"RESULTADOS DA RODADA {numero}")
    for resultado in resultados:
        casa = estado["clubes"][resultado["mandante"]]
        fora = estado["clubes"][resultado["visitante"]]
        destaque = " [yellow]◄[/]" if estado["clube_id"] in (casa["id"], fora["id"]) else ""
        console.print(f" {casa['nome']:>22} [bold]{resultado['gm']} x {resultado['gv']}[/] {fora['nome']}{destaque}")
    sinal = f"{informacao['variacao']:+d}"
    cor = "green" if informacao["variacao"] > 0 else ("red" if informacao["variacao"] < 0 else "yellow")
    console.print(f"\n Confiança da diretoria: [{cor}]{sinal}[/] → {barra(estado['confianca'], 20)}")
    if informacao["trocados"]:
        console.print(f" [yellow]Desfalques substituídos na escalação: {', '.join(informacao['trocados'])}[/]")
    pausar("Enter para continuar...")


def mostrar_evento(evento):
    titulo("EVENTO DA SEMANA")
    console.print(f" {evento['texto']}\n")
    if not evento["opcoes"]:
        return evento["efeito"]
    for numero, opcao in enumerate(evento["opcoes"], start=1):
        console.print(f" {numero} - {opcao['texto']}")
    return evento["opcoes"][ler_opcao(1, len(evento["opcoes"])) - 1]["efeito"]


def mostrar_mensagem(texto, estilo="bold"):
    console.print(f"\n [{estilo}]{texto}[/]")
    pausar("Enter para continuar...")


def mostrar_final(resumo):
    titulo("FIM DA TEMPORADA" if "demitido" not in resumo["desfecho"] else "VOCÊ FOI DEMITIDO")
    cor = "green" if resumo["venceu"] else "red"
    console.print(f" [bold {cor}]{'VITÓRIA' if resumo['venceu'] else 'DERROTA'}: {resumo['desfecho']}[/]\n")
    console.print(f" Clube: {resumo['clube']}   Meta: {resumo['meta']}")
    console.print(f" Posição final: {resumo['posicao']}º   Pontos: {resumo['pontos']}   Saldo: {resumo['saldo']:+d}")
    console.print(f" Pontuação no ranking: [bold]{resumo['pontuacao']}[/]")
    pausar("Enter para continuar...")


def mostrar_ranking(linhas):
    titulo("RANKING DE TÉCNICOS")
    if not linhas:
        console.print(" Ninguém terminou uma temporada ainda.")
    else:
        tabela = Table(header_style="bold")
        for coluna in ("#", "Técnico", "Clube", "Pos", "Pts", "Pontuação", "Desfecho", "Data"):
            tabela.add_column(coluna)
        for numero, linha in enumerate(linhas, start=1):
            tabela.add_row(str(numero), *[str(linha.get(campo) or "-") for campo in ("tecnico", "clube", "posicao", "pontos", "pontuacao", "desfecho", "data")])
        console.print(tabela)
    pausar()


def escolher_save(saves):
    titulo("CARREGAR JOGO")
    if not saves:
        mostrar_mensagem("Nenhum jogo salvo encontrado.", "yellow")
        return None
    tabela = Table(header_style="bold")
    for coluna in ("#", "Técnico", "Clube", "Rodada", "Salvo em"):
        tabela.add_column(coluna)
    for numero, save in enumerate(saves, start=1):
        tabela.add_row(str(numero), save["tecnico"], save["clube"], str(min(save["rodada"], TOTAL_RODADAS)), save["salvo_em"])
    console.print(tabela)
    console.print(" [bold]0[/] Voltar")
    escolha = ler_opcao(0, len(saves))
    return saves[escolha - 1]["caminho"] if escolha else None
