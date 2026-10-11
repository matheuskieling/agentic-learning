# Módulo 10 — Gestão de contexto: janela, caching, compaction, context editing, memória

> Task statements do blueprint: **5.1** (contexto da conversa), **5.4** (codebase grande),
> **5.7** (gestão de contexto server-side), **5.8** (limitar e recuperar execuções longas) e
> **4.8** (prompt caching). Domínio D5 pesa 15% e o 4.8 vem de D4 (20%), mas o tema aparece
> **espalhado em todos os 6 cenários**: quase toda arquitetura longa esbarra em contexto.

A ideia que amarra o módulo: **contexto é um recurso finito e caro**. Cada token na janela é
cobrado de novo a cada turno, compete pela atenção do modelo e pode se perder quando a conversa é
resumida. O arquiteto decide **o que entra, o que sai, o que nunca pode ser parafraseado e o que é
reaproveitado do cache**.

---

## 1. A janela é finita e cada turno paga tudo de novo

**Fato-chave.** System prompt, definições de tools, mensagens e **resultados de tool** ocupam a
mesma janela. A Messages API é **stateless**: a cada turno você reenvia o histórico inteiro, e
todo token de entrada é cobrado de novo (a menos que venha do cache, seção 7). Conversa longa
**degrada**: fica mais cara, mais lenta e o modelo passa a prestar menos atenção aos detalhes.

**Por quê.** Janelas grandes (1M tokens em modelos recentes, **[volátil]**) adiam o problema, não o
eliminam. Uma janela maior cheia de lixo custa mais e piora o efeito *lost in the middle*.

**Lost in the middle.** Informação no **meio** de um contexto longo é a mais provável de ser
ignorada; começo e fim recebem mais atenção. Mitigação:
- coloque **achados-chave no começo** (ou repita-os no fim, perto da pergunta);
- use **cabeçalhos de seção** para o modelo navegar;
- **nada crítico enterrado no meio** de um dump de 300 linhas.

**Corte a saída das tools.** Se o `get_customer` devolve 40 campos e o agente usa 5, devolva **5**.
A saída de tool é o maior consumidor silencioso de contexto em loops agênticos. Filtrar na
própria tool (ou num `PostToolUse` hook) é a correção mais simples.

**Anti-padrões que aparecem como alternativa errada.**
- "Migre para um modelo com janela maior" como solução para degradação. Ataca o sintoma, encarece
  cada turno e não resolve lost in the middle.
- "Devolva o objeto completo da API para o modelo ter todo o contexto."
- "Coloque todas as regras no meio do prompt, entre os exemplos."

**Como cai na prova.** Cenário 1 (Customer Support: tool de pedido devolvendo JSON gigante, agente
"esquece" o valor do reembolso) e Cenário 4 (Developer Productivity: sessão longa ficando vaga).
Pegadinha típica: a alternativa "janela maior" parece moderna e generosa; a resposta é **reduzir o
que entra** e **posicionar o que importa**.

---

## 2. Resumo perde números: o bloco de CASE FACTS

**Fato-chave.** Quando a conversa é resumida (por você, por `/compact` ou por compaction
server-side), o resumo **preserva a narrativa e perde a precisão**: valores exatos, datas,
percentuais, **IDs, números de pedido**, mensagens de erro literais. "O cliente pediu reembolso de
um pedido recente" não serve para chamar `process_refund(order_id="A-99213", amount=184.90)`.

**Correção.** Um bloco persistente de **CASE FACTS**, mantido **fora** do que é resumido e
reinjetado a cada turno (no system ou no início da mensagem), atualizado pelo código quando uma
tool confirma um fato:

```
<case_facts>
customer_id: C-44817 (verificado às 14:02)
order_id: A-99213
valor_cobrado: 184,90 BRL   valor_correto: 149,90 BRL   diferença: 35,00 BRL
erro_gateway: "ERR_DUPLICATE_CAPTURE 0x2F"
política: reembolso até 200 BRL sem aprovação
</case_facts>
```

