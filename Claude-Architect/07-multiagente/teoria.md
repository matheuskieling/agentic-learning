# Módulo 07 — Orquestração multiagente: coordenador, subagents e decomposição

> **D1 — Arquitetura agêntica & orquestração (27%).** TS **1.2** (coordenador e subagents), **1.3**
> (invocação de subagents, passagem de contexto, spawn) e **1.6** (estratégias de decomposição).
> **Onde cai:** cenário **3** (Multi-Agent Research System) acima de todos; também **4** (Developer
> Productivity), **5** (CI: revisão em passos), **2** (Claude Code: investigação com passos fixos × dinâmica)
> e **1** (Customer Support).
> **Só ponte aqui:** sessões `--resume`/`fork_session` em detalhe → M10 (1.7); revisão por instância
> independente → M09 (4.6); propagação de erro e proveniência → M11 (5.3, 5.6); distribuição de tools e
> `verify_fact` → M04 (2.3).

Um sistema multiagente é **um loop agêntico que chama outros loops**. Quase toda questão deste módulo
pergunta, no fundo, **quem sabe o quê** (contexto) e **quem decide o quê** (o coordenador).

---

## 1. Hub-and-spoke: toda comunicação passa pelo coordenador

**Fatos de prova (1.2).**
- Na arquitetura **hub-and-spoke**, o **coordenador** gerencia **toda a comunicação entre
  subagents**, o **tratamento de erros** e o **roteamento da informação**. Subagents não conversam
  entre si.
- Rotear tudo pelo coordenador dá o que o guia nomeia: **observabilidade** (um lugar vê cada pedido e
  resultado), **tratamento de erro consistente** e **fluxo de informação controlado**.

**Por quê.** Se a análise chama a busca direto (fila, store compartilhado, chamada ponto a ponto), o
coordenador não vê a busca que falhou, não decide se tenta de novo, não percebe lacunas, e cada par de
subagents trata erro do seu jeito. (Recuperação **local** de falha transitória continua valendo: o
subagent propaga só o que não resolveu; M04/M11.)

**Anti-padrões que aparecem como alternativa errada.**
- "Para cortar latência, deixe o subagent X chamar o Y direto" ou "um store compartilhado onde cada
  subagent publica, lê a saída dos outros e decide o próximo passo".
- "Pode ir direto, desde que tudo seja logado": log devolve parte da observabilidade, não o controle do
  fluxo nem o erro centralizado.
- Fundir dois subagents num só, com as tools dos dois, "para eliminar o round trip".

**Nuance.** Uma tool **escopada** `verify_fact` na síntese (checagens simples e frequentes) **não**
quebra o hub-and-spoke: é tool, não conversa entre subagents (oficial 9; M04).

**Como cai na prova.** "Um engenheiro propõe que os subagents se falem direto para ganhar velocidade;
como avaliar?" → rejeitar. Sintomas no enunciado: "o trace do coordenador não registra 40% das
buscas", "no timeout da busca, a análise esperou em silêncio".

---

## 2. O papel do coordenador: decompor, delegar, agregar e escolher quem chamar

**Fatos de prova (1.2).**
- O coordenador faz **decomposição**, **delegação**, **agregação** dos resultados e **decide quais
  subagents invocar conforme a complexidade da consulta**.
- Ele **analisa a consulta e seleciona dinamicamente** os subagents, em vez de **passar sempre pelo
  pipeline completo**. "Em que ano a biblioteca entrou no consórcio X?" → só a busca. "Compare o
  impacto de citação de artigos abertos × pagos em química, 2010–2023" → várias buscas em paralelo +
  análise + síntese + relatório. Comportamento diferente por consulta é **esperado**, não bug.

**Por quê.** O coordenador é um LLM que lê as `description` dos subagents: já sabe decidir. Pipeline
fixo gasta latência e custo e devolve o que ninguém pediu.

**Anti-padrões que aparecem como alternativa errada.**
- "Toda consulta passa pelos N subagents, em ordem, por consistência".
- "Um **classificador / routing layer** antes do coordenador decide o tipo de consulta" →
  over-engineering: é trabalho do próprio coordenador (mesmo distrator das oficiais 1, 2 e 3).
- "Rode o pipeline em paralelo": reduz latência, mas segue chamando quem não é necessário.

