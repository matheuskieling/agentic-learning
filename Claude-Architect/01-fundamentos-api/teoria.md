# Módulo 01 — Fundamentos: o exame, a Messages API e a superfície de request

> **Domínio:** base para todos + D4 (task statement **4.7**). **Cenários onde mais cai:** 5 (CI),
> 6 (Structured Data Extraction) e qualquer questão de "migramos de modelo e quebrou".
>
> Teoria **voltada à prova**: para cada tópico, o fato-chave → o porquê → o anti-padrão que aparece
> como alternativa errada → como cai na prova. Código de aplicação em C#; JSON fica como é (formato real).

---

## 1. O exame

| Item | Valor |
|------|-------|
| Questões | **60**, múltipla escolha (1 correta) e múltipla resposta ("Escolha DUAS") |
| Tempo | **120 min** (≈ 2 min por questão), supervisionado, sem consulta |
| Aprovação | **720/1000** (escala), **sem penalidade por chute**: nunca deixe em branco |
| Cenários | **4 sorteados de um banco de 6**; as questões se penduram no cenário |

**Os 6 cenários:** (1) Customer Support Resolution Agent · (2) Code Generation with Claude Code ·
(3) Multi-Agent Research System · (4) Developer Productivity with Claude · (5) Claude Code for
Continuous Integration · (6) Structured Data Extraction.

**Os 5 domínios e pesos:**

| Domínio | Peso |
|---------|------|
| D1 — Arquitetura agêntica & orquestração | **27%** |
| D2 — Design de tools & integração MCP | 18% |
| D3 — Configuração & workflows do Claude Code | 20% |
| D4 — Prompt engineering & saída estruturada | 20% |
| D5 — Gestão de contexto & confiabilidade | 15% |

**Por que importa:** D1 sozinho é mais de 1/4 da prova; D1+D3+D4 somam 67%. Estude na proporção.

**Pegadinha de formato:** "sem penalidade por chute" significa que a estratégia certa é **marcar
tudo**. Nas questões "Escolha DUAS", ambas precisam estar certas.

**Como cai na prova:** não cai como pergunta; muda sua estratégia (ritmo de 2 min, não deixar em
branco, identificar o cenário antes de ler as alternativas).

---

## 2. O espírito da prova e os 10 anti-padrões

A prova quase nunca pergunta "o que é X". Ela descreve um sistema com um **sintoma** e pede a
**melhor** decisão. Três regras de desempate resolvem a maioria das questões:

1. **A correção mais simples que resolve vence.** Melhorar a descrição de uma tool vem antes de criar
   um classificador de roteamento; critério explícito vem antes de "um segundo modelo para checar o primeiro".
2. **Regra crítica (financeira, segurança, compliance) vai em código determinístico** (hook,
   validação, pré-requisito). Prompt é probabilístico: serve para *best-effort*.
3. **Meça antes de mexer.** Métrica agregada esconde falha por tipo/segmento.

**Os 10 anti-padrões clássicos** (aparecem como alternativas erradas; os módulos seguintes aprofundam):

| # | Anti-padrão | Correção | Módulo |
|---|-------------|----------|--------|
| 1 | Encerrar o loop lendo texto ("terminei") | Checar **`stop_reason`** | 06 |
| 2 | Limite de iterações como mecanismo **principal** de parada | `stop_reason`; limite só como *backstop* | 06 |
| 3 | Regra crítica imposta só por prompt | Hook / código | 06 |
| 4 | Escalonar por **confiança autodeclarada** | Critérios explícitos de escalonamento | 11 |
| 5 | Escalonar por **sentimento** | Sentimento ≠ complexidade | 11 |
| 6 | Erro genérico ("Operation failed") | Erro estruturado (categoria, retentável...) | 04 |
| 7 | Suprimir erro em silêncio (lista vazia como sucesso) | Propagar o erro com contexto | 04/11 |
| 8 | Tools demais num agente (ex.: 18) | 4–5 por agente; subagents especializados | 04 |
| 9 | Auto-revisão na **mesma sessão** | Revisão em sessão independente | 07 |
| 10 | Acurácia agregada mascarando falha por tipo | Quebrar por tipo de documento/campo | 11 |

**Como ler uma questão:** (1) identifique o cenário; (2) ache o **sintoma real** (não o que o
enunciado sugere de cara); (3) elimine alternativas que são anti-padrão; (4) entre as restantes,
fique com a **mais simples que ataca a causa**. Desconfie de alternativas que "adicionam um modelo
a mais", "aumentam o limite" ou "pedem ao modelo para ter cuidado".

---

## 3. Anatomia do request da Messages API

