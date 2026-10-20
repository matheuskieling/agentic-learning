# Módulo 01 — O exame e a Messages API: request, histórico, tool use e o loop agêntico

> **Cobre:** orientação do exame pelo **guia oficial v1.0** (§3–5, 9, 10, 17) + **TS 1.1** completo +
> a base que outros módulos aprofundam: **5.1-K4** (histórico completo), **2.1-K1** (descrição da tool),
> **4.3-K1/K2** e **2.3-K4** (`tool_use` + schema, `tool_choice`).
> **Cenários:** 1, 3 e 4 (loop); 5 e 6 (`tool_use`/`tool_choice`); qualquer um ("a API não tem estado").
> Cada seção: fato de prova → por quê → anti-padrão que vira alternativa errada → como cai.

---

## 1. O exame pelo guia oficial v1.0

### Fatos de prova

| Item | Valor (guia v1.0, CCAR-F) |
|------|---------------------------|
| Público | Arquiteto de soluções com **6+ meses** construindo com Claude API, Agent SDK, Claude Code e MCP |
| Itens | **60**: múltipla escolha e **múltipla resposta**; **cada item diz quantas marcar** (pode ser 2, pode ser 3; leia o número) |
| Estrutura | **4 cenários sorteados de um banco de 6**; cada cenário enquadra um bloco de questões |
| Tempo | **120 min** (~2 min por item), supervisionado (online ou centro Pearson VUE), sem consulta |
| Nota | Escala **100–1.000**, corte **720**; avaliação por critério (não é curva) |
| Relatório | Aprovado/reprovado + nota escalada + **% de acerto por domínio** (só informativo: não decide a aprovação) |
| Chute | A v1.0 não repete o ponto, mas o rascunho oficial de fev/2026 dizia: **questão em branco conta como erro e não há penalidade por chute** → nunca deixe em branco |
| Validade | 12 meses; renovação gratuita (avaliação não supervisionada) se feita no prazo |

**Os 6 cenários** (resumo da descrição oficial → domínios primários):

| # | Cenário | O que o enunciado assume | Domínios |
|---|---------|--------------------------|----------|
| 1 | Customer Support Resolution Agent | Agent SDK; tools MCP `get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`; meta 80%+ de resolução no 1º contato, sabendo escalar | D1, D2, D5 |
| 2 | Code Generation with Claude Code | Slash commands, CLAUDE.md, plan mode × execução direta | D3, D5 |
| 3 | Multi-Agent Research System | Agent SDK; coordenador + subagents (busca web, análise de documentos, síntese, relatório); relatório citado | D1, D2, D5 |
| 4 | Developer Productivity with Claude | Agent SDK; tools nativas (Read, Write, Bash, Grep, Glob) + MCP; codebase desconhecido, legado, boilerplate | D2, D3, D1 |
| 5 | Claude Code for Continuous Integration | Review, testes e feedback em PR; acionável, poucos falsos positivos | D3, D4 |
| 6 | Structured Data Extraction | Documentos não estruturados → JSON validado por schema; bordas; sistemas downstream | D4, D5 |

**Os 5 domínios:**

| Domínio | Peso | ≈ itens em 60 | Módulos do curso |
|---------|-----:|--------------:|------------------|
| D1 Agentic Architecture & Orchestration | **27%** | ~16 | 01, 06, 07, 10 |
| D2 Tool Design & MCP Integration | 18% | ~11 | 04, 05 |
| D3 Claude Code Configuration & Workflows | 20% | ~12 | 08, 09 |
| D4 Prompt Engineering & Structured Output | 20% | ~12 | 02, 03, 09 |
| D5 Context Management & Reliability | 15% | ~9 | 06, 10, 11 |

**Os 30 task statements** ("Exam items are written against these objectives"):

