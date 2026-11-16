# Prancheta

Jogo de terminal em Python em que você escolhe um dos 10 clubes fictícios da Liga Prancheta e precisa cumprir a meta da
diretoria na temporada: 9 rodadas de liga e a Copa Prancheta em mata-mata. Escale o time, monte o plano de jogo (formação, estilo, ofensividade e intensidade), faça
substituições e decida os lances da partida, ou simule-a de acordo com o seu plano. O campo é redesenhado a cada jogada,
mostrando onde a bola está.

O design completo está no [GDD](GDD.pdf).

Trabalho Prático 3 de Laboratório de Programação (Engenharia de Software, ULBRA, 2026/2).

## Como instalar

Requer Python 3.10 ou superior.

```bash
pip install -r requirements.txt
```

## Como jogar

```bash
python main.py
```

1. No menu, escolha **Novo jogo**, digite o nome do técnico e escolha o clube. Cada clube tem uma meta: os grandes
   precisam ser campeões, os médios precisam ficar no G4 e os pequenos não podem cair.
2. Na **Central do clube** você vê o elenco (com idade e valor de mercado), ajusta o plano de jogo, treina o
   elenco, consulta a classificação, a chave da copa e o histórico das rodadas, entra no mercado da bola, vê a página de qualquer clube e
   salva o jogo.
3. A temporada alterna liga e copa. A liga tem 9 rodadas em turno único. A copa tem fase preliminar (os 4 clubes de
   menor força), quartas, semifinal e final em campo neutro, sempre em jogo único: empate vai para a disputa de
   pênaltis, cobrada e defendida pelo jogador.
4. Em **Próximo jogo**, escolha entre jogar lance a lance, simular assistindo (Enter avança), simular rápido ou ir
   direto para o resultado. Também dá para ver o adversário: posição, últimos jogos, plano e formação prováveis,
   destaques e desfalques. A simulação segue o seu plano e para no intervalo, em lesões, expulsões e pênaltis.

   Uma vez por semana, pela central do clube ou no pré-jogo, dá para **treinar** o elenco. Você escolhe o foco (finalização, passe,
   desarme, físico, goleiros ou recuperação), a intensidade (leve, normal ou pesado) e quem treina (titulares,
   reservas ou o elenco todo). Quem treina ganha +3 no atributo treinado durante o próximo jogo e tem chance de
   evoluir 1 ponto de vez (maior nos jovens, menor nos veteranos); a cada 2 evoluções a qualidade sobe 1 e o
   jogador se valoriza no mercado. O custo é a energia: o treino pesado cansa mais e pode lesionar alguém por uma
   rodada. O treino de recuperação devolve energia e não dá evolução. Treinar os reservas faz o elenco crescer
   sem cansar quem vai jogar.
5. Durante a partida, todo lance começa na disputa de meio-campo. A posse pode começar no campo de defesa, no
   meio-campo ou na intermediária, e a jogada avança por seis lugares, cada um com suas ações:
    - Campo de defesa: tocar, conduzir, lançar ou inverter o jogo.
    - Meio-campo: tocar, enfiada, driblar, lançar ou abrir na ponta.
    - Intermediária: tocar, enfiada, driblar, abrir na ponta ou chutar de muito longe.
    - Entrada da área: tocar, tabelar, driblar, cruzar ou chutar de fora.
    - Linha de fundo: cruzar, cruzar rasteiro para trás, driblar ou chutar sem ângulo.
    - Dentro da área: chutar, driblar ou tocar.

   Ao driblar, escolha o drible (corte seco, caneta, chapéu ou arrancada). Ao chutar, escolha o tipo (colocado, forte ou
   cavadinha). Sem a bola, escolha dar o bote, pressão alta, fechar espaço, recuar a linha ou falta tática. Também
   aparecem oportunidades especiais: cara a cara com o goleiro, rebote, cruzamento (cabecear, voleio, dominar, escorar
   ou bicicleta), escanteio (primeira ou segunda trave, curto, fechado ou ensaiado), falta na entrada da área (inclusive
   rolar para um companheiro) e goleiro adiantado. Nos pênaltis, escolha o canto e a força (colocado, forte ou
   paradinha), ou para onde o goleiro pula. Enter avança cada lance; digite 0 ou P para pausar e fazer substituições ou
   mudar o plano. Na simulação rápida, aperte P a qualquer momento para pausar ou N para voltar a assistir (funciona
   no terminal e no PyCharm com "Emulate terminal in output console" ligado). Na pausa e na tela de substituição, o
   auxiliar sugere até três trocas com o motivo (cansaço, amarelo, insatisfação, placar ou reserva melhor); digite
   A, B ou C para aplicar uma delas.

   Jogando lance a lance, algumas jogadas viram **minijogos** (umas três por partida), em três formatos:
    - Sequência de setas para digitar com W, A, S e D antes do tempo acabar: dribles (o chapéu é a mais longa),
      desarme quando o time dá o bote ou faz pressão alta, efeito na cobrança de falta direta e concentração no
      pênalti a favor.
    - Memória: as setas aparecem por um instante, somem e você digita de cabeça, na pontaria dos chutes.
    - Reflexo: apertar Enter assim que aparecer AGORA, no pênalti contra (quando o goleiro acerta o canto), na
      saída do goleiro e na batida do cara a cara, e nas cabeçadas.

   Acertar aumenta a chance da jogada (ou de defender) e errar diminui.

   Cerca de 30% dos lances começam numa das 19 jogadas especiais, cada uma com as suas escolhas: tiro de meta,
   lateral no ataque, contra-ataque de três contra dois, falta pelo lado, falta de longe, falta na meia-lua, sobra
   na entrada da área, erro do adversário na saída de bola, arrancada de um craque, pressão na saída do goleiro,
   escanteio conquistado, bola pelo alto, um contra um na linha de fundo, goleiro pressionado, virada de jogo,
   dois contra um, levantamento da intermediária, pivô de costas e contra-ataque sofrido (aqui quem decide é
   quem defende).

   Em cada partida você tem **3 revelações**. Quando uma pergunta mostra a opção **R**, digite R e escolha uma
   única opção para ver a chance dela dar certo; a porcentagem fica ao lado do nome e aí você decide. Nos chutes,
   a porcentagem é a chance de gol. Na defesa, você escolhe o que o goleiro faz no cara a cara (sair abafando, esperar ou fechar o ângulo) e
   às vezes como bloquear um chute (carrinho, fechar o ângulo ou deixar para o goleiro). Ainda podem acontecer desvio,
   frango, bola tirada em cima da linha, VAR revisando pênalti, simulação, impedimento duvidoso, reclamação,
   confusão, paralisação e chuva no meio do jogo, com centenas de frases de narração diferentes.
