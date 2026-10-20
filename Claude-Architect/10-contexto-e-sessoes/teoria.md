# Módulo 10 — Gestão de contexto, codebase grande e sessões

> **Task statements:** **5.1** (preservar informação crítica em interações longas), **5.4** (contexto
> na exploração de codebase grande) e **1.7** (estado de sessão, retomada e fork).
> **Onde cai:** 5.1 nos Cenários **1** (suporte), **3** (pesquisa multiagente) e **6** (extração);
> 5.4 e 1.7 nos Cenários **4** (developer productivity) e **2** (Claude Code); 1.7 também no **3**.

Ideia central: **o contexto é finito e o modelo confia no que está nele**. Você decide o que entra
(aparado), o que não pode ser parafraseado (case facts), onde fica (começo, com cabeçalhos), o que sai
da conversa (scratchpad, manifest) e se a sessão antiga ainda vale (retomar) ou envelheceu (recomeçar).

---

## 1. Histórico completo e o custo do que acumula

**Fatos de prova.**
- **5.1-K4:** a Messages API não guarda estado. Para a conversa ter coerência, **cada request leva o
  histórico completo** (mensagens do usuário, respostas, `tool_use` e `tool_result`). Se o código
  manda só a última mensagem, o modelo "esquece" o que o cliente disse dois turnos atrás.
- **5.1-K3:** resultados de tool **acumulam** no histórico e consomem tokens **desproporcionalmente à
  relevância**: uma consulta de pedido com 40+ campos, quando só 5 importam, repetida em 6 consultas.
- **5.1-S3:** **apare a saída para os campos relevantes antes de ela entrar no histórico** (ex.: só os
  campos que importam para uma devolução). Faça isso na própria tool, no código do loop ou num hook
  `PostToolUse` do Agent SDK (Módulo 06).

```json
// Request do turno 4 (o seu código monta e envia)
{
  "model": "claude-opus-5-5",
  "max_tokens": 1024,
  "system": "Você é o agente de suporte da loja...",
  "messages": [                                              // ← AQUI: histórico COMPLETO a cada request
    { "role": "user", "content": "Quero devolver o pedido A-1042." },
    { "role": "assistant", "content": [
      { "type": "tool_use", "id": "toolu_01", "name": "lookup_order", "input": { "order_id": "A-1042" } } ] },
    { "role": "user", "content": [
      { "type": "tool_result", "tool_use_id": "toolu_01",
        "content": "{\"status\":\"delivered\",\"total\":389.90,\"delivered_at\":\"2026-10-02\",\"return_until\":\"2026-11-01\"}" } ] }, // ← AQUI: só os campos relevantes, não 43
    { "role": "assistant", "content": "Pode ser devolvido até 01/11." },
    { "role": "user", "content": "Prefiro estorno no cartão." }
  ]
}
```

```csharp
// No loop agêntico, ANTES de anexar o tool_result ao histórico
var o = await _orders.LookupAsync(input.OrderId);                       // 43 campos
var relevante = new { o.Status, o.Total, o.DeliveredAt, o.ReturnUntil }; // só o que a devolução usa
messages.Add(Msg.ToolResult(toolUseId, JsonSerializer.Serialize(relevante)));
```

**Por quê.** Tudo no histórico é reenviado e disputa atenção a cada turno. Campos irrelevantes
enchem a janela mais cedo e antecipam resumos (que perdem precisão, seção 2).

**Anti-padrões que aparecem como alternativa errada.**
- "Instrua o agente no prompt a ignorar os campos irrelevantes" (os tokens continuam no contexto).
- "Use um modelo com janela maior" (adia o problema; não muda o que entra).
- "Mande só a última mensagem para economizar" (perde coerência; viola 5.1-K4).
- "Resuma cada resultado com um segundo modelo" (custo e risco extras, quando basta selecionar campos).

**Como cai na prova.** Cenário 1: `lookup_order` com dezenas de campos e valores misturados em
conversas longas; Cenário 3: subagent acumulando registros enormes → **aparar antes de acumular**.

> **Na doc atual [volátil]:** prompt caching existe (reaproveita prefixo repetido, reduz custo e
> latência), e a API tem outros recursos de gestão de contexto. Fora dos objetivos do guia: não decidem questão.

---

## 2. Resumo progressivo perde números: case facts e camada por issue

