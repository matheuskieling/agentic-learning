# Módulo 03 — Saída estruturada, validação com retry e Batch API

> **Task statements:** **4.3** (saída estruturada com tool use e JSON schema), **4.4** (validação,
> retry e loops de feedback) e **4.5** (batch). Domínio D4, 20% da prova.
> **Cenários onde cai:** **6 — Structured Data Extraction** (quase tudo) e **5 — Claude Code for
> Continuous Integration** (findings estruturados, `detected_pattern`, síncrono × batch).
> Código de aplicação em C#; JSON no formato real, com `// ← AQUI` no campo em questão.

> **Se você fez a versão antiga deste módulo, desaprenda duas coisas.** (1) A resposta de prova para
> "saída estruturada confiável" é **tool_use + JSON schema**, não `output_config.format`.
> (2) `tool_choice: "any"` e o forçado `{"type": "tool", ...}` são **respostas certas** na prova.

---

## 1. Tool use com JSON schema, o caminho mais confiável

*(4.3-K1, 4.3-S1)*

**Fatos de prova**
- Pelo guia, **tool use com JSON schema é a abordagem mais confiável** para saída conforme ao schema:
  **elimina erros de sintaxe JSON** (texto em volta, cerca de código, vírgula ou chave faltando).
- Você define uma **tool de extração** cujo **`input_schema` é a saída que você quer**. A tool não
  executa nada. O dado vem no campo **`input` do bloco `tool_use`** da resposta.
- `strict: true` na tool liga o modo estrito (o guia: "strict mode for syntax error elimination").

```jsonc
// Request (o resultado vai para a tabela supplier_invoices do ERP)
{
  "model": "<modelo>", "max_tokens": 2048,
  "tools": [ {
    "name": "extract_invoice",
    "description": "Record the data extracted from ONE supplier invoice.",
    "strict": true,
    "input_schema": {                                       // ← AQUI: o schema da saída
      "type": "object",
      "properties": { "invoice_number": { "type": "string" }, "stated_total": { "type": "number" } },
      "required": ["invoice_number", "stated_total"], "additionalProperties": false
    } } ],
  "tool_choice": { "type": "tool", "name": "extract_invoice" },
  "messages": [ { "role": "user", "content": "<invoice>...</invoice>" } ]
}
// Resposta
{ "stop_reason": "tool_use",
  "content": [ { "type": "tool_use", "id": "toolu_01A", "name": "extract_invoice",
                 "input": { "invoice_number": "F-88231", "stated_total": 1250.00 } } ] }  // ← AQUI: content[0].input
```

```csharp
var fatura = toolUse.GetProperty("input").Deserialize<InvoiceExtraction>(); // não faça parse do texto
```

> **Na doc atual [volátil]:** existe também *structured outputs* (`output_config.format`), que
> restringe a resposta em texto a um schema. O guia não o cita. **Na prova, a resposta é a tool de
> extração + JSON schema.**

**Por quê:** "responda só com JSON" é instrução, e instrução é probabilística; o `input` do
`tool_use` já chega como objeto JSON montado pela API, e com `strict: true` a conformidade ao schema
é garantida.

**Anti-padrões que aparecem como alternativa errada:** reforçar "APENAS JSON" no prompt; regex do
primeiro `{` ao último `}`; try/catch com retry no erro de parse; few-shot como *garantia* de formato
(melhora consistência, não garante sintaxe); devolver o dado num `tool_result` "para confirmar".

**Como cai na prova:** cenário 6: "o parser falha em X% porque vem texto antes do JSON; correção mais
confiável?" → tool de extração com o schema como `input_schema` e `tool_choice` garantindo a chamada.

---

## 2. tool_choice: auto, any e forçado

*(4.3-K2, 4.3-S2, 4.3-S3)*