| TS | Objetivo (título oficial resumido) | Módulo |
|----|-----------------------------------|:------:|
| 1.1 | Agentic loops for autonomous task execution | **01** |
| 1.2 | Multi-agent systems with coordinator-subagent patterns | 07 |
| 1.3 | Subagent invocation, context passing, and spawning | 07 |
| 1.4 | Multi-step workflows with enforcement and handoff | 06 |
| 1.5 | Agent SDK hooks for tool call interception and data normalization | 06 |
| 1.6 | Task decomposition strategies for complex workflows | 07 |
| 1.7 | Session state, resumption, and forking | 10 |
| 2.1 | Tool interfaces with clear descriptions and boundaries | 04 |
| 2.2 | Structured error responses for MCP tools | 04 |
| 2.3 | Distribute tools across agents and configure `tool_choice` | 04 |
| 2.4 | Integrate MCP servers into Claude Code and agent workflows | 05 |
| 2.5 | Built-in tools (Read, Write, Edit, Bash, Grep, Glob) | 05 |
| 3.1 | CLAUDE.md hierarchy, scoping, modular organization | 08 |
| 3.2 | Custom slash commands and skills | 08 |
| 3.3 | Path-specific rules for conditional convention loading | 08 |
| 3.4 | Plan mode vs direct execution | 08 |
| 3.5 | Iterative refinement techniques | 09 |
| 3.6 | Claude Code in CI/CD pipelines | 09 |
| 4.1 | Prompts with explicit criteria (precision, fewer false positives) | 02 |
| 4.2 | Few-shot prompting for consistency and quality | 02 |
| 4.3 | Structured output using tool use and JSON schemas | 03 |
| 4.4 | Validation, retry, and feedback loops for extraction | 03 |
| 4.5 | Efficient batch processing strategies | 03 |
| 4.6 | Multi-instance and multi-pass review architectures | 09 |
| 5.1 | Conversation context across long interactions | 10 |
| 5.2 | Escalation and ambiguity resolution patterns | 06 |
| 5.3 | Error propagation across multi-agent systems | 11 |
| 5.4 | Context in large codebase exploration | 10 |
| 5.5 | Human review workflows and confidence calibration | 11 |
| 5.6 | Information provenance and uncertainty in multi-source synthesis | 11 |

São **só esses 30**. TS como "2.6", "4.7", "4.8", "5.7", "5.8", citados por fontes não oficiais, **não
existem** no guia.

**Fora do escopo (seção 17), nunca decide uma questão:** fine-tuning; autenticação, billing e conta;
detalhes de linguagem/framework além do necessário para tools e schemas; deploy/hospedagem de servidor
MCP; arquitetura interna, treino e pesos; Constitutional AI/RLHF; embeddings e vector DB; computer use;
vision; **streaming/SSE**; rate limits, quotas e cálculo de preço; OAuth e rotação de chave; cloud
providers; benchmarks; prompt caching além de "existe"; tokenização.

### Por quê e como cai

O exame mede **decisão de arquiteto em produção**. A lista de TS diz onde está a nota; o out-of-scope
evita gastar confiança em alternativas que dependem do que o guia nem cobra. Não cai como pergunta;
muda a estratégia: ~2 min por item, identifique o **cenário** antes das alternativas e, em múltipla
resposta, marque **exatamente** o número pedido.

---

## 2. Como é uma questão: distratores e desempates

### Fatos de prova

Uma questão típica = **1 frase do cenário + sintoma concreto (número, log, config) + pergunta de
decisão**: "What's the most effective first step?", "What is the most likely root cause?", "How should
you evaluate this proposal?". As 4 alternativas são **todas plausíveis** e têm tamanho parecido; o
tamanho não denuncia a certa.

Ilustração com a questão oficial 2 (cenário 1):

> *Production logs show the agent frequently calls `get_customer` when users ask about orders (e.g.,
> "check my order #12345"), instead of calling `lookup_order`. Both tools have minimal descriptions
> ("Retrieves customer information" / "Retrieves order details") and accept similar identifier
> formats. What's the most effective first step to improve tool selection reliability?*
> A. Few-shot examples (5-8) routing order queries to `lookup_order` ·
> **B. Expand each description: input formats, example queries, edge cases, boundaries ✔** ·
> C. Routing layer that pre-selects the tool by keywords · D. Consolidate into one `lookup_entity` tool

