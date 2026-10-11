# Módulo 06 — O loop agêntico, enforcement com hooks e handoff humano

> **Domínio D1 — Arquitetura agêntica & orquestração (27%, o MAIOR peso da prova).**
> Task statements: **1.1** (ciclo de vida do loop agêntico), **1.4** (enforcement de workflow e
> handoff), **1.5** (hooks). O Módulo 07 completa o D1 com multiagente, decomposição e sessões.

Este módulo é a base de quase todo cenário da prova: o **Customer Support Resolution Agent**
(cenário 1) é um loop agêntico com tools MCP e regras de negócio; o **Multi-Agent Research System**
(cenário 3) é um loop que chama outros loops; o **Claude Code em CI** (cenário 5) é o mesmo loop rodando
sem humano. Se você entende o loop, metade do D1 vira bom senso.

---

## 1. O loop agêntico em uma frase

**Fato-chave.** Um agente é um **loop**: você manda `messages` + definições de `tools` → Claude
responde → se a resposta pede tool, **você executa** e devolve o resultado → repete até o modelo
sinalizar que terminou. Quem decide **qual tool chamar, em que ordem e quando parar é o modelo**.

```
┌────────────┐   messages + tools    ┌────────┐
│  seu código │ ────────────────────▶ │ Claude │
│  (harness)  │ ◀──────────────────── │        │
└────────────┘   content + stop_reason└────────┘
      │  stop_reason == "tool_use"?  → executa tools → anexa tool_result → volta
      │  stop_reason == "end_turn"?  → entrega a resposta → sai
```

**Por quê.** O valor de um agente está em o modelo adaptar o caminho ao que descobre (o resultado
da tool 1 muda o que ele faz depois). Se você fixa o caminho por fora, não tem agente: tem um script
caro.

**Anti-padrão (aparece como alternativa errada).** Codificar uma **árvore de decisão** externa
("se a mensagem do cliente contém 'reembolso', chame `lookup_order` e depois `process_refund`") para
"ajudar" o modelo. Isso tira do modelo a decisão que é justamente a função dele e quebra no primeiro
caso fora do roteiro. Regras **críticas** vão em código (seção 6), mas **o roteamento entre tools é do
modelo**.

**Como cai na prova.** Cenário 1 (suporte): "o agente às vezes chama as tools numa ordem
inesperada; o que fazer?" A pegadinha é oferecer "um `if/else` que decide a próxima tool". A resposta
certa costuma ser **melhorar a descrição das tools** (D2) ou, se a ordem é uma regra de negócio
obrigatória, **um pré-requisito programático** (hook/gate), nunca um roteador manual de tudo.

---

## 2. `stop_reason`: o único sinal confiável de parada

**Fato-chave.** Toda resposta da Messages API traz `stop_reason`. **É ele que decide o próximo passo
do loop**, não o texto da resposta.

| `stop_reason` | O que significa | O que seu loop faz |
|---|---|---|
| `tool_use` | O modelo quer chamar uma ou mais tools | Executa **todas** as tools pedidas, devolve os `tool_result`, chama de novo |
| `end_turn` | O modelo terminou naturalmente | Entrega a resposta final e **sai do loop** |
| `max_tokens` | Bateu no teto de **saída** (`max_tokens`) no meio da resposta | A resposta está **cortada**: continue (peça para seguir) ou aumente o teto; nunca trate como completa |
| `stop_sequence` | Gerou uma das `stop_sequences` que você configurou | Trate conforme o seu protocolo (`stop_sequence` diz qual foi) |
| `pause_turn` | Um loop de **tool server-side** (web search, code execution...) atingiu o teto de iterações | **Reenvie** a resposta (anexe o `content` como turno do assistant) para o modelo continuar |
| `refusal` | O modelo recusou por segurança | Vem com **HTTP 200**! Cheque antes de ler `content`; trate como recusa (não como sucesso vazio) |
| `model_context_window_exceeded` | Encheu a **janela de contexto** antes do `max_tokens` | Saída válida, porém truncada: compacte/resuma o contexto ou divida a tarefa |