| `tool_choice` | O modelo... | Use quando |
|---------------|-------------|------------|
| `{"type": "auto"}` (padrão) | pode chamar tool **ou responder em texto** | agente conversacional |
| `{"type": "any"}` | **tem que** chamar **alguma** tool, e escolhe qual | **vários schemas** de extração e **tipo de documento desconhecido** |
| `{"type": "tool", "name": "extract_metadata"}` | **tem que** chamar **aquela** tool | garantir que uma extração rode **antes** do enriquecimento |

```jsonc
// "any": três extratores, tipo desconhecido, nenhuma resposta pode vir em prosa
{ "tools": [ { "name": "extract_invoice", "...": "..." }, { "name": "extract_receipt", "...": "..." },
             { "name": "extract_contract", "...": "..." } ],
  "tool_choice": { "type": "any" },                          // ← AQUI: obriga uma das três
  "messages": [ { "role": "user", "content": "<document>...</document>" } ] }

// Forçado só no 1º request: lookup_citations precisa do DOI que extract_metadata produz
// (tools e messages abreviados: só os nomes/papéis; as definições completas seguem o formato acima)
{ "tools": [ "extract_metadata", "lookup_citations", "verify_doi" ],
  "tool_choice": { "type": "tool", "name": "extract_metadata" },   // ← AQUI: turno 1
  "messages": [ { "role": "user", "content": "<paper>...</paper>" } ] }
// Turnos seguintes: mesmo histórico + tool_result com o DOI
{ "tool_choice": { "type": "auto" },                               // ← AQUI: volta para auto
  "messages": [ "user(paper)", "assistant(tool_use extract_metadata)", "user(tool_result: DOI)" ] }
```

**Por quê:** com `auto`, parte das respostas sai em texto. Instrução no prompt tem taxa de falha
diferente de zero (1.4). Forçar em **todos** os turnos prende o modelo naquela tool.

**Anti-padrões que aparecem como alternativa errada**
- **Instrução no system prompt** para "sempre usar uma tool" ou "chamar X primeiro": o distrator clássico.
- Forçar **uma** tool quando o tipo do documento é desconhecido (schema errado → fabricação).
- `"any"` para garantir **ordem**: garante *uma* chamada, não *qual*.
- Forçado em todos os turnos, ou fundir tudo numa tool gigante com campos opcionais.

> **Na doc atual [volátil]:** Opus 5.5, Sonnet 5.5, Fable 5.1 e Mythos 5.1 rejeitam `"any"` e o
> forçado com erro 400 (outros modelos aceitam; onde há suporte, a doc recomenda `any` + `strict`). **Na prova, responda pelo guia:** `"any"` garante uma chamada, o
> forçado garante aquela tool, e "instrução no prompt" é a alternativa errada.

**Como cai na prova:** "3 extratores, tipo desconhecido, 5% em prosa" → `"any"`. "Em 7% das execuções
o enriquecimento roda antes do metadata" → forçado no 1º request, `auto` depois. O M04 (2.3) cobra o
mesmo do lado do design de tools.

---

## 3. Design do schema: opcional, nullable, other e unclear

*(4.3-K4, 4.3-S4, 4.3-S5)*

**Fatos de prova**
- **Required × optional:** só é obrigatório-não-nulo o que **sempre** existe na fonte. Campo
  obrigatório para dado que às vezes falta leva o modelo a **fabricar um valor plausível**.
- **Optional / nullable** (`"type": ["string", "null"]`): o modelo pode dizer "não existe". O guia
  trata "optional (nullable)" como uma ideia só.
- **Enum + `"other"` + campo de detalhe:** categoria extensível, sem empurrar o valor novo para o
  mais próximo.
- **Enum + `"unclear"`:** caso ambíguo ou ilegível. O modelo não chuta.

