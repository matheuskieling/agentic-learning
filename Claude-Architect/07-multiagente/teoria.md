# Módulo 07 — Orquestração multiagente, decomposição, review multi-pass e sessões

> **Domínio D1 — Arquitetura agêntica & orquestração (27%).** Task statements: **1.2**
> (orquestração multiagente), **1.3** (spawn de subagents e passagem de contexto), **1.6**
> (estratégias de decomposição), **1.7** (gestão de sessão) e **4.6** (review multi-pass, do D4).
> Pré-requisito: Módulo 06 (o loop agêntico). Um sistema multiagente é **um loop que chama outros loops**.

O cenário-estrela aqui é o **Multi-Agent Research System** (cenário 3), mas o conteúdo também cai em
**Claude Code for CI** (cenário 5: review multi-pass, sessão independente), **Code Generation**
(cenário 2: subagents, `--resume`) e **Developer Productivity** (cenário 4: subagent Explore, sessões).

---

## 1. O vocabulário base: "Building Effective Agents"

A prova pressupõe o vocabulário do artigo **"Building Effective Agents"** da Anthropic. Ele separa
duas famílias de **sistemas agênticos**:

- **Workflows:** LLMs e tools orquestrados por **caminhos de código predefinidos**. Previsíveis,
  consistentes, bons para tarefas bem definidas.
- **Agents:** o LLM **dirige dinamicamente** o próprio processo e o uso de tools, mantendo controle
  sobre **como** cumprir a tarefa. Bons para problemas abertos, em que não dá para prever os passos.

O bloco de construção de ambos é o **LLM aumentado** (*augmented LLM*): um modelo com **retrieval,
tools e memória**.

### Os 5 padrões de workflow

| Padrão | Como funciona | Quando usar | Exemplo |
|---|---|---|---|
| **Prompt chaining** | Sequência fixa de chamadas; a saída de uma é a entrada da próxima; pode ter **gates** (checagens programáticas) entre passos | Tarefa que se decompõe limpo em **passos fixos** conhecidos de antemão; troca latência por precisão | Gerar o esboço → checar se atende critérios (gate) → escrever o documento |
| **Routing** | Classifica a entrada e a **encaminha** para um fluxo/prompt especializado | Categorias **distintas** que se tratam melhor separadamente | Suporte: dúvida geral / reembolso / suporte técnico, cada um com seu prompt e tools; perguntas fáceis para modelo menor |
| **Parallelization** | Várias chamadas **simultâneas**, resultados agregados por código. Duas variações: **sectioning** (subtarefas independentes em paralelo) e **voting** (a mesma tarefa várias vezes para obter diversidade/consenso) | Subtarefas independentes (velocidade) ou quando múltiplas perspectivas aumentam a confiança | Sectioning: um modelo responde, outro filtra conteúdo impróprio. Voting: vários prompts procurando vulnerabilidade no mesmo código |
| **Orchestrator-workers** | Um LLM central **decompõe dinamicamente** a tarefa, delega a workers e sintetiza | Subtarefas **não previsíveis** de antemão (dependem da entrada) | Mudança de código que toca um número imprevisível de arquivos; pesquisa em fontes variadas |
| **Evaluator-optimizer** | Um LLM gera; outro **avalia e dá feedback**; repete em loop | Há **critérios de avaliação claros** e o refinamento iterativo agrega valor mensurável | Tradução literária com nuances; busca complexa que exige várias rodadas |

**Diferença que mais cai:** *parallelization* tem subtarefas **definidas pelo programador**;
*orchestrator-workers* tem subtarefas **definidas pelo LLM** a partir da entrada.

### Os princípios do artigo

1. **Comece simples.** Uma única chamada de LLM bem feita, com retrieval e exemplos, resolve muita
   coisa. Só adicione complexidade (workflow, depois agente) quando ela **comprovadamente** melhora o
   resultado. Agentes trocam **latência e custo** por desempenho.
2. **Transparência:** mostre os passos de planejamento do agente.
3. **Projete com cuidado a ACI** (*agent-computer interface*): documentação e teste das tools merecem
   o mesmo cuidado de uma interface humana (é o D2).