Leitura: a **causa raiz** está no enunciado (descrições mínimas). A ataca o sintoma com custo de
tokens; C é **over-engineering** e tira do modelo a decisão; D é arquitetura válida, mas **grande demais
para um primeiro passo**. B é a correção mais simples que resolve a causa.

A questão oficial 1 mostra o outro desempate: o agente às vezes pula a verificação de identidade antes
de reembolsar. Certa: **pré-requisito programático** que bloqueia as tools até a verificação. Erradas:
reforçar o system prompt e few-shot (probabilísticos para uma regra com consequência financeira) e um
classificador de roteamento (resolve **disponibilidade** de tools, não **ordem**).

**Taxonomia de distratores** (cada errada é algo que um engenheiro razoável proporia):

| Distrator (cara na alternativa) | Por que perde | Oficial |
|---------------------------------|---------------|---------|
| Fix só por prompt/few-shot ("state that X is mandatory") | Probabilístico onde a regra exige garantia | Q1 B, C |
| Over-engineering (classificador, routing layer, 2º modelo, ML) | Infraestrutura antes do passo simples | Q2 C, Q3 C |
| Resolve outro problema | Real, mas não é a causa do sintoma | Q1 D, Q3 D |
| Feature/flag inexistente | Não existe | Q4 D, Q10 B, D |
| Empurrar o ônus para humanos/devs | Não melhora o sistema | Q12 B |
| Modelo ou janela maior | Não resolve atenção nem lógica | Q12 C |
| Votação entre runs | Suprime bugs reais intermitentes | Q12 D |
| Cache/pré-busca especulativa | Não prevê o que será preciso | Q9 D |
| Retry + status genérico | Esconde o contexto do erro | Q8 B |
| Supressão silenciosa (vazio = sucesso) | Impede a recuperação | Q8 C |
| Abortar o workflow inteiro | Recuperação parcial era possível | Q8 D |
| Dar todas as tools | Viola menor privilégio | Q9 C |
| Consolidar/reescrever cedo demais | Esforço maior que um 1º passo | Q2 D |
| Contexto implícito ("o subagent já sabe") | Subagent não herda contexto (M07) | — |
| Confiança/sentimento como gatilho de escalonamento | Mal calibrado / não mede complexidade | Q3 B, D |

**Os 4 desempates:**

1. **A correção mais simples que resolve a causa raiz** vence (descrição da tool antes de roteador ou de
   fundir tools).
2. **Regra crítica → código/determinismo** (pré-requisito, hook, validação). Prompt tem taxa de falha
   diferente de zero.
3. **Critério explícito > critério vago**, confiança autodeclarada ou sentimento, **para decidir o que
   reportar ou quando escalar**. Atenção: confiança **por campo/achado, calibrada** com conjunto
   rotulado, para **rotear revisão humana** é resposta **certa** (4.6, 5.5; M02 §2 traz as três caras).
4. **Primeiro passo proporcional antes de infraestrutura** (prompt/critério/descrição antes de
   classificador treinado ou modelo extra), quando a regra não é crítica.

### Por quê

O exame quer o julgamento de quem opera o sistema. Os desempates 1 e 2 não conflitam: "crítico"
(dinheiro, identidade, compliance) puxa para código; "qualidade" puxa para o passo simples.

### Anti-padrões de leitura e como cai

Escolher a alternativa mais sofisticada; aceitar o diagnóstico que o enunciado insinua sem ler os logs
(Q7 oficial: os subagents fizeram certo o que receberam; o erro estava na decomposição do
coordenador). Vale para todas as questões: cenário → sintoma real → elimine pela taxonomia → desempate.

---

## 3. Messages API: request, resposta e a ausência de estado

### Fatos de prova

Um endpoint: `POST /v1/messages`. Tools e saída estruturada são recursos dele.