```jsonc
// POST /v1/messages — trecho "tools" (a extração vai para o sistema de reembolso de viagens)
"tools": [ { "name": "extract_booking_document", "input_schema": { "type": "object", "properties": {
  "document_type": { "type": "string", "enum": ["hotel_confirmation", "airline_ticket",
                     "car_rental_voucher", "other", "unclear"] },       // ← AQUI: extensível + ambíguo
  "document_type_detail": { "type": ["string", "null"] },                // ← AQUI: preenchido quando "other"
  "purchase_order": { "type": ["string", "null"] }                       // ← AQUI: null se o documento não traz
}, "required": ["document_type", "document_type_detail", "purchase_order"] } } ]
```

| Valor | Significa | Exemplo |
|-------|-----------|---------|
| `"other"` + detalhe | categoria legível, fora da lista | voucher de cruzeiro → `other`, `"cruise voucher"` |
| `"unclear"` | não dá para saber pela fonte | scan borrado |
| `null` | o dado não está no documento | fatura sem pedido de compra |

**Por quê:** schema que obriga um valor obriga uma escolha, e o modelo escolhe mesmo inventando. Com
`null`, `other` e `unclear`, o dado fica honesto e roteável.

**Anti-padrões que aparecem como alternativa errada:** tudo obrigatório "para o downstream nunca
receber vazio"; enum fechado + mapear para "o mais próximo"; texto livre no lugar do enum; "não
invente" no prompt sem a saída `null`; estender o enum a cada formato novo, sem `other`.

**Como cai na prova:** cenário 6: "o modelo inventa o número do pedido de compra" → nullable;
"vouchers de trem saem como hotel" → `other` + detalhe; "scan ruim, booleano chutado" → `unclear`.

---

## 4. Normalização de formato no prompt, junto com o schema

*(4.3-S6)*

**Fatos de prova**
- O schema estrito garante **tipo e forma**, não **como interpretar a fonte**: `05/04/2026` é 5 de
  abril ou 4 de maio? `1.250,00` é 1250 ou 1,25?
- Por isso o guia pede **regras de normalização no prompt, junto com o schema estrito**: formato de
  saída (ISO 8601, ISO 4217), como resolver ambiguidade (dia/mês pelo país do emissor) e unidades.

```jsonc
// POST /v1/messages (corpo do request)
{ "system": "Normalization rules:\n- Dates: output YYYY-MM-DD; read numeric dates as DD/MM/YYYY unless the supplier country is US.\n- Amounts: plain number; '1.250,00' and '1,250.00' are both 1250.00.\n- Currency: ISO 4217 code ('€' → EUR).",   // ← AQUI
  "tools": [ { "name": "extract_confirmation", "strict": true, "input_schema": { "...": "..." } } ],
  "messages": [ { "role": "user", "content": "<confirmation country=\"DE\">...</confirmation>" } ] }
```

**Por quê:** o schema elimina a sintaxe errada e as regras eliminam a ambiguidade de formato. Few-shot
com fontes variadas (M02, 4.2) reforça as regras.

**Anti-padrões que aparecem como alternativa errada:** achar que `"format": "date"` ou `pattern`
resolve (forçam o formato *de saída*; a ordem dia/mês segue chutada); culpar "lost in the middle" ou
tool não forçada quando todas as saídas são `tool_use` válidos; regex depois, sem saber a origem.

**Como cai na prova:** cenário 6: "100% passa no schema, mas 11% das datas europeias vêm com dia e
mês trocados. Causa raiz?" → faltam regras de normalização no prompt.

---

## 5. Sintaxe × semântica: o que o schema não pega

*(4.3-K3, 4.4-K4, 4.4-S4)*

**Fatos de prova**
- Schema estrito **elimina erro de sintaxe**, mas **não erro semântico**: itens que não somam o
  total, **valor no campo errado** (check-out no check-in), contagem do resumo ≠ itens listados.
- Validação semântica é **código seu**. No ecossistema Python o guia cita **Pydantic** (validadores
  que devolvem a lista de erros por campo, e ela alimenta o retry). Em .NET, um validador próprio.