**Como cai na prova.** "Perguntas simples levam 4 minutos e voltam com seções que ninguém pediu; o
design manda tudo pelos 4 subagents" → o coordenador deve invocar só o necessário.

---

## 3. Decomposição estreita demais e particionamento do escopo

**Fatos de prova (1.2).**
- **Decomposição estreita demais:** o coordenador quebra um tema amplo em subtarefas que cobrem só uma
  fatia → **cobertura incompleta**. Os subagents fazem bem o que receberam; o defeito está **no que
  receberam**.
- **Particionar o escopo** para **minimizar duplicação**: **subtemas distintos** ou **tipos de fonte
  distintos** por subagent (periódicos para um, relatórios governamentais para outro...).

Pedido: *"Como as bibliotecas universitárias se adaptaram ao acesso aberto desde 2015?"*

| Decomposição | Resultado |
|---|---|
| "custo de assinaturas", "orçamento de APC", "cancelamento de *big deals*" | **Estreita:** só finanças; somem repositórios, capacitação, política de acervo |
| 3 subagents, todos com "acesso aberto em bibliotecas" | **Sobreposta:** 70% das fontes repetidas, custo triplicado |
| Subtemas distintos **ou** um tipo de fonte por subagent | Cobre o tema **e** não duplica |

**Anti-padrões que aparecem como alternativa errada.**
- Culpar quem está a jusante: "queries da busca literais demais", "análise com relevância estrita
  demais", "síntese sem checagem de lacunas" (as três erradas da oficial 7).
- Mesma consulta ampla para todos "por redundância", deduplicando depois na síntese.
- Aumentar o número de resultados por busca (mais do mesmo recorte).

**Como cai na prova.** "Relatório preciso, mas ignora X e Y; o log do coordenador mostra as subtarefas
A, B, C" → decomposição estreita. "Dois subagents devolvem 70% das mesmas fontes" → particionar.

---

## 4. Refinamento iterativo: avaliar a síntese e redelegar

**Fatos de prova (1.2).** O coordenador (1) **avalia a saída da síntese** procurando lacunas contra o
escopo pedido, (2) **redelega** à busca e à análise com **consultas direcionadas** às lacunas,
(3) **re-invoca a síntese** com achados novos + anteriores e (4) repete **até a cobertura ser
suficiente**.

**Por quê.** Só o coordenador enxerga o pedido original e tudo o que voltou.

**Anti-padrões que aparecem como alternativa errada.**
- Entregar a primeira síntese com uma seção "questões em aberto" que ninguém investiga.
- Pedir à síntese que "complete as lacunas" sozinha: de memória (inventa) ou ganhando tools de busca
  (sai da especialização).
- Rodar o pipeline inteiro de novo com a mesma consulta.
- Teto de iterações como critério **principal** de parada (o critério é cobertura; teto é só rede de
  segurança).

**Ponte M11 (5.3):** lacuna que não fecha vira **coverage annotation** na síntese.

**Como cai na prova.** "Os relatórios dizem 'não foi possível determinar se o módulo X é chamado pelos
jobs noturnos', a informação era fácil de achar e o log mostra uma única passada" → falta o loop.

---

## 5. Criando subagents: a tool `Task`, `allowedTools` e `AgentDefinition`

**Fatos de prova (1.3).**
- Subagents são criados pela tool **`Task`**, e **`allowedTools` do coordenador precisa incluir
  `"Task"`**. Sem isso, as definições existem mas nunca são usadas: o coordenador faz tudo sozinho.
- Cada tipo de subagent é um **`AgentDefinition`**: **description** (quando usar; é o que o
  coordenador lê para escolher), **system prompt** (papel e formato de saída) e **restrição de
  tools** (só o que o papel precisa).

Agent SDK (oficial em Python/TypeScript; abaixo, TS; em Python: `allowed_tools=[...]`,
`agents={"...": AgentDefinition(...)}`):

```ts
// Opções do COORDENADOR
const options = {
  allowedTools: ["Task", "Read"],                 // ← AQUI: sem "Task", nenhum subagent é criado
  agents: {
    "web-search": {                               // um AgentDefinition
      description: "Finds new sources on an assigned subtopic. Not for analyzing retrieved documents.",
      prompt: "You are a search specialist. Return each source as JSON (claim, excerpt, url, published).",
      tools: ["WebSearch", "WebFetch"]            // ← AQUI: restrição de tools do subagent
    },
    "synthesis": {
      description: "Combines the findings passed in its prompt into a cited synthesis. Does not search.",
      prompt: "You synthesize findings. Preserve every claim-source mapping you receive.",
      tools: ["mcp__research__verify_fact"]
    }
  }
};
```