**Fatos de prova.**
- **5.1-K1:** o resumo progressivo condensa **valores numéricos, percentuais, datas e expectativas
  declaradas pelo cliente** em frases vagas. "Cliente contesta cobranças de uma fatura recente e quer
  resolver logo" no lugar de "INV-30412, US$ 1.840 (12% acima do contrato), crédito até 31/03".
- **5.1-S1:** extraia os **fatos transacionais** (valores, datas, nº de pedido, status) para um bloco
  persistente de **case facts**, **incluído em cada prompt** e **fora do histórico resumido**. Quem
  atualiza o bloco é o **código**, a partir do resultado das tools.
- **5.1-S2:** em sessões com **várias demandas**, guarde os dados estruturados **de cada issue** (order
  ID, valor, status) numa **camada de contexto separada**, um registro por issue. Uma lista solta
  ("valor: 420; pedido: A-1; valor: 1.150...") deixa o modelo misturar o valor de uma demanda com o
  pedido de outra.

```json
// Request do turno 41: histórico antigo resumido + case facts fora do resumo
{
  "model": "claude-opus-5-5",
  "max_tokens": 1024,
  "system": "Você é o agente de suporte...\n\n<case_facts>\ncustomer_id: C-44817 (verificado)\n[ISSUE-1] order: A-99213 | tipo: cobrança duplicada | valor: 35.00 | status: refund_pending\n[ISSUE-2] order: A-99877 | tipo: item faltando | valor: 59.90 | status: investigating\nexpectativa do cliente: estorno no cartão até 2026-10-25\n</case_facts>", // ← AQUI: reconstruído pelo código a cada request
  "messages": [
    { "role": "user", "content": "[Resumo dos turnos 1–30] Cliente relatou dois problemas..." }, // ← AQUI: o resumo pode ser vago; os números não dependem dele
    { "role": "assistant", "content": "Certo, seguimos com os dois casos." },
    { "role": "user", "content": "E o estorno do primeiro, já saiu?" }
  ]
}
```

**Por quê.** Resumo é texto gerado: preserva a narrativa e perde precisão. O que vai virar argumento
de tool (valor do estorno, ID do pedido) ou compromisso com o cliente (prazo) **não pode passar pelo
resumidor**.

**Anti-padrões que aparecem como alternativa errada.**
- "Reescreva o prompt de resumo pedindo para preservar todos os detalhes" (continua probabilístico).
- "Resuma com mais frequência" (mais passadas com perda, não menos).
- "Mande o modelo lembrar bem dos números" / "janela maior para resumir mais tarde".
- Um bloco de fatos **sem estrutura por issue** em sessão com várias demandas.

**Como cai na prova.** Cenário 1: após N turnos, reembolso com valor arredondado ou pedido errado, ou
handoff com "algumas cobranças" no lugar dos valores. Cenário 6: resumo de lote arredonda valores.
Resposta: **case facts fora do resumo**; várias demandas → **um registro por issue**.

---

## 3. Lost in the middle: como montar uma entrada agregada

**Fatos de prova.**
- **5.1-K2:** modelos processam bem o **começo** e o **fim** de entradas longas e podem **omitir
  achados do meio**. A informação **está** no input (os logs mostram), mas some da resposta.
- **5.1-S4:** coloque um **resumo dos achados-chave no início** da entrada agregada e organize os
  resultados detalhados em **seções com cabeçalhos explícitos** (uma por fonte/subagent).

```json
// Request do agente de síntese (montado pelo coordenador)
{
  "model": "claude-opus-5-5",
  "max_tokens": 4096,
  "system": "Você é o agente de síntese. Todo achado listado em KEY FINDINGS deve aparecer no relatório.",
  "messages": [
    { "role": "user",
      "content": "## KEY FINDINGS\n- [S1 Mercado] churn de 7,2%...\n- [S4 Regulatório] regra nova em 2027...\n\n## S1 — Mercado\n...\n\n## S4 — Regulatório\n..." } // ← AQUI: resumo no início + cabeçalho por fonte
  ]
}
```

**Por quê.** Concatenar saídas na ordem em que terminaram deixa a posição ao acaso. Com o resumo no
topo, todo achado-chave fica numa região bem processada; os cabeçalhos servem de mapa para o detalhe.

**Anti-padrões que aparecem como alternativa errada.**
- Embaralhar a ordem a cada execução (espalha a falha em vez de resolvê-la).
- Modelo com janela maior (atenção não é espaço).
- "Revise seu rascunho contra o input inteiro" (a mesma atenção diluída revisando).
- Uma chamada de síntese por subagent (perde o cruzamento entre fontes).