- **Self-correction validation flow:** extraia **`stated_total`** (impresso) **e `calculated_total`**
  (soma dos itens), para que a divergência apareça em vez de ser "corrigida" em silêncio. Para **fonte
  inconsistente** (o documento se contradiz), use o booleano **`conflict_detected`**.

```jsonc
// POST /v1/messages → tools[0] (extract_invoice) → input_schema.properties (trecho)
"properties": {
  "stated_total":      { "type": "number", "description": "Total exactly as printed" },          // ← AQUI
  "calculated_total":  { "type": "number", "description": "Sum of the line_items you extracted" }, // ← AQUI
  "conflict_detected": { "type": "boolean", "description": "true if the document contradicts itself" }, // ← AQUI
  "conflict_detail":   { "type": ["string", "null"] } }
```

```csharp
// C#: não confie na aritmética do modelo; recalcule
var soma = x.LineItems.Sum(i => i.Amount);
if (Math.Abs(soma - x.StatedTotal) > 0.01m && !x.ConflictDetected)
    erros.Add(new("stated_total", $"line_items sum to {soma:F2} but stated_total is {x.StatedTotal:F2}; " +
        "re-read the items table, or set conflict_detected if the document itself disagrees"));
```

| Divergência | Causa | O que fazer |
|-------------|-------|-------------|
| O modelo pulou um item | erro de **extração** | retry com o erro específico (§6) |
| O fornecedor errou a conta | **fonte inconsistente** | `conflict_detected: true` + revisão humana |

**Anti-padrões que aparecem como alternativa errada:** "o strict está ligado, então está certo" (ou
"é bug da API"); escrever "total = soma dos itens" na descrição do campo; `minimum`/`maximum` no
lugar de regra entre campos (JSON Schema não expressa "soma = total"); pedir só o total "corrigido";
campo autoavaliado `looks_correct`.

**Como cai na prova:** cenário 6: "o schema valida 100%, a auditoria acha totais que não batem" →
validação em código + `stated_total`/`calculated_total`. Cenário 5: "o resumo diz 3 críticos e a
lista tem 2; proposta: ligar strict" → strict não pega semântica.

---

## 6. Retry com feedback de erro, e quando ele não adianta

*(4.4-K1, 4.4-S1, 4.4-K2, 4.4-S2)*

**Fatos de prova**
- **Retry-with-error-feedback:** o retry leva os **erros de validação específicos** (campo, regra,
  valor encontrado, esperado), não "falhou, tente de novo".
- O follow-up leva **três coisas**: **documento original + extração que falhou + erros específicos**.
  Sem o documento, o modelo corrige chutando. Sem a extração anterior, refaz tudo e pode quebrar o que
  estava certo.
- **Retry funciona** quando a informação **está** na fonte: formato, estrutura, campo trocado, item
  pulado.
- **Retry não funciona** quando a informação **não está na fonte**: ausente do documento, ou **só num
  documento externo não fornecido** ("conforme Anexo C", "see attached PO"). Mais tentativas só
  produzem invenção. O certo é `null` + revisão, **ou** fornecer o documento que falta.
- O limite (2–3 tentativas) é backstop. Esgotou → fila de revisão. Nunca grave dado inválido.

```jsonc
// POST /v1/messages — request de RETRY (mesmo histórico + o erro de validação)
{ "tools": [ { "name": "extract_invoice", "input_schema": { "...": "..." } } ],
  "tool_choice": { "type": "tool", "name": "extract_invoice" },
  "messages": [
    { "role": "user", "content": "<invoice>...texto integral...</invoice>" },               // ← 1. documento original
    { "role": "assistant", "content": [ { "type": "tool_use", "id": "toolu_01A",
        "name": "extract_invoice", "input": { "stated_total": 1250.00, "line_items": ["...4 itens..."] } } ] },  // ← 2. extração que falhou
    { "role": "user", "content": [ { "type": "tool_result", "tool_use_id": "toolu_01A", "is_error": true,
        "content": "Validation errors: (1) line_items sum to 1205.00 but stated_total is 1250.00; the table has 5 rows, you returned 4. (2) due_date '15/13/2026' is invalid; output YYYY-MM-DD." } ] }  // ← 3. erros específicos
  ] }
```