**Por quê.** O que é transacional (vai virar argumento de tool, valor de reembolso, ID de
ticket) **não pode ser parafraseado**. O resumo é para contexto; os case facts são para exatidão.

### O que sobrevive ao `/compact` (Claude Code)

| Sobrevive | Pode se perder |
|-----------|----------------|
| `CLAUDE.md` (recarregado), system prompt | Detalhes antigos da conversa |
| Mensagens recentes | Resultados específicos de tools do início |
| Memória / arquivos em disco | Números, citações e mensagens de erro exatas do começo |

Consequência prática: **o que não pode se perder vai para arquivo** (CLAUDE.md, scratchpad,
memória), não para o scrollback. `/compact` aceita instruções de foco
("`/compact preserve os IDs de pedido e os erros literais`"), e o hook `PreCompact` permite salvar
estado antes da compactação.

**Anti-padrões.** Confiar que "o resumo vai manter o importante"; pedir ao modelo para "lembrar
bem dos números"; aumentar a frequência de resumos (perde mais, não menos).

**Como cai na prova.** Cenário 1 (agente de suporte depois de 40 turnos reembolsa o valor errado) e
Cenário 6 (extração em lote cujo resumo intermediário arredonda valores). Pegadinha: a alternativa
"melhore o prompt de sumarização para ser mais detalhado" parece razoável, mas sumarização
continua probabilística; a resposta é **case facts fora do resumo**.

---

## 3. Contexto em codebase grande

**Sinais de degradação** (a prova descreve o sintoma, você precisa reconhecê-lo):
- respostas **vagas e genéricas** ("segue os padrões típicos de repository") em vez de citar a
  classe/arquivo específico que já foi lido;
- **inconsistência** com o que o próprio agente disse antes;
- **esquecer descobertas**: reler arquivos já analisados, propor algo que já foi descartado.

**Mitigações (em ordem de simplicidade).**
1. **Scratchpad / arquivo de rascunho:** o agente grava descobertas (`notes/investigacao.md`:
   "PaymentService chama LegacyGateway via reflection em Startup.cs:212"). Arquivo **sobrevive à
   compressão** e pode ser relido.
2. **Subagents que exploram e devolvem só o resumo** (ex.: o subagent `Explore` do Claude Code).
   O ruído da exploração (dezenas de greps e leituras) fica no contexto **do subagent**; o
   coordenador recebe a conclusão.
3. **`/compact` proativo**, com instrução de foco, **antes** de a sessão degradar, não depois.
4. **Estado salvo em local conhecido + manifesto** do coordenador: em workflows longos
   multiagente, o coordenador mantém um manifesto (`state/manifest.json`: tarefas, status,
   caminhos dos resultados parciais). Se o processo cair, a nova sessão **lê o manifesto e
   retoma**, em vez de recomeçar ou depender do histórico perdido.

```json
{
  "job": "migracao-nhibernate-efcore",
  "tarefas": [
    {"id": "T1", "escopo": "src/Billing/**", "status": "concluida", "resultado": "state/T1.md"},
    {"id": "T2", "escopo": "src/Orders/**",  "status": "em_andamento", "resultado": null},
    {"id": "T3", "escopo": "src/Catalog/**", "status": "pendente", "resultado": null}
  ]
}
```

**Anti-padrões.** Ler o repositório inteiro de antemão "para ter contexto"; deixar o coordenador
fazer a exploração bruta ele mesmo; esperar a sessão degradar para só então compactar; depender do
`--resume` de uma sessão que travou no meio sem estado externo.

**Como cai na prova.** Cenário 4 (exploração de codebase legado) e Cenário 2 (migração grande com
Claude Code). Cenário 3 para o manifesto (coordenador de pesquisa cai após 3 de 8 subtarefas).
Pegadinha: "reinicie a sessão do zero" perde tudo; "aumente o `--max-turns`" não tem relação.

---

## 4. Context editing vs. compaction vs. memory tool vs. case facts

Quatro ferramentas, quatro problemas diferentes. A prova adora colocar as quatro como alternativas.