**Como cai na prova.** Cenário 3: achados do subagent cuja saída cai no meio somem do relatório.
Cenário 1: uma cláusula de contrato no meio de 14 documentos de política é ignorada. Pista: "o dado
estava no input" + "o que fica no meio é que falha".

---

## 4. Contratos entre agentes: metadados e dados estruturados

**Fatos de prova.**
- **5.1-S5:** exija que os subagents incluam **metadados** na saída estruturada: **datas**
  (publicação/coleta), **local da fonte** (documento, página, URL) e **contexto metodológico** (bula,
  estudo piloto, pesquisa amostral). Sem isso, o downstream lê diferença temporal como contradição e
  mistura números de naturezas diferentes. (O Módulo 11 aprofunda proveniência, TS 5.6.)
- **5.1-S6:** quando o agente **downstream tem orçamento de contexto limitado**, mude os agentes
  **upstream** para devolver **dados estruturados** (fatos-chave, citações, score de relevância) em
  vez de conteúdo verboso e **cadeias de raciocínio**.

```json
// Resposta final do subagent de análise → volta ao coordenador como tool_result da chamada Task
{
  "document": "Boletim do fornecedor 2026-03",
  "key_facts": [                                              // ← AQUI: fatos, não prosa nem raciocínio
    {
      "fact": "Dose máxima diária revisada",
      "value": "40 mg",
      "citation": { "doc": "boletim-2026-03.pdf", "page": 4, "excerpt": "máximo de 40 mg/dia" },
      "published": "2026-03-02",                                 // ← AQUI: data
      "method": "bula atualizada",                               // ← AQUI: contexto metodológico
      "relevance": 0.92
    }
  ]
}
```

**Por quê.** O downstream só sabe o que recebe (Módulo 07). Prosa e raciocínio do upstream gastam o
orçamento dele com texto que não decide nada e escondem a data e a fonte de cada número.

**Anti-padrões que aparecem como alternativa errada.**
- "Mantenha a saída mínima e deixe o downstream reabrir as fontes quando precisar."
- "Escolha o valor mais recente quando duas fontes divergirem" (seleção arbitrária; anote o conflito).
- "Dê ao downstream um modelo com janela maior" (o problema está no formato do upstream).
- "Melhore o prompt do downstream" (ataca o sintoma; quem gasta o orçamento é o upstream).

**Como cai na prova.** Cenário 6: um passo downstream com orçamento curto começa a falhar quando o
volume cresce → a **root cause está no formato do upstream**. Cenário 3/6: a síntese trata valores de
datas diferentes como contradição → faltou **data/metodologia** na saída do subagent.

---

## 5. Codebase grande: degradação, scratchpad e `/compact`

**Fatos de prova.**
- **5.4-K1 (sintoma):** em sessões longas, o modelo passa a dar **respostas inconsistentes** e a
  falar de **"padrões típicos"** em vez das **classes específicas** que ele mesmo descobriu antes
  ("segue um adapter típico" no lugar de `ModbusFrameAssembler`).
- **5.4-K2 / S2:** **scratchpad files**: o agente mantém um arquivo com os **achados-chave** (classes,
  caminhos, comportamentos confirmados, hipóteses descartadas) e o **consulta** nas perguntas
  seguintes. O arquivo sobrevive a fronteiras de contexto (compactação, sessão nova, handoff para
  subagent).
- **5.4-S5:** **`/compact`** reduz o uso de contexto em explorações longas quando a janela enche de
  saída verbosa de descoberta. Ele **substitui o histórico por um resumo** da conversa (aceita uma
  instrução de foco: `/compact foque nas classes de pagamento confirmadas`).

```markdown
<!-- notes/investigacao-gateway.md: o scratchpad, em disco no repositório -->
Confirmado: frames montados em src/Gateway/ModbusFrameAssembler.cs (Build, l. 88); retry 3x/500 ms
Descartado: "timeout no socket" (respostas < 40 ms nos logs)
Aberto: quem consome AlarmSink?
```

**Erro comum:** `/compact` **não** "preserva as mensagens recentes". A conversa inteira vira um
resumo; o que volta depois vem de fora do histórico (system prompt, `CLAUDE.md` da raiz, arquivos).

