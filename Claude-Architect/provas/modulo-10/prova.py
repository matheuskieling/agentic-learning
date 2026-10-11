#!/usr/bin/env python3
"""
Prova do Módulo 10 — Claude Certified Architect.

Uso:
    python3 Claude-Architect/provas/modulo-10/prova.py

Diferente do quiz da aula, a prova dá feedback por ALTERNATIVA: com base no que
você escolheu, explica por que sua resposta está certa ou errada, e — se errou —
qual é a certa e por quê. Aprovação: 70%.
"""

import os
import sys

ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), *[os.pardir]*3, "engine")
sys.path.insert(0, os.path.abspath(ENGINE_DIR))

from quiz_engine import run_quiz  # noqa: E402

QUESTOES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")

if __name__ == "__main__":
    run_quiz(QUESTOES)
