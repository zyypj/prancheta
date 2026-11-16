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
2. Na **Central do clube** você vê o elenco (com idade e valor de mercado), ajusta o plano de jogo, consulta a
   classificação, a chave da copa e o histórico das rodadas, entra no mercado da bola, vê a página de qualquer clube e
   salva o jogo.
3. A temporada alterna liga e copa. A liga tem 9 rodadas em turno único. A copa tem fase preliminar (os 4 clubes de
   menor força), quartas, semifinal e final em campo neutro, sempre em jogo único: empate vai para a disputa de
   pênaltis, cobrada e defendida pelo jogador.
4. Em **Próximo jogo**, escolha entre jogar lance a lance, simular assistindo (Enter avança), simular rápido ou ir
   direto para o resultado. Também dá para ver o adversário: posição, últimos jogos, plano e formação prováveis,
   destaques e desfalques. A simulação segue o seu plano e para no intervalo, em lesões, expulsões e pênaltis.
5. Durante a partida, todo lance começa na disputa de meio-campo e a jogada avança por três lugares: meio-campo, entrada
   da área e dentro da área. Cada lugar tem suas ações:
    - Meio-campo: tocar, enfiada, driblar, lançar ou abrir na ponta.
    - Entrada da área: tocar, tabelar, driblar, cruzar ou chutar de fora.
    - Dentro da área: chutar, driblar ou tocar.

   Ao driblar, escolha o drible (corte seco, caneta, chapéu ou arrancada). Ao chutar, escolha o tipo (colocado, forte ou
   cavadinha). Sem a bola, escolha dar o bote, pressão alta, fechar espaço, recuar a linha ou falta tática. Também
   aparecem oportunidades especiais: cara a cara com o goleiro, rebote, cruzamento (cabecear, voleio ou dominar),
   escanteio, falta na entrada da área e goleiro adiantado. Nos pênaltis, escolha o canto e a força, ou para onde o
   goleiro pula. Enter avança cada lance; digite 0 ou P para pausar e fazer substituições ou mudar o plano.
6. No **Mercado da bola**, compre jogadores de outros clubes fazendo uma proposta, contrate jogadores sem clube
   pagando luvas ou venda um jogador escolhendo entre as ofertas recebidas. O caixa do clube cresce com vitórias e
   com as fases da copa, e os outros clubes também contratam ao longo da temporada.
7. Depois de cada jogo aparecem os resultados, a confiança da diretoria, as notícias do mercado e um evento da semana.
   O jogo salva sozinho ao fim de cada etapa.

Em todas as narrações, súmulas e mensagens, o nome do jogador aparece depois da posição, por exemplo `ATA Rodrigão`.

## Objetivo

- Vitória: cumprir a meta do clube ao fim da temporada.
- Derrota: ser demitido (a confiança da diretoria chega a 0) ou terminar a temporada sem cumprir a meta.
- Pontuação: (pontos × 10 + saldo × 2 + bônus) × dificuldade do clube. Ser campeão da copa vale +250 de bônus. Vai
  para o ranking ao fim da temporada.

## Estrutura

```
prancheta/
├── main.py            menu, central do clube e fluxo das rodadas
├── config.py          constantes e caminhos
├── partida/           motor dos lances, pênaltis, narração e simulação
├── liga/              calendário, classificação, copa, temporada e eventos
├── mercado/           valores, compras, vendas, jogadores livres e mercado dos outros clubes
├── elenco/            geração de jogadores, escalação e substituições
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