O que o coordenador emite para criar o subagent (resposta da Messages API dentro do loop do SDK):

```json
{
  "role": "assistant",
  "stop_reason": "tool_use",
  "content": [
    { "type": "tool_use", "id": "toolu_01",
      "name": "Task",                              // ← AQUI: a tool que cria o subagent
      "input": {
        "subagent_type": "web-search",             // ← AQUI: qual AgentDefinition usar
        "description": "Search: institutional repositories",
        "prompt": "Goal: ... (todo o contexto vai aqui; ver §6)" } }
  ]
}
```

> **Na doc atual [volátil]:** a tool `Task` foi renomeada para **`Agent`** (Claude Code v2.1.63);
> `Task(...)` segue como alias, e `allowedTools` passou a ser descrito como a lista de tools
> **auto-aprovadas**. **Na prova, responda `Task` / `allowedTools` com `"Task"`.** No Claude Code, o
> equivalente do `AgentDefinition` é um arquivo em `.claude/agents/` (extra da doc; não cai).

**Por quê.** A `description` é o mecanismo de seleção (descrição vaga → subagent errado). Restringir
tools é menor privilégio: com tools fora do papel, a síntese pesquisa em vez de sintetizar.

**Anti-padrões que aparecem como alternativa errada.**
- Coordenador que não delega → "mande delegar no system prompt", "description com 'use
  proactively'", "tire Grep/Read do coordenador". Sem `"Task"` em `allowedTools`, nada disso adianta.
- Proibir por prompt ("nunca chame `process_refund`") em vez de tirar a tool do `AgentDefinition`; ou
  um `PostToolUse` que só **registra** a chamada já feita.
- Todas as tools para todos os subagents "por flexibilidade".

**Como cai na prova.** "O coordenador nunca delega, faz 60 Greps sozinho; `allowedTools` sem `Task`" →
incluir `"Task"`. "O subagent de rastreio chamou `process_refund` em 2 de 500 conversas; compliance
exige que ele não possa" → restringir as tools no `AgentDefinition` dele.

---

## 6. Contexto isolado: tudo o que o subagent precisa vai no prompt

**Fatos de prova (1.2, 1.3).**
- Subagents têm **contexto isolado**: **não herdam** o histórico do coordenador e **não compartilham
  memória entre invocações** (a 2ª chamada ao mesmo subagent começa do zero).
- O contexto vai **explícito no prompt** do `Task`: os **achados completos dos agentes anteriores**
  (ex.: resultados da busca web **e** saídas da análise de documentos no prompt da síntese).
- Use **formato estruturado que separa conteúdo de metadados** (URL da fonte, nome do documento,
  página) para **preservar a atribuição** entre agentes.

| Contexto implícito (falha) | Explícito (certo) |
|---|---|
| "Busque fontes sobre o tema que combinamos." | Meta + escopo (revisados por pares, 2015–2024, sem preprints) + o que já foi coberto + formato de saída |
| 2ª invocação: "Revise seu rascunho conforme os comentários." | Rascunho completo + fontes + comentários + achados originais |
| "Escreva o resumo com os achados das etapas anteriores." | Saídas completas do explorer e da análise de dependências, coladas no prompt |

Cada achado separa conteúdo de metadados; a lista inteira vai **dentro de
`content[].input.prompt`** do `tool_use` `Task` que cria a síntese (o subagent não tem outro canal):

```json
{
  "findings": [
    {
      "content": {                                         // ← AQUI: o que se afirma
        "claim": "62% dos periódicos de química da amostra cobram APC acima de US$ 2.000",
        "excerpt": "Of the 118 chemistry journals sampled, 73 charge APCs above USD 2,000"
      },
      "metadata": {                                        // ← AQUI: de onde veio
        "source_url": "https://example.org/apc-survey-2023",
        "document": "APC Survey 2023 - Final Report",
        "page": 14,
        "published": "2023-11-02"
      }
    }
  ]
}
```

Orquestrando em código .NET em vez de pelo LLM, a regra é a mesma:

```csharp
public record Source(string Url, string Document, int? Page, DateOnly? Published);
public record Finding(string Claim, string Excerpt, Source Source);

string SynthesisPrompt(string goal, IReadOnlyList<Finding> web, IReadOnlyList<Finding> docs) => $"""
    Goal: {goal}
    <web_findings>{JsonSerializer.Serialize(web)}</web_findings>
    <document_findings>{JsonSerializer.Serialize(docs)}</document_findings>
    """;   // achados COMPLETOS e estruturados, não um resumo em prosa
```

**Por quê.** O isolamento é a vantagem do subagent (explora muito no próprio contexto e devolve só o
resultado); o preço é passar o contexto explicitamente. Prosa resumida de prosa resumida perde quem
disse o quê.

**Anti-padrões que aparecem como alternativa errada.**
- Referências ao histórico do coordenador: "o tema que combinamos", "as etapas anteriores".
- "Dê ao subagent acesso ao log da conversa do coordenador" (ou a um store) para ele "recuperar" o
  contexto.
- Resumir os achados em 2–3 frases "para economizar contexto".
- Corrigir só por prompt ("não seja genérico, cite todas as tabelas"): ele não cita o que não recebeu.
- Pôr regras **deste pedido** no system prompt fixo do `AgentDefinition` (lá vão regras permanentes do
  papel; o que é do pedido vai no prompt do `Task`).

**Pontes:** metadados para a síntese → M10 (5.1); claim-source mappings → M11 (5.6).

> **Na doc atual [volátil]:** o Claude Code tem um **"fork subagent"** que herda a conversa do pai
> (recente, posterior ao guia). **Na prova, contexto de subagent é sempre explícito no prompt**; "o
> subagent herda/vê a conversa do coordenador" é alternativa errada.

**Como cai na prova.** "Depois de 12 turnos combinando o escopo, o coordenador delega 'busque fontes
sobre o tema combinado' e vêm preprints fora da faixa de datas" → escopo e restrições no prompt.

---

## 7. Paralelismo, prompt do coordenador por metas e `fork_session`

### 7.1 Paralelo = vários `Task` numa única resposta

**Fatos de prova (1.3).** Para rodar subagents em paralelo, o coordenador **emite várias chamadas
`Task` numa única resposta**. Um `Task` por turno = sequencial (cada um espera o anterior; latência =
soma).

```json
{
  "role": "assistant",
  "stop_reason": "tool_use",
  "content": [
    { "type": "tool_use", "id": "toolu_A", "name": "Task",                    // ← AQUI
      "input": { "subagent_type": "web-search", "prompt": "Subtopic: repositories ..." } },
    { "type": "tool_use", "id": "toolu_B", "name": "Task",                    // ← AQUI
      "input": { "subagent_type": "web-search", "prompt": "Subtopic: APC budgets ..." } }
  ]
}
```

**Anti-padrões.** Um `Task` por turno; juntar N subtarefas num único `Task` (um subagent faz tudo em
série); o coordenador fazer as consultas ele mesmo "para evitar overhead"; aumentar timeout.

### 7.2 Prompt do coordenador: metas e critérios de qualidade, não passo a passo

**Fatos de prova (1.3).** O prompt do coordenador (e as delegações que ele escreve) especifica **metas
de pesquisa e critérios de qualidade**, não **instruções procedimentais passo a passo**. Isso dá
**adaptabilidade** aos subagents quando o tema foge do roteiro.

| Procedural (frágil) | Metas + critérios (adaptável) |
|---|---|
| "1. Busque no catálogo com as palavras exatas do usuário. 2. Pegue os 5 primeiros. ... 14. Formate em APA." | "Meta: panorama de X para um comitê. Critérios: cobrir cada disciplina envolvida; só fontes revisadas por pares; toda afirmação com fonte; sinalizar estatísticas conflitantes." |

**Anti-padrões.** Acrescentar passos ao procedimento para o caso que falhou; few-shot de palavras-chave
por caso; classificador que manda o caso difícil para outro pipeline.

### 7.3 `fork_session`: ramos a partir de uma base comum

**Fatos de prova (1.3; sessões em detalhe no M10).** Depois de uma análise compartilhada (a base),
`fork_session` cria **ramos independentes** para explorar **abordagens divergentes**, sem refazer a
análise e sem que o raciocínio de um ramo contamine o outro.