**Por quê.** O texto é ambíguo: o modelo escreve "Vou verificar o pedido agora..." **e no mesmo
turno** emite um `tool_use`. Ler o texto para decidir é adivinhação; `stop_reason` é o contrato da API.

**Anti-padrões (os clássicos nº 1 e nº 2 do blueprint).**
1. **Parar o loop lendo linguagem natural** ("se a resposta contém 'terminei' / 'Final answer', sai").
2. **Limite fixo de iterações como mecanismo principal** ("roda 5 voltas e para"). Corta tarefas
   longas no meio e deixa as curtas gastarem voltas à toa. Como **backstop** de segurança (um teto
   alto contra loop infinito, com log/alerta quando dispara) é correto; como **critério de parada**, é
   errado.
3. **Tratar HTTP 200 como sucesso** sem olhar `stop_reason` → uma `refusal` vira "resposta vazia" no
   seu sistema.
4. **Ignorar `max_tokens`** → JSON cortado pela metade é "parseado" e falha mais adiante, longe da causa.

**Como cai na prova.** Cenários 1, 3 e 5. Sintoma típico: "o agente às vezes encerra antes de
executar a tool / o pipeline marca como concluído um relatório incompleto". Alternativas erradas:
"aumentar o limite de iterações", "procurar a palavra 'concluído' na resposta", "pedir no prompt para
o modelo sempre dizer DONE". Certa: **dirigir o loop por `stop_reason`**.

---

## 3. A anatomia de uma resposta com tools

**Fato-chave 1: `content` é uma lista de blocos e pode misturar tipos.** Uma única resposta pode
ter um bloco `text` ("Vou consultar o pedido e o cliente") **e** um ou mais blocos `tool_use`.
**Ter texto não significa que terminou.** Quem diz se terminou é `stop_reason`.

```json
{
  "stop_reason": "tool_use",
  "content": [
    { "type": "text", "text": "Vou consultar o pedido e o histórico do cliente." },
    { "type": "tool_use", "id": "toolu_01A", "name": "get_order",    "input": { "order_id": "8812" } },
    { "type": "tool_use", "id": "toolu_01B", "name": "get_customer", "input": { "customer_id": "C-77" } }
  ]
}
```

**Fato-chave 2: tool use paralelo.** Vários `tool_use` na mesma resposta = o modelo pediu chamadas
**independentes**. Execute-as (pode ser em paralelo) e devolva **todos** os resultados.

**Fato-chave 3: como devolver os resultados.**
- A resposta do assistant (com os `tool_use`) é **anexada inteira** ao histórico.
- Em seguida vem **uma única mensagem `user`** contendo **um `tool_result` para cada `tool_use`**.
- Cada `tool_result` tem o **`tool_use_id` exato** do pedido correspondente.
- Uma tool que **falhou também recebe resultado**, com `"is_error": true` e uma mensagem útil, para o
  modelo **raciocinar sobre a recuperação** (tentar outra tool, pedir dado ao usuário, escalar).

```json
{
  "role": "user",
  "content": [
    { "type": "tool_result", "tool_use_id": "toolu_01A", "content": "{\"status\":\"delivered\",\"total\":129.90}" },
    { "type": "tool_result", "tool_use_id": "toolu_01B", "is_error": true,
      "content": "CRM timeout após 5s (transitório, pode tentar de novo)" }
  ]
}
```

**Por quê.** O modelo casa cada resultado com o pedido pelo id. Resultado faltando, id errado ou
resultados espalhados em várias mensagens `user` quebram o protocolo (erro 400 ou modelo confuso).
Omitir a falha impede o modelo de se recuperar.

