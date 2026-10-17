# Curso 4 — Claude Certified Architect (Foundations) — preparação para a certificação

Curso de preparação para a certificação **Claude Certified Architect – Foundations (CCAR-F)** da
Anthropic. O objetivo é duplo: **passar na prova** e sair com **critério de arquiteto** para desenhar
sistemas com Claude: agentes, tools, MCP, Claude Code em equipe e em CI, saída estruturada e
confiabilidade.

A base de conhecimento do exame (domínios, task statements, fatos-chave, anti-padrões) está em
**`blueprint.md`**, a referência que todo conteúdo do curso deve respeitar.

## O exame (o que estamos mirando)

| Item | Valor |
|------|-------|
| Código | CCAR-F (Foundations), guia oficial v1.0 (vigente desde jul/2026) |
| Formato | 60 questões de múltipla escolha / múltipla resposta, **baseadas em cenários** |
| Tempo | 120 min, supervisionado (Pearson VUE), sem consulta |
| Aprovação | **720/1000** (escala), sem penalidade por chute |
| Cenários | **4 sorteados de um banco de 6** e as questões se penduram neles (ver abaixo) |
| Público | arquiteto com ~6 meses de prática com Claude API, Agent SDK, Claude Code e MCP |

| Domínio | Peso | Módulos do curso |
|---------|------|------------------|
| D1 — Arquitetura agêntica & orquestração | **27%** | 06, 07 (+ hooks no 08) |
| D2 — Design de tools & integração MCP | 18% | 04, 05 (+ tools nativas no 08) |
| D3 — Configuração & workflows do Claude Code | 20% | 08, 09 |
| D4 — Prompt engineering & saída estruturada | 20% | 01, 02, 03 (+ revisão multi-pass no 07) |
| D5 — Gestão de contexto & confiabilidade | 15% | 10, 11 |

**Banco de 6 cenários do exame** (os simulados deste curso seguem exatamente esse formato):
1. Customer Support Resolution Agent (Agent SDK, tools MCP, escalonamento)
2. Code Generation with Claude Code (CLAUDE.md, plan mode, slash commands/skills)
3. Multi-Agent Research System (coordenador + subagents, tratamento de erro, proveniência)
4. Developer Productivity with Claude (tools nativas, servidores MCP, exploração de codebase)
5. Claude Code for Continuous Integration (`-p`, saída estruturada, Batch API, review multi-pass)
6. Structured Data Extraction (JSON schema, tool use, validação com retry)

**O "espírito" da prova** (cai em quase toda questão): vence a **correção mais simples que resolve**;
**regras críticas vão em código** (hooks/validação), não em prompt; **critérios explícitos** batem
"use seu bom senso"; **`stop_reason`** decide o loop; **erros estruturados**, nunca silenciados.

## Foco do curso: PROVA, não prática

Este curso é **preparação para o exame**, não um curso "aprenda a usar o Claude". Por decisão do
aluno: **não há aulas práticas** (nada de `pratica.md`, laboratório ou API key). O volume do curso está
em **teoria enxuta voltada à prova + muitas questões + muitos simulados**.

- A teoria ensina **o que a prova cobra** e **como ela cobra**: fato-chave → por que → anti-padrão
  que aparece como alternativa errada → em qual cenário costuma cair.
- Exemplos de código aparecem só quando ajudam a reconhecer algo na prova (um JSON de `tool_use`,
  um `.mcp.json`, um hook). Quando houver código de aplicação, a **linguagem-base é C# (.NET)**:
  o aluno é dev .NET. JSON/YAML/shell ficam como são (é o formato real).
- **Linguagem dos exemplos (preferência salva):** no beat `intro` do Módulo 01, o agente lê
  `Claude-Architect/.sessions/preferencias.json`; se não existir, pergunta e grava
  `{ "linguagem": "<nome>" }`; nas retomadas, traduz ao vivo os trechos de código para ela.

## Idioma: aula em PT-BR, avaliação em INGLÊS