Tudo passa por **um endpoint**: `POST /v1/messages`. Tools, saída estruturada e thinking são
**recursos desse endpoint**, não APIs separadas. A API é **stateless**: a cada chamada você reenvia
o histórico inteiro.

```json
{
  "model": "claude-...",
  "max_tokens": 1024,
  "system": "Você é um assistente de suporte da ACME. Responda em português.",
  "messages": [
    { "role": "user", "content": "Qual o status do pedido 4411?" }
  ],
  "tools": [ ... ]
}
```

| Campo | O que é | Pegadinha |
|-------|---------|-----------|
| `model` | Qual modelo | Parâmetros aceitos **mudam por modelo** (seção 7) |
| `max_tokens` | Teto **de saída** (obrigatório) | É invisível ao modelo: corta no meio e vira `stop_reason: "max_tokens"` |
| `system` | Instruções de operador: papel, regras, contexto | Fica **fora** de `messages`; não é um `role` comum |
| `messages` | Histórico, alternando `user` / `assistant` | Você reenvia tudo a cada chamada (stateless) |
| `tools` | Definições (`name`, `description`, `input_schema`) | A `description` é o critério de seleção (Módulo 04) |

**Content blocks.** `content` pode ser uma string ou uma **lista de blocos**:

- `text` — texto.
- `tool_use` — o **modelo** pede para chamar uma tool: `id`, `name`, `input` (vem na mensagem `assistant`).
- `tool_result` — **você** devolve o resultado: `tool_use_id` (o id exato), `content`, opcional
  `is_error: true` (vai na mensagem `user`).
- Outros: `image`, `document`, `thinking`...

```json
{ "role": "assistant", "content": [
  { "type": "text", "text": "Vou consultar o pedido." },
  { "type": "tool_use", "id": "toolu_01A", "name": "get_order", "input": { "order_id": "4411" } }
]}
{ "role": "user", "content": [
  { "type": "tool_result", "tool_use_id": "toolu_01A", "content": "{\"status\":\"enviado\"}" }
]}
```

**Por que importa:** a prova mostra trechos assim e pergunta o que está errado. Os erros clássicos:
`tool_result` sem o `tool_use_id` exato; resultados de tools paralelas espalhados em várias
mensagens (devem ir **todos numa única mensagem `user`**); tool que falhou sem resultado (deve ir
com `is_error: true`).

**Anti-padrão:** achar que a API "lembra" a conversa e reenviar só a última mensagem.

**Como cai na prova:** cenários 1 e 6 (loop manual de tools; extração), geralmente como "o agente
perdeu o contexto" ou "o request retornou 400 depois de uma tool".

---

## 4. A resposta: content, `stop_reason` e `usage`

A resposta traz `content` (lista de blocos), **`stop_reason`** e **`usage`**.

**`stop_reason` (visão geral; o Módulo 06 aprofunda):**

| Valor | Significa | Ação |
|-------|-----------|------|
| `end_turn` | Terminou naturalmente | Apresente a resposta |
| `tool_use` | Quer chamar tool(s) | Execute, devolva `tool_result`, continue o loop |
| `max_tokens` | Bateu no teto de saída | Saída truncada: aumente ou continue |
| `stop_sequence` | Bateu numa stop sequence configurada | Trate conforme seu protocolo |
| `pause_turn` | Loop de tool **server-side** bateu no teto | Reenvie para continuar |
| `refusal` | Recusou por segurança — chega com **HTTP 200** | Cheque antes de ler `content` |

Fatos de prova:
- `content` pode **misturar** `text` e `tool_use`. **Ter texto não significa que terminou.**
- Pode vir **mais de um `tool_use`** (paralelo).
- **Recusa é HTTP 200.** Código que só olha o status HTTP trata recusa como sucesso vazio.

**`usage`:** `input_tokens`, `output_tokens` e, com caching, `cache_creation_input_tokens` /
`cache_read_input_tokens` (Módulo 10). Você paga entrada **e** saída, e como a API é stateless, o
histórico reenviado é cobrado **a cada turno**.

**Anti-padrão #1:** decidir que acabou procurando "terminei" / "FINAL ANSWER" no texto.

**Como cai na prova:** cenário 1 ou 3 ("o agente às vezes para antes de executar a tool") e
cenário 6 ("JSON vem cortado no fim": `max_tokens`, não "o modelo é ruim em JSON").

---

## 5. As quatro formas de construir

Da que exige mais código seu à mais pronta. **Escolha a mais simples que atende.**