> **Na doc atual [volátil]:** o Claude Code também relê até cinco arquivos recentes e reinjeta skills
> invocadas. Na prova: "/compact troca o histórico verboso por um resumo; o crítico fica em arquivo".

**Por quê.** Os achados antigos competem com centenas de linhas de grep e leituras. Tirá-los da
conversa (scratchpad) e encolher o ruído (`/compact`, subagents) atacam as duas pontas.

**Anti-padrões que aparecem como alternativa errada.**
- "Instrua o agente a sempre citar classes específicas" (prompt não devolve o que se diluiu).
- "Releia todos os arquivos antes de cada resposta" (enche ainda mais o contexto).
- "Recomece a sessão a cada 45 min" sem salvar nada (perde os achados).
- `/clear` ou copiar as últimas mensagens para outra sessão (descarta conclusões antigas).
- Logar **toda** saída de tool no scratchpad (vira outro dump verboso).

**Como cai na prova.** Cenário 4: "após 90 min, respostas genéricas e contraditórias" → **scratchpad**
(e/ou subagents, seção 6). Cenário 2: sessão de exploração lenta e cheia de grep → **`/compact`**.
Em "escolha DUAS" de sintomas, separe degradação (padrão típico, contradição) de outros problemas.

---

## 6. Subagents de exploração, resumo entre fases e manifest

