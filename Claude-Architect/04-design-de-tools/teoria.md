# Módulo 04 — Design de tools: descrições, erros estruturados, `tool_choice`, tool search

> Domínio **D2 — Design de tools & integração MCP (18%)**. Task statements **2.1, 2.2, 2.3 e 2.6**.
> Cenários onde mais cai: **1 (Customer Support)**, **3 (Multi-Agent Research)**, **4 (Developer
> Productivity)** e **6 (Structured Data Extraction)**.

Ideia central do módulo: para o modelo, **a tool é o que a definição diz que ela é**. Ele escolhe a
tool lendo `name` + `description` + `input_schema`, e decide o próximo passo lendo o `tool_result`.
Quase todo problema de "o agente chamou a tool errada" ou "o agente desistiu / insistiu à toa" se
resolve na **interface** (descrição, schema, formato do erro), não com mais infraestrutura.

---

## 1. Interface da tool: a descrição é o critério de seleção

**Fato-chave.** Uma tool (client-side) é definida por `name`, `description` e `input_schema` (JSON
Schema com `properties` e `required`). A `description` **não é documentação decorativa**: é o texto
que o modelo usa para decidir **se** e **quando** chamar a tool. Uma boa descrição diz:

1. **Propósito e quando usar** (e quando **não** usar).
2. **Formato de entrada** com exemplo (ex.: "ID no formato `PED-123456`").
3. **O que devolve** (campos principais).
4. **Casos de borda**: entrada inválida, zero resultados, limites.
5. **Como difere das tools parecidas** ("para pedidos já faturados use `consultar_nota_fiscal`").

Descrições por propriedade e `enum` restringem as entradas (menos chute, menos erro de validação).

```json
{
  "name": "buscar_pedido",
  "description": "Busca UM pedido pelo ID e devolve status, itens, valor total e data de entrega prevista. Use quando o cliente informar o número do pedido. NÃO use para listar pedidos de um cliente (use listar_pedidos_cliente). Entrada: order_id no formato PED-123456. Se o pedido não existir, devolve found=false (não é erro).",
  "input_schema": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "ID do pedido, formato PED-123456"
      },
      "incluir_itens": {
        "type": "boolean",
        "description": "true para trazer a lista de itens (resposta maior)"
      }
    },
    "required": ["order_id", "incluir_itens"],
    "additionalProperties": false
  },
  "strict": true
}
```

**`strict: true`** → as entradas que o modelo gera para a tool **seguem o schema exatamente** (tipos,
campos obrigatórios, nada de campo extra). Exige **`additionalProperties: false` em todo objeto**.
Propriedades opcionais são permitidas, mas contam para um limite total por request [volátil]; a
recomendação prática é pôr tudo em `required` e usar tipo nullable (ex.: `["string","null"]`) para o
que pode faltar. Só aceita um **subconjunto** de JSON Schema: faixa numérica (`minimum`/`maximum`),
tamanho de string (`minLength`/`maxLength`), restrições de array além de `minItems` 0/1, recursão e
`$ref` externo ficam de fora (num schema cru, a API responde **400**) → **valide isso no seu código**.
`pattern` funciona para regex **simples** (sem backreference, lookaround, `\b`).

**Por quê.** O modelo não vê seu código; vê só a definição. Se duas tools têm descrições quase
iguais, a escolha vira cara-ou-coroa.

**Anti-padrões (alternativas erradas típicas):**
- Nome/descrição vagos: `search` — "busca coisas".
- **Tools sobrepostas** (`get_customer_info` e `lookup_customer` com descrições quase idênticas) →
  roteamento errado. Correção: **renomeie e reescreva as descrições para separar propósitos**, ou
  **funda** as duas numa só.
- "Treinar um classificador de roteamento" / "adicionar um modelo para escolher a tool" /
  "few-shot gigante no system prompt" como **primeira** resposta a seleção errada — mais complexo
  que o necessário. A correção mais simples é a descrição.
