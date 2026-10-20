# Módulo 04 — Design de tools: descrições, erros estruturados, distribuição e `tool_choice`

> **Domínio D2 — Tool Design & MCP Integration** (18% da prova, dividido com o Módulo 05).
> **Task statements:** **2.1** descrições e fronteiras de tools · **2.2** erros estruturados em tools
> MCP · **2.3** distribuição de tools entre agentes e `tool_choice`.
> **Cenários onde cai:** 1 (Customer Support) · 3 (Multi-Agent Research) · 4 (Developer
> Productivity) · 6 (Structured Data Extraction).

**Ideia-mãe.** O modelo não vê o seu código: **escolhe** a tool pela descrição, **decide a
recuperação** pelo resultado (inclusive o erro) e **só usa** as tools que recebeu. Quase toda questão
daqui se resolve na **interface**, não com infraestrutura extra (classificador, roteador, modelo maior).
Mapa: seções 1–3 = TS 2.1 · 4–6 = TS 2.2 · 7–9 = TS 2.3 (cada fato cita o bullet do guia).

---

## 1. A descrição é o mecanismo de seleção

**Fatos de prova**
- A tool entra no request como `name` + `description` + `input_schema`, em `tools`, em **todo** request
  do loop. A `description` é o **principal mecanismo** de seleção (2.1-K1); descrição mínima → escolha
  instável entre tools parecidas.
- Boa descrição (2.1-K2, S1): **propósito e saída** · **formato de entrada** com exemplo · **exemplos
  de consulta** · **casos de borda** · **fronteira** (quando usar esta e quando usar a parecida).

```jsonc
// Corpo do POST /v1/messages
{ "model": "<modelo>", "max_tokens": 1024,
  "tools": [{ "name": "lookup_order",
    "description": "Returns status, items and shipping events for ONE order. Input: ORD- plus 8 digits (customers often type '#48213377'; add the prefix). Use for a specific purchase, e.g. 'order 48213377 never arrived'. Do NOT use to identify the customer: use get_customer. Unknown numbers return found=false (not an error).",  // ← AQUI: o que o modelo lê para escolher
    "input_schema": { "type": "object", "properties": { "order_number": { "type": "string" } }, "required": ["order_number"] } }],
  "messages": [{ "role": "user", "content": "Order 48213377 never arrived." }] }
```

- **Primeiro passo** quando tools parecidas com descrição mínima são confundidas: **reescrever e
  expandir as descrições** (Q2 oficial): baixo esforço, alta alavancagem, ataca a causa.
- **Desempate com few-shot (TS 4.2):** descrição mínima → descrição primeiro. Descrições já boas e
  pedido **genuinamente ambíguo** → 2–4 exemplos mostrando **por que** uma tool e não a alternativa.

**Por quê.** O modelo só vê a definição: "Retrieves X data" não diz que entrada aceita nem quando usar.

**Anti-padrões que aparecem como alternativa errada**
- 5–8 few-shot com descrições ainda mínimas; roteador por palavra-chave (over-engineering); modelo maior.
- **Consolidar** as duas tools: escolha **válida**, mas esforço maior do que um "primeiro passo" pede.

**Como cai na prova.** Cenários 1 e 4: "tool errada em X%, descrições de uma linha, *most effective
first step*?" → expandir descrições; "evaluate a proposal" de descrição completa → adotar.

---

## 2. Sobreposição: renomear e separar

**Fatos de prova**
- Descrições ambíguas ou sobrepostas causam **misrouting** (2.1-K3); exemplo do guia:
  `analyze_content` × `analyze_document` quase idênticas.
- **Renomear + reescrever** (2.1-S2): `analyze_content` → `extract_web_results`, com descrição
  específica de web. O nome é sinal: verbo genérico ("analyze") atrai qualquer pedido.
