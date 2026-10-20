# Módulo 06 — Workflows com enforcement, hooks do Agent SDK e escalonamento

> **TS:** **1.4** (enforcement e handoff), **1.5** (hooks do Agent SDK: interceptação e normalização),
> **5.2** (escalonamento e ambiguidade). Domínios **D1** (27%) e **D5** (15%).
> **Onde cai:** cenário **1** (Customer Support, "em profundidade"), e também **4** e **3**.

Cenário 1: agente de suporte no **Claude Agent SDK** com tools MCP `get_customer`, `lookup_order`,
`process_refund`, `escalate_to_human` e meta de **80%+ de first-contact resolution** "sabendo quando
escalar". O módulo responde: **o que tem que ser garantido em código**, **como o código intercepta
tools** e **quando passar o caso a um humano**.

---

## 0. Ponte com o M01: onde o enforcement entra no loop

No M01: o modelo pede tools (`stop_reason: "tool_use"`), o harness executa, anexa o `tool_result` ao
histórico e chama de novo, até `"end_turn"`. O enforcement mora **no harness**, antes da execução e
antes de o modelo ler o resultado:

```
modelo pede tool ──▶ [PreToolUse]  pode NEGAR ou ajustar a chamada ──▶ tool executa
                                                                          │
modelo lê resultado ◀── [PostToolUse] pode TRANSFORMAR o resultado ◀──────┘
```

O modelo continua decidindo **qual** tool chamar (M01/M04); o hook só garante o que **não pode falhar**.

---

## 1. Enforcement programático × orientação por prompt (1.4, 1.5)

**Fatos de prova**
- Instrução no prompt (system prompt, few-shot) é **conformidade probabilística**: melhora a média,
  mas tem **taxa de falha não nula**. Nenhum "MANDATORY" em maiúsculas zera essa taxa.
- **Enforcement programático** (hook, prerequisite gate, validação na própria tool) é **garantia
  determinística**: o código roda em toda chamada, o modelo não tem como "esquecer".
- Quando a regra exige **conformidade garantida** (identidade antes de operação financeira, teto de
  valor, compliance, PII), a resposta é **código**. Prompt fica para o que é julgamento ou
  best-effort (tom, formato, calibrar *quando* escalar, §10).

**Por quê.** "Funciona em 99,4% das conversas" num reembolso = 6 reembolsos indevidos a cada mil.
Só código fecha essa fração.

**Anti-padrões que aparecem como alternativa errada**
- Reforçar o prompt ("deixe a regra mais enfática", "repita no fim do prompt").
- **Few-shot** com a ordem certa como "garantia" (bom para julgamento; continua probabilístico).
- **Segundo LLM** revisando a conversa antes da ação (probabilístico e mais caro).
- **Routing classifier** que habilita só um subconjunto de tools por tipo de pedido: resolve
  *disponibilidade* de tools, não *ordem* entre elas (é o distrator D da questão oficial 1).
- O inverso também erra: hook para regra de estilo ("seja cordial") é engenharia demais.

**Como cai na prova.** "Em X% dos casos o agente fez a operação crítica fora de ordem; o prompt já
diz que é obrigatório." Certa: **gate/hook programático**. Erradas: prompt, few-shot, revisor LLM,
classificador.

---

## 2. Prerequisite gate: `process_refund` só depois de `get_customer` verificado (1.4)

**Fatos de prova**
- Desenho do guia: **pré-requisito programático** que **bloqueia chamadas downstream** (`lookup_order`,
  `process_refund`) **até `get_customer` devolver um customer ID verificado**.
- Quem marca "verificado" é o **resultado da tool**, não a afirmação do modelo ("já verifiquei").
- Quando o gate nega, o motivo volta ao modelo como resultado da chamada; ele se corrige (chama
  `get_customer`) e segue. Nada de abortar a conversa.

Forma no **Agent SDK** (o SDK oficial é **Python/TypeScript**, não há SDK em C#; trecho em TS,
simplificado):