```jsonc
// REQUEST — POST /v1/messages
{
  "model": "claude-...",            // ← AQUI: qual modelo
  "max_tokens": 1024,               // ← AQUI: teto de SAÍDA desta resposta (obrigatório)
  "system": "You are the support agent of an electronics store...", // ← AQUI: fora de messages
  "messages": [                     // ← AQUI: histórico COMPLETO, alternando user/assistant
    { "role": "user", "content": "Where is my order 55120?" }
  ],
  "tools": [ /* definições: name, description, input_schema (seção 4) */ ],
  "tool_choice": { "type": "auto" } // ← AQUI: auto | any | tool (seção 4.4)
}
```

```jsonc
// RESPOSTA
{
  "id": "msg_01...",
  "role": "assistant",
  "content": [                      // ← AQUI: lista de content blocks
    { "type": "text", "text": "Let me look that up." },
    { "type": "tool_use", "id": "toolu_01A", "name": "lookup_order",
      "input": { "order_id": "55120" } }
  ],
  "stop_reason": "tool_use",        // ← AQUI: por que parou (tool_use | end_turn | max_tokens)
  "usage": { "input_tokens": 812, "output_tokens": 64 } // ← AQUI: contagem de tokens
}
```

`content` pode **misturar** `text` e `tool_use` e trazer **vários** `tool_use`. `max_tokens` é corte
duro: ao bater, `stop_reason: "max_tokens"` e a resposta está **cortada**. Preço/`usage` em detalhe:
out-of-scope.

**A API não tem estado (5.1-K4).** Cada request leva **todo** o histórico: mensagens do usuário,
respostas do assistant (incluindo os blocos `tool_use`) e os `tool_result`. O que não está no request
não existe para o modelo.

### Por quê

O modelo só "lembra" o que você manda. Sem o histórico completo, ele pergunta de novo o que o cliente
já disse, contradiz decisões anteriores e repete tools que já rodou ("conversational coherence").

### Anti-padrões que aparecem como alternativa errada

- Mandar só a última mensagem achando que "a API guarda a conversa" (feature inexistente).
- Reconstruir `messages` só com o texto visível ao cliente e perder os turnos de tool.
- Trocar o histórico por um resumo vago para economizar tokens (perde valores, datas e compromissos;
  o M10 ensina o jeito certo: bloco de *case facts*).
- Achar que `max_tokens` "avisa" o modelo para ser breve: é corte, não instrução.

### Como cai na prova

Cenário 1: "o agente pede de novo o número do pedido" ou "contradiz o que já disse"; os logs mostram
tokens de entrada **constantes** com a conversa crescendo → o histórico não está indo. Cenário 6: o
retry de validação manda só os erros, sem o documento e a extração anterior.

---

## 4. Tool use: definição, ciclo `tool_use` → `tool_result` e `tool_choice`

### 4.1 Definição da tool

```jsonc
// REQUEST — trecho "tools"
"tools": [{
  "name": "lookup_order",                                   // ← AQUI
  "description": "Returns status, items and return window of ONE order. Input: order_id like '55120'. Use for questions about a specific order; for account data use get_customer.", // ← AQUI: critério de seleção
  "input_schema": {                                         // ← AQUI: JSON Schema dos argumentos
    "type": "object",
    "properties": { "order_id": { "type": "string" } },
    "required": ["order_id"]
  }
}]
```

**Fato (2.1-K1):** a **`description` é o principal mecanismo de seleção**. Descrição mínima entre tools
parecidas = seleção instável. Inclua formato de entrada, exemplos, bordas e "quando usar esta × a
outra" (aprofundado no M04).

### 4.2 O ciclo e as regras do `tool_result`

O **modelo não executa nada**: ele emite `tool_use`; **o seu código** executa e devolve `tool_result`.