- **Separar** a tool genérica em tools com **contrato de entrada/saída** (2.1-S3): `analyze_document`
  → `extract_data_points`, `summarize_content`, `verify_claim_against_source`.

```jsonc
// Request do subagent de análise. ANTES: tool genérica
{ "model": "<modelo>",
  "tools": [{ "name": "analyze_document", "description": "Analyzes a document.",  // ← AQUI: sem propósito
              "input_schema": { "...": "document_id, instructions (texto livre)" } }],
  "messages": ["..."] }

// DEPOIS: propósito e contrato por tool (schemas abreviados)
{ "model": "<modelo>",
  "tools": [
    { "name": "extract_data_points", "description": "Numeric facts from ONE document -> [{metric, value, unit, page}].", "input_schema": { "...": "..." } },
    { "name": "summarize_content", "description": "3-7 bullet summary of ONE document.", "input_schema": { "...": "..." } },
    { "name": "verify_claim_against_source", "description": "ONE claim vs ONE document -> {verdict, excerpt}.", "input_schema": { "...": "..." } }
  ],
  "messages": ["..."] }
```

- **Separar × consolidar:** tool **genérica** com vários propósitos → **separar**; duas tools com
  descrição mínima → **descrição primeiro** ("consolidar" é o distrator de primeiro passo).

> **Na doc atual [volátil]:** a página de definição de tools sugere agrupar operações afins numa tool
> com parâmetro `action` (ex.: `create_pr`/`review_pr`/`merge_pr`). **Na prova, vale o guia:**
> sobreposição → renomear; tool genérica → separar com contrato; consolidar não é o primeiro passo.

**Por quê.** Descrições que "fazem a mesma coisa" viram cara-ou-coroa. A tool genérica deixa o modelo
decidir **o que** ela faz a cada chamada e devolve saída sem contrato que o próximo passo não consome.

**Anti-padrões que aparecem como alternativa errada**
- Parâmetro `mode`/`instructions` livre na genérica; normalizar a saída depois (regex).
- Juntar tudo numa tool; regra no prompt ou few-shot mantendo as definições sobrepostas.

**Como cai na prova.** Cenário 3: "claims com citação exata" vão para a tool de resumo, que promete as
mesmas "key claims". Cenário 4: tool genérica para três tarefas quebrando a automação → separar.

---

## 3. O system prompt também escolhe tools

**Fatos de prova**
- Instruções **sensíveis a palavra-chave** no system prompt criam associações não intencionais entre
  uma palavra e uma tool (2.1-K4) e podem **atropelar descrições bem escritas** → **revise o system
  prompt** (2.1-S4) e reescreva a regra pela **intenção** (ou remova-a).

```jsonc
// Request do agente de produtividade (cenário 4)
{ "model": "<modelo>",
  "system": "You help engineers with this repo. When the user mentions tests, run run_test_suite.",  // ← AQUI: gatilho por palavra
  "tools": [{ "name": "run_test_suite", "description": "Runs the full suite (~8 min) when asked to run or verify tests. NOT for explaining test code.", "input_schema": { "...": "..." } },
            { "name": "read_file", "description": "...", "input_schema": { "...": "..." } }],
  "messages": [{ "role": "user", "content": "Explain what tests/PaymentRetryTests.cs covers." }] }
// Resultado: roda a suíte apesar da descrição. Correção: "Run run_test_suite only when asked to run or verify tests."
```

- **Assinatura no enunciado:** o erro **segue uma palavra**, **persiste** com descrições boas, ou
  **começou** junto com uma mudança no prompt.

**Por quê.** Regra explícita "palavra → tool" no system prompt pesa mais que a nuance da descrição.

**Anti-padrões que aparecem como alternativa errada:** alongar ainda mais as descrições; few-shot por
cima da regra conflitante; classificador; mais palavras-chave na regra.

**Como cai na prova.** "Descrições avaliadas, mas o erro continua em pedidos com a palavra X" → root
cause = instrução por palavra-chave. "Alguém propõe few-shot" → revisar o prompt primeiro.