```ts
import { HookCallback, PreToolUseHookInput, PostToolUseHookInput } from "@anthropic-ai/claude-agent-sdk";

const verified = new Map<string, string>();          // session_id → customer ID verificado

// PostToolUse em get_customer: grava o ID que a TOOL devolveu como verificado
const recordVerified: HookCallback = async (input) => {
  const post = input as PostToolUseHookInput;
  const res = post.tool_response as { customer_id?: string; verified?: boolean };
  if (res?.verified && res.customer_id) verified.set(post.session_id, res.customer_id);
  return {};
};

// PreToolUse em lookup_order / process_refund: nega sem ID verificado (ou com outro ID)
const requireVerified: HookCallback = async (input) => {
  const pre = input as PreToolUseHookInput;
  const { customer_id } = pre.tool_input as { customer_id?: string };
  if (customer_id && verified.get(pre.session_id) === customer_id) return {};   // libera
  return { hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: "Customer not verified. Call get_customer first and use the verified customer_id." } };
};

const options = { hooks: {
  PostToolUse: [{ matcher: "mcp__support__get_customer", hooks: [recordVerified] }],
  PreToolUse:  [{ matcher: "mcp__support__lookup_order|mcp__support__process_refund", hooks: [requireVerified] }],
} };
```

**Por quê.** O passo crítico vira **condição técnica** da chamada seguinte, não um pedido ao modelo.
O gate também pode morar **no backend da tool** (seu servidor MCP em C# devolve erro estruturado
`permission`); para a prova conta o princípio: **código, não prompt**.

**Anti-padrões que aparecem como alternativa errada:** verificação "obrigatória" no system prompt;
few-shot com `get_customer` primeiro; o modelo declarar o ID antes de reembolsar (autodeclaração);
classificador de tools; mandar todo reembolso para humanos (mata a meta de FCR).

**Como cai na prova.** Cenário 1 (é a questão oficial 1) e, com outra roupa, cenário 4: "aplicar
mudança de configuração só depois de `get_change_request` devolver um change ID aprovado". Sempre:
**bloquear a tool downstream até a de pré-requisito devolver o dado verificado**.

---

## 3. Hooks do Agent SDK: a forma (1.5)

**Fatos de prova**
- No Agent SDK, hook é uma **função callback** registrada em `options.hooks` (TS) /
  `ClaudeAgentOptions(hooks=...)` com `HookMatcher` (Python), por **evento** e com um **`matcher`**
  pelo nome da tool. Tools MCP têm nome `mcp__<servidor>__<tool>`.
- **`PreToolUse`** = **interceptação da chamada de saída**: roda **antes** da tool, recebe
  `tool_name` + `tool_input`, pode **negar** (`permissionDecision: "deny"` + `permissionDecisionReason`,
  que o modelo lê) ou ajustar o input.
- **`PostToolUse`** = **interceptação do resultado**: roda **depois** da tool e **antes de o modelo
  processar o resultado**; pode **substituir** o que o modelo vê ou acrescentar contexto. **Não
  impede** a execução: a tool já rodou.
- Hook = **determinístico** (o harness executa sempre). Prompt = **probabilístico**.

**Por quê.** O callback roda na aplicação, fora do modelo: a decisão é código, igual em toda chamada.

**Anti-padrões que aparecem como alternativa errada:** `PostToolUse` para **impedir** uma ação (tarde
demais: só dá para alertar); `PreToolUse` para normalizar resultado (ainda não existe); hook que pede a
um LLM para julgar a chamada (volta a ser probabilístico).

> **Na doc atual [volátil]:** há muitos outros eventos (`Stop`, `SubagentStop`...), `permissionDecision`
> aceita também `allow`/`ask`/`defer` e o Post substitui o resultado via `updatedToolOutput`. Na prova
> basta o padrão: **Pre intercepta a chamada, Post transforma o resultado**.

> **Nota (Claude Code):** lá o mesmo padrão é um *shell hook* em `.claude/settings.json`
> (`"type": "command"`; `exit 2` bloqueia). O TS 1.5 fala de **hooks do Agent SDK** (callback no código).

**Como cai na prova.** "Qual hook?": bloquear/redirecionar → **Pre**; normalizar/mascarar resultado →
**Post**. Pegadinha de causa raiz: Post usado para bloquear.

---

## 4. `PostToolUse` para normalizar formatos heterogêneos (1.5)

**Fatos de prova**
- Tools MCP diferentes devolvem o mesmo dado em formatos diferentes: **Unix timestamp**, **ISO 8601**
  com fuso, **status numérico**. Um `PostToolUse` **normaliza antes de o agente processar**, em toda
  chamada, inclusive de **servidores MCP de terceiros que você não controla**.

O que chega das tools (resultados brutos; cada linha é uma chamada, e o `result` é o que o hook recebe
em `input.tool_response`, antes de virar o `tool_result` que o modelo lê):