4. Frameworks ajudam a começar, mas **abstraem** prompts e respostas e dificultam o debug: entenda o
   que roda por baixo.

**Anti-padrão.** Montar um sistema multiagente para uma tarefa que um prompt chain (ou uma chamada
só) resolve. "Mais agentes = melhor" é a alternativa errada clássica.

**Como cai na prova.** Qualquer cenário: "qual arquitetura?". Passos fixos → **prompt chaining**;
categorias distintas → **routing**; subtarefas independentes → **parallelization**; subtarefas que
dependem da entrada → **orchestrator-workers**; critério claro de qualidade + iteração →
**evaluator-optimizer**; e sempre: **a mais simples que resolve**.

---

## 2. Hub-and-spoke: o coordenador e seus subagents

**Fato-chave.** Na arquitetura **hub-and-spoke**, um **coordenador** (o hub):
1. **Decompõe** a tarefa;
2. **Delega** a subagents especializados (os spokes);
3. **Roteia toda a comunicação**: subagents **não conversam entre si**, tudo passa pelo coordenador;
4. **Agrega** os resultados;
5. **Trata os erros** dos subagents (resultado parcial, falha, timeout);
6. **Avalia a síntese** e **redelega** quando há lacunas.

**Acione só os subagents que a consulta precisa.** Uma pergunta simples sobre um dado específico
não precisa passar por busca web + acadêmico + análise + revisão. O coordenador decide o que acionar.

**Refinamento iterativo.** Roda os subagents → **avalia** o resultado → identifica **lacunas** →
faz uma **2ª rodada direcionada** só para elas → sintetiza.

**Decomposição estreita demais (anti-padrão clássico).** Pedido: "impacto da IA nas **indústrias
criativas**". O coordenador decompõe em "IA nas artes visuais" e entrega um relatório que ignora
música, cinema, escrita, games, design. **A falha está no coordenador** (decomposição), não nos
subagents que fizeram bem o que receberam. Correção: **decompor mais amplo** e **checar
explicitamente a cobertura** contra o escopo do pedido antes de sintetizar.

**Por quê.** Centralizar no coordenador dá **observabilidade** (um lugar vê tudo), **controle de
erro** e **consistência**. Comunicação direta entre subagents cria acoplamento, perde rastreabilidade
e impede o coordenador de detectar lacunas.

**Anti-padrões.**
- Subagents trocando mensagens diretamente.
- Pipeline fixo que passa **toda** consulta por **todos** os subagents.
- Culpar/ajustar o subagent quando o defeito é a decomposição do coordenador.
- Sintetizar sem avaliar cobertura.

**Como cai na prova.** Cenário 3: "o relatório final cobre só parte do tema; os subagents
funcionaram corretamente" → **corrigir a decomposição do coordenador** e checar cobertura. Pegadinha:
"melhorar o prompt do subagent de busca" ou "adicionar mais subagents de busca".

---

## 3. Spawn de subagents e passagem de contexto

### 3.1 A tool `Agent` e o contexto isolado

**Fato-chave.** Subagents são criados pela tool **`Agent`** (nome anterior: **`Task`**). Para o
coordenador conseguir criar subagents, `Agent` precisa estar nas **`allowedTools`** dele; dá para
restringir quais **tipos** de subagent ele pode criar.

**O contexto do subagent é isolado.** Ele **não herda** o histórico do coordenador. Ele recebe:
o **prompt de delegação** que o coordenador escreveu (+ o system prompt/definição do subagent e,
no Claude Code, o CLAUDE.md). E devolve **só o resultado final**.

Consequência: **tudo o que ele precisa vai explícito no prompt**.

| Delegação ruim | Delegação boa |
|---|---|
| "Analise o problema do cliente." | "Cliente C-77 (plano Pro, verificado) relata cobrança duplicada de US$ 129,90 no pedido 8812 em 03/10. Verifique no gateway se houve duas capturas e devolva: ids das capturas, valores, datas e se uma delas foi estornada." |
| "Pesquise o que falamos antes." | Objetivo, escopo, o que já se sabe, o que **não** precisa repetir, formato de saída esperado, critério de pronto |