```csharp
for (var t = 1; t <= 3; t++)                                      // C#, helpers ilustrativos
{
    var (toolUse, x) = await ExtrairAsync(historico);             // histórico começa com o documento
    var erros = Validador.Validar(x);
    if (erros.Count == 0) return await GravarNoErpAsync(x);
    if (erros.Any(e => e.AusenteNaFonte)) return await RevisaoAsync(x, erros); // retry não adianta
    historico.Add(Assistente(toolUse)); historico.Add(ToolResultComErros(toolUse.Id, erros));
}
return await RevisaoAsync(ultima, ultimosErros);                  // backstop: falha explícita
```

**Anti-padrões que aparecem como alternativa errada:** mensagem genérica; mais tentativas; só os
erros num request novo, sem o documento ("para não enviesar"); retry ou few-shot "de valores bons"
para dado que não está na fonte; modelo maior só no retry; afrouxar o validador.

**Como cai na prova:** "o retry recupera só 12%, e a mensagem é genérica" → erros específicos +
documento + extração anterior. "Após 3 retries o campo segue inventado; o documento diz 'ver anexo'" →
`null` + revisão, ou envie o anexo.

---

## 7. detected_pattern: aprendendo com os achados descartados

*(4.4-K3, 4.4-S3)*

**Fatos de prova**
- Em review automatizado (cenário 5), cada achado estruturado ganha um campo **`detected_pattern`**:
  a construção de código que disparou o achado (`async-void-method`, `phi-in-log-message`...).
- Quando os devs **descartam** achados, você agrega os descartes **por padrão** e acha os falsos
  positivos sistemáticos. Aí refina critério e few-shot daquela categoria (M02) ou a desliga
  temporariamente. Vale também para flags de anomalia em extração.

```jsonc
// Resposta do review: bloco content[i] do tipo tool_use (tool report_findings)
{ "type": "tool_use", "name": "report_findings", "input": { "findings": [
  { "file": "src/Claims/ClaimService.cs", "line": 142, "severity": "major",
    "detected_pattern": "async-void-method",          // ← AQUI: input.findings[].detected_pattern
    "issue": "async void handler swallows exceptions", "suggested_fix": "return Task and await it" } ] } }
```

Para onde vai: o pipeline posta o comentário no PR e grava `{finding_id, detected_pattern, outcome}`
na tabela `review_findings`. O "dismiss" no PR atualiza `outcome`. Uma consulta semanal agrupa a taxa
de descarte por padrão.

**Anti-padrões que aparecem como alternativa errada:** filtrar por confiança autodeclarada (o 4.1
rejeita); pedir ao dev o motivo de cada descarte (ônus humano, dado não estruturado); um segundo
modelo resumindo os descartes em texto livre; limitar o número de achados por PR.

**Como cai na prova:** "40% dos achados são descartados; quais tipos geram falso positivo?" →
`detected_pattern` + agregação.

---

## 8. Message Batches API: fatos e quando usar

*(4.5-K1, 4.5-K2, 4.5-K3, 4.5-K4, 4.5-S1)*

**Fatos de prova**
- **50% de economia**, processamento em **até 24 h**, **sem SLA de latência** (minutos ou quase 24 h).
- **`custom_id`** em cada request correlaciona request e resultado. Os resultados podem vir fora de
  ordem.
- **Polling:** consulte até `processing_status` = `"ended"` e então leia os resultados.
- **Sem multi-turn tool calling dentro de um request:** o batch não executa uma tool no meio do
  request. Se a resposta termina em `tool_use` de uma tool que precisa rodar (ex.: `lookup_supplier`),
  ninguém a executa. **Extração via tool_use funciona**, porque o `input` já é o produto.