```jsonc
{ "tool": "mcp__support__get_customer",
  "result": { "customer_id": "C-58213", "verified": true, "member_since": 1718035200 } }      // ← epoch
{ "tool": "mcp__support__lookup_order",
  "result": { "order_id": "A-99127", "delivered_at": "2026-10-02T14:05:00-03:00" } }          // ← ISO c/ fuso
{ "tool": "mcp__carrier__track_shipment",
  "result": { "tracking": "TRK-4471", "last_event_ts": 1790960700, "status_code": 3 } }       // ← epoch + código
```

O hook (TS, simplificado: assume resultado em JSON):

```ts
const STATUS: Record<number, string> = { 1: "IN_TRANSIT", 2: "OUT_FOR_DELIVERY", 3: "DELIVERED", 4: "RETURNED" };

const normalize: HookCallback = async (input) => {
  const post = input as PostToolUseHookInput;
  const data = { ...(post.tool_response as Record<string, unknown>) };
  for (const [k, v] of Object.entries(data)) {
    if (/(_at|_ts|_since)$/.test(k) && (typeof v === "number" || typeof v === "string"))
      data[k] = new Date(typeof v === "number" ? v * 1000 : v).toISOString();   // tudo ISO 8601 UTC
  }
  if (typeof data.status_code === "number") data.status = STATUS[data.status_code] ?? "UNKNOWN";
  return { hookSpecificOutput: { hookEventName: "PostToolUse", updatedToolOutput: data } };
};
// registro: PostToolUse: [{ matcher: "^mcp__", hooks: [normalize] }]   → todas as tools MCP
```

O modelo passa a ver `"last_event_ts": "2026-10-02T17:05:00.000Z"` e `"status": "DELIVERED"`.

**Por quê.** Converter epoch, fuso e código "de cabeça" a cada resultado é o tipo de passo que o
modelo acerta quase sempre; o "quase" vira prazo de devolução calculado errado.

**Anti-padrões que aparecem como alternativa errada:** regras de conversão no system prompt; few-shot
de datas; tool `convert_date` que o modelo **precisa lembrar** de chamar; pedir ao fornecedor do
servidor MCP que mude o formato (fora do seu controle).