A prova real é **inteiramente em inglês**, então o curso treina a leitura em inglês desde já (pedido
do aluno):

- **Em PT-BR:** a aula. Teoria (`teoria.md`, `blueprint.md`), narração dos beats, explicações,
  dúvidas e os comentários do instrutor depois de cada questão.
- **Em inglês:** tudo que é avaliação. Quizzes, provas de módulo, bancos por cenário, simulados e a
  revisão `/revisar` (que sorteia desses mesmos bancos). Os arquivos de questões já estão em inglês.
- **Ao conduzir questões:** apresente enunciado e alternativas **em inglês, como o driver mostra,
  sem traduzir**, e repasse o feedback do banco também em inglês. Os rótulos do `engine/` (`Questão`,
  `Resultado`...) são do motor compartilhado e ficam em PT; não precisa repeti-los ao aluno. Depois do
  feedback, a sua análise ("por que cada errada é tentadora") é em PT-BR.
- **Mini-perguntas de checagem** (o `checkpoint` dos beats de teoria): formule a pergunta em inglês,
  no estilo do exame, traduzindo o texto do roteiro ao vivo. O aluno responde no idioma que quiser e a
  discussão segue em PT-BR.
- **Vocabulário:** em quiz/prova/banco por cenário, se o aluno travar numa palavra, explique o termo
  (sem traduzir a questão inteira). Em **simulado completo**, nada de tradução: é condição de prova.

## O formato do curso: aula ao vivo (one-on-one)

Idêntico ao padrão da plataforma (ver `../CLAUDE.md` e `../engine/CLAUDE.md`). O Claude **conduz**:
`python3 engine/aula.py current` (ou `start Claude-Architect/NN-nome/roteiro.json`), narra os
`pontos` com as próprias palavras, para no `checkpoint`, só faz `next` quando o aluno confirma,
registra dúvidas com `note`, e em beats `quiz`/`prova` dispara o `engine/session.py`.

Regra para o instrutor neste curso: **sempre amarrar ao formato da prova**. Ao fim de cada beat de
teoria, diga em qual dos 6 cenários aquilo costuma cair e qual é a "pegadinha" típica. Ao conduzir
questões, depois de cada resposta, explique **por que cada alternativa errada é tentadora** (é assim
que a prova engana).

## Anatomia de um módulo

| Peça | Arquivo | Conteúdo |
|------|---------|----------|
| Roteiro | `NN-nome/roteiro.json` | beats: `intro` → teoria (t1..tn, cada um com mini-pergunta de checagem) → quiz (q1) → prova → fim |
| Teoria | `NN-nome/teoria.md` | fatos de prova, anti-padrões, "como cai na prova", tabela de decisão, glossário, resumo de 1 página |
| Quiz | `apps/modulo-NN/questions.json` (+`quiz.py`) | **15** questões curtas para fixar |
| Prova | `provas/modulo-NN/questions.json` (+`prova.py`) | **20** questões **em estilo de cenário**, `feedbacks` por alternativa, 70% |

## Plano completo do curso

**Legenda:** ✅ pronto · 🔜 próximo · ⬜ planejado.