| Ferramenta | O que faz | Quando usar | Não resolve |
|------------|-----------|-------------|-------------|
| **Context editing** (`clear_tool_uses`, `clear_thinking`) | **Limpa** resultados antigos de tool e/ou blocos de thinking antes do modelo ver | Loop agêntico **verboso**: muitos tool results antigos que já foram usados | Não preserva narrativa; não persiste entre sessões |
| **Compaction** (server-side) | **Resume** o contexto anterior num bloco de compaction quando passa de um limiar | Trabalho **longo** que precisa da **narrativa** (o que foi tentado, por quê) | Perde números exatos (veja seção 2) |
| **Memory tool** | **Arquivos persistentes fora da conversa**; o modelo chama `view/create/str_replace...` e **você implementa** o armazenamento | Achados que precisam valer **entre sessões** | Não reduz o contexto da sessão atual sozinho |
| **Case facts** | Bloco fixo reinjetado, mantido pelo seu código | **Valores que nunca podem ser parafraseados** | Não é mecanismo de economia de tokens |

Nomes de beta e versões de estratégia são **[volátil]**: o que a prova cobra é **qual mecanismo
para qual problema**.

### Duas regras de implementação que viram pegadinha

- **Anexe o `response.content` inteiro** ao histórico, não só o texto. Com compaction, a resposta
  traz um **bloco de compaction**; se o client extrai só `text` e anexa uma string, o estado de
  compaction **se perde em silêncio** (nenhum erro, só a compaction "não funciona"). O mesmo vale
  para blocos `tool_use` e `thinking`.
- **Histórico append-only.** Não edite nem reescreva turnos antigos no client. Em modelos com
  thinking preservado, editar turnos anteriores invalida os blocos de thinking e pode gerar
  **400** no request seguinte (**[volátil]** os detalhes por modelo). Também quebra o cache
  (seção 6). Para dar uma instrução nova, **anexe**; não reescreva o passado.

**Anti-padrões.** Usar memory tool para "liberar contexto" na sessão corrente; usar compaction para
preservar um número de pedido; apagar mensagens antigas do array manualmente "para economizar"
(quebra thinking e cache); anexar `response.content[0].text` como se fosse a resposta toda.

**Como cai na prova.** Cenário 3 (pesquisa longa: compaction ou context editing?), Cenário 1
(memória entre atendimentos do mesmo cliente) e Cenário 4. Pegadinha clássica: "o loop faz 200
chamadas de busca e cada resultado tem 3k tokens; os resultados antigos já foram sintetizados" →
**context editing**, não memory tool nem janela maior.

---

## 5. Limitando e recuperando execuções longas: task budget, `max_tokens`, recusa

**Task budget vs. `max_tokens`.**

| | Task budget | `max_tokens` |
|-|-------------|--------------|
| O modelo sabe? | **Sim**, é visível: o modelo vê a contagem e **se organiza** para caber | **Não**, é invisível |
| O que acontece no limite | Fecha o trabalho de forma ordenada (prioriza, resume, entrega) | **Corta no meio** (`stop_reason: "max_tokens"`) |
| Escopo | O loop/tarefa agêntica | Cada resposta individual |

Task budget é **[volátil, beta]**: o princípio é "teto **visível** → o modelo planeja; teto
**invisível** → truncamento". Para limitar uma tarefa agêntica longa com término gracioso, use o
teto visível. `max_tokens` continua necessário como teto de segurança por resposta.

**Recusa chega com HTTP 200.** Quando o modelo recusa por segurança, o request **não falha**:
volta **200** com `stop_reason: "refusal"`. Código que só checa o status HTTP e lê `content`
trata a recusa como **sucesso vazio** (ou parcial) e segue o pipeline com lixo. Regra: **cheque
`stop_reason` antes de ler `content`**, e trate `refusal`, `max_tokens` e
`model_context_window_exceeded` explicitamente.

```csharp
var resp = await client.Messages.Create(req);
switch (resp.StopReason)
{
    case "refusal":   return Resultado.Recusado(resp.StopDetails);       // não é sucesso
    case "max_tokens": return await ContinuarOuFalhar(resp);             // truncado
    case "model_context_window_exceeded": return Resultado.Truncado(resp);
    case "end_turn":  return Resultado.Ok(resp.Content);
}
```