**Como cai na prova.** Cenário 1 ("o agente erra janelas de devolução; as tools usam formatos
diferentes; uma é de terceiros") e cenários 3/4. Certa: **`PostToolUse` normalizando antes do modelo**.

---

## 5. Interceptar a chamada: teto de US$ 500 e redirecionar para humano (1.5)

**Fatos de prova**
- Política "reembolso acima de US$ 500 exige humano" = **hook de interceptação (`PreToolUse`)** na
  tool de reembolso: acima do teto, **nega** a chamada e **redireciona** para o workflow alternativo
  (`escalate_to_human`).
- O modelo continua resolvendo sozinho os casos **abaixo** do teto (a meta de FCR fica preservada).

```ts
const refundCap: HookCallback = async (input) => {
  const pre = input as PreToolUseHookInput;
  const { amount } = pre.tool_input as { amount: number };
  if (amount <= 500) return {};                                   // dentro da alçada: segue
  return { hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",                                   // garantia: o dinheiro NÃO sai
    permissionDecisionReason:
      "Refunds above $500 require human approval. Do not retry process_refund. " +
      "Call escalate_to_human with customer_id, root_cause, refund_amount and recommended_action." } };
};
// registro: PreToolUse: [{ matcher: "mcp__support__process_refund", hooks: [refundCap] }]
```

**Por quê.** Teto com consequência financeira exige garantia, e só a interceptação **antes** da
execução impede o dinheiro de sair. A parte garantida é o bloqueio; o redirecionamento chega pelo
motivo da negação (se abrir o caso também precisa ser garantido, o próprio hook cria o ticket).

**Anti-padrões que aparecem como alternativa errada:** teto no prompt "com exemplos de valores";
`PostToolUse` que alerta um supervisor para estornar (o dinheiro já saiu); escalar **todo** reembolso
(derruba a FCR); escalar por confiança autodeclarada.

**Como cai na prova.** Cenário 1 (reembolso) e cenário 4 (compensação, crédito, desconto acima de um
teto). Variação "causa raiz": o bloqueio foi registrado como `PostToolUse` (o alerta dispara, mas a
ação já aconteceu).

---

## 6. Pedido com várias demandas: decompor, investigar em paralelo, resolver uma vez (1.4)

**Fatos de prova**
- Várias demandas ("fone quebrado, cobrança dupla na assinatura, cupom recusado") → **decompor em
  itens distintos**, **investigar cada um em paralelo com contexto compartilhado** (cliente verificado
  uma vez, pedidos e política já carregados) e **sintetizar uma resolução única**.
- "Em paralelo" = vários `tool_use` no mesmo turno (ou subagents via `Task`, M07). "Contexto
  compartilhado" = os fatos do caso são buscados uma vez e valem para todos os itens.
- Um item pode ser escalado (acima do teto) e os outros resolvidos; a resposta continua **unificada**.

**Por quê.** Em série é lento. Cada item **isolado** (sem contexto comum) gera respostas que se
contradizem ("estornamos no cartão" × "creditamos em pontos") e verificações repetidas.

**Anti-padrões que aparecem como alternativa errada:** resolver só a primeira demanda e pedir outro
contato para o resto; uma sessão isolada por item, cada uma buscando os próprios dados e respondendo
separado; em série e "juntar no fim"; escalar tudo por ter várias demandas; pedir a humanos que
quebrem o ticket.

**Como cai na prova.** Cenário 1 (cliente com 2–3 problemas) e cenário 4 (ticket com vários
sintomas). Certa: **decompor → paralelo com contexto compartilhado → resolução unificada**.

---

## 7. Handoff estruturado para humano (1.4)

**Fatos de prova**
- Ao escalar no meio do processo, o humano **não vê o transcript**. O handoff carrega o mínimo
  **acionável**: **customer ID** (verificado), **causa raiz**, **valor** e **ação recomendada** (+ o que
  já foi feito e por que escalou).
- Vai como **input estruturado** de `escalate_to_human`; o harness grava como ticket na fila humana
  (é só isso que o atendente vê):

```json
{
  "role": "assistant",
  "content": [
    { "type": "tool_use", "id": "toolu_07", "name": "escalate_to_human",
      "input": {                                              // ← AQUI: o handoff inteiro
        "customer_id": "C-58213",                             // verificado por get_customer
        "issue": "Duplicate charge on order A-99127",
        "root_cause": "Payment gateway retry captured the card twice",
        "actions_taken": ["get_customer: verified", "lookup_order: 2 captures of $640.00"],
        "refund_amount": 640.00,
        "escalation_reason": "Refund above the $500 autonomous limit",
        "recommended_action": "Approve refund of the second capture ($640.00)"
      } }
  ]
}
```

**Por quê.** Sem isso o humano refaz a investigação ou age sobre informação errada. Campos fixos não
esquecem a causa raiz nem o valor; prosa livre esquece.

**Anti-padrões que aparecem como alternativa errada:** **transcript completo** ("para não perder
nada"); parágrafo em prosa livre; link para a conversa; **sentimento e confiança** no lugar de causa
raiz e ação; só ID e valor.

**Como cai na prova.** "Os atendentes reclamam que precisam reconstruir o caso" / "o atendente não vê
a conversa". Certa: **resumo estruturado com customer ID, causa raiz, valor e ação recomendada**.

---

## 8. Quando escalar: os três gatilhos certos (5.2)

**Fatos de prova** (gatilhos apropriados, segundo o guia):
1. **O cliente pede um humano explicitamente** → escale **imediatamente**, **sem investigar antes** e
   sem "tentar resolver primeiro". Mande junto o que já souber (handoff).
2. **Exceção ou lacuna de política** (não "caso complexo"): o pedido exige exceção, **ou a política é
   omissa/ambígua**. Exemplo do guia: **price match com concorrente** quando a política só cobre
   **ajuste no próprio site** → escalar. Nem regra inventada por analogia, nem silêncio lido como "não".
3. **Sem progresso significativo**: o agente esgotou os caminhos válidos e não avança.

**Frustração × pedido de humano (a distinção que a prova cobra):**

| Situação | O que fazer |
|---|---|
| "Quero falar com uma pessoa." | Escalar **já**, com handoff. Sem investigar antes. |
| Cliente irritado, problema simples **dentro da alçada**, sem pedir humano | **Reconhecer a frustração** e **oferecer a resolução** |
| ...e o cliente **reitera** que quer um humano | Escalar |
| Cliente calmo pedindo algo que a política não cobre | Escalar (lacuna de política) |
| Caso longo, com muitos pedidos, tudo coberto pela política | Resolver (complexidade ≠ gatilho) |

**Por quê.** Os gatilhos certos são **objetivos** e ligados a **autoridade** (quem pode decidir).
Escalar por "parece complexo" lota a fila com casos resolvíveis (FCR cai) e deixa passar casos calmos
que exigiam exceção.

**Anti-padrões que aparecem como alternativa errada:** "tentar resolver mais uma vez" após o pedido
explícito; perguntar "tem certeza?"; escalar todo cliente irritado; ignorar o tom; aplicar a regra
mais próxima por analogia quando a política é omissa; crédito parcial "como meio-termo".

**Como cai na prova.** Cenário 1: transcrição + "o que o agente deveria ter feito?" ou "qual
afirmação sobre o comportamento observado está correta?".

---

## 9. Proxies ruins e o caso dos vários clientes (5.2)

**Fatos de prova**
- **Sentimento** mede estado emocional, **não complexidade**: cliente furioso com cobrança duplicada
  coberta pela política → resolver; cliente educado pedindo exceção → escalar.
- **Confiança autodeclarada** ("confidence: 8/10") é **mal calibrada** como gatilho de escalonamento:
  o agente costuma estar **confiante justamente nos casos difíceis que erra**.
- **Vários clientes encontrados** (`get_customer` devolve 3 "Daniel Kim") → **pedir um identificador
  adicional** (nº do pedido, e-mail da conta). **Não escolher por heurística** (o pedido mais recente,
  o nome mais parecido, o primeiro da lista, "o que tem um pedido de notebook").

> **As três caras da confiança (não generalize):** (a) filtrar achados por "confiança" em vez de
> critério explícito = errado (4.1, M02); (b) **escalonar atendimento por confiança autodeclarada ou
> sentimento = errado (5.2, aqui)**; (c) confiança **por campo/achado, calibrada com conjunto
> rotulado**, para **rotear revisão humana** = certo (4.6, 5.5; M09/M11). Nunca "confiança do modelo
> não serve para nada".

**Por quê.** Os dois sinais medem outra coisa (emoção, autoavaliação), não política nem autoridade.
Escolher conta por heurística age sobre um cliente não confirmado (risco financeiro e de privacidade).

**Anti-padrões que aparecem como alternativa errada:** limiar de sentimento "calibrado com CSAT";
mexer no limiar de confiança; score combinado; listar as contas com e-mail e endereço para o cliente
escolher (expõe terceiros); escalar só por haver vários matches.

**Como cai na prova.** "Escalar quando sentimento < X / confiança < Y; como avaliar?" e
"`get_customer` devolveu N contas; primeiro passo?".

---

## 10. Calibrar o escalonamento: critérios explícitos + few-shot no system prompt (5.2)

**Fatos de prova**
- Agente escala casos simples e resolve sozinho casos que exigiam exceção → **fronteira de decisão
  mal definida**. Primeiro passo proporcional: **critérios explícitos de escalonamento com exemplos
  few-shot no system prompt** (quando escalar × quando resolver).
- Aqui o prompt é a ferramenta certa porque a decisão é de **julgamento** ("é exceção de política?").
  Regras **objetivas e com consequência** (teto de US$ 500, identidade) seguem em **hook**. Convivem.

```text
## Escalation criteria (call escalate_to_human)
Escalate when ANY of these is true:
1. The customer explicitly asks for a human. Escalate right away; do not investigate first.
2. The request needs a policy exception, or the policy does not address it.
3. You cannot make progress after trying the valid options.
Not reasons to escalate on their own: anger or frustration, long conversations, many order lines.

## Examples
Customer: "Third time writing!! The mouse I got is broken, photo attached."
→ RESOLVE: acknowledge the frustration; damaged item with photo is a standard replacement.
Customer: "Another store sells this TV for $80 less. Can you match it?"
→ ESCALATE: policy covers own-site price adjustments only; competitor match is not addressed.
Customer (after you offered the replacement): "I still want to talk to a person."
→ ESCALATE: the customer reiterated the request for a human.
```

**Por quê.** O problema é de fronteira de decisão; critérios + exemplos mostram a fronteira ao
modelo com custo mínimo, antes de qualquer infraestrutura.

**Anti-padrões que aparecem como alternativa errada:** classificador treinado em tickets (antes de
tentar o prompt); limiar de sentimento ou de confiança autodeclarada; hook que escala uma categoria
inteira (rígido para decisão de julgamento); "use o bom senso".

**Como cai na prova.** A questão oficial 3 (FCR abaixo da meta) é o modelo; espere o princípio em
outra roupa (casos simples escalados, exceções resolvidas sem autorização).

---

## Tabela de decisão

| Se... | Então... |
|---|---|
| Regra crítica (financeira/compliance) tem que valer 100% | Hook/gate programático, não prompt |
| Tool B só depois de A devolver dado verificado | Prerequisite gate (`PreToolUse` nega B) |
| Ação acima de um teto (US$ 500) exige humano | `PreToolUse` nega e redireciona para `escalate_to_human` |
| Formatos heterogêneos vindos de tools MCP | `PostToolUse` normaliza antes do modelo |
| Várias demandas numa mensagem | Decompor → paralelo com contexto compartilhado → resolução única |
| Humano que não vê o transcript | Handoff: customer ID, causa raiz, valor, ação recomendada |
| Pedido explícito de humano | Escalar já, sem investigar antes |
| Frustrado, problema simples na alçada | Reconhecer e oferecer; escalar se **reiterar** |
| Política omissa/ambígua, ou sem progresso | Escalar |
| Várias contas encontradas | Pedir identificador adicional |
| Escalonamento mal calibrado | Critérios explícitos + few-shot no system prompt |

## Glossário

- **Enforcement programático:** regra imposta por código em toda chamada (determinística).
- **Prerequisite gate:** bloqueia uma tool downstream até um passo anterior produzir o dado exigido.
- **Hook (Agent SDK):** callback da aplicação em `options.hooks`, por evento e `matcher`.
- **`PreToolUse` (tool call interception):** antes da execução; pode negar com motivo.
- **`PostToolUse`:** depois da execução, antes de o modelo ler o resultado; pode transformá-lo.
- **Handoff estruturado:** campos fixos (customer ID, causa raiz, valor, ação recomendada).
- **FCR:** first-contact resolution.

## Cola de véspera

- **Prompt = probabilístico** (falha ≠ 0); **hook/gate = determinístico**. Regra crítica → código.
  Few-shot, revisor LLM e maiúsculas não garantem; routing classifier resolve disponibilidade, não ordem.
- **Gate:** `lookup_order`/`process_refund` bloqueados até `get_customer` devolver **customer ID
  verificado** (resultado da tool, não a palavra do modelo).
- **Agent SDK** (Python/TS): callback em `options.hooks` + `matcher` (`mcp__<servidor>__<tool>`).
  **Pre** intercepta a chamada; **Post** transforma o resultado (epoch/ISO 8601/status) e não impede nada.
- **US$ 500:** `PreToolUse` nega e manda para `escalate_to_human`; abaixo do teto, o agente resolve.
- **Várias demandas:** decompor → paralelo com contexto compartilhado → uma resolução.
- **Handoff:** customer ID, causa raiz, valor, ação recomendada. Nada de transcript bruto.
- **Escalar:** pedido explícito (já), exceção/lacuna de política (price match com concorrente), sem
  progresso. **Não** por sentimento, confiança autodeclarada ou tamanho do caso.
- **Frustrado + simples:** reconhecer e oferecer; escalar se **reiterar**. **Várias contas:** pedir
  identificador. **Calibrar:** critérios explícitos + few-shot no system prompt.

## Perguntas de checagem

1. **O prompt já exige `get_customer` e a conformidade é 99,2%. Por que não basta?** Prompt é
   probabilístico: 0,8% de reembolsos sem verificação continua. Só um gate programático garante.
2. **Impedir reembolso acima de US$ 500: Pre ou Post? O que o hook devolve?** `PreToolUse`: nega com
   motivo que manda usar `escalate_to_human`. Post rodaria com o dinheiro já devolvido.
3. **Epoch, ISO 8601 com fuso e status numérico vindos de 3 tools MCP: onde normalizar?** Num
   `PostToolUse`, antes de o modelo processar, inclusive a tool de terceiros.
4. **Cliente irritado, item com defeito coberto pela política, sem pedir humano. E se depois insistir
   numa pessoa?** Reconhecer a frustração e oferecer a troca; se reiterar, escalar.
5. **`get_customer` devolveu duas contas "Ana Lima".** Pedir identificador adicional (nº do pedido,
   e-mail); nada de heurística nem de expor as duas contas.
6. **Casos simples escalados e exceções resolvidas sozinho: primeiro passo?** Critérios explícitos
   de escalonamento com few-shot no system prompt.