- Achar que `strict: true` garante que o **valor** está certo. Garante **forma**, não semântica.

**Como cai na prova.** Cenário 1 ou 4: "o agente chama `get_customer` quando deveria chamar
`get_order`; as descrições são 'Retrieves customer data' e 'Retrieves order data'". A resposta é
**melhorar as descrições** (propósito, entrada, diferença entre elas), não um roteador nem fine-tuning.
Pegadinha: a alternativa "adicionar exemplos few-shot no system prompt" parece razoável, mas ataca o
sintoma — a definição continua ambígua.

---

## 2. Erros estruturados: o modelo precisa saber o que fazer com a falha

**Fato-chave.** Quando a execução falha, o `tool_result` volta com **`is_error: true`** e um
conteúdo **estruturado** que permite ao modelo decidir a recuperação:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
      "is_error": true,
      "content": "{\"errorCategory\": \"transient\", \"isRetryable\": true, \"retryAfterSeconds\": 5, \"description\": \"Serviço de pedidos indisponível (HTTP 503) ao consultar PED-123456\", \"attempted_action\": \"buscar_pedido(order_id=PED-123456)\", \"partial_results\": null}"
    }
  ]
}
```

Campos úteis: `isError`, `errorCategory`, `isRetryable`, descrição legível, `attempted_action`,
`partial_results` (o que deu para obter), alternativas.

| Categoria | Exemplos | Retentável? | O que o agente faz |
|-----------|----------|-------------|--------------------|
| **Transitório** | timeout, 503, rate limit | **Sim** | retry com backoff |
| **Validação** | formato errado, campo faltando | Sim, **corrigindo a entrada** | ajusta os argumentos e tenta de novo |
| **Negócio** | acima do limite de reembolso, conta congelada | **Não** | explica a política ao usuário ou escala |
| **Permissão** | acesso negado, token expirado | **Não** | escala (não adianta insistir) |

**Vazio ≠ falha.** Busca que rodou e não achou nada = **sucesso** com resultado vazio (`200`, `[]`,
`found=false`) — é **informação** ("o cliente não tem pedidos"). Timeout/503 = a busca **não
rodou** — é **erro** (`is_error: true`). Confundir os dois faz o agente afirmar coisas falsas
("você não tem pedidos") ou entrar em retry infinito numa busca que legitimamente não acha nada.

**Recuperação local.** Em multiagente, o subagent **tenta resolver o transitório localmente**
(backoff) e só **propaga** ao coordenador o que não resolveu — com contexto (o que tentou, resultado
parcial, se é retentável).

**Por quê.** Com "Operation failed" o modelo não sabe se deve tentar de novo, mudar a entrada,
desistir ou escalar. A categoria transforma a falha em decisão.

**Anti-padrões:**
- Erro genérico ("Operation failed", "Erro interno").
- **Supressão silenciosa**: backend caiu e a tool devolve `[]` como se fosse sucesso.
- Status sem contexto do que foi tentado.
- **Abortar o workflow inteiro** por uma falha pontual (o certo: seguir com o parcial, anotar a lacuna).
- Retry automático em erro de **negócio/permissão** (nunca vai passar).
- Lançar exceção que derruba o loop em vez de devolver `tool_result` com `is_error`.

**Como cai na prova.** Cenário 3: "o subagent de busca sofre timeout e devolve lista vazia; o
coordenador conclui que não há fontes". Resposta: **distinguir vazio de falha** e devolver erro
estruturado com `isRetryable`. Cenário 1: "reembolso acima do limite → o agente fica tentando de
novo". Resposta: erro de **negócio, não retentável**, com explicação para o agente informar/escalar.

---

## 3. Distribuição de tools: 4–5 por agente e subagents especializados

**Fato-chave.** A seleção de tools **degrada** quando o agente vê muitas tools ao mesmo tempo.
Diretriz: **4–5 tools por agente** no momento da decisão. Com, por exemplo, 18 tools num agente só,
a correção é **dividir em subagents especializados** (coordenador, busca, análise, ação), cada um
com o seu conjunto pequeno e coeso. Melhorar descrições **sozinho** não resolve o excesso.

Também é princípio de **menor privilégio**: o subagent de pesquisa não precisa de `emitir_reembolso`.

**Anti-padrões:**
- Um agente "faz-tudo" com 15–20 tools.
- "Use um modelo maior" ou "escreva um system prompt mais longo explicando todas as tools" como
  solução para 18 tools.
- Ir para o extremo oposto: um subagent por tool (overhead de coordenação sem ganho).

**Como cai na prova.** Cenário 3 ou 4: "o agente tem 18 tools e escolhe a errada com frequência".
A alternativa correta fala em **distribuir em subagents com 4–5 tools cada** (ou tool search, se o
problema é catálogo grande — ver seção 4). Pegadinha: "reescrever as 18 descrições" é tentador,
mas é insuficiente quando o problema é volume.

---

## 4. Tool search e `defer_loading`: catálogo grande sem poluir a decisão

**Fato-chave.** Com **tool search**, as definições marcadas `defer_loading: true` **não entram no
contexto** de início; o modelo usa a tool de busca para encontrar e carregar só as que precisa.
Use quando houver **10+ tools**, definições somando **mais de ~10k tokens**, ou **vários servidores
MCP**. Mantenha **3–5 tools frequentes não deferidas** (pelo menos uma tem que ficar não deferida).

```json
{
  "tools": [
    { "type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex" },
    { "name": "buscar_pedido", "description": "...", "input_schema": { "...": "..." } },
    { "name": "gerar_relatorio_fiscal", "description": "...", "input_schema": { "...": "..." },
      "defer_loading": true }
  ]
}
```

[volátil] Existem variantes **regex** e **BM25**; os nomes versionados mudam — confira na doc.

**Conciliação com "4–5 tools":** "4–5" é o que o modelo **vê** na hora de decidir; tool search mantém
esse número baixo enquanto o **catálogo** cresce. Tool search também **preserva o prompt cache**
(as tools deferidas não ficam no prefixo; as descobertas entram como referência ao longo da conversa).

**Anti-padrões:**
- Carregar 200 tools de 6 servidores MCP direto no request "porque o modelo tem janela grande".
- Deferir **todas** as tools, inclusive as usadas em quase todo turno (latência e erro à toa).
- Trocar o array `tools` a cada turno para "mostrar só as relevantes" → **invalida o cache** (ver seção 7).

**Como cai na prova.** Cenário 4: "a equipe conectou vários servidores MCP; as definições ocupam
~40k tokens e a seleção piorou". Resposta: **tool search com `defer_loading`**, mantendo as poucas
tools mais usadas carregadas.

---

## 5. `tool_choice` e `disable_parallel_tool_use`

**Fato-chave.**

| Valor | Efeito |
|-------|--------|
| `{"type": "auto"}` | **Padrão.** O modelo decide: chama tool(s) ou responde em texto. |
| `{"type": "any"}` | Obrigado a chamar **alguma** tool. |
| `{"type": "tool", "name": "x"}` | Obrigado a chamar **aquela** tool. |
| `{"type": "none"}` | Só texto; as tools continuam declaradas (não somem do request). |

`"disable_parallel_tool_use": true` (dentro do `tool_choice`) limita a **no máximo uma** chamada de
tool por resposta (com `auto`: no máximo uma; com `any`/`tool`: exatamente uma).

```json
"tool_choice": { "type": "auto", "disable_parallel_tool_use": true }
```

**[volátil] Restrição em modelos novos.** Em modelos mais recentes (ex.: Fable 5.1, Opus 5.5), `any`
e `tool` forçado **retornam 400**. Alternativas:
- `auto` + **instrução explícita** nomeando a tool + `strict: true` na tool; ou
- **structured outputs** (`output_config.format` com `json_schema`) quando o "forçar a tool" existia
  só para obter **JSON no formato certo**.
Modelos anteriores aceitam as quatro opções. Suporte é **por modelo** → cheque as capabilities.
(Também vale lembrar: com extended/adaptive thinking ligado, historicamente só `auto` e `none` são
aceitos.)

**Anti-padrões:**
- Usar `any`/`tool` forçado num agente conversacional → ele nunca consegue só responder.
- Usar `none` achando que "remove" as tools (elas continuam no request e no cache).
- Ao migrar de modelo, manter `tool_choice: tool` para extração e tomar 400 em produção sem testar a forma do request.

**Como cai na prova.** Cenário 6: "pipeline de extração precisa SEMPRE devolver JSON no schema; em
modelo anterior usava `tool_choice` forçado". Em modelo que aceita, forçar a tool de extração é
válido; se o enunciado mencionar 400 ao migrar, a resposta é **structured outputs** (ou `auto` +
instrução + `strict`). Cenário 1: "o agente faz duas ações de escrita em paralelo e gera conflito"
→ `disable_parallel_tool_use: true`.

---

## 6. Tools definidas pela Anthropic e server-side

**Fato-chave.** Tools definidas pela Anthropic são declaradas por **`type` + `name`** (sem
`input_schema`; o schema já é conhecido pelo modelo):

```json
{ "type": "web_search_20250305", "name": "web_search", "max_uses": 5 }
```

- **Server-side** (rodam na Anthropic): **web search**, **web fetch**, **code execution**, **tool
  search**. O resultado volta **na mesma resposta** (blocos `server_tool_use` +
  `*_tool_result`); **você não executa nada**.
- **Client-side** (você executa): **bash**, **text editor**, **memory** (e computer use). O modelo
  emite `tool_use` e você devolve `tool_result`, como nas suas tools.

**Erro server-side vem com HTTP 200.** A falha não é status HTTP: vem como objeto de erro **dentro**
do bloco de resultado, ex.:

```json
{
  "type": "web_search_tool_result",
  "tool_use_id": "srvtoolu_01...",
  "content": { "type": "web_search_tool_result_error", "error_code": "max_uses_exceeded" }
}
```

Código que só checa `HTTP != 200` **não vê** essa falha.

**`pause_turn`.** O loop server-side (ex.: várias buscas seguidas) bateu no teto de iterações. A
resposta é **parcial**: **reenvie** a conversa com essa resposta do assistant como está para o
modelo continuar. Não é erro e não é fim.

**Web fetch só busca URLs que já estão na conversa** (mensagens do usuário ou resultados anteriores
de tools, como uma busca). Não é crawler: não inventa nem gera URLs para buscar.

[volátil] **Programmatic tool calling**: o modelo chama tools de dentro do sandbox de code execution;
resultados grandes são processados lá e **não lotam o contexto**.

**Como cai na prova.** Cenário 3/4: "o agente de pesquisa às vezes devolve resposta incompleta e o
log mostra `stop_reason: pause_turn`; o código trata como fim". Resposta: **reenviar para continuar**.
Pegadinha: "aumentar `max_tokens`" — não tem nada a ver (isso seria `max_tokens`).

---

## 7. Tool use paralelo, devolução dos resultados e cache

**Fato-chave.** O modelo pode emitir **vários `tool_use`** na mesma resposta (e misturar com texto):

```json
{
  "role": "assistant",
  "content": [
    { "type": "text", "text": "Vou consultar o pedido e o cliente." },
    { "type": "tool_use", "id": "toolu_A", "name": "buscar_pedido",
      "input": { "order_id": "PED-123456", "incluir_itens": false } },
    { "type": "tool_use", "id": "toolu_B", "name": "buscar_cliente",
      "input": { "customer_id": "C-889" } }
  ],
  "stop_reason": "tool_use"
}
```

Regras de devolução:
- Execute (pode ser em paralelo) e devolva **todos** os `tool_result` numa **única mensagem `user`**.
- Cada `tool_result` referencia o **`tool_use_id` exato**.
- Os blocos `tool_result` vêm **primeiro** no `content` (texto adicional, se houver, depois).
- A que falhou **também** recebe resultado, com `is_error: true` — nunca omita.

```json
{
  "role": "user",
  "content": [
    { "type": "tool_result", "tool_use_id": "toolu_A",
      "content": "{\"status\": \"enviado\", \"total\": 129.90}" },
    { "type": "tool_result", "tool_use_id": "toolu_B", "is_error": true,
      "content": "{\"errorCategory\": \"permission\", \"isRetryable\": false, \"description\": \"Token do CRM expirado\"}" }
  ]
}
```

**Cache:** o prefixo cacheado segue a ordem **tools → system → messages**. **Trocar o array `tools`
entre turnos invalida o cache** de tudo. Mantenha a lista estável (ou use tool search).

**Anti-padrões:**
- Mandar cada `tool_result` numa mensagem `user` separada (quebra o padrão e degrada o paralelismo).
- Devolver só os resultados bem-sucedidos e "esquecer" o que falhou → request inválido/estado confuso.
- Achar que ter texto no `content` significa que terminou — quem decide é o `stop_reason`.

---

## 8. MCP connector (visão geral)

**Fato-chave.** O **MCP connector** permite que a **Messages API** se conecte **direto** a um
servidor MCP **remoto** (sem você escrever um client MCP): o request declara `mcp_servers` (URL,
nome, token) e um toolset que expõe as tools daquele servidor. [volátil] É beta; nomes de campo e
header mudam — confira na doc. Detalhes de MCP (arquitetura, transportes, escopos) estão no
**Módulo 05**.

**Como cai na prova.** Raramente como detalhe de sintaxe; mais como "qual a forma mais simples de dar
a um app na Messages API acesso a um servidor MCP remoto já existente?" → MCP connector.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| O agente confunde duas tools parecidas | Reescreva as descrições (propósito, entrada, diferença) ou funda as tools |
| Precisa garantir que os argumentos batem com o schema | `strict: true` (+ `additionalProperties: false` em todo objeto; prefira `required` + nullable) |
| Precisa validar faixa, tamanho, regex complexa, soma, regra de negócio | Valide no **seu código** (strict não cobre) |
| A tool falhou por timeout/503 | `is_error: true`, categoria transitória, `isRetryable: true` → retry com backoff |
| A busca rodou e não achou nada | Sucesso com resultado vazio (não é erro) |
| Violação de política (limite, conta congelada) | Erro de negócio, **não retentável** → explicar/escalar |
| Token expirado / acesso negado | Erro de permissão, **não retentável** → escalar |
| Agente com 15–20 tools escolhendo errado | Subagents especializados com **4–5 tools** cada |
| Catálogo grande / vários servidores MCP / >10k tokens de definições | **Tool search** + `defer_loading`, 3–5 frequentes carregadas |
| O modelo deve só conversar agora, sem chamar tools | `tool_choice: none` |
| Uma chamada por vez (escritas que conflitam) | `disable_parallel_tool_use: true` |
| Forçar tool retorna 400 no modelo novo | `auto` + instrução + `strict`, ou **structured outputs** |
| `stop_reason: pause_turn` | Reenvie a resposta para continuar |
| Resposta 200 mas busca server-side "não funcionou" | Leia o objeto de erro **dentro** do resultado |
| Vários `tool_use` numa resposta | Todos os `tool_result` numa única mensagem `user`, incluindo os com erro |
| Quer variar as tools por turno | Não troque o array `tools` (invalida o cache); use tool search |

## Glossário

- **`input_schema`** — JSON Schema dos argumentos de uma tool client-side.
- **`strict`** — garante que os argumentos gerados obedecem ao schema (forma, não semântica).
- **`tool_use` / `tool_result`** — bloco em que o modelo pede a execução / bloco em que você devolve o resultado, ligados pelo `tool_use_id`.
- **`is_error`** — marca o `tool_result` como falha para o modelo raciocinar sobre a recuperação.
- **`errorCategory` / `isRetryable`** — convenção de erro estruturado (transitório, validação, negócio, permissão).
- **`tool_choice`** — `auto` / `any` / `tool` / `none`; controla se e qual tool o modelo deve chamar.
- **`disable_parallel_tool_use`** — no máximo uma chamada de tool por resposta.
- **Tool search / `defer_loading`** — carregar definições de tools sob demanda.
- **Tool definida pela Anthropic** — declarada por `type` + `name` (web search, web fetch, code execution, bash, text editor, memory...).
- **Server-side tool** — roda na Anthropic; resultado na mesma resposta; erro com HTTP 200.
- **`pause_turn`** — loop server-side atingiu o teto de iterações; reenvie para continuar.
- **MCP connector** — Messages API falando direto com servidor MCP remoto.

## Cola de véspera

- **Descrição = critério de seleção.** Propósito, quando usar/não usar, formato de entrada com exemplo, saída, bordas, diferença das vizinhas. Tools sobrepostas → renomeie/reescreva ou funda.
- **`strict: true`** → forma garantida (`additionalProperties: false` em todo objeto; opcionais contam para um limite, prefira `required` + nullable); semântica, faixas e tamanhos = seu código.
- **Erro estruturado** com `is_error: true` + categoria: **transitório** (retry/backoff) · **validação** (corrija e tente) · **negócio** (não retenta; explique/escale) · **permissão** (não retenta; escale).
- **Vazio ≠ falha.** `[]` é informação; timeout é erro. Nunca devolva `[]` quando o backend caiu.
- Subagent resolve transitório **localmente**, propaga o resto **com contexto**; não aborte o workflow por uma falha.
- **4–5 tools por agente.** 18 tools → subagents especializados. Catálogo grande → **tool search** (`defer_loading`, 3–5 frequentes carregadas).
- **`tool_choice`**: `auto` (padrão) · `any` (alguma) · `tool` (aquela) · `none` (só texto). `disable_parallel_tool_use` = uma por vez. [volátil] modelos novos: `any`/`tool` → 400 → `auto` + instrução + `strict` ou structured outputs.
- **Anthropic-defined**: `type` + `name`. **Server-side** (web search/fetch, code execution, tool search): resultado na mesma resposta, **erro com HTTP 200**, `pause_turn` → reenvie.
- **Web fetch** só URLs já presentes na conversa.
- **Paralelo:** todos os `tool_result` numa só mensagem `user`, `tool_use_id` exato, com erro também.
- **Trocar `tools` entre turnos invalida o cache.**

## Perguntas de checagem

1. **Duas tools, `get_customer` e `lookup_client`, têm descrições quase iguais e o agente alterna entre elas sem critério. Qual a primeira correção?**
   Reescrever as descrições para separar propósitos (ou fundir as tools). Nada de classificador ou fine-tuning antes disso.
2. **A tool de busca de pedidos sofre timeout e devolve `[]`. Qual o problema?**
   Supressão silenciosa: falha disfarçada de "nada encontrado". Deve devolver `is_error: true`, categoria transitória, `isRetryable: true`.
3. **O agente tenta reembolsar acima do limite e recebe erro; fica tentando de novo. O que muda?**
   O erro deve ser de categoria **negócio** com `isRetryable: false` e explicação, para o agente informar a política ou escalar.
4. **A resposta chegou com `stop_reason: pause_turn`. O que fazer?**
   Reenviar a conversa com a resposta do assistant como está para o modelo continuar o loop server-side.
5. **O modelo emitiu 3 `tool_use`; um falhou. Como devolver?**
   Uma única mensagem `user` com os 3 `tool_result` (cada um com seu `tool_use_id`); o que falhou com `is_error: true`.