- **Use** para trabalho **não bloqueante e tolerante a latência**: relatório overnight, auditoria
  semanal, testes noturnos, backlog. **Não use** em fluxo **bloqueante**: pré-merge, gate de deploy,
  alguém esperando.

```jsonc
// POST /v1/messages/batches
{ "requests": [ { "custom_id": "contract-2026-00417",                 // ← AQUI: requests[].custom_id
                  "params": { "model": "<modelo>", "max_tokens": 2048, "tools": ["..."],
                              "messages": [ { "role": "user", "content": "<contract>...</contract>" } ] } } ] }
// GET /v1/messages/batches/{id}  (polling)
{ "id": "msgbatch_01...", "processing_status": "in_progress",         // ← AQUI: repita até "ended"
  "request_counts": { "processing": 18000, "succeeded": 0, "errored": 0, "canceled": 0, "expired": 0 } }
// Resultados (JSONL, uma linha por request, em qualquer ordem)
{"custom_id": "contract-2026-00988", "result": {"type": "errored", "error": {"type": "error", "error": {"type": "invalid_request_error", "message": "prompt is too long ..."}}}}
```

> **Na doc atual [volátil]:** *server tools* (web search, code execution), que a própria API executa,
> funcionam dentro do batch; o que não roda no meio do request são as tools do **seu** código (client
> tools). **Na prova: o batch não suporta multi-turn tool calling num request.**

**Anti-padrões que aparecem como alternativa errada:** batch em passo bloqueante "com polling" ou
"com fallback por timeout"; batches pequenos "para sair mais rápido" (sem SLA); casar resultados pela
ordem; tudo síncrono "porque o batch bagunça a ordem"; batch com tool a executar no meio (pré-busque
o dado e ponha no prompt).

**Como cai na prova:** "mover X e Y para batch?" → só o não bloqueante. "30% dos resultados do batch
terminam em `tool_use` de `lookup_supplier`" → sem multi-turn.

---

## 9. Operando o batch: cadência pelo SLA, falhas e amostra

*(4.5-S2, 4.5-S3, 4.5-S4)*

**Cadência pelo SLA.** No pior caso, o documento chega logo depois de uma submissão: espera **até a
próxima (janela W)**, depois **até 24 h de processamento**, e ainda precisa de **folga** (polling,
validação, reprocessar falhas). Regra: **`W + 24 h + folga ≤ SLA`**. Exemplo do guia, SLA de 30 h:

| Submissão a cada | Pior caso | Resultado |
|------------------|-----------|-----------|
| 24 h | 24 + 24 = 48 h | estoura |
| 12 h | 12 + 24 = 36 h | estoura |
| 6 h | 6 + 24 = 30 h | no limite, **sem folga** |
| **4 h** | 4 + 24 = **28 h** | **cumpre com 2 h de folga** (a resposta do guia) |

"Submeter quando acumular N documentos" não garante SLA: num dia fraco, a espera não tem limite.

**Falhas.** Filtre os resultados `errored`/`expired` pelo **`custom_id`** e reenvie **só esses**,
**com a modificação adequada**: o documento que **estourou o contexto** passa por **chunking** (cada
parte com seu `custom_id`, ex.: `contract-2026-00988-p1`); erro transitório de servidor volta como
está. Reenviar o lote inteiro paga de novo o que deu certo. Reenviar sem modificar falha de novo.

**Amostra antes do volume.** Antes de 100 mil documentos, refine prompt e schema numa **amostra
representativa** (síncrona, iteração rápida). Isso maximiza o sucesso na primeira passada e reduz o
custo de reenvio. Anti-padrão: "manda tudo e corrige entre lotes".

