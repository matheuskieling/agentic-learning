# Claude Certified Architect (Foundations) — como fazer o curso

Preparação para a certificação **Claude Certified Architect – Foundations (CCAR-F)** da Anthropic.
É um curso **focado na prova**: teoria enxuta sobre o que o exame cobra (e como ele tenta te
enganar), seguida de **muitas questões e simulados no formato real**.

- **Não precisa de API key** nem de prática de laboratório: tudo roda aqui no chat, com a sua
  assinatura do Claude.
- Exemplos de código em **C#** (você pode pedir outra linguagem no começo; a escolha fica salva).
- ~**800 questões** originais: quiz e prova por módulo, 6 bancos por cenário e 5 simulados completos.

## A prova

| Item | Valor |
|------|-------|
| Questões | 60, múltipla escolha e múltipla resposta, baseadas em cenários |
| Tempo | 120 min, supervisionado, sem consulta |
| Aprovação | 720/1000 |
| Cenários | 4 sorteados de 6 (atendimento, geração de código, pesquisa multiagente, produtividade dev, CI/CD, extração de dados) |

| Domínio | Peso |
|---------|------|
| Arquitetura agêntica & orquestração | 27% |
| Configuração & workflows do Claude Code | 20% |
| Prompt engineering & saída estruturada | 20% |
| Design de tools & integração MCP | 18% |
| Gestão de contexto & confiabilidade | 15% |

## Módulos

| # | Módulo |
|---|--------|
| 01 | Fundamentos: o exame, a Messages API e a superfície de request |
| 02 | Prompt engineering: critérios explícitos, few-shot, refinamento iterativo |
| 03 | Saída estruturada, validação com retry e Batch API |
| 04 | Design de tools: descrições, erros estruturados, `tool_choice`, tool search |
| 05 | MCP: arquitetura, transportes, escopos, `.mcp.json`, autenticação |
| 06 | O loop agêntico, enforcement com hooks e handoff humano |
| 07 | Orquestração multiagente, decomposição, review multi-pass e sessões |
| 08 | Configurando o Claude Code: CLAUDE.md, rules, skills, subagents, permissões |
| 09 | Claude Code em CI/CD e refinamento iterativo |
| 10 | Gestão de contexto: janela, caching, compaction, context editing, memória |
| 11 | Confiabilidade: escalonamento, propagação de erro, revisão humana, proveniência |
| — | **Simulados:** 6 bancos por cenário (20 questões cada) + 5 simulados completos (60 questões, 120 min) |

Cada módulo tem: aula conduzida (teoria) → quiz (15) → prova (20, 70% para passar).

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
70% (detalhes em `simulados/CLAUDE.md`).

> As questões são **originais**, baseadas no blueprint público do exame. O guia oficial da Anthropic
> (Partner Academy) é a autoridade final; detalhes de versão de modelo mudam rápido.