```jsonc
// PRÓXIMO REQUEST — "messages" depois de uma resposta com 2 tool_use
"messages": [
  { "role": "user", "content": "My order 55120 arrived broken. Can I return it?" },
  { "role": "assistant", "content": [                        // ← a resposta INTEIRA, sem editar
      { "type": "text", "text": "Let me check the order and your account." },
      { "type": "tool_use", "id": "toolu_01A", "name": "lookup_order", "input": { "order_id": "55120" } },
      { "type": "tool_use", "id": "toolu_01B", "name": "get_customer", "input": { "email": "ana@ex.com" } }
  ]},
  { "role": "user", "content": [                             // ← UMA mensagem user com TODOS os resultados
      { "type": "tool_result", "tool_use_id": "toolu_01A",   // ← AQUI: id exato do tool_use
        "content": "{\"status\":\"delivered\",\"return_until\":\"2026-11-02\"}" },
      { "type": "tool_result", "tool_use_id": "toolu_01B",
        "is_error": true,                                    // ← AQUI: falha também volta
        "content": "CRM timeout after 8s (transient, safe to retry)" }
  ]}
]
```

**Fatos de prova:**
- Anexe a resposta do assistant **inteira** (texto + todos os `tool_use`).
- **Vários `tool_use`** = chamadas independentes: execute todas (pode ser em paralelo) e devolva
  **todos** os `tool_result` **numa única mensagem `user`** (os `tool_result` primeiro; texto, se houver,
  depois), cada um com o `tool_use_id` certo. Faltar o `tool_result` de algum `tool_use` dá **400**;
  mandar um por mensagem não dá erro, mas a doc diz que isso "ensina" o modelo a evitar chamadas
  paralelas.
- Falhou? `tool_result` com **`is_error: true`** e mensagem útil; o modelo decide a recuperação. No MCP o
  flag é **`isError`** (M04/M05): os dois nomes estão certos, cada um na sua camada.

### 4.3 Tool use como saída estruturada (4.3-K1)

Defina uma tool de extração cujo `input_schema` **é** o formato que você quer e leia o dado de
`tool_use.input`. Pelo guia, é **a forma mais confiável** de obter saída conforme o schema: elimina
erro de **sintaxe** JSON. **Não** elimina erro **semântico** (soma que não fecha, valor no campo errado):
isso exige validação (M03).

### 4.4 `tool_choice` (2.3-K4, 4.3-K2): visão geral

```jsonc
// REQUEST — as três opções do guia
"tool_choice": { "type": "auto" }                              // ← pode responder em TEXTO em vez de chamar tool
"tool_choice": { "type": "any" }                               // ← TEM de chamar uma tool; escolhe qual
"tool_choice": { "type": "tool", "name": "extract_metadata" }  // ← TEM de chamar ESTA tool
```

| Opção | Use quando (resposta **correta** na prova) |
|-------|--------------------------------------------|
| `auto` | Agente conversacional: às vezes a resposta certa é texto |
| `any` | Precisa **garantir** que venha uma tool, não texto (2.3-S5); ex.: vários schemas de extração e tipo de documento desconhecido (4.3-S2) |
| forçado | Uma tool tem de rodar **primeiro** (ex.: `extract_metadata` antes do enriquecimento); os passos seguintes vêm em turnos posteriores, com `auto` |

Distratores típicos: "instrua no prompt a sempre chamar X" (probabilístico) e "use `any`" quando o
requisito é uma tool **específica** (`any` não escolhe por você). M03 e M04 aprofundam.

> **Na doc atual [volátil]:** Opus 5.5, Sonnet 5.5, Fable 5.1 e Mythos 5.1 retornam 400 para
> `any`/forçado (outros modelos aceitam; thinking manual também bloqueia); a doc também lista
> `"none"`. **Na prova, responda pelo guia:** `any` e forçado são respostas corretas.

### Anti-padrões que aparecem como alternativa errada

Uma mensagem `user` por resultado; mandar só os que deram certo; esconder a falha (vazio ou sucesso
falso); descartar o texto ou os `tool_use` do assistant; pôr o resultado no system prompt; "o modelo
chamou o CRM sozinho".

### Como cai na prova

Cenários 1 e 4: "3 tools pedidas, uma deu timeout; como montar o próximo request?". Cenários 5 e 6:
"6% das respostas vêm em prosa em vez da tool" → `tool_choice`.

---

## 5. O loop agêntico (TS 1.1)

### Fatos de prova