**Anti-padrões.**
- Mandar **uma mensagem `user` por resultado** (ou só o primeiro resultado).
- **Descartar o bloco `text`** do assistant ao montar o histórico, ou anexar só o texto e perder os `tool_use`.
- **Esconder a falha**: devolver `"content": ""` ou um sucesso falso quando a tool caiu; ou, no
  extremo oposto, **abortar o loop inteiro** por causa de uma tool que falhou.
- Desabilitar o paralelismo "por segurança" sem motivo (`disable_parallel_tool_use` existe para quando
  a ordem importa ou o backend não aguenta; não é o padrão).

**Como cai na prova.** Cenário 1 ou 4: "o agente pediu 3 tools; uma deu timeout; como montar o
próximo request?" Certa: **uma mensagem `user` com 3 `tool_result`**, cada um com seu `tool_use_id`, o
que falhou com `is_error: true`. Pegadinha: "reexecute só as que deram certo e omita a que falhou" ou
"lance exceção e reinicie a conversa".

---

## 4. O loop em C# (conceitual)

Um loop manual mínimo com `HttpClient` + `System.Text.Json`. É conceitual (sem tratamento de
retry/HTTP), mas mostra exatamente o que a prova cobra: **decidir por `stop_reason`**, anexar o
`content` inteiro, devolver todos os `tool_result` numa única mensagem `user`, `is_error` na falha e
um **backstop** (não o critério principal).

```csharp
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Nodes;

var http = new HttpClient { BaseAddress = new Uri("https://api.anthropic.com/") };
http.DefaultRequestHeaders.Add("x-api-key", Environment.GetEnvironmentVariable("ANTHROPIC_API_KEY"));
http.DefaultRequestHeaders.Add("anthropic-version", "2023-06-01");

var messages = new JsonArray { new JsonObject { ["role"] = "user", ["content"] = pedidoDoCliente } };
const int Backstop = 50;                       // rede de segurança, NÃO o critério de parada

for (var volta = 1; volta <= Backstop; volta++)
{
    var req = new JsonObject { ["model"] = modelo, ["max_tokens"] = 4096,
                               ["tools"] = tools.DeepClone(), ["messages"] = messages.DeepClone() };
    var resp = await (await http.PostAsJsonAsync("v1/messages", req)).Content.ReadFromJsonAsync<JsonObject>();
    var content = resp!["content"]!.AsArray();
    messages.Add(new JsonObject { ["role"] = "assistant", ["content"] = content.DeepClone() }); // content INTEIRO

    switch ((string)resp["stop_reason"]!)
    {
        case "tool_use":
            var results = new JsonArray();
            foreach (var bloco in content.Where(b => (string)b!["type"]! == "tool_use"))
            {
                var (ok, saida) = await ExecutarToolAsync((string)bloco!["name"]!, bloco["input"]!);
                results.Add(new JsonObject { ["type"] = "tool_result",
                    ["tool_use_id"] = (string)bloco["id"]!,      // id EXATO
                    ["content"] = saida, ["is_error"] = !ok });  // falha também volta
            }
            messages.Add(new JsonObject { ["role"] = "user", ["content"] = results }); // UMA mensagem
            continue;
        case "end_turn":    return TextoFinal(content);
        case "pause_turn":  continue;                       // tool server-side: reenvia e continua
        case "max_tokens":  messages.Add(PedirContinuacao()); continue; // resposta cortada
        case "refusal":     return Recusa(content);         // veio com HTTP 200!
        default:            throw new InvalidOperationException($"stop_reason: {resp["stop_reason"]}");
    }
}
throw new TimeoutException("Backstop atingido: logar e alertar (sinal de bug, não fim normal).");
```

Repare no que **não** existe: nenhum `if (texto.Contains("pronto"))`, nenhuma árvore decidindo qual
tool chamar, nenhum `for` de 5 voltas como regra de parada.

---

## 5. Task budget vs. `max_tokens`; e as 4 formas de construir