```ts
// Agent SDK: cada ramo retoma a sessão da análise e ganha um NOVO id de sessão
const options = { resume: baselineSessionId, forkSession: true };   // ← AQUI (Python: fork_session=True)
```

O fork ramifica a **conversa**, não o filesystem. **Anti-padrões:** seguir na mesma sessão (a 2ª
abordagem herda o raciocínio da 1ª); duas sessões novas com um resumo de um parágrafo (perdem o
detalhe); dois subagents "contando que vejam a análise".

**Como cai na prova (7.1–7.3).** "Três consultas independentes levam a soma dos tempos; o trace mostra
um `Task` por turno" → vários `Task` na mesma resposta. "O coordenador segue 14 passos e falha em
pedidos interdisciplinares" → metas + critérios. "Comparar dois enquadramentos a partir da mesma
análise de 40 minutos" → `fork_session`.

---

## 8. Estratégias de decomposição: prompt chaining × decomposição dinâmica

**Fatos de prova (1.6).**
- **Prompt chaining** (pipeline sequencial fixo): passos conhecidos de antemão; serve para **revisões
  previsíveis multi-aspecto**. Padrão canônico: revisão em passos, **cada arquivo individualmente** e
  depois um **passo de integração entre arquivos**.
- **Decomposição dinâmica/adaptativa**: subtarefas **geradas a partir do que se descobre** em cada
  passo; serve para **investigação aberta**. O valor do plano adaptativo é seguir a pista que surge no
  meio do caminho.

### 8.1 Revisão grande = passos por arquivo + passo de integração

| Passo | Entrada | Procura |
|---|---|---|
| **1. Local, por arquivo** | Um arquivo, com os mesmos critérios para todos | Bugs locais, tratamento de erro, segurança, convenções |
| **2. Integração** | Achados do passo 1 + interfaces dos módulos alterados | Fluxo de dados entre arquivos, contratos, unidades, chamadores quebrados |

**Por quê.** Uma passada única sobre muitos arquivos sofre **diluição de atenção**: profundidade
desigual, achados contraditórios, bugs óbvios perdidos. Cada passo com um foco só recebe atenção
total; o de integração vê o que nenhum arquivo isolado mostra.

**Anti-padrões.** Passada única "com mais atenção"; modelo/janela maior (janela não resolve atenção);
obrigar os devs a quebrar o PR; rodar 3 vezes e votar; **só** passos por arquivo (perde o bug entre
arquivos). Ponte M09 (4.6): revisar com **instância independente** de quem gerou o código.

### 8.2 Decomposição dinâmica: investigação aberta

**"Adicionar testes abrangentes a um codebase legado"**: (1) **mapear a estrutura** (módulos, pontos
de entrada, dependências); (2) **identificar áreas de alto impacto** (incidentes, dinheiro, lógica
crítica); (3) **plano priorizado que se adapta** conforme surgem dependências (descobriu que o cálculo
de dose usa um singleton estático → primeiro criar um ponto de injeção; o plano muda).

**Anti-padrões.** Plano fixo arquivo por arquivo (ou alfabético): enche de testes de DTO e deixa o
módulo crítico sem nada; começar a testar o primeiro módulo sem mapear; plano fixo "mais completo".
E o inverso: comando fixo ("ler serviço → listar commits → propor fix") numa **investigação** cujo
próximo passo depende do que aparece.

> **Nota de contexto — "Building Effective Agents".** O artigo da Anthropic descreve prompt chaining,
> routing, parallelization, orchestrator-workers e evaluator-optimizer. **Como estratégia de
> decomposição (1.6), o guia só cobra prompt chaining e decomposição dinâmica**; orchestrator-workers e
> paralelismo aparecem com o vocabulário do guia (coordenador-subagent, vários `Task` na mesma
> resposta: §1–§7). Na prova, "routing layer/classificador", "segundo modelo" e "votar entre
> execuções" são **distratores de over-engineering**. Do artigo, leve só: comece pela solução mais
> simples que resolve.

**Como cai na prova.** Cenário 5: revisão de PR com aspectos fixos → chaining (por arquivo +
integração). Cenário 4: testes num legado → dinâmica. Cenário 2: regressão investigada com comando de
passos fixos que não acha a causa → chaining onde cabia dinâmica. E "qual padrão para cada workflow?"
com dois workflows lado a lado.