**Como cai na prova:** "SLA de 36 h, uma submissão por dia; por que atrasa?" (24 h de espera + 24 h
de processamento). "371 estouraram o contexto, 25 erros de servidor" → só esses, com chunking nos 371.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| JSON garantidamente conforme ao schema | Tool de extração (`input_schema` = saída), leia `tool_use.input` |
| Vários schemas, tipo desconhecido, respostas em prosa | `tool_choice: {"type": "any"}` |
| Uma extração antes do enriquecimento | Forçado `{"type": "tool", "name": ...}` no 1º request, `auto` depois |
| Dado pode faltar / categoria fora da lista / fonte ambígua | Nullable / `"other"` + detalhe / `"unclear"` |
| Passa no schema, mas soma ou campos não batem | Validação semântica em código; `stated_total` × `calculated_total`; `conflict_detected` |
| Validação falhou, dado está na fonte | Retry: documento + extração falha + erros específicos, com limite |
| Dado ausente ou só num anexo não enviado | Sem retry: `null` + revisão, ou forneça o documento |
| Alguém espera (pré-merge, deploy) / noturno, semanal | Síncrona / Message Batches API |
| SLA com batch | W + 24 h + folga ≤ SLA (30 h → a cada 4 h) |
| Requests do batch falharam | Só os `custom_id` falhos, modificados (chunking se estourou contexto) |

## Glossário

- **Tool de extração** — tool cujo `input_schema` é a saída; o dado vem em `tool_use.input`.
- **Strict mode** — schema aplicado exatamente; elimina sintaxe, não semântica.
- **Pydantic** — validação Python citada no guia; erros por campo alimentam o retry.
- **`conflict_detected`** — booleano para fonte que se contradiz.
- **`custom_id`** — chave por request do batch. **Polling** — consultar até `"ended"`.

## Cola de véspera

- **Mais confiável:** tool_use + JSON schema, que elimina **sintaxe**. Dado em `tool_use.input`.
  `output_config.format` é nota volátil, fora do guia.
- **`auto`** pode vir texto · **`any`** garante alguma tool (vários schemas, tipo desconhecido) ·
  **forçado** garante aquela (`extract_metadata` primeiro, depois `auto`). "Instrução no prompt" é
  distrator. O 400 em alguns modelos novos é volátil; na prova vale o guia.
- **Schema:** obrigatório só o que sempre existe · **nullable** · **`other` + detalhe** · **`unclear`**
  · **regras de normalização no prompt** junto com o schema.
- **Strict ≠ semântica** → valide em código (Pydantic). `stated_total` × `calculated_total`,
  `conflict_detected`.
- **Retry:** documento + extração falha + **erros específicos**, com limite. **Inútil** se o dado não
  está na fonte ou só num documento externo não enviado.
- **`detected_pattern`** → analisar os padrões de descarte.
- **Batch:** 50% · até 24 h · **sem SLA** · `custom_id` · polling · **sem multi-turn tool calling**.
  Síncrono para bloqueante; batch para overnight/semanal.
- **SLA:** W + 24 + folga ≤ SLA (30 h → **a cada 4 h**). Falhas: **só os `custom_id` falhos,
  modificados**. **Amostra antes do volume.**

## Perguntas de checagem

1. **3% das respostas "só JSON" falham no parse. Correção?** Tool de extração + `tool_choice`, lendo `tool_use.input`.
2. **Três extratores, tipo desconhecido, 5% em prosa? E `extract_metadata` primeiro?** `"any"`; forçado no 1º request.
3. **Strict ligado, 100% válido, totais não batem. O strict deveria pegar?** Não: valide em código.
4. **Campo inventado após 3 retries; o dado está num memo anexo não enviado.** `null` + revisão, ou envie o memo.
5. **SLA de 30 h, batch de até 24 h: frequência?** A cada 4 h (pior caso 28 h). Uma vez por dia dá 48 h.
6. **312 de 10 mil estouraram o contexto. O que reenviar?** Só esses `custom_id`, em partes.