### 5.1 Task budget vs. `max_tokens`

**Fato-chave.**
- **`max_tokens`** = teto **invisível** de saída **por resposta**. O modelo não sabe dele; quando
  bate, **corta no meio** (`stop_reason: "max_tokens"`).
- **Task budget** [volátil, beta] = teto de tokens para a **tarefa inteira** (várias voltas do loop),
  **visível ao modelo**, que **se organiza para caber** (prioriza, resume, encerra com elegância).

**Por quê.** Cortar no meio produz lixo; um orçamento visível produz um resultado menor, porém
completo.

**Anti-padrão.** "Para limitar o custo de um agente longo, reduza o `max_tokens`." Isso só corta
respostas pela metade; não limita o número de voltas nem ajuda o modelo a planejar.

**Como cai na prova.** Cenário 3 ou 5: "a pesquisa está estourando custo; queremos que o agente
entregue algo completo dentro de um orçamento". Certa: orçamento **visível** (task budget) e/ou
backstop; errada: baixar `max_tokens`.

### 5.2 As 4 formas de construir um agente (escolha a mais simples que atende)

| Forma | Quem roda o loop | Quem hospeda as tools/ambiente | Quando escolher |
|---|---|---|---|
| **Loop manual** (Messages API) | Você | Você | Controle total, poucas tools, lógica própria entre voltas |
| **Tool Runner** (SDK) | O SDK roda o loop | Você (suas funções viram tools) | Quer o loop padrão sem escrever boilerplate |
| **Managed Agents** [beta] | Anthropic | Anthropic (loop + **sandbox** hospedados) | Não quer operar infraestrutura de execução |
| **Claude Agent SDK** | O harness do Claude Code como biblioteca | Você (com tools nativas, subagents, hooks, sessões, MCP) | Precisa do "Claude Code programável": arquivos, subagents, hooks, permissões |

**Por quê.** Cada degrau traz mais pronto **e** mais coisa para entender/operar. A regra de ouro da
prova vale aqui: **a solução mais simples que resolve**.

**Anti-padrão.** Escolher o Agent SDK com subagents para algo que é "uma chamada de extração com uma
tool"; ou escrever o loop à mão quando precisa de hooks, subagents e sessões (reinventar o harness).

**Como cai na prova.** "Uma equipe precisa de um agente de suporte com 4 tools internas, sem
subagents nem acesso a arquivos." Mais simples que atende: **loop manual ou Tool Runner**. Se o
enunciado pede hooks, subagents, sessões retomáveis, tools de arquivo → **Agent SDK**.

---

## 6. Enforcement: programático vs. prompt

**Fato-chave.**
- **Prompt** = **probabilístico**. "NUNCA processe reembolso sem verificar a identidade" funciona
  quase sempre, ou seja, tem **taxa de falha não nula**.
- **Programático** (hook, pré-requisito no código da tool, gate no harness) = **determinístico**.
- Regra com **consequência financeira, de segurança ou de compliance → programática. Obrigatório.**
  Prompt fica para o que é **best-effort** (tom, formato, preferências).

**Formas de enforcement programático.**
1. **Hook `PreToolUse`** que nega `process_refund` se a verificação não ocorreu na sessão.
2. **Pré-requisito dentro da tool**: o próprio `process_refund` exige um `verification_token` emitido
   por `verify_identity` (sem token válido, devolve erro estruturado).
3. **Limite de valor em código**: acima de US$ X, a tool devolve "requer aprovação humana" e o
   agente escala.

**Por quê.** "Funciona em 99% dos casos" num reembolso significa 1 reembolso indevido a cada 100.
Nenhuma frase em maiúsculas fecha esse 1%.

**Anti-padrões.**
- Reforçar o prompt ("IMPORTANTE", "NUNCA", repetir a regra 3 vezes, colocar no system prompt e no
  user) como correção de uma regra crítica.