---

## Tabela de decisão

| Se... | Então... |
|---|---|
| Subagents precisam trocar informação | **Via coordenador**, nunca direto nem por store compartilhado |
| Consulta simples num sistema multiagente | Coordenador invoca **só** os subagents necessários |
| Relatório preciso, mas cobre só parte do tema | **Decomposição estreita** do coordenador |
| Subagents trazem as mesmas fontes | **Particionar** por subtema ou tipo de fonte |
| Síntese com lacunas | **Avaliar → redelegar consultas direcionadas → re-sintetizar** |
| Coordenador nunca delega | **`"Task"` em `allowedTools`** |
| Subagent não pode usar certa tool | **Restringir tools no `AgentDefinition`** |
| Delegar a um subagent | **Contexto explícito no prompt** (achados completos) |
| Passar achados entre agentes | **Conteúdo separado de metadados** (URL, documento, página) |
| Subtarefas independentes rodando em série | **Vários `Task` na mesma resposta** |
| Coordenador preso a roteiro rígido | **Metas + critérios de qualidade** |
| Abordagens divergentes da mesma análise | **`fork_session`** |
| Revisão previsível, vários aspectos / PR grande | **Prompt chaining**: por arquivo + integração |
| Investigação aberta / testes num legado | **Dinâmica**: mapear → alto impacto → plano adaptável |

## Glossário

- **Hub-and-spoke:** o coordenador centraliza comunicação, erro e roteamento entre subagents.
- **Contexto isolado:** sem herança do histórico do coordenador e sem memória entre invocações.
- **`Task` / `AgentDefinition`:** tool que cria subagents / tipo de subagent (description, system
  prompt, tools).
- **`fork_session`:** ramo independente de uma sessão a partir de uma base comum.
- **Diluição de atenção:** perda de profundidade e consistência ao revisar muitos arquivos de uma vez.

## Cola de véspera

- **Hub-and-spoke:** coordenador roteia **toda** comunicação, trata erro, controla o fluxo →
  observabilidade. Subagent falando com subagent = errado, mesmo com log.
- **Coordenador** decompõe, delega, agrega e **escolhe quem chamar pela complexidade**. Pipeline
  completo para tudo = errado; classificador na frente = over-engineering.
- **Cobertura parcial com subagents corretos = decomposição estreita.** Duplicação = particionar.
- **Refinamento:** avaliar lacunas → busca/análise com consultas direcionadas → síntese de novo.
- **`Task`** cria subagent; **`allowedTools` inclui `"Task"`** (doc atual: `Agent`; na prova, `Task`).
- **`AgentDefinition`** = description (seleção) + system prompt + **restrição de tools**.
- **Contexto isolado → tudo explícito no prompt:** achados **completos**, **estruturados**
  (conteúdo × metadados).
- **Paralelo = vários `Task` numa única resposta.** Prompt do coordenador = **metas + critérios**.
- **`fork_session`** = ramos divergentes da mesma base.
- **Chaining** = passos fixos (por arquivo + integração). **Dinâmica** = investigação aberta (legado:
  mapear → alto impacto → plano que se adapta).

## Perguntas de checagem

1. **O relatório sobre acesso aberto só trata de custos, e cada subagent fez bem o que recebeu. Onde
   está o defeito?** Na decomposição do coordenador, estreita demais; ampliar as dimensões, sem
   sobreposição.
2. **O coordenador tem `AgentDefinition`s bem escritos, mas nunca delega. O que checar primeiro?** Se
   `"Task"` está em `allowedTools` dele.
3. **Na 2ª invocação, a síntese ignora o rascunho que ela mesma escreveu. Por quê?** Subagents não
   guardam memória entre invocações: rascunho, fontes e achados vão no prompt da nova chamada.
4. **Quatro buscas independentes levam a soma dos tempos. O que o trace deve mostrar após a
   correção?** Os quatro `tool_use` `Task` numa única resposta do coordenador.
5. **Revisão de PR sempre igual × investigação de falha noturna?** Chaining (por arquivo + integração)
   para a revisão; decomposição dinâmica para a investigação.
6. **Como decompor "adicionar testes abrangentes ao sistema legado"?** Mapear a estrutura, achar as
   áreas de alto impacto e seguir um plano priorizado que se adapta às dependências descobertas.