---

## 4. Erro de tool no MCP: `isError`

**Fatos de prova**
- No MCP, a falha de **execução** volta **dentro do resultado da tool** com **`isError: true`**
  (2.2-K1), não como exceção. Assim o **agente vê** a falha e decide.
- Duas camadas, dois nomes, **os dois corretos**: **`isError`** (camelCase) no resultado de
  `tools/call` do **MCP** (servidor → cliente); **`is_error`** (snake_case) no bloco `tool_result` da
  **Messages API** (host → modelo). Num agente com tools MCP (Agent SDK, Claude Code), o host repassa
  a falha ao modelo como `tool_result` com `is_error`.

```jsonc
// 1) Servidor MCP → cliente: resposta a tools/call (envelope JSON-RPC; não cai na prova)
{ "jsonrpc": "2.0", "id": 7,
  "result": {
    "content": [{ "type": "text", "text": "{\"errorCategory\":\"transient\",\"isRetryable\":true,\"description\":\"License service timed out after 5 s; safe to retry.\"}" }],
    "isError": true                                   // ← AQUI: flag do MCP
  } }

// 2) Host → modelo: próximo request à Messages API
{ "model": "<modelo>", "tools": ["..."],
  "messages": [ "...pergunta do usuário...", "...assistant com tool_use id toolu_01...",
    { "role": "user", "content": [{ "type": "tool_result", "tool_use_id": "toolu_01",
        "is_error": true,                             // ← AQUI: flag da API
        "content": "{\"errorCategory\":\"transient\",\"isRetryable\":true,\"description\":\"...\"}" }] } ] }
```

- O flag diz **que** falhou; o **conteúdo** diz **o que fazer** (§5). `errorCategory`/`isRetryable` são
  o padrão de metadados do guia dentro do `content`, não campos do protocolo.

**Por quê.** Falha devolvida como texto de sucesso ("Error: access denied") vira **conteúdo** que o
agente resume e cita; exceção que derruba a execução tira dele a chance de reagir.

**Anti-padrões que aparecem como alternativa errada:** erro como resultado normal, sem `isError`;
exceção que encerra a execução; mandar o modelo "descartar textos que começam com Error"; hook que
filtra por tamanho e some com o resultado.

**Como cai na prova.** A certa pode dizer "return the failure with the MCP isError flag and structured
metadata". `isError` não é erro de digitação de `is_error`.

---

## 5. Categorias de erro e `isRetryable`

**Fatos de prova** (2.2-K2)

| `errorCategory` | Exemplos | Repetir igual resolve? | O agente... |
|---|---|---|---|
| `transient` | timeout, serviço fora | **sim** (`isRetryable: true`) | tenta de novo, com espera |
| `validation` | entrada inválida | **não** como está | corrige o argumento |
| `business` | política (prazo, limite) | **não** (`false`) | explica a regra, oferece alternativa |
| `permission` | sem acesso, aprovação de admin | **não** (`false`) | diz quem libera ou escala |

- Metadados (2.2-S1): **`errorCategory`** + **`isRetryable`** (boolean) + **descrição legível** (o
  que falhou e o que resolveria).
- Negócio (2.2-S2): **`retriable: false`** (grafia do guia nesse bullet) + **explicação amigável ao
  cliente**, para o agente comunicar a regra em vez de inventar "problema técnico".
- **"Operation failed" uniforme** (2.2-K3) impede a recuperação: o agente retenta o permanente e
  desiste do transitório. **Retentável × não retentável** (2.2-K4): o metadado evita tentativas
  desperdiçadas.