- Adicionar **few-shot** de verificação como garantia (melhora a média, não garante).
- **Um segundo LLM** que "revisa se a verificação foi feita" (continua probabilístico e mais caro).
- O inverso também é erro: usar hook para algo puramente estilístico ("responda em tom cordial") é
  engenharia demais; isso é prompt.

**Como cai na prova.** Cenário 1, quase certo: "em 2% das conversas o agente processou reembolso
antes de verificar a identidade". As erradas são todas variantes de "reforce o prompt". A certa é
**enforcement programático** (hook `PreToolUse`/pré-requisito na tool).

---

## 7. Handoff para humano com resumo estruturado

**Fato-chave.** Quando o agente escala, **o humano normalmente não vê o transcript** (ou não tem
tempo de ler 40 turnos). O handoff precisa de um **resumo estruturado** com, no mínimo:

| Campo | Exemplo |
|---|---|
| Cliente (identidade **já verificada?**) | Maria S., conta C-77, verificada via OTP |
| Problema | Cobrança duplicada no pedido 8812 |
| Pedido do cliente | Estorno de uma das cobranças |
| Causa raiz (o que o agente descobriu) | Retry do gateway gerou 2 capturas |
| Ações já tomadas | Consultou pedido e gateway; confirmou 2 capturas de US$ 129,90 |
| Por que escalou | Estorno acima do limite de alçada do agente (política) |
| Ação recomendada | Aprovar estorno de US$ 129,90 da captura #2 |
| Valor envolvido | US$ 129,90 |

**Por quê.** Sem isso, o humano refaz toda a investigação (pior experiência e custo dobrado) ou age
com informação errada. Estruturado (campos fixos, de preferência JSON via tool de handoff) é
**completo e verificável**; texto livre esquece campos.

**Anti-padrões.**
- Encaminhar o **transcript bruto** inteiro como handoff.
- Um resumo em prosa livre "o cliente está com um problema de cobrança".
- Transferir sem dizer **o que já foi feito** (o humano repete a verificação, o cliente se irrita).
- (Do Módulo 11, mas aparece junto) escalar por **sentimento** ou por **confiança autodeclarada**.
  Escala-se por: pedido explícito de humano, exceção/lacuna de política, falta de progresso.

**Como cai na prova.** Cenário 1: "os atendentes reclamam que precisam reler a conversa toda
quando o agente transfere". Certa: **tool de handoff com schema estruturado** (os campos acima).
Pegadinha: "enviar o transcript completo para não perder nada" (perde o tempo do humano e não destaca
o que importa).

---

## 8. Hooks: eventos, tipos e o contrato de saída

Hooks são **código seu que o harness executa automaticamente** em pontos do ciclo de vida do
Claude Code / Agent SDK. Diferente do prompt, **o modelo não pode "esquecer" um hook**: é o harness
que roda.

### 8.1 Eventos que a prova cobra

| Evento | Quando dispara | Uso típico na prova |
|---|---|---|
| `SessionStart` | Início/retomada de sessão | Injetar contexto (branch atual, tickets abertos) |
| `UserPromptSubmit` | Antes de processar o prompt do usuário | Validar/bloquear prompt, adicionar contexto |
| `PreToolUse` | **Antes** de uma tool rodar | **Bloquear/permitir/pedir confirmação** (ex.: `process_refund` sem verificação, `rm -rf`, escrita em `prod/`) |
| `PermissionRequest` | Quando apareceria um diálogo de permissão | Aprovar/negar automaticamente |
| `PostToolUse` | **Depois** de uma tool rodar com sucesso | **Normalizar, limpar, anotar** o resultado (mascarar PII, cortar campos, rodar formatter/lint após Edit) |
| `PostToolUseFailure` | Depois de uma tool falhar | Tratar/registrar erro, dar contexto de recuperação |
| `SubagentStop` | Um subagent terminou | Validar a entrega do subagent |
| `PreCompact` | Antes de compactar o contexto | Salvar estado/fatos críticos |
| `Stop` | O agente principal vai encerrar o turno | Checar "terminou mesmo?" (ex.: testes passaram?); pode forçar continuar |
| `SessionEnd` | Fim da sessão | Limpeza, log, métricas |

