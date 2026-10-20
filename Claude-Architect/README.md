# Claude Certified Architect (Foundations) — como fazer o curso

Preparação para a certificação **Claude Certified Architect – Foundations (CCAR-F)** da Anthropic.
É um curso **focado na prova**: teoria enxuta sobre o que o exame cobra (e como ele tenta te
enganar), seguida de **muitas questões e simulados no formato real**.

- **Não precisa de API key** nem de prática de laboratório: tudo roda aqui no chat, com a sua
  assinatura do Claude.
- **Aulas em português; quizzes, provas e simulados em inglês**, como na prova real (que é toda em
  inglês). Assim você treina a leitura das questões desde o primeiro módulo.
- Exemplos de código em **C#** (você pode pedir outra linguagem no começo; a escolha fica salva).
- **805 questões** originais no formato do exame (quiz e prova por módulo, 6 bancos por cenário e 5
  simulados completos), cobrindo os 240 itens de conhecimento/habilidade do guia oficial.

## A prova

| Item | Valor |
|------|-------|
| Questões | 60, múltipla escolha e múltipla resposta (o item diz quantas marcar), baseadas em cenários |
| Tempo | 120 min, supervisionado, sem consulta |
| Aprovação | 720 numa escala de 100–1000 (responda todas: em branco conta como erro) |
| Cenários | 4 sorteados de 6 (atendimento, geração de código, pesquisa multiagente, produtividade dev, CI/CD, extração de dados) |

| Domínio | Peso |
|---------|------|
| Arquitetura agêntica & orquestração | 27% |
| Configuração & workflows do Claude Code | 20% |
| Prompt engineering & saída estruturada | 20% |
| Design de tools & integração MCP | 18% |
| Gestão de contexto & confiabilidade | 15% |

## Módulos

Cada módulo cobre um conjunto de *task statements* do guia oficial v1.0 da prova.

| # | Módulo | Task statements |
|---|--------|-----------------|
| 01 | O exame e a Messages API: request, histórico, tool use e o loop agêntico | orientação + 1.1 |
| 02 | Prompt engineering: critérios explícitos e few-shot | 4.1, 4.2 |
| 03 | Saída estruturada, validação com retry e Batch API | 4.3, 4.4, 4.5 |
| 04 | Design de tools: descrições, erros estruturados, distribuição e `tool_choice` | 2.1, 2.2, 2.3 |
| 05 | MCP no Claude Code e no agente + tools nativas | 2.4, 2.5 |
| 06 | Workflows com enforcement, hooks do Agent SDK e escalonamento | 1.4, 1.5, 5.2 |
| 07 | Orquestração multiagente: coordenador, subagents e decomposição | 1.2, 1.3, 1.6 |
| 08 | Configurando o Claude Code: CLAUDE.md, rules, commands/skills, plan mode | 3.1–3.4 |
| 09 | Refinamento iterativo, CI/CD e review multi-instância/multi-pass | 3.5, 3.6, 4.6 |
| 10 | Gestão de contexto, codebase grande e sessões | 5.1, 5.4, 1.7 |
| 11 | Propagação de erro, revisão humana e proveniência | 5.3, 5.5, 5.6 |
| — | **Simulados:** 6 bancos por cenário (20 questões cada) + 5 simulados completos (60 questões, 120 min) | todos |

Cada módulo tem: aula conduzida (teoria) → quiz de fixação (15) → prova no formato do exame (20, 70% para passar).

## Como fazer

### Aula guiada pelo agente (recomendado)
Abra o Claude Code na raiz do repositório e digite **`/retomar-curso Claude-Architect`** (ou diga
*"vamos começar o curso de Claude Architect"*). O agente explica um ponto por vez, aplica quiz e
prova, e salva onde você parou.

Para os simulados, peça: *"quero fazer o simulado 1"* ou *"me treina no cenário 5"*.

### Estudo solo
- `blueprint.md`: resumo do exame inteiro (ótimo para a véspera).
- `NN-nome/teoria.md`: a teoria de cada módulo.
- `python3 Claude-Architect/apps/modulo-NN/quiz.py` e `python3 Claude-Architect/provas/modulo-NN/prova.py`.
- `python3 Claude-Architect/simulados/simulado.py simulado-1.json` (ou `cenarios/cenario-3.json`).

## Quando marcar a prova

Quando tirar **≥ 80% em 3 simulados completos diferentes**, no tempo, sem nenhum domínio abaixo de
70%, e conferir que o guia oficial ainda é o **v1.0** (detalhes em `simulados/CLAUDE.md`).

> As questões são **originais**, escritas contra o
> [guia oficial v1.0](https://anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification)
> da Anthropic, que é a autoridade final. Onde a documentação atual diverge do guia (ex.:
> `tool_choice` forçado em modelos novos), o curso ensina a resposta do guia e marca a nuance como
> volátil.