```jsonc
// Servidor MCP → cliente: process_refund fora da política (cenário 1)
{ "jsonrpc": "2.0", "id": 12,
  "result": {
    "isError": true,
    "content": [{ "type": "text", "text": "{\"errorCategory\":\"business\",\"isRetryable\":false,\"description\":\"Refund denied: delivered 94 days ago; return window is 60 days.\",\"customerMessage\":\"This order is outside our 60-day return window. I can ask billing to review an exception.\"}" }]
    // ← AQUI (dentro do text): business + não retentável + mensagem amigável
  } }
```

No servidor (.NET), o handler monta esse resultado: `IsError = true` + um bloco de texto com o JSON,
via um helper como `ToolError(category, retryable, description, customerMessage)`.

**Por quê.** A categoria transforma a falha em **decisão** (repetir, corrigir, explicar, pedir acesso).
Sem ela o agente chuta e o cliente ouve "erro técnico".

**Anti-padrões que aparecem como alternativa errada**
- `{"error": "failed"}` para tudo; retry cego (no servidor ou no agente); stack trace cru.
- Permissão ou negócio marcados `transient`; só código interno (`POL-60D`); sucesso com `"denied"` opaco.
- Bloquear e escalar **tudo** para humano (a regra já está na tool; falta o agente saber explicá-la).

**Como cai na prova.** Cenário 1: reembolso fora da política retentado → `business` + `isRetryable:
false` + mensagem amigável; aprovação de admin marcada `transient` → é `permission`. Cenários 3 e 4:
"Operation failed" para tudo → root cause = erro uniforme.

---

## 6. Recuperação local e vazio válido vs. falha de acesso

**Fatos de prova**
- **Recuperação local** (2.2-S3): o subagent resolve o transitório **ali mesmo** (retry com espera) e
  **propaga ao coordenador só o que não resolveu**, com **o que tentou** e os **resultados parciais**.
- **Falha de acesso ≠ vazio válido** (2.2-S4): timeout/serviço fora/sem permissão = a consulta **não
  rodou** (decisão de retry); rodou e não achou nada = **sucesso** com zero resultados (informação).

```jsonc
// search_archive: (a) vazio VÁLIDO
{ "jsonrpc": "2.0", "id": 21, "result": { "isError": false,      // ← AQUI: sucesso
  "content": [{ "type": "text", "text": "{\"query\":\"port strike 2026\",\"sourcesSearched\":5,\"matches\":[]}" }] } }
// (b) FALHA DE ACESSO
{ "jsonrpc": "2.0", "id": 22, "result": { "isError": true,       // ← AQUI: falha
  "content": [{ "type": "text", "text": "{\"errorCategory\":\"transient\",\"isRetryable\":true,\"description\":\"Archive unreachable; no sources searched.\"}" }] } }

// O que o subagent devolve ao coordenador (resultado da chamada Task) quando sobrou algo
{ "status": "partial", "findings": ["..."],
  "unresolved": [{ "errorCategory": "transient", "source": "regional-archive",
    "attempted": "3 tries over 40 s, all timed out",           // ← AQUI: o que tentou
    "partialResults": "2 of 5 regional papers retrieved",       // ← AQUI: o parcial
    "alternatives": ["retry in 10 min", "national wire covers 3 of the missing papers"] }] }
```

**Por quê.** O coordenador não precisa ver cada soluço de rede, mas precisa do que **ficou faltando**
para decidir. O vazio disfarçado faz o agente **afirmar** algo falso ("não há estudos").

**Anti-padrões que aparecem como alternativa errada**
- **Supressão silenciosa:** `[]` com sucesso quando o backend caiu (mesmo com um "warning").
- Tratar vazio válido como erro; "chamar duas vezes e comparar"; retentar no servidor "até voltar".
- Propagar todo timeout sem tentar; retentar e devolver só "search unavailable"; **abortar o workflow**.

**Como cai na prova.** Cenário 3: fonte fora do ar vira "não há estudos". Cenário 4: índice de código
fora vira "pode apagar a função". Cenário 1: lookup vazio × timeout. O lado do coordenador é o TS 5.3
(Módulo 11).

---

