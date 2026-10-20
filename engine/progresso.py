#!/usr/bin/env python3
"""
Relatório de PROGRESSO de um curso — visão geral (não conduz aula, só reporta).

Diferente do `aula.py status` (que olha UMA sessão/módulo), este driver varre o curso
INTEIRO: soma os beats de todos os módulos (`<curso>/NN-*/roteiro.json`) e cruza com o
progresso salvo (`<curso>/.sessions/aula-*.json`) para mostrar, em formato de painel:

  • uma barra grande com o % do curso completo (beats e módulos concluídos);
  • uma linha por módulo com barra fina (blocos parciais) + concluídos/total;
  • o último beat concluído e quando (responde "onde paramos?");
  • o ritmo (beats/dia) como um sparkline + colunas dos últimos dias.

É agnóstico de curso: descobre o curso por `--curso <dir>` ou autodetecção (mesma regra
dos outros drivers). Só leitura — nunca altera progresso.

Cores ANSI: ligadas só quando a saída é um terminal (`--color auto`, padrão). Quando a
saída é capturada (pipe/agente), saem desligadas, então o texto fica limpo. Force com
`--color always` / `--color never`.

Uso:
    python3 engine/progresso.py [--curso AWS] [--color auto|always|never]
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime

import _common

WIDTH = 60          # largura de referência das réguas de seção
CURSO_BAR = 46      # largura da barra do curso completo
MOD_BAR = 12        # largura das barras por módulo
TITLE_W = 30        # largura da coluna de título do módulo
DAY_COL = 7         # largura de cada coluna do ritmo

# barra com preenchimento fino: cheios + um bloco parcial + trilho vazio
_FULL = "█"
_EMPTY = "░"
_PART = " ▏▎▍▌▋▊▉█"          # 8 níveis de bloco parcial
_SPARK = "▁▂▃▄▅▆▇█"          # sparkline do ritmo


# --- cores -------------------------------------------------------------------
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"


def _paint(text, *codes, on=True):
    if not on or not codes:
        return text
    return "".join(codes) + text + C.RESET


def _fmt_dt(iso):
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso).astimezone().strftime("%d/%m %H:%M")
    except (ValueError, TypeError):
        return None


def _dia_local(iso):
    """Dia (YYYY-MM-DD) na hora local: o carimbo é UTC, e 'iso[:10]' joga a noite no dia seguinte."""
    try:
        return datetime.fromisoformat(iso).astimezone().strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return iso[:10]


def _bar(frac, width):
    """Barra com um bloco parcial no final — leitura suave do percentual."""
    frac = max(0.0, min(1.0, frac))
    total = frac * width
    full = int(total)
    bar = _FULL * full
    if full < width:
        level = round((total - full) * 8)
        if level > 0:
            bar += _PART[level]
    bar += _EMPTY * (width - len(bar))
    return bar[:width]


def _spark(values):
    if not values:
        return ""
    mx = max(values) or 1
    return "".join(_SPARK[min(len(_SPARK) - 1, round(v / mx * (len(_SPARK) - 1)))]
                   for v in values)


def _rule(title, width, color):
    """Régua de seção: ──── Título ─────────────..."""
    left = f"──── {title} "
    line = left + "─" * max(0, width - len(left))
    return _paint(line, C.DIM, on=color)


def _trunc(s, w):
    return s if len(s) <= w else s[:w - 1].rstrip() + "…"


def _modulos(curso_root):
    """Lista (roteiro, session_state) por módulo, ordenada pelo número do módulo."""
    out = []
    for rot_path in sorted(glob.glob(os.path.join(curso_root, "[0-9]*", "roteiro.json"))):
        try:
            roteiro = _common.load_json(rot_path)
        except json.JSONDecodeError:
            continue
        if not roteiro or "beats" not in roteiro:
            continue
        modulo = roteiro.get("modulo", os.path.basename(os.path.dirname(rot_path)))
        sess_path = os.path.join(_common.sessions_dir(curso_root), f"aula-{modulo}.json")
        state = _common.load_json(sess_path)  # None se ainda não iniciado
        out.append((modulo, roteiro, state))
    return out


def cmd_progresso(args):
    color = args.color == "always" or (args.color == "auto" and sys.stdout.isatty())

    curso_root = _common.detectar_curso_root(args.curso)
    if not curso_root:
        raise SystemExit("Curso não detectado; informe --curso <dir>.")
    curso_nome = os.path.basename(curso_root.rstrip(os.sep))
    mods = _modulos(curso_root)
    if not mods:
        raise SystemExit(f"Nenhum módulo com roteiro.json encontrado em {curso_nome}.")

    tot_beats = tot_feitos = mods_concluidos = 0
    por_dia = {}
    ultimo = None  # (chave_ordem, modulo, beat_id, ts)
    dados = []  # (modulo, roteiro, state, feitos, n, concluido)

    for modulo, roteiro, state in mods:
        beats = roteiro["beats"]
        n = len(beats)
        status = (state or {}).get("status", {})
        concl = (state or {}).get("concluido_em", {})
        feitos = sum(1 for b in beats if status.get(b["id"]) == "visto")
        tot_beats += n
        tot_feitos += feitos
        concluido = n > 0 and feitos == n
        if concluido:
            mods_concluidos += 1
        # ritmo + último beat, a partir das datas carimbadas
        idx = {b["id"]: i for i, b in enumerate(beats)}
        for b_id, ts in concl.items():
            dia = _dia_local(ts)
            por_dia[dia] = por_dia.get(dia, 0) + 1
            # ordena por (data, módulo, posição do beat) — desempata beats do mesmo segundo
            chave = (ts, modulo, idx.get(b_id, -1))
            if ultimo is None or chave > ultimo[0]:
                ultimo = (chave, modulo, b_id, ts)
        dados.append((modulo, roteiro, state, feitos, n, concluido))

    # o módulo "atual" é o do último beat concluído; sem datas, o último em progresso
    modulo_atual = ultimo[1] if ultimo else next(
        (m for m, r, s, f, n, c in reversed(dados) if s is not None and not c), None)

    out = []

    # --- cabeçalho -----------------------------------------------------------
    out.append(_paint(f"📊 Progresso — Curso {curso_nome}", C.BOLD, on=color))
    out.append(_paint("═" * WIDTH, C.DIM, on=color))
    out.append("")

    # --- curso completo ------------------------------------------------------
    frac_curso = tot_feitos / tot_beats if tot_beats else 0
    bar = _bar(frac_curso, CURSO_BAR)
    bar = _paint(bar, C.CYAN, C.BOLD, on=color)
    out.append("  " + _paint("Curso completo", C.BOLD, on=color))
    out.append(f"  {bar}  {round(frac_curso * 100)}%")
    resumo = f"  {tot_feitos} / {tot_beats} beats   ·   {mods_concluidos} / {len(mods)} módulos ✅"
    out.append(_paint(resumo, C.DIM, on=color))
    out.append("")

    # --- módulos -------------------------------------------------------------
    out.append(_rule("Módulos", WIDTH, color))
    for modulo, roteiro, state, feitos, n, concluido in dados:
        frac = feitos / n if n else 0
        atual = modulo == modulo_atual
        if concluido:
            icon, cor = "●", (C.GREEN,)
        elif atual:
            icon, cor = "▶", (C.CYAN, C.BOLD)
        else:
            icon, cor = "·", (C.DIM,)
        titulo = _trunc(roteiro.get("titulo", ""), TITLE_W)
        seta = "  ← aqui" if atual else ""
        linha = (f"  {icon} {modulo}  {titulo:<{TITLE_W}}  {_bar(frac, MOD_BAR)}  "
                 f"{round(frac * 100):>3}%  {feitos:>2}/{n:<2}{seta}")
        out.append(_paint(linha, *cor, on=color))
    out.append("")

    # --- ritmo ---------------------------------------------------------------
    out.append(_rule("Ritmo", WIDTH, color))
    if por_dia:
        dias = sorted(por_dia)
        media = sum(por_dia.values()) / len(dias)
        recentes = dias[-7:]
        vals = [por_dia[d] for d in recentes]
        spark = _paint(_spark(vals), C.MAGENTA, C.BOLD, on=color)
        total = "beats/dia" if len(dias) <= 7 else "beats/dia (últimos 7)"
        out.append(f"  {spark}   média {media:.1f} {total}")
        out.append("")
        labels = "".join(f"{d[8:10]}/{d[5:7]}".center(DAY_COL) for d in recentes)
        counts = "".join(str(por_dia[d]).center(DAY_COL) for d in recentes)
        out.append("  " + _paint(labels, C.DIM, on=color))
        out.append("  " + _paint(counts, C.BOLD, on=color))
    else:
        out.append(_paint("  ainda sem datas registradas "
                          "(aparecem conforme você avança os beats).", C.DIM, on=color))
    out.append("")

    # --- último beat ---------------------------------------------------------
    if ultimo:
        _chave, modulo, b_id, ts = ultimo
        roteiro, state = next((r, s) for m, r, s in mods if m == modulo)
        titulo = next((b["titulo"] for b in roteiro["beats"] if b["id"] == b_id), b_id)
        ap = "~" if b_id in set((state or {}).get("concluido_aprox", [])) else ""
        out.append("  " + _paint(f"🎯 Último: M{modulo} · {b_id} — {_trunc(titulo, 40)}",
                                 C.BOLD, on=color))
        out.append("  " + _paint(f"   concluído {ap}{_fmt_dt(ts)}", C.DIM, on=color))

    print("\n".join(out))


def main():
    parser = argparse.ArgumentParser(description="Relatório de progresso de um curso (visão geral).")
    parser.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto",
                        help="cores ANSI (padrão: auto — só em terminal)")
    parser.set_defaults(func=cmd_progresso)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