### 8.2 Tipos de hook

| Tipo | O que roda |
|---|---|
| `command` | Um comando/script de shell; recebe o evento em **JSON pelo stdin** |
| `http` | POST do evento para um endpoint seu |
| `mcp_tool` | Chama uma tool de um servidor MCP |
| `prompt` | **Uma** chamada a um LLM com resposta sim/não (decisão leve por julgamento) |
| `agent` | Um subagent **multi-turn com tools** para verificar algo (ex.: rodar e ler testes) |

**Lembre:** `prompt`/`agent` são hooks **probabilísticos** (há um modelo decidindo). Para regra
crítica com critério objetivo, o hook `command` (código) é o determinístico.

### 8.3 O contrato do hook `command`

- **exit 0** → passa. O stdout pode trazer **JSON** com a decisão estruturada.
- **exit 2** → **bloqueia**. O **stderr** é devolvido ao Claude como motivo (ele lê e se ajusta).
- Outros códigos → erro **não bloqueante** (registrado; a ação segue).

No `PreToolUse`, o JSON pode trazer `permissionDecision`:
- `"allow"` → permite (pula o diálogo de permissão);
- `"deny"` → **nega**, com `permissionDecisionReason` explicado ao Claude;
- `"ask"` → pede confirmação ao usuário.

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Identidade do cliente não verificada. Chame verify_identity antes de process_refund."
  }
}
```

### 8.4 Exemplo: `PreToolUse` bloqueando `process_refund` sem verificação

`.claude/settings.json` (projeto, versionado: vale para o time todo):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__support__process_refund",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/require-verification.sh"
          }
        ]
      }
    ]
  }
}
```

`.claude/hooks/require-verification.sh`:

```bash
#!/usr/bin/env bash
# Recebe o evento em JSON pelo stdin (session_id, tool_name, tool_input...)
evento=$(cat)
sessao=$(echo "$evento" | jq -r '.session_id')

if [ ! -f "/var/run/support/verified/$sessao" ]; then
  echo "Bloqueado: identidade não verificada. Use verify_identity antes de process_refund." >&2
  exit 2          # BLOQUEIA: o stderr volta para o Claude como motivo
fi
exit 0            # verificado: segue
```

O `matcher` casa pelo **nome da tool** (tools MCP aparecem como `mcp__<servidor>__<tool>`; o matcher
aceita regex, ex.: `Edit|Write`). O registro "verificado" é gravado por quem roda o `verify_identity`
(por exemplo, um `PostToolUse` nessa tool ou o próprio servidor MCP).

### 8.5 `PostToolUse`: normalizar e mascarar

**Fato-chave.** O `PostToolUse` roda **depois** que a tool executou: **não impede** a execução (para
impedir, use `PreToolUse`), mas pode **limpar/anotar o que o modelo vai ver**: mascarar PII
(cartão, CPF), padronizar datas/moedas vindas de sistemas diferentes, cortar os 40 campos para os 5
relevantes, adicionar contexto, rodar formatter após `Edit`.

**Pegadinha.** "Usar `PostToolUse` para impedir a tool de apagar arquivos" → tarde demais, já
executou. Bloquear = **Pre**; tratar resultado = **Post**; tratar falha = **PostToolUseFailure**.

### 8.6 Onde configurar