## 7. Quantas e quais tools por agente

**Fatos de prova**
- Muitas tools num agente (**18 em vez de 4–5**) **degradam** a seleção: cada decisão fica mais
  complexa (2.3-K1).
- Tool **fora da especialidade** é mal usada (2.3-K2): a **síntese** fazendo **buscas na web**, sem os
  critérios de fonte do agente de busca.
- **Acesso escopado** (2.3-K3, S1): cada agente com **só as tools do seu papel**, mais tools de escopo
  cruzado **limitadas** para necessidades frequentes (seção 8). No Agent SDK, isso fica na
  **`AgentDefinition`** de cada subagent (description, system prompt, **tools**); o coordenador delega
  pela tool **`Task`**, que precisa estar no seu `allowedTools` (Módulo 07).

```ts
// Agent SDK (o SDK oficial é Python/TS; nomes de tools ilustrativos)
const options = {
  allowedTools: ["Task"],                                    // coordenador delega via Task (doc atual: Agent [volátil], M07)
  agents: {
    "web-search": { description: "...", prompt: "...", tools: ["web_search", "load_document"] },  // ← AQUI: tools do papel
    "synthesis":  { description: "...", prompt: "...", tools: ["verify_fact"] },  // ← AQUI: sem busca; só escopo cruzado
  },
};
```

- **Lendo o sintoma:** erros espalhados = **volume**; concentrados num par = **sobreposição** (§2); que
  seguem uma palavra = **system prompt** (§3).

**Por quê.** Cada tool a mais pesa em toda decisão, e tool disponível é tool usada.

**Anti-padrões que aparecem como alternativa errada:** todas as tools para todos "para serem
autossuficientes"; manter a tool e proibir no prompt; modelo maior; reescrever as 18 descrições; um
subagent por tool.

> **Na doc atual [volátil]:** catálogos grandes podem ser carregados sob demanda (tool search com
> `defer_loading`); o guia não cobra isso. **Na prova, "tools demais" se resolve distribuindo por papel.**

**Como cai na prova.** Cenário 1: agente "tudo-em-um" com 19 tools. Cenário 3: síntese com
`web_search`. Cenários 4 e 6: subagents com o mesmo pacote, um deles agindo fora do seu papel.

---

## 8. Tool de escopo cruzado e tool restrita

**Fatos de prova**
- **Escopo cruzado** (2.3-S3): necessidade **frequente e simples** de outro papel → **uma tool
  estreita** (ex.: `verify_fact` no agente de síntese), com os **casos complexos ainda pelo
  coordenador**. Na Q9 oficial, 85% das verificações eram simples e 15% pediam investigação.
- **Restrita no lugar de genérica** (2.3-S2): `fetch_url` → `load_document`, que **valida** se a URL é
  de documento e devolve erro de validação no resto. A restrição vira **código da tool**.

```jsonc
// Request do subagent de análise: tool restrita no lugar de fetch_url
{ "model": "<modelo>",
  "tools": [{ "name": "load_document",
    "description": "Loads ONE article or PDF report from an allowed domain. Other URLs (search pages, logins, social posts) return a validation error saying why.",  // ← AQUI: fronteira no contrato
    "input_schema": { "type": "object", "properties": { "url": { "type": "string" } }, "required": ["url"] } }],
  "messages": ["..."] }
```

**Por quê.** O escopo cruzado corta as idas e voltas no caso **comum** sem dar o pacote inteiro (menor
privilégio). A tool restrita tira a **capacidade** de errar, em vez de pedir que o agente não erre.

**Anti-padrões que aparecem como alternativa errada:** dar à síntese **todas** as tools de busca;
**acumular** verificações e mandar em lote no fim (dependência bloqueante); **pré-cache
especulativo**; manter `fetch_url` e listar domínios no prompt, filtrar depois com hook ou mantê-la
como fallback.