**Ciclo de vida (1.1-K1):** enviar request → inspecionar **`stop_reason`** → se `"tool_use"`, executar
as tools pedidas → **anexar os resultados ao histórico** → próxima iteração → se `"end_turn"`, entregar.

| `stop_reason` | Significa | O loop faz |
|---------------|-----------|------------|
| `tool_use` | Quer chamar tool(s) | Executa **todas**, anexa resultados, **continua** |
| `end_turn` | Terminou o turno | **Para** e entrega |
| `max_tokens` | Bateu no teto de saída | **Corte, não fim**: não entregue como resposta; aumente o teto ou continue (se cortou dentro de um `tool_use`, repita com `max_tokens` maior) |

**Resultados anexados ao histórico (1.1-K2, S2):** é assim que o modelo raciocina sobre a próxima ação.
O resultado tem de estar **no request seguinte**, completo e vinculado ao `tool_use_id`. Log, banco de
dados ou "processado em segundo plano" não contam: o modelo não vê.

**Decisão do modelo × árvore de decisão fixa (1.1-K3):** **Claude escolhe a próxima tool pelo
contexto**, inclusive pelo que os resultados anteriores revelaram. Árvore de decisão ou sequência fixa
de tools é script: funciona no caminho previsto e quebra fora dele. Não confunda com dois padrões
legítimos: **pré-requisito programático** para regra crítica de ordem (M06) e **prompt chaining** para
revisão previsível (M07).

**Anti-padrões de término (1.1-S3), os três do guia:**

1. **Ler linguagem natural** para decidir o fim ("done", "TASK COMPLETE", "anything else?").
2. **Teto arbitrário de iterações como mecanismo principal** de parada (corta tarefas longas no meio).
   Um teto **alto**, com log e alerta, como **backstop** contra loop infinito é correto.
3. **Usar "tem texto do assistant" como indicador de conclusão**: a mesma resposta traz texto
   ("Let me check...") **e** `tool_use`.

### O loop em C# (conceitual)

```csharp
var messages = new JsonArray { Msg("user", pedidoDoCliente) };
const int Backstop = 50;                         // rede de segurança, NÃO o critério de parada

for (var i = 0; i < Backstop; i++)
{
    var resp = await claude.SendAsync(new { model, max_tokens = 2048, system, tools, messages }); // histórico COMPLETO
    var content = resp["content"]!.AsArray();
    messages.Add(Msg("assistant", content.DeepClone()));          // resposta INTEIRA

    switch ((string)resp["stop_reason"]!)
    {
        case "tool_use":
            var results = new JsonArray();
            foreach (var call in content.Where(b => (string)b!["type"]! == "tool_use"))
            {
                var (ok, output) = await RunToolAsync((string)call!["name"]!, call["input"]!);
                results.Add(new JsonObject { ["type"] = "tool_result",
                    ["tool_use_id"] = (string)call["id"]!, ["content"] = output, ["is_error"] = !ok });
            }
            messages.Add(Msg("user", results));                   // UMA mensagem com todos
            continue;
        case "end_turn":   return FinalText(content);
        case "max_tokens": return HandleTruncation(resp);         // corte ≠ fim
        default:           throw new InvalidOperationException($"stop_reason inesperado: {resp["stop_reason"]}");
    }
}
throw new LoopBackstopException("Backstop atingido: logar e alertar (sinal de bug, não fim normal).");
```

Não existe: `texto.Contains("done")`, `break` quando há texto, `for` de 5 voltas como regra, `if/else`
escolhendo a próxima tool.

### Por quê

O valor do agente está em adaptar o caminho ao que descobre. `stop_reason` é o contrato da API; o
texto é ambíguo e o teto fixo não sabe o tamanho da tarefa.

### Anti-padrões que aparecem como alternativa errada

"Procure a frase de conclusão", "aumente o teto para 15", "peça no prompt que termine em N chamadas",
"pare quando houver texto", "pré-execute as buscas e aceite a 1ª resposta", "roteador por
palavra-chave escolhe a próxima tool", "trate `max_tokens` como fim".

### Como cai na prova