**Por quê.** O isolamento é a **vantagem** do subagent: ele explora muito (lê 50 arquivos, faz 30
buscas) num contexto próprio e devolve só a conclusão, mantendo o contexto do coordenador limpo. O
preço é ter de **passar o contexto explicitamente**.

**Anti-padrão.** Delegar com referência a algo que só existe no histórico do coordenador ("o
problema", "aquele arquivo", "como discutimos").

### 3.2 Paralelismo

**Fato-chave.** Para rodar subagents **em paralelo**, o coordenador emite **várias chamadas `Agent`
na mesma resposta** (são `tool_use` paralelos, lembra do Módulo 06?). Uma chamada por turno =
**sequencial**. [volátil] O Claude Code tem limites de concorrência e de profundidade de aninhamento.

**Como cai.** "O coordenador dispara 4 pesquisas independentes, mas elas rodam uma após a outra" →
emitir os 4 `Agent` **numa única resposta** (instrução no prompt do coordenador). Pegadinha: "criar 4
processos/sessões separadas" ou "aumentar o limite de concorrência" (não é o gargalo).

### 3.3 Agent SDK: `AgentDefinition` e `parent_tool_use_id`

No **Claude Agent SDK** (Python/TypeScript), subagents são declarados por **`AgentDefinition`**:
**descrição** (quando usar: dirige a escolha do coordenador), **prompt** (o system prompt do
subagent), **tools** permitidas e **modelo**. Forma conceitual:

```json
{
  "allowedTools": ["Agent", "Read", "Grep"],
  "agents": {
    "verificador-de-cobranca": {
      "description": "Verifica capturas e estornos no gateway de pagamento. Use para disputas de cobrança.",
      "prompt": "Você verifica cobranças. Devolva JSON com captura, valor, data, fonte.",
      "tools": ["mcp__gateway__get_captures", "mcp__gateway__get_refunds"],
      "model": "sonnet"
    }
  }
}
```

As mensagens geradas **dentro** de um subagent chegam ao seu código com **`parent_tool_use_id`**
apontando para o `tool_use` do `Agent` que o criou. É assim que você faz **atribuição** (qual
subagent produziu o quê) em logs e UIs.

No **Claude Code**, o equivalente é um arquivo em **`.claude/agents/<nome>.md`** com frontmatter
(`description`, `tools`, `model`...; detalhes no Módulo 08).

### 3.4 Fork vs. subagent "fresco"

| | **Fork** | **Subagent fresco** |
|---|---|---|
| Contexto | **Herda a conversa toda** do pai | Começa **do zero** (só o prompt de delegação) |
| Custo | **Compartilha o cache de prompt** do pai (mais barato para começar) | Paga o próprio contexto |
| O que volta | Só o resultado final | Só o resultado final |
| Quando usar | A subtarefa **depende de muito do que já foi discutido**; reexplicar seria caro e arriscado | Tarefa **delimitada e bem especificada**; você quer **visão independente** (sem o viés da conversa) |

**Pegadinha de nome.** Na skill do Claude Code, `context: fork` roda a skill num **subagent
isolado** (o histórico **não** vai). Não confunda com o fork que herda a conversa.

**Como cai.** "Precisamos de uma revisão imparcial do plano" → subagent **fresco** (um fork herdaria
o viés do raciocínio). "Explorar uma alternativa que depende de tudo que já discutimos" → **fork**.

### 3.5 Passagem estruturada: conteúdo + metadados

**Fato-chave.** O que os subagents devolvem (e o que o coordenador repassa) deve separar
**conteúdo** de **metadados**: afirmação, evidência/trecho, **fonte** (URL/documento), **data**
(publicação/coleta), tipo de fonte, confiança. Assim a **atribuição sobrevive** à síntese.

```json
{
  "claim": "O mercado de música gerada por IA cresceu 38% em 2025",
  "evidence": "trecho literal do relatório, p. 12",
  "source": { "url": "https://...", "type": "relatório setorial", "published": "2026-02-10" },
  "retrieved_at": "2026-10-01"
}
```

**Anti-padrão.** Subagent devolve um parágrafo em prosa; o coordenador resume os resumos; no final
ninguém sabe de onde veio cada número (e conflitos entre fontes somem; ver proveniência no Módulo 11).

---

## 4. Estratégias de decomposição: chaining vs. dinâmica

**Fato-chave.**
- **Prompt chaining:** os passos são **fixos, sequenciais e conhecidos de antemão** (extrair →
  validar → traduzir → formatar). Previsível, fácil de testar, com gates entre os passos.
- **Decomposição dinâmica/adaptativa:** as subtarefas **surgem do que se descobre** (investigação
  aberta, debug de causa desconhecida, pesquisa). É o orchestrator-workers / agente.

**Por quê.** Usar decomposição dinâmica num processo fixo é pagar imprevisibilidade e custo sem
ganho. Usar chaining numa investigação aberta é engessar: o passo 3 não sabe que o passo 2 descobriu
algo que muda o plano.

**Como cai.** "Pipeline de onboarding de contratos: extrair cláusulas → classificar risco → gerar
resumo, sempre igual" → **chaining**. "Investigar por que a conversão caiu" → **dinâmica**. Pegadinha:
oferecer um agente autônomo com 6 subagents para o pipeline fixo.

---

## 5. Review multi-pass e o viés do contexto de raciocínio

### 5.1 Revise em sessão independente

**Fato-chave.** O modelo que **gerou** o conteúdo carrega o **contexto de raciocínio** que o levou
àquelas decisões e tende a **não questioná-las** (viés do contexto de raciocínio). A revisão deve
acontecer numa **sessão/instância independente**, que vê o **artefato** (código, documento), não o
raciocínio de quem o produziu.

**Anti-padrões.**
- "Agora revise o que você escreveu" **na mesma sessão** (anti-padrão nº 9 do blueprint).
- Fork da sessão geradora para revisar (herda o mesmo viés).
- Pedir que o mesmo agente "seja mais crítico" (instrução não remove o contexto enviesado).

### 5.2 PR grande: passo 1 por arquivo + passo 2 de integração

Num PR de 30 arquivos, uma revisão única sofre de **diluição de atenção**: achados superficiais,
**padrão inconsistente** entre arquivos (o arquivo 3 é cobrado por algo que passa no arquivo 27) e
**bugs entre arquivos** perdidos.

| Passo | Escopo | O que procura | Como |
|---|---|---|---|
| **1. Local, por arquivo** | Cada arquivo isoladamente | Bugs locais, estilo, tipos, segurança, tratamento de erro | **O mesmo prompt** para todos os arquivos (consistência); dá para paralelizar |
| **2. Integração** | O conjunto | Fluxo de dados entre módulos, contratos/interfaces, erro na fronteira, mudança de assinatura sem atualizar chamadores | **Prompt separado**, recebendo os **achados do passo 1** + o diff relevante |

**Por quê.** Cada passo tem um foco só, o que dá atenção total ao que importa. O passo 2 não
precisa repetir o trabalho local; ele usa o resumo do passo 1 para olhar o que nenhum arquivo
isolado mostra.

**Anti-padrões.**
- Uma passada única no PR inteiro ("revise tudo com atenção").
- Só o passo por arquivo (perde o bug que está **entre** arquivos).
- Trocar por um modelo maior/janela maior "para caber tudo" (janela não resolve diluição de atenção).
- Rodar dois revisores idênticos na mesma passada e "votar" como substituto do passo de integração.

**Como cai.** Cenário 5 (CI): "a revisão automática de PRs grandes perde bugs que atravessam módulos
e é inconsistente entre arquivos" → **passo por arquivo + passo de integração, em sessão
independente da que gerou o código**.

---

## 6. Gestão de sessão: `--resume`, `--fork-session` e recomeçar com resumo

**Fato-chave.**
- **`--resume <sessão>`** (ou `--continue` para a mais recente) **continua** a conversa com o
  histórico inteiro. Bom quando os **resultados de tool no histórico ainda valem**.
- **`--fork-session`** (junto com `--resume`/`--continue`) cria um **novo ID de sessão** a partir
  da base comum: dá para explorar dois caminhos **sem que um contamine o outro**. No Agent SDK, a
  mesma ideia aparece como opções de retomada (`resume`) e de fork da sessão.
- Se **arquivos/serviços mudaram** ou o contexto **derivou** (muita tentativa e erro, decisões
  revertidas), **comece uma sessão nova com um resumo estruturado** em vez de retomar.
- Se for retomar depois de mudanças, **diga explicitamente o que mudou** ("desde a última sessão, o
  módulo X foi refatorado; os resultados de leitura de `x.cs` estão desatualizados"). Os resultados
  velhos continuam no histórico, e o modelo confia neles.
- **O que não pode se perder vai para arquivo/memória** (notas, manifesto, `NOTES.md`, memória),
  não para o scrollback.

**Por quê.** O histórico é tratado como verdade. Resultados de tool velhos (o conteúdo de um
arquivo antes do refactor) levam o modelo a editar com base em código que não existe mais.

**Anti-padrões.**
- Retomar uma sessão de 3 dias atrás depois de um rebase grande, sem avisar nada.
- Usar a mesma sessão para testar duas abordagens alternativas (uma contamina a outra) em vez de
  `--fork-session`.
- Confiar que "está no histórico" para fatos críticos de longo prazo.

**Como cai.** Cenários 2 e 4. "Ontem o Claude mapeou o módulo de pagamentos; hoje outro dev mudou
metade dele" → **sessão nova com resumo estruturado** (ou retomar **informando o que mudou**).
"Quero comparar duas estratégias de migração a partir da mesma análise" → **`--fork-session`**.

---

## Tabela de decisão

| Se... | Então... |
|---|---|
| Passos fixos, conhecidos de antemão | **Prompt chaining** (com gates) |
| Entradas de categorias distintas | **Routing** |
| Subtarefas independentes definidas por você / quer consenso | **Parallelization** (sectioning / voting) |
| Subtarefas dependem da entrada / investigação aberta | **Orchestrator-workers** (decomposição dinâmica) |
| Critério de qualidade claro e iteração ajuda | **Evaluator-optimizer** |
| Dá para resolver com uma chamada/workflow | **Não** monte agente/multiagente: comece simples |
| Subagents precisam trocar informação | **Via coordenador** (hub-and-spoke), nunca direto |
| Consulta simples num sistema multiagente | Acione **só** os subagents necessários |
| Relatório cobre só parte do tema | Corrigir a **decomposição do coordenador** + checar cobertura |
| Síntese com lacunas | 2ª rodada **direcionada** às lacunas |
| Delegar a um subagent | Prompt com **todo** o contexto explícito (isolado!) |
| Quer subagents em paralelo | **Vários `Agent` na mesma resposta** |
| Atribuir mensagens a subagents no Agent SDK | **`parent_tool_use_id`** |
| Subtarefa depende de muito do que já foi discutido | **Fork** (herda conversa, compartilha cache) |
| Tarefa delimitada / visão imparcial | **Subagent fresco** |
| Resultado de subagent vai para síntese | **Conteúdo + metadados** (fonte, data, evidência) |
| Revisar o que foi gerado | **Sessão independente** |
| PR grande | **Passo 1 por arquivo** (mesmo prompt) + **passo 2 de integração** |
| Resultados de tool ainda válidos | `--resume` |
| Arquivos/serviços mudaram | **Sessão nova + resumo estruturado** (ou retomar dizendo o que mudou) |
| Explorar alternativas a partir da mesma base | `--fork-session` |
| Fato que não pode se perder | Arquivo/memória, não scrollback |

## Glossário

- **Workflow:** LLM + tools em caminhos de código predefinidos.
- **Agent:** o LLM dirige dinamicamente o próprio processo e as tools.
- **Augmented LLM:** LLM com retrieval, tools e memória; bloco base dos dois.
- **Prompt chaining / routing / parallelization / orchestrator-workers / evaluator-optimizer:** os 5 padrões de workflow.
- **Sectioning / voting:** as duas variações de parallelization (dividir vs. repetir).
- **ACI (agent-computer interface):** a interface entre agente e tools; merece o cuidado de uma UI.
- **Hub-and-spoke:** coordenador central que roteia toda a comunicação entre subagents.
- **Coordenador / subagent:** quem decompõe e sintetiza / quem executa uma subtarefa com contexto próprio.
- **Tool `Agent` (antes `Task`):** a tool que cria subagents.
- **`AgentDefinition`:** declaração de subagent no Agent SDK (descrição, prompt, tools, modelo).
- **`parent_tool_use_id`:** campo que liga mensagens do subagent ao `tool_use` que o criou.
- **Fork:** subagent/sessão que herda a conversa e compartilha cache.
- **Viés do contexto de raciocínio:** quem gerou tende a não questionar as próprias decisões.
- **Review multi-pass:** passo local por arquivo + passo de integração.
- **`--resume` / `--continue` / `--fork-session`:** retomar uma sessão / a mais recente / ramificar com novo ID.

## Cola de véspera

- **Workflows** (caminho em código) vs. **agents** (o LLM dirige). **Comece simples**; só complique se medir ganho.
- **5 padrões:** chaining (passos fixos), routing (categorias), parallelization (sectioning/voting),
  orchestrator-workers (subtarefas definidas pelo LLM), evaluator-optimizer (gera ↔ avalia).
- **Hub-and-spoke:** coordenador decompõe, delega, **roteia tudo**, agrega, trata erro, redelega lacunas.
  Subagents **não** se falam.
- **Só os subagents necessários.** Refinamento: avaliar → lacunas → 2ª rodada direcionada.
- **Cobertura parcial = decomposição estreita do coordenador** ("indústrias criativas" ≠ artes visuais).
- **Tool `Agent`** (ex-`Task`) em `allowedTools`. **Contexto isolado → tudo explícito no prompt.**
- **Paralelo = vários `Agent` na mesma resposta.**
- Agent SDK: **`AgentDefinition`**; atribuição por **`parent_tool_use_id`**.
- **Fork** herda conversa + cache; **fresco** para tarefa delimitada/visão imparcial.
- Devolva **conteúdo + metadados** (fonte, data, evidência).
- **Chaining** = passos fixos; **dinâmica** = subtarefas surgem das descobertas.
- **Review em sessão independente.** PR grande: **por arquivo (mesmo prompt) + integração (prompt separado, recebe achados)**.
- **`--resume`** se os resultados valem; mudou algo → **sessão nova com resumo** ou **diga o que mudou**;
  **`--fork-session`** para ramos sem contaminação; crítico → **arquivo**.

## Perguntas de checagem

1. **Qual a diferença entre parallelization e orchestrator-workers?**
   Em parallelization as subtarefas são definidas de antemão pelo programador (sectioning) ou são a
   mesma tarefa repetida (voting); em orchestrator-workers um LLM decide as subtarefas dinamicamente a
   partir da entrada.
2. **O relatório sobre "IA nas indústrias criativas" falou só de artes visuais, e cada subagent fez
   bem o que recebeu. Onde está o defeito e qual a correção?**
   Na decomposição do coordenador (estreita demais). Decompor de forma mais ampla e checar
   explicitamente a cobertura contra o escopo antes de sintetizar.
3. **Por que "analise o problema do cliente" é uma delegação ruim?**
   O subagent tem contexto isolado e não vê o histórico do coordenador; precisa receber explicitamente
   cliente, problema, dados já levantados, objetivo e formato de saída.
4. **Como revisar um PR de 40 arquivos gerado pelo próprio Claude?**
   Em sessão independente da que gerou; passo 1 por arquivo com o mesmo prompt; passo 2 de integração
   com prompt separado, recebendo os achados do passo 1.
5. **Ontem a sessão leu todo o módulo de faturamento; hoje ele foi refatorado. `--resume` ou sessão nova?**
   Sessão nova com resumo estruturado (os resultados de leitura no histórico estão velhos); se retomar,
   informar explicitamente o que mudou. `--fork-session` serviria para explorar alternativas, não para isso.