**Como cai na prova.** "X% simples, Y% complexas, cortar latência sem perder confiabilidade" → tool
escopada + complexos via coordenador. "Trocar a genérica por uma restrita?" → adotar.

---

## 9. `tool_choice`: `auto`, `any` e forçado

**Fatos de prova** (2.3-K4)

| `tool_choice` | Garante | Quando (guia) |
|---|---|---|
| `{"type": "auto"}` | nada: tool **ou** texto (padrão) | conversa; turnos após um passo forçado |
| `{"type": "any"}` | **alguma** tool (o modelo escolhe) | garantir chamada em vez de texto (2.3-S5); vários schemas, tipo desconhecido (4.3) |
| `{"type": "tool", "name": "..."}` | **aquela** tool | ela roda **primeiro** (`extract_metadata`); passos seguintes em turnos posteriores (2.3-S4) |

- `tool_choice` vale **por request**; nada muda sozinho no turno seguinte.

```jsonc
// Turno 1: força extract_metadata (o DOI alimenta o enriquecimento)
{ "model": "<modelo>", "max_tokens": 2048,
  "tools": [{ "name": "extract_metadata", "...": "..." }, { "name": "lookup_citations", "...": "..." },
            { "name": "enrich_author", "...": "..." }],
  "tool_choice": { "type": "tool", "name": "extract_metadata" },   // ← AQUI: só esta neste turno
  "messages": [{ "role": "user", "content": "<texto do artigo>" }] }
// Resposta: stop_reason "tool_use" com o tool_use de extract_metadata.

// Turno 2: devolve o resultado e libera o enriquecimento
{ "model": "<modelo>", "max_tokens": 2048, "tools": ["...as mesmas três..."],
  "tool_choice": { "type": "auto" },                                 // ← AQUI: o modelo escolhe o resto
  "messages": [ "<texto do artigo>", "...assistant com o tool_use toolu_07...",
    { "role": "user", "content": [{ "type": "tool_result", "tool_use_id": "toolu_07", "content": "{\"doi\":\"10.1000/xyz123\"}" }] } ] }
// "any" fica no mesmo lugar: "tool_choice": { "type": "any" } (ex.: extract_invoice/receipt/contract, tipo desconhecido)
```

**Por quê.** `auto` deixa o modelo responder em texto: bom para conversa, ruim quando o código
**precisa** de um `tool_use`. `any` fecha essa porta sem tirar a escolha da tool; o forçado fecha também
a escolha, útil quando a **ordem** importa no primeiro passo.

**Anti-padrões que aparecem como alternativa errada**
- **Instrução no prompt** "always call extract_metadata first" / "you must call a tool": probabilística.
- `any` quando a **ordem** importa (garante **uma** chamada, não **qual**); forçar uma tool específica
  com tipo de documento **desconhecido** (aí é `any`).
- Forçar a mesma tool em **todo** turno; `any` em agente conversacional; fundir as tools.
- Achar que texto com `stop_reason: "end_turn"` foi corte (corte é `"max_tokens"`).

> **Na doc atual [volátil]:** alguns modelos recentes (Opus 5.5, Sonnet 5.5, Fable 5.1, Mythos 5.1)
> recusam `any` e tool forçada com erro 400; outros aceitam. A API também tem `{"type": "none"}` e
> `disable_parallel_tool_use`, fora do guia. **Na prova, responda pelo guia:** `any` garante chamada
> de tool; forçado garante que aquela tool rode primeiro.

**Como cai na prova.** Cenários 1 e 6: "N% das respostas vêm em prosa" (triagem, extração) → `any`;
"o enriquecimento às vezes roda antes dos metadados" → forçar `extract_metadata` no 1º request.

---

## Tabela de decisão

