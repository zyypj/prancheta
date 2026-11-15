# Prancheta

Jogo de terminal em Python em que você escolhe um dos 10 clubes fictícios da Liga Prancheta e precisa cumprir a meta da diretoria em 18 rodadas. Escale o time, monte o plano de jogo (formação, estilo, ofensividade e intensidade), faça substituições e decida os lances da partida, ou simule-a de acordo com o seu plano. O campo é redesenhado a cada jogada, mostrando onde a bola está.

O design completo está no [GDD](GDD.pdf).

Trabalho Prático 3 de Laboratório de Programação (Engenharia de Software, ULBRA, 2026/2).

## Status

Em desenvolvimento.

## Como instalar

Requer Python 3.10 ou superior.

```bash
pip install -r requirements.txt
```

## Como jogar

```bash
python main.py
```

## Objetivo

- Vitória: cumprir a meta do clube ao fim da temporada (título para os grandes, G4 para os médios, escapar do rebaixamento para os pequenos).
- Derrota: ser demitido (a confiança da diretoria chega a 0) ou terminar a temporada sem cumprir a meta.

## Estrutura

```
prancheta/
├── main.py            menu e laço principal
├── config.py          constantes e caminhos
├── partida/           motor dos lances, narração e simulação
├── liga/              rodadas e tabela
├── elenco/            escalação e substituições
├── interface/         campo, telas e leitura de entrada
├── persistencia/      save, load, ranking e arquivos
├── dados/             times.json, narracao.txt, ranking.csv e saves
├── docs/              GDD.docx editável
└── GDD.pdf            Game Design Document
```

## Integrantes

- Samuel Henrique
- Eguiedson Cardoso
- Otavio Rodrigues
- Lucas Henrique