| Local | Arquivo | Alcance |
|---|---|---|
| Usuário | `~/.claude/settings.json` | Todos os seus projetos (só você) |
| Projeto | `.claude/settings.json` | **Compartilhado com o time** via git |
| Local | `.claude/settings.local.json` | Só você neste projeto (gitignored) |
| Managed policy | Política da organização (admin) | **Toda a organização**, não sobrescrevível pelo usuário |
| Skill / subagent | Frontmatter `hooks:` do `SKILL.md` ou de `.claude/agents/*.md` | Só enquanto aquela skill/subagent está ativa |
| Agent SDK | Opção `hooks` (callbacks no código) | A aplicação que usa o SDK |

**Como escolher.** Regra que o **time inteiro** precisa → projeto. Regra de **compliance da empresa**
que ninguém pode desligar → managed policy. Preferência pessoal → usuário/local. Regra que só faz
sentido dentro de um fluxo específico → frontmatter da skill/subagent.

**Como cai na prova.** Cenários 1, 2 e 4. "Precisamos garantir que nenhum dev do time rode `Edit` em
`migrations/` sem confirmação" → `PreToolUse` com `ask` em `.claude/settings.json` (projeto). "A
empresa exige que nenhum dado de cartão apareça no contexto" → `PostToolUse` mascarando (e, por ser
política da empresa, managed). Pegadinha: colocar a regra do time em `settings.local.json` (não é
compartilhado) ou em `~/.claude/settings.json` (só vale para você).

---

## Tabela de decisão

| Se... | Então... |
|---|---|
| Precisa saber se o loop continua | Olhe **`stop_reason`**, nunca o texto |
| `stop_reason: "tool_use"` | Execute **todas** as tools pedidas; **uma** mensagem `user` com todos os `tool_result` (ids exatos) |
| Uma das tools falhou | Devolva `tool_result` com **`is_error: true`** e mensagem útil; não aborte, não omita |
| `stop_reason: "max_tokens"` | Resposta cortada: continue ou aumente o teto; não trate como completa |
| `stop_reason: "pause_turn"` | Tool server-side pausou: reenvie para continuar |
| `stop_reason: "refusal"` | É recusa com HTTP 200: trate explicitamente |
| `model_context_window_exceeded` | Janela cheia: compacte/edite contexto ou divida a tarefa |
| Medo de loop infinito | **Backstop** alto + alerta; o critério de parada continua sendo `end_turn` |
| Quer limitar custo/escopo de tarefa longa | Orçamento **visível** (task budget), não `max_tokens` menor |
| Agente simples, poucas tools, sem arquivos | Loop manual / Tool Runner |
| Precisa de subagents, hooks, sessões, tools de arquivo | Claude Agent SDK |
| Regra financeira/segurança/compliance | **Código**: hook `PreToolUse` ou pré-requisito na tool |
| Regra de estilo/tom | Prompt |
| Bloquear uma ação antes de acontecer | `PreToolUse` (exit 2 ou `permissionDecision: deny`) |
| Pedir confirmação humana antes de uma ação | `PreToolUse` com `permissionDecision: ask` |
| Mascarar/normalizar o que a tool devolveu | `PostToolUse` |
| Regra para o time todo | `.claude/settings.json` (projeto) |
| Regra corporativa inegociável | Managed policy |
| Escalar para humano | Tool de handoff com **resumo estruturado** |

## Glossário

- **Loop agêntico:** ciclo request → resposta → executar tools → devolver resultados → repetir, até o modelo encerrar.
- **`stop_reason`:** campo da resposta que diz por que o modelo parou; dirige o loop.
- **Bloco `tool_use`:** pedido de chamada de tool (`id`, `name`, `input`).
- **Bloco `tool_result`:** resposta sua à tool, com `tool_use_id`, `content` e opcional `is_error`.
- **Tool use paralelo:** vários `tool_use` numa só resposta; resultados voltam juntos numa mensagem `user`.
- **Backstop:** teto de iterações de segurança contra loop infinito; não é o critério de parada.
- **Task budget [volátil]:** orçamento de tokens da tarefa visível ao modelo.
- **Tool Runner:** helper do SDK que roda o loop por você.
- **Managed Agents [beta]:** loop + sandbox hospedados pela Anthropic.
- **Claude Agent SDK:** o harness do Claude Code como biblioteca (tools nativas, subagents, hooks, sessões).
- **Enforcement programático:** regra imposta por código (determinística), não por instrução.
- **Hook:** código executado pelo harness num evento do ciclo de vida.
- **`permissionDecision`:** saída de `PreToolUse`: `allow` / `deny` / `ask`.
- **Exit 2:** código de saída que faz um hook `command` bloquear (stderr volta ao Claude).
- **Handoff estruturado:** transferência para humano com campos fixos (cliente, problema, ações, recomendação...).
- **Managed policy:** configuração imposta pela organização, acima das do usuário/projeto.