| # | Forma | Quem roda o loop | Quem hospeda | Tools | Quando |
|---|-------|------------------|--------------|-------|--------|
| 1 | **Loop manual** (Messages API) | Você (`while stop_reason == "tool_use"`) | Você | Só as suas | Controle total do fluxo |
| 2 | **Tool Runner** (helper do SDK) | O SDK | Você | Só as suas | Agente com tools próprias sem escrever o loop |
| 3 | **Managed Agents** [beta] | A Anthropic | A Anthropic (sandbox por sessão) | Sandbox (bash, arquivos) + MCP + as suas | Loop **e** infraestrutura gerenciados; sessões longas |
| 4 | **Claude Agent SDK** | O SDK (é o harness do Claude Code) | Você | Nativas (Read, Edit, Bash, Grep...) + MCP + subagents + hooks | Agente "baterias inclusas" na sua infra |

Distinção que a prova explora: **Tool Runner ≠ Agent SDK.** O Tool Runner é um helper do SDK da API
que só automatiza o ciclo request → executar → repetir com **as suas** tools. O Agent SDK é o Claude
Code como biblioteca: tools nativas, hooks, subagents, permissões, sessões. Só o **Managed Agents**
hospeda o loop **e** a execução.

**Antes de "construir um agente":** muitas tarefas (classificar, extrair, resumir) são **uma
chamada** só. Agente é para tarefa multi-etapa, aberta, em que o modelo decide o caminho.

**Anti-padrão:** escolher a opção mais poderosa "por garantia" (Managed Agents/multiagente para
uma extração de um campo).

**Como cai na prova:** cenário 1 (Agent SDK, hooks), cenário 4 (tools nativas). A pegadinha é a
alternativa sofisticada demais para o problema.

---

## 6. Thinking e effort (task statement 4.7)

**Fatos-chave [volátil nos detalhes, estável no princípio]:**

- **Adaptive thinking** — `thinking: {"type": "adaptive"}` — o modelo decide **quando e quanto**
  pensar. **Substitui** o antigo `thinking: {"type": "enabled", "budget_tokens": N}`.
- Nos modelos novos, `budget_tokens` **retorna 400**.
- **`effort`** fica em **`output_config`** (não no topo): `low` / `medium` / `high` / `xhigh` / `max`.
  Controla profundidade de raciocínio e gasto de tokens. `low` para tarefa simples/subagent barato;
  `high`+ para trabalho que exige inteligência.
- O **default de `effort` pode mudar de um modelo para outro** → defina explicitamente e
  **re-calibre ao migrar**.

```json
{
  "model": "claude-...",
  "max_tokens": 16000,
  "thinking": { "type": "adaptive" },
  "output_config": { "effort": "high" },
  "messages": [ ... ]
}
```

**Por que:** o orçamento fixo de thinking obrigava você a adivinhar quanto o modelo precisava pensar;
o modo adaptativo + `effort` deixa o modelo dosar e te dá um único botão de custo × qualidade.

**Anti-padrões que aparecem como alternativa errada:**
- "Aumente `budget_tokens`" num modelo novo (400).
- "Coloque `effort` no topo do request" (o lugar é `output_config`).
- Trocar de modelo para economizar sem antes **medir o mesmo modelo com `effort` menor**.

**Como cai na prova:** cenário 5 (pipeline de CI que quebrou após trocar o modelo) e cenário 6
(extração com custo alto: baixar `effort` em tarefa simples).

---

## 7. Prefill, sampling e migração de modelo (task statement 4.7)

**Fatos-chave:**
- **Prefill do assistant** (terminar `messages` com uma mensagem `assistant` parcial, ex.: `{`, para
  forçar JSON) **retorna 400** nos modelos novos. Substitutos: **structured outputs**
  (`output_config.format`, Módulo 03) ou instrução no `system`.
- **`temperature`, `top_p`, `top_k`** são **rejeitados (400)** nos modelos mais novos (em alguns,
  só valores diferentes do padrão). Não dependa deles para "deixar determinístico": consistência vem
  de **critérios explícitos, exemplos e schema**.
- Em modelos novos, **forçar tool** via `tool_choice` `any`/`tool` também pode retornar 400 (Módulo 04).
- **Ao migrar de modelo: teste a forma do request.** Parâmetros aceitos **mudam por modelo**;
  suporte é por modelo (consulte capabilities/doc). Rode a suíte de requests reais contra o modelo
  novo **antes** de virar a chave, e re-calibre `effort`.

**Por que:** os modelos novos têm thinking sempre disponível e raciocinam antes de responder; prefill
e sampling manual brigam com isso. A API prefere te dar **garantias estruturais** (schema) a botões
estatísticos.

