# Prancheta

Jogo de terminal em Python em que você é o técnico de um time numa liga de 8 clubes fictícios. Escale o time, escolha formação e postura, faça substituições e decida cada lance da partida: tocar, driblar, lançar, cruzar ou chutar. O campo é redesenhado a cada jogada, mostrando onde a bola está.

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

- Vitória: terminar a liga em 1º lugar.
- Derrota: terminar em último (rebaixado) ou ser demitido após 3 derrotas seguidas.

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
└── dados/             times.json, narracao.txt, ranking.csv e saves
```

## Integrantes

- Samuel Henrique
- Eguiedson Cardoso
- Otavio Rodrigues
- Lucas Henrique
