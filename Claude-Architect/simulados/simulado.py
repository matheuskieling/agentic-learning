#!/usr/bin/env python3
"""
Simulados do Claude Certified Architect (modo solo, pelo teclado).

Uso:
    python3 Claude-Architect/simulados/simulado.py simulado-1.json
    python3 Claude-Architect/simulados/simulado.py cenarios/cenario-3.json

Simulado completo: 60 questões, 120 min, sem consulta. Corte 72%.
"""

import os
import sys

ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), *[os.pardir]*2, "engine")
sys.path.insert(0, os.path.abspath(ENGINE_DIR))

from quiz_engine import run_quiz  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    # simulados completos seguem a ordem dos blocos de cenário; bancos por cenário podem embaralhar
    banco = sys.argv[1]
    run_quiz(os.path.join(os.path.dirname(os.path.abspath(__file__)), banco),
             embaralhar=banco.startswith("cenarios/"))