**Anti-padrões:**
- "Use prefill `{` para garantir JSON" → 400 nos modelos novos e sem garantia de schema.
- "`temperature: 0` resolve inconsistência" → rejeitado nos novos e ataca o sintoma errado.
- "Troque o model ID em produção e monitore os erros" → teste antes.

**Como cai na prova:** cenários 5 e 6. Enunciado típico: "depois de atualizar o modelo, o job
começou a retornar 400" ou "o time quer saída JSON consistente; um dev propõe prefill + temperatura
zero". Resposta: structured outputs / remover os parâmetros rejeitados / testar a forma do request.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| O loop precisa saber se terminou | Cheque `stop_reason`, nunca o texto |
| A resposta tem texto **e** `tool_use` | Execute as tools; não terminou |
| JSON chega cortado no fim | `stop_reason: "max_tokens"` → aumente `max_tokens` |
| HTTP 200 mas `content` vazio/estranho | Cheque `stop_reason: "refusal"` |
| Várias tools pedidas de uma vez | Execute; devolva **todos** os `tool_result` numa só mensagem `user` |
| Tool falhou | `tool_result` com `is_error: true` (nunca omita) |
| Quer controlar quanto o modelo pensa | `thinking: adaptive` + `output_config.effort` |
| `budget_tokens` / `temperature` / prefill deram 400 | Remova; use adaptive + effort / structured outputs / instrução no system |
| Vai migrar de modelo | Teste a forma do request e re-calibre `effort` antes do deploy |
| Tarefa é extrair/classificar uma coisa | Uma chamada, não um agente |
| Agente com tools próprias, você hospeda, sem escrever o loop | Tool Runner |
| Quer tools nativas, hooks, subagents (harness do Claude Code) | Claude Agent SDK |
| Quer loop **e** sandbox hospedados | Managed Agents |

## Glossário

- **Messages API** — endpoint único `POST /v1/messages`; stateless.
- **Content block** — unidade de conteúdo (`text`, `tool_use`, `tool_result`, `thinking`, `image`...).
- **`tool_use_id`** — id que liga o `tool_result` ao `tool_use` que o originou.
- **`stop_reason`** — por que o modelo parou; é o sinal de controle do loop.
- **`usage`** — contagem de tokens de entrada/saída/cache da chamada.
- **Adaptive thinking** — o modelo decide quando e quanto pensar; substitui `budget_tokens`.
- **`effort`** — botão de profundidade/custo em `output_config` (low → max).
- **Prefill** — começar a resposta do assistant por você; rejeitado nos modelos novos.
- **Tool Runner** — helper do SDK que roda o loop de tools para você.
- **Claude Agent SDK** — harness do Claude Code como biblioteca.
- **Managed Agents** — loop + sandbox hospedados pela Anthropic [beta].

## Cola de véspera

- **60 questões · 120 min · 720/1000 · sem penalidade por chute · 4 de 6 cenários.**
- Pesos: **D1 27** · D2 18 · D3 20 · D4 20 · D5 15.
- Desempate: **mais simples que resolve** · **crítico em código** · **medir antes**.
- Loop: **`stop_reason`** decide. Texto ≠ fim. `refusal` vem com **HTTP 200**.
- `tool_result` com **`tool_use_id` exato**, todos numa **única** mensagem `user`, falha com `is_error: true`.
- API **stateless**: reenvia histórico; `max_tokens` é teto **de saída**, invisível ao modelo.
- 4 formas: **manual → Tool Runner → Managed Agents → Agent SDK**; escolha a mais simples.
- 4.7: **adaptive thinking** (sem `budget_tokens`) · **`output_config.effort`** · **prefill, `temperature`/`top_p`/`top_k` → 400** nos novos · **migrou? teste a forma do request e re-calibre effort**.

## Perguntas de checagem

1. **A resposta trouxe um bloco `text` dizendo "vou verificar" e um `tool_use`. O loop terminou?**
   Não. `stop_reason` é `tool_use`: execute a tool e devolva o `tool_result`.
2. **Onde fica o `effort`?** Em `output_config` (`low`…`max`), não no topo do request.
3. **Um job passou a dar 400 após trocar de modelo; o request usa `temperature: 0` e prefill `{`. O que fazer?**
   Remover os dois; usar structured outputs (ou instrução no system) para formato; testar a forma do request no modelo novo.
4. **Qual a diferença entre Tool Runner e Agent SDK?** Tool Runner só roda o loop das **suas**
   tools; o Agent SDK é o harness do Claude Code (tools nativas, hooks, subagents). Ambos você hospeda.
5. **Por que a recusa é perigosa para código ingênuo?** Porque chega com HTTP 200; sem checar
   `stop_reason: "refusal"` o código trata como sucesso.
