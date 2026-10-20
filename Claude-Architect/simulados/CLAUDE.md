# Claude-Architect/simulados — Simulados da certificação CCAR-F

O coração do curso. Aqui ficam as questões no **formato do exame real**: cenário de negócio +
pergunta de decisão de arquitetura. Diferente das provas de módulo, misturam todos os domínios.
Tudo foi escrito em out/2026 contra o **guia oficial v1.0**: cada questão mira um bullet específico
do guia (campos `ts` e `bullet`), e nenhuma situação se repete entre simulados.

## O que tem aqui

```
simulados/
├── CLAUDE.md
├── simulado.py              ← runner solo: python3 Claude-Architect/simulados/simulado.py simulado-1.json
├── cenarios/
│   └── cenario-N.json       ← 20 questões de UM cenário do exame (N = 1..6), modo treino
└── simulado-N.json          ← simulado completo (N = 1..5): 60 questões · 120 min · 4 cenários · corte 72%
```

| Cenário | Tema (texto oficial resumido) | Banco |
|---------|-------------------------------|-------|
| 1 | Customer Support Resolution Agent — Agent SDK, tools MCP `get_customer`/`lookup_order`/`process_refund`/`escalate_to_human`, 80%+ de resolução no 1º contato | `cenarios/cenario-1.json` |
| 2 | Code Generation with Claude Code — slash commands, CLAUDE.md, plan mode × execução direta | `cenarios/cenario-2.json` |
| 3 | Multi-Agent Research System — coordenador + busca web, análise de documentos, síntese, relatório com citações | `cenarios/cenario-3.json` |
| 4 | Developer Productivity with Claude — agente do **Agent SDK** com tools nativas (Read, Write, Bash, Grep, Glob) + MCP | `cenarios/cenario-4.json` |
| 5 | Claude Code for Continuous Integration — review automático, **geração de testes**, feedback em PR, poucos falsos positivos | `cenarios/cenario-5.json` |
| 6 | Structured Data Extraction — documentos não estruturados, JSON schema, casos de borda, integração downstream | `cenarios/cenario-6.json` |

| Simulado | Cenários sorteados | Observação |
|----------|--------------------|------------|
| 1 | 1, 2, 3, 6 | primeiro contato |
| 2 | 1, 3, 4, 5 | |
| 3 | 2, 4, 5, 6 | |
| 4 | 1, 3, 5, 6 | o bloco do cenário 5 concentra o D3 |
| 5 | 2, 3, 4, 6 | **simulado final**: o mais difícil no julgamento (duas alternativas quase certas) |

Cada simulado segue a distribuição do guia: **D1 16 · D2 11 · D3 12 · D4 12 · D5 9** (= 60), em
blocos de 15 questões por cenário, e cobre quase todos os 30 task statements (os que dependem de um
cenário não sorteado ficam de fora, como na prova real). **9 questões por simulado** são de
múltipla resposta ("Choose TWO."; responda `answer A,C`).

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

**Banco por cenário:** modo treino (pode embaralhar; cada enunciado é autocontido). Depois de cada
resposta, explique por que cada alternativa errada é tentadora e qual anti-padrão ela representa.

**Simulado completo:** modo prova. Sempre com **`--no-shuffle`**: as questões vêm em blocos de 15 por
cenário, como no exame (a 1ª de cada bloco apresenta o cenário). Anote o horário de início e cobre os
120 min. **Não dê dicas nem traduza** durante a prova (o feedback do driver depois de cada resposta
basta; aprofunde só no fim). Ao final:
1. Dê a nota e a nota **por domínio** (cada questão tem `"dominio"`), como no relatório oficial.
2. Liste os anti-padrões em que o aluno caiu e os task statements (`"ts"`) mais errados.
3. Registre o resultado com `python3 engine/aula.py note "..."` se houver aula ativa, e avalie os
   portões abaixo.

## Portões de prontidão (antes de marcar a prova real)

O aluno está **pronto** quando:
- ✅ tirou **≥ 80%** em **pelo menos 3 simulados completos diferentes**, feitos no tempo;
- ✅ nenhum domínio abaixo de **70%** no último simulado;
- ✅ o simulado 5 foi feito **sem ter visto as questões antes**;
- ✅ conferiu na [página da certificação](https://anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification)
  que o guia ainda é o **v1.0** (se houver versão nova, revisar as divergências antes).

Abaixo de 72% num simulado: voltar à teoria dos task statements mais errados e treinar os bancos por
cenário correspondentes antes do próximo simulado.

## Convenções das questões (para quem escrever mais)

- Formato do `engine/CLAUDE.md`, mais `"cenario"` (1..6), `"dominio"` ("D1".."D5"), `"ts"` ("2.3") e
  `"bullet"` (id do bullet do guia, ex. "2.3-S4") por questão (o motor ignora campos extras).
- Padrão de questão e controle de pistas: ver "Convenções específicas" em `../CLAUDE.md`.
  `feedbacks` em **todas** as alternativas, dizendo por que é tentadora e por que está errada.
- Questões **originais**, em **inglês**, coerentes com `../blueprint.md` (o guia oficial decide a
  resposta; detalhe volátil ou fora do escopo nunca decide uma questão).