**Fatos de prova.**
- **5.4-K3 / S1:** delegue **perguntas específicas** a subagents ("find all test files", "trace refund
  flow dependencies"). A saída verbosa da exploração fica no contexto **do subagent**; o agente
  principal recebe a conclusão e **preserva a coordenação de alto nível**. No Claude Code, o
  **Explore subagent** faz exatamente isso (Módulo 08).
- **5.4-S3:** **resuma os achados de uma fase antes de lançar os subagents da fase seguinte** e
  **injete o resumo no contexto inicial** deles. Subagents não herdam nada: sem o resumo, eles
  redescobrem a estrutura (mais lentos) e podem contradizer a fase anterior.
- **5.4-K4 / S4:** **recuperação de crash**: cada agente **exporta seu estado para um local conhecido**;
  o coordenador **carrega um manifest ao retomar** e **injeta** o estado relevante **nos prompts** dos
  agentes.

```json
// state/manifest.json: em disco; cada agente grava seu estado ao concluir um passo
{
  "phase_summary": "Fase 1: 12 módulos mapeados; acesso a dados em src/Data/Legacy/*",
  "tasks": [
    { "id": "M01", "status": "done",        "notes": "ajuste manual em RouteRepo.cs" },
    { "id": "M07", "status": "in_progress", "notes": "parou em TripMapper.cs" },
    { "id": "M08", "status": "pending",     "notes": null }
  ]
}
```

```json
// Resposta do coordenador ao retomar: o manifest vira contexto no prompt do subagent
{
  "stop_reason": "tool_use",
  "content": [
    { "type": "tool_use", "id": "toolu_07", "name": "Task",
      "input": { "description": "Retomar M07",
                 "prompt": "Resumo da fase 1: ...\nEstado (manifest): M07 in_progress, parou em TripMapper.cs; M01–M06 done, não refaça.\nTarefa: concluir M07 e gravar state/M07.json." } } // ← AQUI: estado injetado
  ]
}
```

**Por quê.** O histórico de um processo que caiu não registra com confiança o que terminou, e
subagents só sabem o que está no prompt; estado em disco é verificável e reinjetável.

**Anti-padrões que aparecem como alternativa errada.**
- Coordenador fazendo a exploração bruta ele mesmo (enche o contexto que coordena).
- Ler o repositório inteiro de antemão "para ter contexto".
- Passar ao subagent da fase 2 só a string da tarefa (ou as saídas brutas inteiras da fase 1).
- Após crash: `--resume` da sessão que caiu e perguntar "o que você já tinha feito?"; ou instruir o
  coordenador a "conferir o git log" (heurística, não estado).

**Como cai na prova.** Cenário 4: fase 2 refaz a descoberta da fase 1 → **resumo injetado**.
Cenário 2: workflow com subagents cai e refaz o que já tinha terminado → **manifest + injeção**.
"Deixe toda a descoberta na sessão principal" → rejeite; **delegue a subagents**.

---

## 7. Sessões: retomar, fork e recomeçar com resumo

**Fatos de prova.**
- **1.7-K1 / S1:** **`--resume <session-name>`** continua **uma conversa específica** pelo nome,
  com o contexto anterior: várias investigações nomeadas ao longo de dias. `--continue` abre só **a
  mais recente** do diretório (pega a errada quando você alterna tarefas).
- **1.7-K2 / S2:** **`fork_session`** cria **ramos independentes** a partir de uma **base de análise
  comum**: comparar duas estratégias de teste ou de refatoração sem refazer a análise e sem que um
  ramo contamine o outro.
- **1.7-K3 / S4:** ao retomar depois de mudanças no código, **diga à sessão quais arquivos mudaram**
  para uma **reanálise direcionada**, em vez de exigir reexploração completa.
- **1.7-K4 / S3:** se os resultados de tool da sessão **envelheceram** (muita coisa mudou), **começar
  uma sessão nova com um resumo estruturado** é mais confiável do que retomar: o modelo trata os
  resultados antigos do histórico como verdade. Regra: **contexto ainda majoritariamente válido →
  retomar (e informar as mudanças)**; **resultados obsoletos → recomeçar com resumo injetado**.

```bash
claude -n fare-capping                 # nomeia a sessão ao abrir (ou /rename dentro dela)
claude --resume fare-capping           # dias depois: volta exatamente a essa conversa
claude --resume fare-capping --fork-session   # copia a conversa para um ramo novo
```

```python
# Agent SDK em Python (o nome do campo é exatamente fork_session; em TypeScript, forkSession)
base = "5b3f2c1a-..."   # session_id da análise comum (vem do ResultMessage)
for estrategia in ["A: testes de contrato por serviço", "B: testes end-to-end por fluxo"]:
    async for m in query(prompt=f"Estratégia {estrategia}",
                         options=ClaudeAgentOptions(resume=base, fork_session=True)):  # ← AQUI
        ...
```

Mensagem de retomada direcionada (1.7-S4):

```text
Desde a última sessão: src/Parsing/FeedParser.cs e src/Parsing/StopTimeMapper.cs foram reescritos
(PR #412); o restante não mudou. Releia só esses dois e atualize as conclusões que dependem deles.
```

> **Na doc atual [volátil]:** o fork ramifica **a conversa, não o filesystem**: edições feitas num ramo
> são reais no diretório. Nomear com `-n`/`/rename` e o `/branch` são detalhes da CLI atual; o termo
> de prova é `--resume <session-name>` e `fork_session`.

**Por quê.** O histórico é tratado como verdade: a leitura de um arquivo já reescrito gera
conclusões sobre código que não existe mais. O resumo leva só o que vale; o fork leva a base comum
sem contaminar o outro ramo.

**Anti-padrões que aparecem como alternativa errada.**
- Retomar após grande refatoração "porque o agente vai notar ao reler" (ele confia no histórico).
- Reexplorar tudo do zero quando só 2 arquivos mudaram (informe as mudanças).
- Duas abordagens **na mesma sessão** ("esqueça a A") em vez de `fork_session`; ou sessões/subagents
  **novos** sem a análise comum (perdem a base).
- Colar a transcrição inteira numa sessão nova, ou forkar uma sessão obsoleta (herdam o velho).

**Como cai na prova.** Cenário 2: dev alterna investigações e `--continue` abre a errada → **sessão
nomeada + `--resume <nome>`**. Cenário 4: comparar duas refatorações após 90 min de análise →
**`fork_session`**. Cenários 3/4: fontes ou arquivos mudaram muito desde ontem → **sessão nova com
resumo estruturado**; mudaram poucos → **retomar e informar os arquivos alterados**.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| Bot esquece o que o cliente disse dois turnos antes | **Histórico completo** em cada request |
| Tool devolve 40+ campos e o agente usa 5 | **Apare** os campos antes de acumular |
| Após resumo, valor/data/pedido viram vagos | **Case facts** fora do resumo; várias demandas → **registro por issue** |
| Achado no meio de uma entrada longa some | **Resumo no início** + **cabeçalhos** por seção |
| Downstream com orçamento curto perde documentos | Upstream devolve **fatos-chave, citações, relevância** |
| Síntese lê datas diferentes como contradição | Subagents incluem **data, fonte, metodologia** |
| Sessão longa: "padrões típicos", contradições | **Scratchpad** consultado + subagents |
| Contexto cheio de saída de descoberta | **`/compact`** |
| Pergunta ruidosa ("find all test files") | **Subagent** (ex.: Explore); o principal coordena |
| Fase 2 refaz o trabalho da fase 1 | **Resumo da fase 1** injetado nos subagents |
| Workflow multiagente pode cair no meio | Estado exportado + **manifest** carregado e injetado |
| Continuar uma investigação específica | **`--resume <session-name>`** |
| Comparar duas abordagens da mesma análise | **`fork_session`** |
| Poucos arquivos mudaram / resultados obsoletos | Retome **informando os arquivos** / **sessão nova + resumo** |

## Glossário

- **Resumo progressivo:** condensar turnos antigos; arrisca perder números, datas e expectativas.
- **Case facts:** bloco de fatos transacionais em cada prompt, fora do resumo. **Camada por issue:** um registro por demanda.
- **Trimming de tool output:** manter só os campos relevantes antes de o resultado acumular.
- **Lost in the middle:** omissão do que está no meio de entradas longas.
- **Scratchpad file:** arquivo de achados-chave consultado nas perguntas seguintes.
- **`/compact`:** substitui o histórico do Claude Code por um resumo; aceita instrução de foco.
- **Manifest:** estado (tarefas, status) que o coordenador carrega ao retomar e injeta nos prompts.
- **`--resume <session-name>`:** retoma uma sessão nomeada. **`fork_session`:** ramo novo com cópia do histórico.

## Cola de véspera

- Cada request leva o **histórico completo**; mandar só a última mensagem quebra a coerência.
- Tool result acumula: **apare para os campos relevantes antes** de anexar (tool, loop ou `PostToolUse`).
- Resumo perde **números, percentuais, datas e expectativas do cliente** → **case facts** fora do resumo,
  em cada prompt; várias demandas → **um registro por issue** numa camada separada.
- **Lost in the middle:** achados-chave **no início**, detalhes sob **cabeçalhos explícitos**.
- Upstream → downstream com orçamento curto: **fatos-chave, citações, relevância**, sem prosa nem raciocínio.
  Subagents incluem **data, local da fonte e metodologia**.
- Degradação = "**padrões típicos**" + **contradições**. Cura: **scratchpad** consultado, **subagents**
  para perguntas específicas, **`/compact`** quando a descoberta enche o contexto.
- `/compact` **substitui o histórico por um resumo** (não guarda "as mensagens recentes").
- Entre fases: **resuma e injete** no prompt dos novos subagents (eles não herdam nada).
- Crash: **estado em local conhecido + manifest** carregado pelo coordenador e **injetado nos prompts**.
- `--resume <session-name>` para a investigação certa; `--continue` = só a mais recente.
- `fork_session` = ramos independentes a partir da mesma análise (duas estratégias de teste/refatoração).
- Mudou pouco → **retomar e dizer quais arquivos mudaram**. Mudou muito → **sessão nova com resumo estruturado**.
- Janela maior, "lembre bem", "ignore campos" e "resuma mais vezes" são distratores típicos.

## Perguntas de checagem

1. **Um chatbot responde bem ao primeiro turno, mas no terceiro não sabe qual pedido o cliente citou.
   O código envia `messages` com um único item. Qual é a correção?**
   Enviar o histórico completo em cada request (5.1-K4).
2. **Depois de 30 turnos, o handoff diz "cliente quer reembolso de uma fatura recente". O que faltou?**
   Case facts (fatura, valor, %, prazo, expectativa) fora do resumo, incluídos em cada prompt (5.1-K1/S1).
3. **Sete saídas de subagents concatenadas; as do meio somem do relatório. O que mudar?**
   Resumo dos achados-chave no início e uma seção com cabeçalho por subagent (5.1-S4).
4. **Após 2 horas, o agente diz "segue o padrão repository típico". Sintoma e duas mitigações?**
   Degradação de contexto (5.4-K1); scratchpad consultado, subagents ou `/compact` (5.4-S1/S2/S5).
5. **A migração com subagents caiu no módulo 7 e recomeçou do 1. Que desenho evita isso?**
   Estado exportado por agente; o coordenador carrega o manifest e o injeta nos prompts (5.4-S4).
6. **Ontem a sessão analisou 60 arquivos; hoje 41 foram reescritos. Retomar ou recomeçar? E se fossem 2?**
   41: sessão nova com resumo estruturado (1.7-K4/S3). 2: retomar e informar os 2 arquivos (1.7-S4).
   Para comparar duas refatorações a partir da mesma análise: `fork_session` (1.7-K2/S2).