## Cola de véspera

- **`stop_reason` manda.** `tool_use` → executa e volta; `end_turn` → fim; `max_tokens` → cortado;
  `pause_turn` → reenvie; `refusal` → recusa **com HTTP 200**; `stop_sequence`; `model_context_window_exceeded`.
- **Texto + `tool_use` juntos** é normal. Texto ≠ terminou.
- **Paralelo:** N `tool_use` → N `tool_result`, **ids exatos**, **uma** mensagem `user`, falha com `is_error: true`.
- **O modelo decide** a próxima tool e quando parar. Nada de árvore de decisão externa.
- **Backstop de iterações:** ok como rede de segurança; errado como critério principal.
- **Task budget** (visível, o modelo se organiza) ≠ **`max_tokens`** (invisível, corta).
- **4 formas:** loop manual → Tool Runner → Managed Agents → Agent SDK. **A mais simples que atende.**
- **Regra crítica = código** (hook/pré-requisito). Prompt = best-effort. "Reforçar o prompt" é a alternativa errada.
- **Handoff = resumo estruturado** (cliente verificado?, problema, pedido, causa, ações, motivo, recomendação, valor). Nada de transcript bruto.
- **Hooks:** `PreToolUse` bloqueia/permite/pergunta (`deny`/`allow`/`ask`); `PostToolUse` normaliza/mascara; `Stop` checa se terminou.
- **`command`:** exit 0 passa, **exit 2 bloqueia** (stderr volta ao Claude).
- **Onde:** time → `.claude/settings.json`; você → `~/.claude/` ou `settings.local.json`; empresa → managed; fluxo específico → frontmatter da skill/subagent.

## Perguntas de checagem

1. **O modelo respondeu com um bloco `text` "Pronto, vou processar seu reembolso." e um `tool_use`
   de `process_refund`. O loop deve terminar?**
   Não. `stop_reason` será `tool_use`: execute a tool, devolva o `tool_result` e continue. Texto não indica fim.
2. **Três tools pedidas em paralelo; uma deu timeout. Como fica o próximo request?**
   Uma única mensagem `user` com três `tool_result`, cada um com o `tool_use_id` exato; o do timeout com
   `is_error: true` e mensagem que diga que é transitório.
3. **Por que um limite de 10 iterações não é um bom critério de parada, mas um teto de 50 com alerta é aceitável?**
   O primeiro decide a parada por um número arbitrário (corta tarefas legítimas). O segundo é backstop
   contra bug/loop infinito; a parada normal continua sendo `end_turn`.
4. **Em 1,5% das conversas o agente processa reembolso sem verificar identidade. Melhor correção?**
   Enforcement programático: hook `PreToolUse` que nega `process_refund` sem verificação (ou
   pré-requisito na própria tool). Reforçar o prompt continua probabilístico.
5. **Qual a diferença de papel entre `PreToolUse` e `PostToolUse`? Dê um uso de cada.**
   `PreToolUse` age antes da execução e pode bloquear/permitir/pedir confirmação (negar `rm -rf`,
   bloquear reembolso). `PostToolUse` age depois e trata o resultado (mascarar PII, normalizar formatos).