**Anti-padrões.** Usar `max_tokens` baixo para "fazer o agente ser conciso" numa tarefa longa;
`try/catch` em volta da chamada como única detecção de falha; limite fixo de iterações como
mecanismo **principal** de parada.

**Como cai na prova.** Cenário 5 (pipeline de CI que "às vezes devolve review vazio" → recusa
tratada como sucesso) e Cenário 6 (extração com saída truncada). Pegadinha: "aumente o timeout" ou
"adicione retry no 5xx" não pegam um 200.

---

## 6. Prompt caching: a mecânica

**Fato-chave.** O cache casa **prefixo exato**, renderizado na ordem **`tools` → `system` →
`messages`**. Qualquer byte diferente no prefixo **invalida tudo o que vem depois dele**.

- Você marca **breakpoints** com `cache_control: {"type": "ephemeral"}` no último bloco de um
  trecho estável. **Até 4 breakpoints** por request.
- **Estável primeiro, volátil depois.** Definições de tools, instruções fixas, documentos de
  referência e few-shot ficam **antes** do último breakpoint; timestamp, ID do usuário, dados da
  sessão e a pergunta em si ficam **depois**.
- **Mínimo cacheável:** abaixo de um tamanho mínimo de prefixo (depende do modelo, **[volátil]**),
  o cache **simplesmente não acontece, em silêncio**: nenhum erro, só
  `cache_creation_input_tokens: 0`.
- TTL padrão de **5 minutos** (renovado a cada leitura); opção de **1 hora**.