6. No **Mercado da bola**, compre jogadores de outros clubes fazendo uma proposta, contrate jogadores sem clube
   pagando luvas ou venda um jogador escolhendo entre as ofertas recebidas. Em **Sugestões do olheiro** aparecem até
   seis contratações que cabem no caixa, com o motivo (vira titular, posição carente, jovem promissor ou reforço de
   banco), e dá para contratar direto dali. Cada clube começa com 22 jogadores (máximo de 28), há 30 jogadores sem
   clube e, a cada semana, chegam 1 ou 2 dispensados do exterior. Os outros clubes também contratam ao longo da
   temporada.
7. O caixa cresce com bilheteria nos jogos em casa (maior quando o time vem vencendo), cota de TV por rodada, prêmio
   por vitória e empate, fases da copa, desafios, objetivos e eventos como patrocínio, amistoso, camisa nova e
   investidor. Em **Finanças e objetivos** fica o extrato da temporada por categoria.
8. Antes de cada jogo a diretoria lança um **desafio** conforme o favoritismo (vencer, não sofrer gols, golear, ter
   mais posse, escalar um jovem...). Cumprido, rende dinheiro, confiança e pontos no ranking. Também há cinco
   **objetivos da temporada**, como vencer 3 jogos seguidos ou chegar à semifinal da copa.
9. Depois de cada jogo aparecem os resultados, a confiança, o desafio, o dinheiro da semana e as notícias do
   mercado. Em seguida vem um evento da semana (aumento de salário, folga, treino especial, joia da base pedindo
   chance, proposta do exterior e outros) ou uma **discussão no vestiário**: pênalti perdido, expulsão, goleada,
   briga por posição ou vaidade entre artilheiros. Quem você apoia fica motivado; quem é contrariado fica
   insatisfeito e rende menos por algumas rodadas. O jogo salva sozinho ao fim de cada etapa.
10. De vez em quando, antes ou depois do jogo, acontece um **bastidor** (jogador gripado, provocação do
    adversário, ônibus atrasado, festa depois da vitória, bicho extra, revolta com a arbitragem) ou um evento da
    **torcida organizada** (mosaico que empurra o time no jogo em casa, protesto no aeroporto, cobrança no CT,
    festa no desembarque, briga punida). A imprensa também chama para **entrevistas**, muito mais nos clubes
    grandes; prometer vitória agrada a torcida, mas a diretoria cobra se o time perder o jogo seguinte.

Em todas as narrações, súmulas e mensagens, o nome do jogador aparece depois da posição, por exemplo `ATA Rodrigão`.

## Objetivo

- Vitória: cumprir a meta do clube ao fim da temporada.
- Derrota: ser demitido (a confiança da diretoria chega a 0) ou terminar a temporada sem cumprir a meta.
- Pontuação: (pontos × 10 + saldo × 2 + bônus) × dificuldade do clube. Ser campeão da copa vale +250 de bônus, cada
  desafio cumprido +25 e cada objetivo da temporada +60. Vai para o ranking ao fim da temporada.

## Estrutura

```
prancheta/
├── main.py            menu, central do clube e fluxo das rodadas
├── config.py          constantes e caminhos
├── partida/           motor dos lances, jogadas especiais, laço da partida, pênaltis, narração e simulação
├── liga/              calendário, classificação, copa, temporada, finanças, desafios, eventos e vestiário
├── mercado/           valores, compras, vendas, jogadores livres e mercado dos outros clubes
├── elenco/            geração de jogadores, escalação, substituições e treino
├── interface/         campo animado, telas, mercado, controles e leitura de entrada
├── persistencia/      save, load, ranking e arquivos
├── dados/             times.json, nomes.txt, narracao.txt, eventos.json, ranking.csv e saves
├── docs/              GDD.docx editável
└── GDD.pdf            Game Design Document
```

## Arquivos gerados

| Arquivo                       | Formato | Conteúdo                                                    |
|-------------------------------|---------|-------------------------------------------------------------|
| `dados/saves/<técnico>.json`  | JSON    | estado completo da temporada                                |
| `dados/ranking.csv`           | CSV     | técnico, clube, posição, pontos, pontuação, desfecho e data |
| `dados/sumulas/<técnico>.txt` | TXT     | súmula de cada partida do jogador                           |

## Integrantes

- Samuel Henrique
- Eguiedson Cardoso
- Otavio Rodrigues
- Lucas Henrique