| # | Módulo | Diretório | Task statements (blueprint) | Status |
|---|--------|-----------|------------------------------|--------|
| 01 | Fundamentos: o exame, a Messages API e a superfície de request | `01-fundamentos-api/` | base + 4.7 | ✅ |
| 02 | Prompt engineering: critérios explícitos, few-shot, refinamento iterativo | `02-prompt-engineering/` | 4.1, 4.2, 3.5 | ✅ |
| 03 | Saída estruturada, validação com retry e Batch API | `03-saida-estruturada/` | 4.3, 4.4, 4.5 | ✅ |
| 04 | Design de tools: descrições, erros estruturados, `tool_choice`, tool search | `04-design-de-tools/` | 2.1, 2.2, 2.3, 2.6 | ✅ |
| 05 | MCP: arquitetura, transportes, escopos, `.mcp.json`, autenticação | `05-mcp/` | 2.4 | ✅ |
| 06 | O loop agêntico, enforcement com hooks e handoff humano | `06-agentic-loop/` | 1.1, 1.4, 1.5 | ✅ |
| 07 | Orquestração multiagente, decomposição, review multi-pass e sessões | `07-multiagente/` | 1.2, 1.3, 1.6, 1.7, 4.6 | ✅ |
| 08 | Configurando o Claude Code: CLAUDE.md, rules, skills, subagents, permissões, tools nativas | `08-claude-code-config/` | 3.0–3.4, 2.5 | ✅ |
| 09 | Claude Code em CI/CD e refinamento iterativo | `09-claude-code-cicd/` | 3.5, 3.6 | ✅ |
| 10 | Gestão de contexto: janela, caching, compaction, context editing, memória | `10-gestao-de-contexto/` | 5.1, 5.4, 5.7, 5.8, 4.8 | ✅ |
| 11 | Confiabilidade: escalonamento, propagação de erro, revisão humana, proveniência | `11-confiabilidade/` | 5.2, 5.3, 5.5, 5.6 | ✅ |

Ordem recomendada: 01 → 11, depois os simulados. Os módulos 06 e 07 (D1, 27%) são os mais densos.

## Simulados — `simulados/` (o coração do curso)

Ver `simulados/CLAUDE.md`. Resumo:
- **Banco por cenário** (`simulados/cenarios/cenario-N.json`, N=1..6): **20 questões por cenário**
  (120 no total), para treinar um cenário de cada vez.
- **Simulados completos** (`simulados/simulado-N.json`, N=1..5): **60 questões, 120 min, 4 cenários**
  do banco de 6, distribuição por domínio do blueprint (27/18/20/20/15), corte **72%**.
- **Portões de prontidão** antes de marcar a prova real (em `simulados/CLAUDE.md`).

Total do curso: 11×15 (quiz) + 11×20 (provas) + 120 (cenários) + 300 (simulados) ≈ **800 questões**.

## Estrutura de arquivos

```
Claude-Architect/
├── CLAUDE.md · AGENTS.md · README.md
├── blueprint.md              ← referência do exame (domínios, task statements, fatos, anti-padrões)
├── .sessions/                ← progresso (versionado no fork/branch; zerado na main)
├── NN-nome/{roteiro.json, teoria.md}
├── apps/modulo-NN/{questions.json, quiz.py}
├── provas/modulo-NN/{questions.json, prova.py}
└── simulados/{CLAUDE.md, cenarios/cenario-N.json, simulado-N.json}
```

## Convenções específicas

- **Volatilidade.** O ecossistema Claude muda rápido (modelos, betas, flags). O `blueprint.md` marca
  como **[volátil]** os detalhes de versão/modelo. Em aula, ensine o **princípio** (o que a prova
  cobra) e trate o detalhe volátil como "confira na doc atual". Questões de prova evitam depender de
  detalhe volátil, salvo quando ele é o próprio ponto (ex.: "`any` forçado retorna 400 em modelos
  novos → use structured outputs").
- **Questões são originais**, escritas em **inglês** (o idioma da prova), no estilo cenário do exame,
  com múltipla resposta como "Choose TWO.". As **chaves** do JSON (`pergunta`, `opcoes`, `correta`,
  `feedbacks`...) continuam em português porque são o contrato do `engine/`; só os valores são em inglês.
- **Não reordene questões dentro de um banco:** a revisão (`revisar.py`) identifica cada questão pelo
  índice (`m04-quiz#7`). Questão nova vai no fim do banco.
- **Progresso** em `Claude-Architect/.sessions/`: versionado no fork/branch do aluno; `main` zerada.

## Estado atual

- ✅ Curso completo: 11 módulos + simulados.
- 🎓 Começar/retomar: `/retomar-curso Claude-Architect` (ou "vamos começar o curso de Claude Architect").
