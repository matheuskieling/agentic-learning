# Claude-Architect/simulados — Simulados da certificação CCAR-F

O coração do curso. Aqui ficam as questões no **formato do exame real**: cenário de negócio +
pergunta de decisão de arquitetura. Diferente das provas de módulo, misturam todos os domínios.

## O que tem aqui

```
simulados/
├── CLAUDE.md
├── simulado.py              ← runner solo: python3 Claude-Architect/simulados/simulado.py simulado-1.json
├── cenarios/
│   └── cenario-N.json       ← 20 questões de UM cenário do exame (N = 1..6)
└── simulado-N.json          ← simulado completo (N = 1..5): 60 questões · 120 min · 4 cenários · corte 72%
```

| Cenário | Tema | Banco |
|---------|------|-------|
| 1 | Customer Support Resolution Agent | `cenarios/cenario-1.json` |
| 2 | Code Generation with Claude Code | `cenarios/cenario-2.json` |
| 3 | Multi-Agent Research System | `cenarios/cenario-3.json` |
| 4 | Developer Productivity with Claude | `cenarios/cenario-4.json` |
| 5 | Claude Code for Continuous Integration | `cenarios/cenario-5.json` |
| 6 | Structured Data Extraction | `cenarios/cenario-6.json` |

| Simulado | Cenários sorteados | Ênfase extra |
|----------|--------------------|--------------|
| 1 | 1, 2, 3, 6 | panorama equilibrado (primeiro contato) |
| 2 | 1, 3, 4, 5 | agentes e erros (D1/D2) |
| 3 | 2, 4, 5, 6 | Claude Code e saída estruturada (D3/D4) |
| 4 | 1, 3, 5, 6 | contexto e confiabilidade (D5), pegadinhas |
| 5 | 2, 3, 4, 6 | "prova final": o mais difícil, alternativas todas plausíveis |

Cada simulado segue a distribuição do blueprint: **D1 16 · D2 11 · D3 12 · D4 12 · D5 9** (= 60),
em blocos de 15 questões por cenário. Cerca de 15% são de **múltipla resposta** ("Choose TWO.",
responda `answer A,C`).

## Como conduzir (Claude)

```bash
python3 engine/session.py start Claude-Architect/simulados/cenarios/cenario-1.json --id cenario
python3 engine/session.py start Claude-Architect/simulados/simulado-1.json --id simulado --no-shuffle
python3 engine/session.py answer B --id simulado
python3 engine/session.py answer A,D --id simulado     # múltipla resposta
python3 engine/session.py status --id simulado
```

**Idioma:** questões, alternativas e feedbacks em **inglês**, apresentados sem tradução; seus comentários
de instrutor em PT-BR (ver "Idioma" em `../CLAUDE.md`).

**Banco por cenário:** modo treino. Depois de cada resposta, explique por que cada alternativa errada
é tentadora e qual anti-padrão ela representa.

**Simulado completo:** modo prova. Sempre com **`--no-shuffle`**: as questões vêm em blocos de 15 por cenário, como no exame (a 1ª de cada bloco apresenta o cenário). Os bancos por cenário podem ser embaralhados. Anote o horário de início e cobre os 120 min. **Não dê dicas nem traduza**
durante a prova (o feedback do driver depois de cada resposta basta; aprofunde só no fim). Ao final:
1. Dê a nota e a nota **por domínio** (cada questão tem `"dominio"`).
2. Liste os anti-padrões em que o aluno caiu.
3. Registre o resultado com `python3 engine/aula.py note "..."` se houver aula ativa, e avalie os
   portões abaixo.

## Portões de prontidão (antes de marcar a prova real)

O aluno está **pronto** quando:
- ✅ tirou **≥ 80%** em **pelo menos 3 simulados completos diferentes**, feitos no tempo;
- ✅ nenhum domínio abaixo de **70%** no último simulado;
- ✅ o último simulado (5) foi feito **sem ter visto as questões antes**.

Abaixo de 72% num simulado: voltar à teoria dos domínios mais fracos e treinar os bancos por cenário
correspondentes antes do próximo simulado.

## Convenções das questões (para quem escrever mais)

- Formato do `engine/CLAUDE.md`, mais os campos `"cenario"` (1..6) e `"dominio"` ("D1".."D5") por
  questão (o motor ignora campos extras).
- Sempre `feedbacks` em **todas** as alternativas, dizendo por que é tentadora e por que está errada.
- Questões **originais**, em **inglês** (idioma da prova), coerentes com `../blueprint.md`. Distribua a posição da correta e
  evite que a alternativa mais longa seja sempre a certa.