| Se o enunciado mostra... | A resposta é... |
|---|---|
| Tools parecidas, descrições de uma linha, tool errada em X% | Expandir as descrições (primeiro passo) |
| Descrições boas, pedido genuinamente ambíguo | 2–4 few-shot com o porquê da escolha (TS 4.2) |
| Duas tools com nome/descrição sobrepostos | Renomear + reescrever |
| Tool genérica com vários propósitos, saída variável | Separar em tools com contrato |
| Erro que segue uma palavra, descrições boas | Revisar a regra por palavra-chave no system prompt |
| Falha devolvida como texto de sucesso | `isError: true` + metadados estruturados |
| "Operation failed" para tudo, retries desperdiçados | `errorCategory` + `isRetryable` + descrição legível |
| Violação de política retentada / "problema técnico" | `business`, `retriable: false`, mensagem amigável |
| Aprovação/permissão marcada como transitória | `permission`, não retentável |
| Timeout dentro do subagent | Retry local; propagar o resto com tentativa + parcial |
| `[]` quando o backend caiu | `isError` + `transient`; vazio só quando a consulta rodou |
| ~18 tools num agente, erros espalhados | Distribuir por papel, 4–5 por agente |
| Agente usando tool de outro papel | Restringir tools na `AgentDefinition` |
| Necessidade frequente e simples de outro papel | Tool de escopo cruzado; complexos via coordenador |
| Tool genérica mal usada (`fetch_url`) | Tool restrita que valida (`load_document`) |
| Texto quando o código precisa de tool | `tool_choice: {"type": "any"}` |
| Tool X precisa rodar primeiro | Forçar X no 1º request; depois `auto` |

## Glossário

- **Tool description** — o que o modelo lê para escolher a tool. **Misrouting** — chamar a tool errada.
- **Keyword-sensitive instruction** — regra do system prompt que liga uma palavra a uma tool.
- **Input/output contract** — schema de entrada e formato de saída definidos por tool.
- **`isError`** (MCP) / **`is_error`** (Messages API) — flag de falha no resultado da tool.
- **`errorCategory` / `isRetryable`** — transient/validation/business/permission; se repetir resolve.
- **Scoped / cross-role / constrained tool** — só as tools do papel; tool estreita de outro papel
  (`verify_fact`); alternativa restrita a uma genérica (`load_document`).

## Cola de véspera

- **Descrição = mecanismo principal de seleção.** Mínima → **reescrever é o primeiro passo**
  (consolidar é válido, mas não primeiro). Sobreposição → renomear; genérica → separar com contrato.
- **Regra por palavra-chave no system prompt** atropela boas descrições → revisar o prompt.
- **`isError`** (MCP) e **`is_error`** (API), ambos certos; a falha volta no resultado, não como exceção.
- **`errorCategory` + `isRetryable` + descrição legível**; "Operation failed" impede a recuperação.
  Negócio: `retriable: false` + mensagem amigável. Permissão: não retenta.
- **Subagent:** retry local; propaga o resto com o que tentou e o parcial. **Vazio válido ≠ falha.**
- **4–5 tools por agente**, escopo por papel; `verify_fact` para o simples e frequente;
  `fetch_url` → `load_document`.
- **`tool_choice`:** `auto` pode dar texto · `any` garante alguma tool · forçado garante aquela
  primeiro (resto nos turnos seguintes). [volátil] 400 e tool search nunca decidem questão.

## Perguntas de checagem

1. **Duas tools com descrição de uma linha são confundidas; um colega quer fundi-las. Primeiro passo?**
   Não: expandir as descrições; fundir é mudança maior.
2. **Descrições ótimas, mas pedidos com "content" vão para a tool de web. O que procurar?** Regra por
   palavra-chave no system prompt.
3. **`find_callers` devolve `[]` com o índice fora do ar. O que muda?** `isError: true` + `transient`;
   lista vazia só quando a busca rodou.
4. **`lookup_citations` às vezes roda antes de `extract_metadata`. Como garantir a ordem?** Forçar
   `extract_metadata` no 1º request; enriquecimento nos turnos seguintes, com `auto`.