### Request bem montado

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 2048,
  "tools": [
    {"name": "get_order", "description": "...", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
    {"name": "process_refund", "description": "...", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "amount": {"type": "number"}}, "required": ["order_id", "amount"]},
     "cache_control": {"type": "ephemeral"}}
  ],
  "system": [
    {"type": "text", "text": "Você é o agente de suporte da Loja X. Políticas de reembolso: ... (8 mil tokens fixos)",
     "cache_control": {"type": "ephemeral"}}
  ],
  "messages": [
    {"role": "user", "content": [
      {"type": "text", "text": "Contexto da sessão: cliente C-44817, agora 2026-10-11T14:02Z"},
      {"type": "text", "text": "Fui cobrado duas vezes no pedido A-99213."}
    ]}
  ]
}
```

Breakpoint 1 no fim das `tools` (estáveis e em **ordem determinística**), breakpoint 2 no fim do
`system` estável. Tudo que muda por request (cliente, horário, pergunta) está **depois**.

### Contra-exemplo: timestamp no system

```json
{
  "system": [
    {"type": "text", "text": "Data/hora atual: 2026-10-11T14:02:37Z. Você é o agente de suporte da Loja X. Políticas: ... (8 mil tokens)",
     "cache_control": {"type": "ephemeral"}}
  ]
}
```

O timestamp muda a cada request → o prefixo nunca é igual → **todo request paga escrita de cache
(mais cara que input normal) e nunca lê**. Pior que não ter cache. Correção: mova a data para a
mensagem do usuário (ou para depois do último breakpoint), ou arredonde para o dia se a granularidade
bastar.

**Anti-padrões.** Pôr o breakpoint no último bloco da mensagem do usuário que muda sempre;
montar a lista de tools dinamicamente por request; serializar JSON com ordem de chaves não
determinística; colocar ID de sessão no topo do system "para rastreabilidade".

**Como cai na prova.** Cenário 1 (agente de suporte com system enorme e custo alto) e Cenário 5
(CI que roda o mesmo prompt de review em centenas de PRs). Pegadinha: "o cache está habilitado mas
a conta não caiu" → procure o **invalidador silencioso** no prefixo.

---

## 7. Prompt caching: custos, verificação e invalidadores silenciosos

**Custos (ordem de grandeza; multiplicadores exatos [volátil]).**
- **Escrita** no cache custa **prêmio**: ~**1,25×** o input base (TTL 5 min) ou ~**2×** (TTL 1 h).
- **Leitura** custa **uma fração pequena** do input base (~0,1× ou menos).
- Logo, cache compensa quando o mesmo prefixo é **reutilizado**; um prefixo que nunca se repete
  só paga o prêmio.

**Verificação.** Leia `usage`:
- `cache_creation_input_tokens`: quanto foi **escrito** neste request.
- `cache_read_input_tokens`: quanto foi **lido** do cache.
- Se `cache_read_input_tokens` é **zero em requests repetidos**, algo está **invalidando**. Se
  `cache_creation_input_tokens` também é zero, o prefixo provavelmente está **abaixo do mínimo**.

**Invalidadores silenciosos (decore a lista).**
1. **Timestamp** (ou qualquer valor que muda) no system / antes do breakpoint.
2. **Ordem não determinística de chaves JSON** (ex.: serializar um `Dictionary` sem ordenação).
3. **Lista de tools que varia por request** (adicionar/remover/reordenar tools). Tool search
   (`defer_loading`) existe em parte para **não** mexer no array de tools.
4. **ID de sessão/usuário no prefixo.**
5. **Mudar thinking/effort entre requests** (muda o que é renderizado).
6. **Editar turnos antigos** do histórico (veja append-only, seção 4).

**Anti-padrões.** "Aumente o TTL para 1 h" quando o problema é invalidação (TTL não ajuda se o
prefixo muda); "adicione mais breakpoints" (breakpoint não conserta prefixo que muda); "desligue o
cache, não está funcionando".

**Como cai na prova.** Qualquer cenário com "custo alto" ou "latência alta em system prompt grande".
Pegadinha: a alternativa que **aumenta TTL** ou **adiciona breakpoints** soa técnica, mas a causa é
um byte variável no prefixo.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| O agente "esquece" um valor/ID exato depois de muitos turnos | Bloco de **case facts** fora do resumo |
| Tool devolve 40 campos e o agente usa 5 | **Corte a saída** da tool (na tool ou `PostToolUse`) |
| Instrução crítica está no meio de um prompt longo e é ignorada | Mova para o **começo** (e/ou fim), com cabeçalhos |
| Loop com centenas de tool results antigos já consumidos | **Context editing** (`clear_tool_uses`) |
| Trabalho longo que precisa lembrar a **narrativa** do que foi feito | **Compaction** (e anexe `response.content` inteiro) |
| Achado precisa valer **na próxima sessão** | **Memory tool** / arquivo persistente |
| Sessão no Claude Code ficando vaga e genérica | `/compact` **proativo** com foco + **scratchpad** |
| Exploração ruidosa de codebase enchendo o coordenador | **Subagent** que explora e devolve **só o resumo** |
| Workflow multiagente longo pode cair no meio | **Manifesto** + estado em local conhecido; retome dele |
| Tarefa agêntica longa deve terminar de forma ordenada dentro de um teto | **Task budget** (visível), não só `max_tokens` |
| Pipeline trata algumas respostas como "vazias" sem erro | Cheque **`stop_reason`** (pode ser `refusal` com HTTP 200) |
| Cache habilitado, `cache_read_input_tokens` sempre 0 | Procure **invalidador silencioso** no prefixo |
| Cache habilitado, `cache_creation_input_tokens` também 0 | Prefixo **abaixo do mínimo** cacheável |
| Precisa dar data/hora ao modelo e usar cache | Data **depois** do último breakpoint (mensagem do usuário) |

## Glossário

- **Janela de contexto:** total de tokens que o modelo considera num request (system + tools + mensagens + resultados).
- **Lost in the middle:** perda de atenção a informações no meio de contextos longos.
- **Case facts:** bloco persistente de fatos exatos (IDs, valores, datas) que nunca é resumido.
- **`/compact`:** comando do Claude Code que resume a conversa; aceita instruções de foco.
- **`PreCompact`:** hook disparado antes da compactação (salvar estado).
- **Scratchpad:** arquivo de rascunho onde o agente grava descobertas que sobrevivem à compressão.
- **Manifesto:** arquivo de estado do coordenador (tarefas, status, caminhos de resultados) para retomar após crash.
- **Context editing:** limpeza server-side de tool results/thinking antigos.
- **Compaction:** resumo server-side do contexto anterior num bloco de compaction.
- **Memory tool:** tool client-side de arquivos persistentes entre sessões (você implementa o storage).
- **Append-only:** só anexar ao histórico; nunca reescrever turnos antigos.
- **Task budget:** teto de tokens visível ao modelo para uma tarefa agêntica.
- **`max_tokens`:** teto invisível por resposta; trunca com `stop_reason: "max_tokens"`.
- **`refusal`:** `stop_reason` de recusa, entregue com HTTP 200.
- **Breakpoint (`cache_control`):** marca o fim de um prefixo cacheável; até 4 por request.
- **`cache_read_input_tokens` / `cache_creation_input_tokens`:** tokens lidos / escritos no cache.
- **Invalidador silencioso:** byte variável no prefixo que impede o cache sem gerar erro.

## Cola de véspera

- Cada turno **reenvia e paga** o histórico todo. Janela maior **não** é solução para degradação.
- **Lost in the middle:** crítico no **começo**, com cabeçalhos. **Corte a saída das tools.**
- Resumo **perde números/IDs/erros literais** → **CASE FACTS** fora do resumo.
- `/compact`: sobrevive CLAUDE.md, system, mensagens recentes, memória. Perde detalhe antigo e números do começo.
- Codebase grande: sintoma = respostas **vagas/genéricas**, inconsistência, esquecer descobertas.
  Cura = **scratchpad**, **subagent que devolve resumo**, **`/compact` proativo**, **manifesto** para crash.
- **Context editing** = limpa tool results velhos (loop verboso). **Compaction** = resume narrativa
  (trabalho longo). **Memory tool** = entre sessões. **Case facts** = números intocáveis.
- Compaction: **anexe `response.content` inteiro**, senão perde o estado em silêncio. Histórico **append-only**.
- **Task budget** visível (modelo se organiza) vs. **`max_tokens`** invisível (corta no meio).
- **Recusa = HTTP 200** com `stop_reason: "refusal"` → cheque `stop_reason` antes de `content`.
- Cache: **prefixo exato**, ordem **tools → system → messages**, **estável primeiro**, até **4 breakpoints**,
  abaixo do mínimo **não cacheia em silêncio**. Escrita ~1,25× (5 min) / 2× (1 h); leitura fração pequena.
- `cache_read_input_tokens = 0` repetido → **invalidador**: timestamp, chaves JSON fora de ordem,
  tools variando, ID no prefixo, thinking/effort mudando, histórico editado.

## Perguntas de checagem

1. **Por que "trocar para um modelo com janela de 1M" não resolve um agente que esquece o número do
   pedido após 50 turnos?**
   Porque o problema não é falta de espaço: é atenção (lost in the middle) e/ou o número ter sido
   perdido num resumo. A correção é um bloco de case facts reinjetado e cortar o ruído do contexto.
2. **Um loop de pesquisa faz 150 buscas; os resultados antigos já foram sintetizados. Context
   editing, compaction ou memory tool?**
   Context editing (`clear_tool_uses`): limpa os resultados velhos já consumidos. Compaction seria
   para preservar narrativa; memory tool, para persistir entre sessões.
3. **O cliente implementou compaction mas o histórico continua crescendo até estourar. Causa
   provável?**
   O código anexa só o texto da resposta, descartando o bloco de compaction. É preciso anexar o
   `response.content` inteiro.
4. **Um pipeline de CI às vezes registra "review vazio" e marca o job como verde. O que checar?**
   `stop_reason`: provavelmente `refusal` (HTTP 200) ou `max_tokens`, tratados como sucesso.
5. **O cache está ligado, o system tem 10 mil tokens fixos, mas `cache_read_input_tokens` é sempre
   0. Primeiros suspeitos?**
   Algo variável no prefixo: timestamp ou ID no system, tools montadas dinamicamente, chaves JSON em
   ordem não determinística, thinking/effort mudando. Aumentar TTL ou breakpoints não resolve.