Cenários 1, 3, 4 (e 5). Sintomas: "o agente anuncia uma ação e encerra sem executá-la", "resposta
cortada no meio da frase", "chama a mesma tool 4 vezes seguidas", "sessões longas param no meio".

> **Na doc atual [volátil]:** thinking adaptativo, `effort`, sampling/prefill (400 em modelos novos),
> outros `stop_reason` (`refusal`, `pause_turn`, `stop_sequence`), Tool Runner/Managed Agents e
> `output_config.format` existem na doc, mas **não estão no guia e não caem**. Numa alternativa,
> são distrator ou irrelevantes.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| O loop precisa saber se continua | `stop_reason`: `tool_use` continua, `end_turn` para |
| Resposta tem texto **e** `tool_use` | Não terminou: execute as tools |
| `stop_reason: "max_tokens"` | Corte: não entregue; aumente o teto ou continue |
| Várias tools pedidas de uma vez | Execute todas; todos os `tool_result` numa única mensagem `user` |
| Uma tool falhou | `tool_result` com `is_error: true` e mensagem útil |
| Modelo repete tool / pergunta o que já sabe | Confira se o histórico completo (com `tool_result`) vai no request |
| Proteger contra loop infinito | Backstop alto com log/alerta, nunca regra de parada |
| Seleção errada entre tools parecidas | Melhore a `description` primeiro |
| JSON conforme schema | Tool de extração + `input_schema`; leia `tool_use.input` |
| Prosa onde precisava de tool (vários schemas) | `tool_choice: "any"` |
| Uma tool tem de rodar primeiro | `tool_choice` forçado no 1º turno, depois `auto` |

## Glossário

- **Agentic loop** — request → `stop_reason` → executar tools → anexar resultados → repetir.
- **Content block** — `text`, `tool_use` (do modelo) ou `tool_result` (seu, com `tool_use_id`).
- **`is_error`** — marca no `tool_result` que a tool falhou (no MCP: `isError`).
- **Backstop** — teto alto de iterações contra loop infinito, com alerta; não é critério de parada.
- **Model-driven decision-making** — o modelo escolhe a próxima tool pelo contexto.

## Cola de véspera

- **60 itens · 120 min · corte 720 (100–1.000) · 4 de 6 cenários · marque quantas o item pede ·
  % por domínio só informa · não deixe em branco.**
- Pesos: **D1 27** · D2 18 · D3 20 · D4 20 · D5 15. **30 TS**; out-of-scope nunca decide.
- Desempates: **mais simples que ataca a causa** · **crítico → código** · **critério explícito** ·
  **passo proporcional antes de infraestrutura**.
- API **sem estado**: histórico completo (com `tool_use` e `tool_result`) em todo request.
- `tool_result`: `tool_use_id` exato, todos numa mensagem `user`, falha com `is_error: true`.
- **`description`** é o critério de seleção. **`tool_use` + schema** = saída estruturada mais confiável
  (sintaxe sim, semântica não).
- `tool_choice`: `auto` pode dar texto · `any` garante tool · forçado garante **aquela** tool.
- Loop: `tool_use` continua, `end_turn` para, `max_tokens` = corte. Nada de frase de conclusão, teto
  como regra ou "tem texto".
- Próxima tool: **o modelo decide**, não uma árvore fixa.

## Perguntas de checagem

1. **A resposta tem "I'll check the order now" + `tool_use`, `stop_reason: "tool_use"`. O loop para?**
   Não: executa a tool, anexa resultado, continua.
2. **Tokens de entrada constantes enquanto a conversa cresce; o agente pergunta de novo o nº do
   pedido. Causa?** O histórico completo não está indo no request.
3. **3 `tool_use`, um falhou. Próximo request?** Uma mensagem `user` com 3 `tool_result`, ids
   corretos, o que falhou com `is_error: true`.
4. **Três tools de extração, tipo de documento desconhecido, 5% em prosa. Qual `tool_choice`?**
   `"any"`.
5. **Quando um teto de iterações é aceitável?** Como backstop alto, com log e alerta; nunca como
   critério principal de parada.
