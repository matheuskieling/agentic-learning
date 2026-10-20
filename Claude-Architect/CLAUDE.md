# Curso 4 — Claude Certified Architect (Foundations) — preparação para a certificação

Curso de preparação para a certificação **Claude Certified Architect – Foundations (CCAR-F)** da
Anthropic. O objetivo é duplo: **passar na prova** e sair com **critério de arquiteto** para desenhar
sistemas com Claude: agentes, tools, MCP, Claude Code em equipe e em CI, saída estruturada e
confiabilidade.

A base de conhecimento do exame está em **`blueprint.md`**: os 30 task statements do guia oficial
com todos os bullets de *Knowledge of* / *Skills in*, fatos-chave, distratores típicos e as
divergências guia × doc atual. Todo conteúdo do curso deve respeitá-lo.

## Autoridade: o guia oficial decide

- **Fonte de verdade da prova:** o *Exam Guide* oficial **v1.0 (vigente desde jul/2026)**, baixado da
  [página da certificação](https://anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification)
  ([PDF](https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F6nizmqk8tpzpfjvt6qmmav7rh%2Fpublic%2F1783542750%2FClaude+Certified+Architect+%E2%80%93+Foundations+Exam+Guide.pdf)).
  "Exam items are written against these objectives." O curso foi **reconstruído em out/2026**
  contra esse guia: cada módulo = um conjunto de task statements; cada questão de prova, banco por
  cenário e simulado mira um bullet específico do guia (campos `ts` e `bullet`).
- **A doc atual** (code.claude.com, platform.claude.com, modelcontextprotocol.io) serve para
  exatidão técnica. **Quando ela diverge do guia, a resposta de prova é a do guia**; a divergência
  aparece na teoria como caixa `> **Na doc atual [volátil]:**`. Divergências conhecidas (tabela
  completa no `blueprint.md`): `tool_choice` `"any"`/forçado (corretos na prova; alguns modelos
  novos retornam 400), tool **`Task`** (doc atual: `Agent`), **`.claude/commands/`** (doc atual:
  fundidos em skills), `allowed-tools` **restringe** (doc atual: pré-aprova), Edit ambíguo → **Read +
  Write**. **Nenhuma questão do curso depende de uma divergência**, em nenhum dos dois sentidos.
- **Fora do escopo oficial** (não cai): fine-tuning, autenticação/billing, OAuth e protocolos de
  autenticação, deploy/hospedagem de MCP server, streaming/SSE, rate limit/quotas/cálculo de preço,
  **detalhes de prompt caching** (só saber que existe), tokenização, computer use, vision,
  embeddings, cloud providers, benchmarks, arquitetura interna/treino. Extras da doc que o guia não
  lista (thinking adaptativo, `effort`, task budgets, context editing, memory tool, tool search,
  Managed Agents...) aparecem no máximo como nota de 1–3 linhas.
- **Antes de marcar a prova:** confira na página da certificação se o guia ainda é o v1.0. Se houver
  versão nova, revise as divergências antes de fazer a prova.

## O exame (o que estamos mirando)

| Item | Valor |
|------|-------|
| Código | CCAR-F (Foundations), guia oficial v1.0 (jul/2026) |
| Formato | 60 itens de múltipla escolha e **múltipla resposta (o item diz quantas marcar)**, baseados em cenários |
| Tempo | 120 min, supervisionado (Pearson VUE, online ou centro de testes), sem consulta |
| Aprovação | escala 100–1000, corte **720**; relatório traz % de acerto por domínio; questão em branco conta como erro e não há penalidade por chute (dito no guia de fev/2026; a v1.0 não repete), então responda todas |
| Cenários | **4 sorteados de um banco de 6**; as questões se penduram no cenário |
| Público | arquiteto com ~6 meses de prática com Claude API, Agent SDK, Claude Code e MCP |

| Domínio | Peso | Task statements → módulos |
|---------|------|---------------------------|
| D1 — Agentic Architecture & Orchestration | **27%** | 1.1 → M01 · 1.4, 1.5 → M06 · 1.2, 1.3, 1.6 → M07 · 1.7 → M10 |
| D2 — Tool Design & MCP Integration | 18% | 2.1, 2.2, 2.3 → M04 · 2.4, 2.5 → M05 |
| D3 — Claude Code Configuration & Workflows | 20% | 3.1–3.4 → M08 · 3.5, 3.6 → M09 |
| D4 — Prompt Engineering & Structured Output | 20% | 4.1, 4.2 → M02 · 4.3, 4.4, 4.5 → M03 · 4.6 → M09 |
| D5 — Context Management & Reliability | 15% | 5.2 → M06 · 5.1, 5.4 → M10 · 5.3, 5.5, 5.6 → M11 |

**Os 6 cenários oficiais** (os bancos e simulados seguem exatamente esse formato):
1. **Customer Support Resolution Agent:** agente do Agent SDK com tools MCP `get_customer`,
   `lookup_order`, `process_refund`, `escalate_to_human`; meta de 80%+ de resolução no primeiro
   contato sabendo quando escalar. Domínios primários: D1, D2, D5.
2. **Code Generation with Claude Code:** time usando Claude Code com slash commands, CLAUDE.md, plan
   mode × execução direta. D3, D5.
3. **Multi-Agent Research System:** coordenador + subagents de busca web, análise de documentos,
   síntese e relatório; relatórios com citações. D1, D2, D5.
4. **Developer Productivity with Claude:** ferramentas de produtividade construídas com o **Agent
   SDK** (explorar codebase desconhecida, legado, boilerplate, automação) usando as tools nativas
   (Read, Write, Bash, Grep, Glob) e servidores MCP. D2, D3, D1.
5. **Claude Code for Continuous Integration:** reviews automáticos, **geração de testes** e
   feedback em PR; feedback acionável e poucos falsos positivos. D3, D4.
6. **Structured Data Extraction:** extração de documentos não estruturados, validação com JSON
   schema, casos de borda, integração downstream. D4, D5.

**Os desempates que valem para quase toda questão:** vence a **correção mais simples que ataca a
causa raiz** (descrição de tool antes de routing layer; critério explícito antes de segundo modelo);
**regra crítica (financeira, segurança, compliance) → código determinístico** (hook, pré-requisito),
não prompt; **critério explícito** bate "use seu bom senso"/"seja conservador"; o **primeiro passo
proporcional** vem antes de infraestrutura nova; **erro estruturado**, nunca silenciado nem
genérico.

## Foco do curso: PROVA, não prática

Este curso é **preparação para o exame**, não um curso "aprenda a usar o Claude". Por decisão do
aluno: **não há aulas práticas** (nada de `pratica.md`, laboratório ou API key). O volume do curso está
em **teoria enxuta voltada à prova + muitas questões + muitos simulados**.

- A teoria ensina **o que a prova cobra** e **como ela cobra**: fato-chave → por que → anti-padrão
  que aparece como alternativa errada → em qual cenário costuma cair.
- Exemplos de código aparecem só quando ajudam a reconhecer algo na prova (um JSON de `tool_use`,
  um `.mcp.json`, um hook). Quando houver código de aplicação, a **linguagem-base é C# (.NET)**:
  o aluno é dev .NET. JSON/YAML/shell ficam como são (é o formato real). O Agent SDK oficial é
  Python/TypeScript: hooks e `AgentDefinition` aparecem nessa forma, com a ideia explicada.
- **JSON sempre contextualizado:** ao citar um campo de request/response/schema, mostre o JSON
  **inteiro** do request (`model`, `max_tokens`, `system`, `messages`, `tools`, `tool_choice`...) e/ou
  da response (`content`, `stop_reason`, `usage`), com o campo marcado `// ← AQUI`. Pode encurtar o
  miolo de um schema com `/* ... */`, mas nunca omita as chaves de topo nem mostre só um trecho
  (`"tools": [...]`, `"tool_choice": {...}` soltos), mesmo onde o `teoria.md` usa trecho (pedido do
  aluno: sem o JSON inteiro ele não sabe onde a propriedade fica).
- **Linguagem dos exemplos (preferência salva):** no beat `intro` do Módulo 01, o agente lê
  `Claude-Architect/.sessions/preferencias.json`; se não existir, pergunta e grava
  `{ "linguagem": "<nome>" }`; nas retomadas, traduz ao vivo os trechos de código para ela.

## Idioma: aula em PT-BR, avaliação em INGLÊS

A prova real é **inteiramente em inglês**, então o curso treina a leitura em inglês desde já (pedido
do aluno):

- **Em PT-BR:** a aula. Teoria (`teoria.md`, `blueprint.md`), narração dos beats, explicações,
  dúvidas e os comentários do instrutor depois de cada questão.
- **Em inglês:** tudo que é avaliação. Quizzes, provas de módulo, bancos por cenário, simulados e a
  revisão `/revisar` (que sorteia desses mesmos bancos).
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
teoria, diga em qual dos 6 cenários aquilo costuma cair, qual task statement é e qual é a
"pegadinha" típica. Ao conduzir questões, depois de cada resposta, explique **por que cada
alternativa errada é tentadora** (é assim que a prova engana).

## Anatomia de um módulo

| Peça | Arquivo | Conteúdo |
|------|---------|----------|
| Roteiro | `NN-nome/roteiro.json` | beats: `intro` → teoria (t1..tn, cada um com mini-pergunta de checagem) → quiz (q1) → prova → fim |
| Teoria | `NN-nome/teoria.md` | por task statement: fatos de prova, por quê, distratores, "como cai na prova"; tabela de decisão, glossário, cola de véspera |
| Quiz | `apps/modulo-NN/questions.json` (+`quiz.py`) | **15** questões de fixação do conteúdo da aula (podem ser conceituais) |
| Prova | `provas/modulo-NN/questions.json` (+`prova.py`) | **20** questões **no formato do exame real** (cenário + decisão, distratores plausíveis), `feedbacks` por alternativa, 70% |

## Plano completo do curso

| # | Módulo | Diretório | Task statements (guia v1.0) |
|---|--------|-----------|------------------------------|
| 01 | O exame e a Messages API: request, histórico, tool use e o loop agêntico | `01-exame-e-api/` | orientação + 1.1 |
| 02 | Prompt engineering: critérios explícitos e few-shot | `02-prompt-engineering/` | 4.1, 4.2 |
| 03 | Saída estruturada, validação com retry e Batch API | `03-saida-estruturada/` | 4.3, 4.4, 4.5 |
| 04 | Design de tools: descrições, erros estruturados, distribuição e `tool_choice` | `04-design-de-tools/` | 2.1, 2.2, 2.3 |
| 05 | MCP no Claude Code e no agente + tools nativas | `05-mcp-e-tools-nativas/` | 2.4, 2.5 |
| 06 | Workflows com enforcement, hooks do Agent SDK e escalonamento | `06-enforcement-e-escalonamento/` | 1.4, 1.5, 5.2 |
| 07 | Orquestração multiagente: coordenador, subagents e decomposição | `07-multiagente/` | 1.2, 1.3, 1.6 |
| 08 | Configurando o Claude Code: CLAUDE.md, rules, commands/skills, plan mode | `08-claude-code-config/` | 3.1, 3.2, 3.3, 3.4 |
| 09 | Refinamento iterativo, CI/CD e review multi-instância/multi-pass | `09-claude-code-workflows-ci/` | 3.5, 3.6, 4.6 |
| 10 | Gestão de contexto, codebase grande e sessões | `10-contexto-e-sessoes/` | 5.1, 5.4, 1.7 |
| 11 | Propagação de erro, revisão humana e proveniência | `11-confiabilidade/` | 5.3, 5.5, 5.6 |

Ordem recomendada: 01 → 11, depois os bancos por cenário e os simulados.

## Simulados — `simulados/` (o coração do curso)

Ver `simulados/CLAUDE.md`. Resumo:
- **Banco por cenário** (`simulados/cenarios/cenario-N.json`, N=1..6): **20 questões por cenário**
  (120 no total), modo treino.
- **Simulados completos** (`simulados/simulado-N.json`, N=1..5): **60 questões, 120 min, 4 cenários**
  em blocos de 15, distribuição por domínio do guia (D1 16 · D2 11 · D3 12 · D4 12 · D5 9), corte
  **72%**. Nenhuma situação se repete entre simulados.
- **Portões de prontidão** antes de marcar a prova real (em `simulados/CLAUDE.md`).

Total do curso: 11×15 (quiz) + 11×20 (provas) + 120 (cenários) + 300 (simulados) = **805 questões**,
cobrindo os 240 bullets do guia.

## Estrutura de arquivos

```
Claude-Architect/
├── CLAUDE.md · AGENTS.md · README.md
├── blueprint.md              ← os 30 task statements do guia + divergências + out-of-scope
├── .sessions/                ← progresso (versionado no fork/branch; zerado na main)
├── NN-nome/{roteiro.json, teoria.md}
├── apps/modulo-NN/{questions.json, quiz.py}
├── provas/modulo-NN/{questions.json, prova.py}
└── simulados/{CLAUDE.md, simulado.py, cenarios/cenario-N.json, simulado-N.json}
```

## Convenções específicas (para quem escrever ou corrigir conteúdo)

- **Questões são originais**, em **inglês**, no formato do exame. As **chaves** do JSON (`pergunta`,
  `opcoes`, `correta`/`corretas`, `explicacao`, `feedbacks`) ficam em português (contrato do
  `engine/`). Campos extras (o motor ignora): `ts` em todas; `cenario`, `dominio`, `bullet` nas
  provas, bancos e simulados.
- **Padrão de questão de prova:** enunciado autocontido com situação concreta (sintoma, números,
  trecho de config) e pergunta de decisão; 4 alternativas (ou 5 com "Choose TWO."), **todas
  plausíveis**, de tamanho e estrutura parecidos; pelo menos duas erradas "fortes". Proibido
  distrator espantalho. **Controle de pistas:** a correta não pode ser sistematicamente a mais longa
  (nem a 2ª mais longa); posição balanceada; palavras de slogan também nas erradas. `feedbacks` em
  todas as alternativas (por que é tentadora, por que falha aqui).
- **Volatilidade:** detalhe de versão/modelo/beta nunca decide uma questão. Ensine o princípio do
  guia; trate o detalhe da doc atual como nota `[volátil]`.
- **Não reordene questões dentro de um banco já usado:** a revisão (`revisar.py`) identifica cada
  questão pelo índice (`m04-quiz#7`). Questão nova vai no fim do banco; correção é no lugar.
- **Progresso** em `Claude-Architect/.sessions/`: versionado no fork/branch do aluno; `main` zerada.

## Estado atual

- ✅ Curso completo e **reconstruído em out/2026 contra o guia oficial v1.0**: 11 módulos + 6 bancos
  por cenário + 5 simulados.
- 🎓 Começar/retomar: `/retomar-curso Claude-Architect` (ou "vamos começar o curso de Claude Architect").
