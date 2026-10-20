# Blueprint do exame CCAR-F — base de conhecimento do curso

Base do **Claude Certified Architect – Foundations (CCAR-F)**. Teoria, roteiros, quizzes, provas,
bancos por cenário e simulados **têm de ser coerentes com este arquivo**.

## 1. Fonte e regra de autoridade

- **Fonte única:** *Exam Guide* oficial **v1.0 (vigente desde jul/2026)** —
  [PDF](https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F6nizmqk8tpzpfjvt6qmmav7rh%2Fpublic%2F1783542750%2FClaude+Certified+Architect+%E2%80%93+Foundations+Exam+Guide.pdf)
  · [página da certificação](https://anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification).
  São **30 task statements (TS) e 240 bullets**. Os TS 2.6, 3.0, 4.7, 4.8, 5.7 e 5.8 **não existem**:
  vieram de guias não oficiais que alimentaram o blueprint anterior.
- **Autoridade:** (1) o guia decide o que cai e qual é a resposta ("Exam items are written against these
  objectives"); (2) a doc atual (code.claude.com/docs, platform.claude.com/docs, modelcontextprotocol.io)
  serve só para exatidão técnica; (3) se a doc diverge do guia, **na prova vale o guia**. Na teoria, a
  divergência vira a caixa `> **Na doc atual [volátil]:** … na prova, responda X`, e nenhuma questão
  depende dela (§5); (4) conteúdo fora do escopo (§6) nunca decide uma questão.
- **Antes de marcar a prova:** o guia é "subject to change without notice". Confira na página da
  certificação se ainda é o v1.0. Se houver versão nova, revise as §4–§6 contra ela.

## 2. O exame (seção 3 do guia)

| Item | Guia v1.0 |
|---|---|
| Itens | 60, múltipla escolha e múltipla resposta. **Cada item diz quantas marcar** (não assuma sempre 2) |
| Estrutura | **4 cenários sorteados de um banco de 6**; as questões se penduram no cenário |
| Tempo / aplicação | 120 min, supervisionada (Pearson VUE: online ou centro de testes) |
| Aprovação | nota escalada **720** (escala 100–1.000), padrão fixo (*criterion-referenced*), sem curva |
| Resultado | aprovado/reprovado + nota + % de acerto por domínio (o % não entra no corte) |
| Taxa / validade | US$ 125 · 12 meses (renovação gratuita no prazo) |
| Chute | a v1.0 não repete o ponto; o rascunho oficial de fev/2026 dizia que questão em branco conta como erro e não há penalidade por chute |

| Domínio | Peso | TS | ≈ itens |
|---|---|---|---|
| D1 Agentic Architecture & Orchestration | 27% | 1.1–1.7 | 16 |
| D2 Tool Design & MCP Integration | 18% | 2.1–2.5 | 11 |
| D3 Claude Code Configuration & Workflows | 20% | 3.1–3.6 | 12 |
| D4 Prompt Engineering & Structured Output | 20% | 4.1–4.6 | 12 |
| D5 Context Management & Reliability | 15% | 5.1–5.6 | 9 |

**Os 6 cenários (descrição oficial):**
1. **Customer Support Resolution Agent:** agente de resolução de atendimento com o Claude Agent SDK, para
   pedidos muito ambíguos (devoluções, disputas de cobrança, problemas de conta). Acessa o backend por tools
   MCP customizadas (`get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`). Meta: **80%+
   de resolução no primeiro contato**, sabendo quando escalar. *Primários: D1, D2, D5.*
2. **Code Generation with Claude Code:** o time usa o Claude Code para gerar código, refatorar, depurar e
   documentar, e precisa integrá-lo ao fluxo com slash commands customizados e CLAUDE.md, sabendo quando
   usar plan mode vs execução direta. *D3, D5.*
3. **Multi-Agent Research System:** com o Agent SDK, um coordenador delega a subagents especializados (um
   busca na web, um analisa documentos, um sintetiza achados, um gera relatórios). Pesquisa tópicos e
   produz relatórios abrangentes e com citações. *D1, D2, D5.*
4. **Developer Productivity with Claude:** ferramentas com o Agent SDK que ajudam engenheiros a explorar
   codebases desconhecidas, entender legados, gerar boilerplate e automatizar tarefas repetitivas, com as
   tools nativas (Read, Write, Bash, Grep, Glob) e servidores MCP. *D2, D3, D1.*
5. **Claude Code for Continuous Integration:** o Claude Code no pipeline de CI/CD faz review automático,
   gera casos de teste e comenta PRs; os prompts precisam dar feedback acionável e minimizar falsos
   positivos. *D3, D4.*
6. **Structured Data Extraction:** extrai informação de documentos não estruturados, valida a saída com
   JSON schemas e mantém alta acurácia; trata casos de borda com elegância e integra com sistemas
   downstream. *D4, D5.*

## 3. Desempates e taxonomia de distratores

**Desempates que valem para quase toda questão** (das explicações das 12 questões oficiais):
1. **Causa raiz primeiro:** a certa ataca o que os sintomas e logs mostram; as erradas culpam o que
   funciona (Q7).
2. **Primeiro passo proporcional:** baixo esforço e alta alavancagem antes de infraestrutura nova
   (descrição antes de routing layer, Q2; critérios + few-shot antes de classificador, Q3).
3. **Regra crítica → determinismo:** consequência financeira, de segurança ou de compliance pede
   enforcement programático (pré-requisito, hook); prompt e few-shot são probabilísticos (Q1).
4. **Julgamento → critério explícito:** calibrar decisão (escalar, o que reportar) se resolve com critério
   + few-shot, não com código nem modelo extra (Q3, 4.1).
5. **Técnica casada com o requisito declarado:** bloqueante → síncrono; tolerante a latência → Batch
   (Q11); complexidade já declarada → plan mode desde o início (Q5).
6. **Menor privilégio com exceção escopada:** só as tools do papel; tool cruzada restrita para a
   necessidade frequente; casos complexos via coordenador (Q9).
7. **Informação estruturada para quem decide:** erro com tipo/tentativa/parcial, handoff com resumo,
   contexto explícito no prompt do subagent (Q8).
8. **Atenção não se resolve com tamanho:** modelo ou janela maior não cura diluição; passes focados curam (Q12).
9. **Não empurre o ônus para pessoas** (dev quebrar PR, cliente repetir dados) (Q12-B).
10. **Feature inexistente é errada**, por mais plausível: `.claude/config.json`, `CLAUDE_HEADLESS`, `--batch`.
11. **O termo do guia vence:** `Task`, `.claude/commands/`, `allowed-tools` restringe, Read + Write (§5).
12. **Confiança do modelo tem três caras:** (a) filtrar achados por confiança em vez de critério = errado
    (4.1); (b) escalar atendimento por confiança autodeclarada ou sentimento = errado (5.2); (c) confiança
    **por campo/achado, calibrada** com conjunto rotulado, para **rotear revisão humana** = certo (4.6,
    5.5). Nunca ensine que "confiança autodeclarada é sempre inútil".

**Taxonomia de distratores** (varie; cada errada é algo que um engenheiro razoável proporia): fix só por
prompt onde é preciso determinismo · over-engineering (classificador, routing layer, segundo modelo, ML
treinado) · resolve outro problema · feature/flag inexistente (≤1 por questão, ≤10% das questões) ·
empurrar o ônus para humanos/devs · modelo ou janela maior · votação/consenso entre runs · cache ou
pré-busca especulativa · retry + status genérico · supressão silenciosa · abortar o workflow · dar todas as
tools · consolidar/reescrever cedo demais · contexto implícito ("o subagent já sabe") · confiança ou
sentimento como gatilho de escalonamento. **Proibido:** espantalho ("just in case", "ignore the error",
"add more phrases"), correta identificável pelo tamanho, absolutos só nas erradas.

**As 12 questões oficiais (§9):** calibre por elas, mas **não reutilize as situações**.

| Q | C | TS | Situação → resposta (distratores) |
|---|---|---|---|
| 1 | 1 | 1.4 | 12% pula `get_customer` → pré-requisito programático (prompt, few-shot, routing classifier) |
| 2 | 1 | 2.1 | descrições mínimas, tool errada → expandir descrições (few-shot, routing layer, consolidar) |
| 3 | 1 | 5.2 | 55% FCR, escala o simples → critérios + few-shot (confiança 1–10, classificador, sentimento) |
| 4 | 2 | 3.2 | `/review` do time → `.claude/commands/` (`~/.claude/commands/`, CLAUDE.md, `.claude/config.json`) |
| 5 | 2 | 3.4 | monolito → microsserviços → plan mode (direto incremental, direto detalhado, trocar depois) |
| 6 | 2 | 3.3 | testes espalhados → `.claude/rules/` com glob (CLAUDE.md raiz, skills, CLAUDE.md por pasta) |
| 7 | 3 | 1.2 | relatório só de artes visuais → decomposição estreita (culpar os subagents) |
| 8 | 3 | 5.3 | timeout da busca → erro estruturado (retry + genérico, vazio = sucesso, abortar) |
| 9 | 3 | 2.3 | síntese verifica fatos 85/15 → `verify_fact` escopada (lote, todas as tools, cache) |
| 10 | 5 | 3.6 | job trava esperando input → `-p` (`CLAUDE_HEADLESS`, `< /dev/null`, `--batch`) |
| 11 | 5 | 4.5 | pre-merge + relatório noturno → batch só no noturno (ambos + polling, nenhum, fallback) |
| 12 | 5 | 4.6/1.6 | PR de 14 arquivos inconsistente → por arquivo + integração (PR menor, modelo maior, consenso) |

## 4. Os 30 task statements

**K** = *Knowledge of*; **S** = *Skills in*. O id `<TS>-<K|S>n` (ex.: `2.3-S4`) é o do campo `bullet` das
questões. Tradução fiel; termos do guia no original. Cada TS traz o módulo que o cobre e os cenários onde
cai no plano. Módulos: M01 `01-exame-e-api` · M02 `02-prompt-engineering` · M03 `03-saida-estruturada` ·
M04 `04-design-de-tools` · M05 `05-mcp-e-tools-nativas` · M06 `06-enforcement-e-escalonamento` · M07
`07-multiagente` · M08 `08-claude-code-config` · M09 `09-claude-code-workflows-ci` · M10
`10-contexto-e-sessoes` · M11 `11-confiabilidade`.

### D1 — Agentic Architecture & Orchestration (27%)

#### 1.1 — Design and implement agentic loops for autonomous task execution
`M01` · C1 C3 C4
- **K1** Ciclo de vida do loop agêntico: enviar o request ao Claude, inspecionar o `stop_reason` (`"tool_use"` vs `"end_turn"`), executar as tools pedidas e devolver os resultados para a próxima iteração.
- **K2** Como os resultados das tools são anexados ao histórico da conversa para o modelo raciocinar sobre a próxima ação.
- **K3** Decisão conduzida pelo modelo (o Claude raciocina, pelo contexto, qual tool chamar a seguir) vs árvores de decisão ou sequências de tools pré-configuradas.
- **S1** Controle de fluxo do loop que continua quando `stop_reason` é `"tool_use"` e termina quando é `"end_turn"`.
- **S2** Adicionar os resultados das tools ao contexto da conversa entre iterações, para o modelo incorporar a nova informação ao raciocínio.
- **S3** Evitar anti-padrões: interpretar sinais em linguagem natural para encerrar o loop, teto arbitrário de iterações como mecanismo **principal** de parada, ou presença de texto do assistant como indicador de conclusão.

**Fatos:** a API não guarda estado: cada request leva o histórico inteiro, com o turno `assistant` (blocos
`tool_use`) seguido da mensagem `user` com os `tool_result` (cada um aponta o `tool_use_id`). Resposta pode
ter texto **e** `tool_use`. `max_tokens` (apêndice) = corte por limite, não conclusão. Teto de iterações só
como rede de segurança. **Distratores:** parar ao ver "done" ou qualquer texto; `max_iterations` como
solução; sequência fixa de tools no código; resultado descartado ou posto no system prompt.

#### 1.2 — Orchestrate multi-agent systems with coordinator-subagent patterns
`M07` · C3 C4
- **K1** Arquitetura hub-and-spoke: o coordenador gerencia toda a comunicação entre subagents, o tratamento de erros e o roteamento de informação.
- **K2** Subagents operam com contexto isolado: não herdam automaticamente o histórico da conversa do coordenador.
- **K3** Papel do coordenador: decompor a tarefa, delegar, agregar resultados e decidir quais subagents invocar conforme a complexidade da consulta.
- **K4** Riscos de decomposição estreita demais pelo coordenador, levando a cobertura incompleta de tópicos amplos de pesquisa.
- **S1** Coordenadores que analisam os requisitos da consulta e escolhem dinamicamente quais subagents invocar, em vez de sempre passar pelo pipeline completo.
- **S2** Particionar o escopo da pesquisa entre subagents para minimizar duplicação (ex.: subtópicos ou tipos de fonte distintos para cada um).
- **S3** Loops de refinamento iterativo: o coordenador avalia a síntese em busca de lacunas, redelega à busca e à análise com consultas direcionadas e reinvoca a síntese até a cobertura bastar.
- **S4** Rotear toda a comunicação dos subagents pelo coordenador, para observabilidade, tratamento de erro consistente e fluxo de informação controlado.

**Fatos:** lacuna no relatório com todos os subagents "funcionando" → olhe o log do coordenador: é a
decomposição (Q7). **Distratores:** culpar subagents que cumpriram o que receberam; subagents falando
direto entre si; pipeline inteiro sempre; uma rodada só, sem checar cobertura.

#### 1.3 — Configure subagent invocation, context passing, and spawning
`M07` · C1 C3 C4
- **K1** A tool `Task` como mecanismo para criar subagents, e a exigência de que `allowedTools` inclua `"Task"` para o coordenador invocá-los.
- **K2** O contexto do subagent tem de ir explícito no prompt: subagents não herdam automaticamente o contexto do pai nem compartilham memória entre invocações.
- **K3** A configuração `AgentDefinition`: descrição, system prompt e restrições de tools de cada tipo de subagent.
- **K4** Gestão de sessão baseada em fork para explorar abordagens divergentes a partir de uma base de análise compartilhada.
- **S1** Incluir os achados completos dos agentes anteriores diretamente no prompt do subagent (ex.: passar os resultados da busca web e da análise de documentos ao subagent de síntese).
- **S2** Formatos de dados estruturados que separam conteúdo de metadados (URL da fonte, nome do documento, página) ao passar contexto entre agentes, preservando a atribuição.
- **S3** Disparar subagents em paralelo emitindo várias chamadas de `Task` numa única resposta do coordenador, e não em turnos separados.
- **S4** Prompts de coordenador que especificam objetivos de pesquisa e critérios de qualidade, em vez de instruções procedurais passo a passo, para os subagents se adaptarem.

**Fatos:** coordenador nunca cria subagents → falta `"Task"` em `allowedTools`. Subagent "não sabe" do
caso → o prompt não levou o contexto. O fork do guia é o `fork_session` (1.7). **Distratores:** "o
subagent herda a conversa"; arquivo/memória comum que ele "lê sozinho"; citar "as restrições combinadas"
sem trazê-las; um `Task` por turno; roteiro rígido no prompt do coordenador.

#### 1.4 — Implement multi-step workflows with enforcement and handoff patterns
`M06` · C1 C4
- **K1** Enforcement programático (hooks, gates de pré-requisito) vs orientação por prompt para a ordem do workflow.
- **K2** Quando a conformidade determinística é exigida (ex.: verificar identidade antes de operações financeiras), instruções de prompt sozinhas têm taxa de falha diferente de zero.
- **K3** Protocolos de handoff estruturado para escalonamento no meio do processo, com dados do cliente, análise de causa raiz e ações recomendadas.
- **S1** Pré-requisitos programáticos que bloqueiam chamadas de tools downstream até os passos anteriores terminarem (ex.: bloquear `process_refund` até `get_customer` devolver um customer ID verificado).
- **S2** Decompor pedidos com várias demandas em itens distintos, investigar cada um em paralelo com contexto compartilhado e sintetizar uma resolução unificada.
- **S3** Compilar resumos de handoff estruturados (customer ID, causa raiz, valor do reembolso, ação recomendada) ao escalar para humanos sem acesso à transcrição.

**Fatos:** "em X% dos casos pula a verificação" + consequência financeira → gate programático (Q1). O
humano não vê o transcript: o resumo tem de se bastar. **Distratores:** prompt mais enfático; few-shot com
a ordem certa; routing classifier que liga subconjuntos de tools; repassar a transcrição; tratar só a 1ª demanda.

#### 1.5 — Apply Agent SDK hooks for tool call interception and data normalization
`M06` · C1 C3 C4
- **K1** Padrões de hook (ex.: `PostToolUse`) que interceptam resultados de tools para transformá-los antes de o modelo processá-los.
- **K2** Padrões de hook que interceptam chamadas de tool de saída para impor regras de compliance (ex.: bloquear reembolsos acima de um limite).
- **K3** Hooks para garantias determinísticas vs instruções de prompt para conformidade probabilística.
- **S1** Hooks `PostToolUse` que normalizam formatos heterogêneos (Unix timestamps, ISO 8601, códigos numéricos de status) de tools MCP diferentes antes de o agente processá-los.
- **S2** Hooks de interceptação de chamada que bloqueiam ações contra a política (ex.: reembolso acima de US$ 500) e redirecionam para workflows alternativos (ex.: escalonamento humano).
- **S3** Escolher hooks em vez de enforcement por prompt quando a regra de negócio exige conformidade garantida.

**Fatos:** no Agent SDK o hook é um callback no código da aplicação, com matcher de tool. A interceptação
(`PreToolUse` na doc) roda antes e pode negar com um motivo que redireciona ("acima de US$ 500: use
`escalate_to_human`"); o `PostToolUse` roda depois e transforma o resultado, inclusive de servidores MCP de
terceiros que você não controla. **Distratores:** regra só no prompt; pedir ao modelo que converta datas;
reescrever servidores de terceiros; validar depois que o reembolso rodou.

#### 1.6 — Design task decomposition strategies for complex workflows
`M07` · C2 C3 C4 C5
- **K1** Quando usar pipelines sequenciais fixos (prompt chaining) vs decomposição dinâmica e adaptativa baseada em descobertas intermediárias.
- **K2** Padrões de prompt chaining que quebram reviews em passos sequenciais (ex.: analisar cada arquivo individualmente e depois rodar um passe de integração entre arquivos).
- **K3** O valor de planos de investigação adaptativos, que geram subtarefas com base no que é descoberto a cada passo.
- **S1** Escolher o padrão de decomposição do workflow: prompt chaining para reviews previsíveis de vários aspectos; decomposição dinâmica para investigações abertas.
- **S2** Dividir code reviews grandes em passes locais por arquivo mais um passe separado de integração entre arquivos, para evitar diluição de atenção.
- **S3** Decompor tarefas abertas (ex.: "adicionar testes abrangentes a uma codebase legada") mapeando a estrutura, identificando áreas de alto impacto e criando um plano priorizado que se adapta conforme surgem dependências.

**Fatos:** passos conhecidos de antemão → chaining; subtarefas que dependem do que se descobre → dinâmica.
Review por arquivo + integração **é** prompt chaining (ver 4.6). **Distratores:** plano fixo completo
antes de explorar; decomposição dinâmica para checklist previsível; passe único sobre tudo.

#### 1.7 — Manage session state, resumption, and forking
`M10` · C2 C3 C4
- **K1** Retomada de sessão nomeada com `--resume <session-name>` para continuar uma conversa anterior específica.
- **K2** `fork_session` para criar ramos independentes a partir de uma base de análise compartilhada e explorar abordagens divergentes.
- **K3** A importância de informar o agente sobre mudanças em arquivos já analisados ao retomar a sessão depois de modificar o código.
- **K4** Por que começar uma sessão nova com resumo estruturado é mais confiável do que retomar com resultados de tools desatualizados.
- **S1** Usar `--resume` com nomes de sessão para continuar investigações nomeadas entre períodos de trabalho.
- **S2** Usar `fork_session` para criar ramos de exploração paralelos (ex.: comparar duas estratégias de teste ou de refatoração a partir da mesma análise da codebase).
- **S3** Escolher entre retomar (contexto anterior majoritariamente válido) e começar do zero com resumos injetados (resultados de tools desatualizados).
- **S4** Informar à sessão retomada as mudanças específicas em arquivos, para reanálise direcionada em vez de reexploração completa.

**Fatos:** contexto vale → `--resume`; mudança pontual → `--resume` + "X e Y mudaram assim"; resultados
velhos em massa → sessão nova + resumo. O fork ramifica a conversa, não o filesystem (doc).
**Distratores:** retomar confiando em tool results velhos; reexplorar tudo; recomeçar quando o contexto
vale; colar o scrollback.

### D2 — Tool Design & MCP Integration (18%)

#### 2.1 — Design effective tool interfaces with clear descriptions and boundaries
`M04` (base no M01) · C1 C3 C4 C6
- **K1** Descrições de tool são o mecanismo principal de seleção de tools pelo LLM; descrições mínimas deixam a seleção pouco confiável entre tools parecidas.
- **K2** A importância de incluir formatos de entrada, consultas de exemplo, casos de borda e explicações de fronteira nas descrições.
- **K3** Como descrições ambíguas ou sobrepostas causam roteamento errado (ex.: `analyze_content` vs `analyze_document` com descrições quase idênticas).
- **K4** O impacto da redação do system prompt na seleção: instruções sensíveis a palavras-chave podem criar associações não intencionais com tools.
- **S1** Descrições que diferenciam claramente propósito, entradas esperadas, saídas e quando usar cada tool em vez de alternativas parecidas.
- **S2** Renomear tools e atualizar descrições para eliminar sobreposição funcional (ex.: `analyze_content` → `extract_web_results`, com descrição específica de web).
- **S3** Dividir tools genéricas em tools de propósito específico com contratos de entrada/saída definidos (ex.: `analyze_document` → `extract_data_points`, `summarize_content` e `verify_claim_against_source`).
- **S4** Revisar system prompts em busca de instruções sensíveis a palavras-chave que possam se sobrepor a descrições de tool bem escritas.

**Fatos:** descrição mínima + tools parecidas → reescrever as descrições é o 1º passo (Q2). Descrições
boas e o erro persiste → procure no system prompt regra do tipo "se disser 'pedido', use X". O guia
**especializa** (renomeia, divide). Few-shot com o porquê é para pedido genuinamente ambíguo (4.2-K2).
**Distratores:** few-shot como 1º passo com descrição mínima; routing layer por palavra-chave; fundir tudo
numa tool genérica.

#### 2.2 — Implement structured error responses for MCP tools
`M04` · C1 C3 C4
- **K1** O padrão da flag `isError` do MCP para comunicar falhas de tool ao agente.
- **K2** Erros transitórios (timeout, serviço indisponível) vs de validação (entrada inválida) vs de negócio (violação de política) vs de permissão.
- **K3** Por que respostas de erro uniformes ("Operation failed" genérico) impedem o agente de decidir a recuperação adequada.
- **K4** Erros retentáveis vs não retentáveis, e como metadados estruturados evitam retries desperdiçados.
- **S1** Devolver metadados de erro estruturados com `errorCategory` (transient/validation/permission), o booleano `isRetryable` e descrição legível por humanos.
- **S2** Incluir `retriable: false` e explicações amigáveis ao cliente em violações de regra de negócio, para o agente se comunicar adequadamente.
- **S3** Recuperação local de erros transitórios dentro dos subagents, propagando ao coordenador só o que não se resolveu localmente, com resultados parciais e o que foi tentado.
- **S4** Distinguir falhas de acesso (exigem decisão de retry) de resultados vazios válidos (consulta bem-sucedida sem correspondência).

**Fatos:** transitório → retry; validação → corrigir a entrada; negócio → explicar a política, sem retry;
permissão → escalar. `isError` é do resultado de tool do MCP; `is_error`, do `tool_result` da Messages
API. **Distratores:** "Operation failed" para tudo; backoff em erro de negócio; `[]` com sucesso quando o
backend caiu; propagar todo transitório.

#### 2.3 — Distribute tools appropriately across agents and configure tool choice
`M04` (K4 no M01) · C1 C3 C4 C6
- **K1** Tools demais num agente (ex.: 18 em vez de 4–5) degradam a confiabilidade da seleção por aumentar a complexidade da decisão.
- **K2** Por que agentes com tools fora da sua especialização tendem a usá-las mal (ex.: agente de síntese tentando buscar na web).
- **K3** Acesso escopado: cada agente só com as tools do seu papel, com tools cruzadas limitadas para necessidades específicas e frequentes.
- **K4** Opções de `tool_choice`: `"auto"`, `"any"` e seleção forçada (`{"type": "tool", "name": "..."}`).
- **S1** Restringir as tools de cada subagent às relevantes para o seu papel, evitando uso indevido fora da especialização.
- **S2** Substituir tools genéricas por alternativas restritas (ex.: `fetch_url` → `load_document`, que valida URLs de documento).
- **S3** Tools cruzadas escopadas para necessidades frequentes (ex.: `verify_fact` para o agente de síntese), com os casos complexos roteados pelo coordenador.
- **S4** `tool_choice` forçado para garantir que uma tool específica seja chamada primeiro (ex.: `extract_metadata` antes das tools de enriquecimento), processando os passos seguintes nos turnos subsequentes.
- **S5** `tool_choice: "any"` para garantir que o modelo chame uma tool em vez de responder com texto conversacional.

**Fatos:** `auto` pode responder texto; `any` obriga a chamar alguma (o modelo escolhe); forçado obriga
aquela. Ordem: forçado no 1º turno, `auto` depois. No request, `"any"` é `{"type": "any"}` (JSON em 4.3).
**Distratores:** todas as tools de busca para a síntese (Q9-C); verificações acumuladas em lote (Q9-B);
"sempre chame `extract_metadata` primeiro" no prompt; melhorar descrições quando o problema são 18 tools.

#### 2.4 — Integrate MCP servers into Claude Code and agent workflows
`M05` · C1 C2 C4
- **K1** Escopo de servidores MCP: projeto (`.mcp.json`) para ferramental compartilhado do time vs usuário (`~/.claude.json`) para servidores pessoais/experimentais.
- **K2** Expansão de variáveis de ambiente no `.mcp.json` (ex.: `${GITHUB_TOKEN}`) para gerenciar credenciais sem commitar segredos.
- **K3** As tools de todos os servidores MCP configurados são descobertas na conexão e ficam disponíveis simultaneamente ao agente.
- **K4** Resources MCP como mecanismo para expor catálogos de conteúdo (ex.: resumos de issues, hierarquias de documentação, schemas de banco) e reduzir chamadas exploratórias de tools.
- **S1** Configurar servidores compartilhados no `.mcp.json` do projeto com expansão de variáveis de ambiente para tokens de autenticação.
- **S2** Configurar servidores pessoais/experimentais no `~/.claude.json` do usuário.
- **S3** Enriquecer as descrições das tools MCP, detalhando capacidades e saídas, para o agente não preferir tools nativas (como Grep) a tools MCP mais capazes.
- **S4** Preferir servidores MCP da comunidade a implementações próprias em integrações padrão (ex.: Jira), reservando servidores customizados para workflows específicos do time.
- **S5** Expor catálogos de conteúdo como resources MCP, dando ao agente visibilidade dos dados disponíveis sem chamadas exploratórias.

```jsonc
// .mcp.json na raiz do repositório (versionado: o time recebe ao clonar)
{ "mcpServers": { "jira": { "command": "npx", "args": ["-y", "<servidor-jira-da-comunidade>"],
    "env": { "JIRA_TOKEN": "${JIRA_TOKEN}" } } } }   // ← AQUI: expandido do ambiente de cada dev
```
**Fatos:** resource = catálogo para ler/descobrir; tool = ação. **Distratores:** token literal no
`.mcp.json`; servidor do time no `~/.claude.json` de cada dev; servidor experimental no `.mcp.json`;
servidor próprio para Jira; tool `list_catalog` chamada a cada sessão; "sempre use MCP" no prompt ou negar
Grep em vez de melhorar a descrição; "alternar o servidor ativo".

#### 2.5 — Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively
`M05` · C2 C4
- **K1** Grep para busca de conteúdo (padrões dentro de arquivos: nomes de função, mensagens de erro, imports).
- **K2** Glob para casar padrões de caminho (achar arquivos por nome ou extensão).
- **K3** Read/Write para operações em arquivo inteiro; Edit para modificações pontuais por casamento de texto único.
- **K4** Quando o Edit falha por texto não único, Read + Write como fallback confiável.
- **S1** Escolher Grep para buscar conteúdo na codebase (ex.: todos os chamadores de uma função, mensagens de erro).
- **S2** Escolher Glob para achar arquivos por padrão de nome (ex.: `**/*.test.tsx`).
- **S3** Read para carregar o conteúdo completo e depois Write quando o Edit não acha uma âncora única.
- **S4** Entender a codebase de forma incremental: Grep para achar pontos de entrada, depois Read para seguir imports e rastrear fluxos, em vez de ler todos os arquivos de antemão.
- **S5** Rastrear o uso de funções através de módulos wrapper: identificar primeiro todos os nomes exportados e depois buscar cada nome na codebase.

**Distratores:** ler tudo antes de começar; Glob para achar texto; repetir o Edit com a mesma âncora;
`sed` em todas as ocorrências; buscar só o nome original quando o wrapper reexporta com outro.

### D3 — Claude Code Configuration & Workflows (20%)

#### 3.1 — Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization
`M08` · C2 C4 C5
- **K1** Hierarquia do CLAUDE.md: usuário (`~/.claude/CLAUDE.md`), projeto (`.claude/CLAUDE.md` ou `CLAUDE.md` na raiz) e diretório (CLAUDE.md em subdiretórios).
- **K2** Configuração de usuário vale só para aquele usuário: o que está em `~/.claude/CLAUDE.md` não chega aos colegas via controle de versão.
- **K3** A sintaxe `@import` para referenciar arquivos externos e manter o CLAUDE.md modular (ex.: importar os padrões relevantes para cada pacote).
- **K4** O diretório `.claude/rules/` para organizar regras por tema, como alternativa a um CLAUDE.md monolítico.
- **S1** Diagnosticar problemas de hierarquia (ex.: dev novo não recebe as instruções porque estão no nível de usuário, não no de projeto).
- **S2** `@import` para incluir seletivamente os padrões relevantes no CLAUDE.md de cada pacote, conforme o conhecimento de domínio de quem o mantém.
- **S3** Dividir CLAUDE.md grandes em arquivos temáticos em `.claude/rules/` (ex.: `testing.md`, `api-conventions.md`, `deployment.md`).
- **S4** O comando `/memory` para verificar quais arquivos de memória estão carregados e diagnosticar comportamento inconsistente entre sessões.

**Distratores:** cada dev copiar as regras para o próprio `~/.claude/CLAUDE.md`; tudo no CLAUDE.md raiz;
importar todos os padrões no raiz (não é seletivo); reiniciar a sessão em vez de checar com `/memory`.

#### 3.2 — Create and configure custom slash commands and skills
`M08` · C2 C4 C5
- **K1** Comandos de projeto em `.claude/commands/` (compartilhados via controle de versão) vs comandos de usuário em `~/.claude/commands/` (pessoais).
- **K2** Skills em `.claude/skills/` com `SKILL.md` e frontmatter que aceita `context: fork`, `allowed-tools` e `argument-hint`.
- **K3** `context: fork` roda a skill num contexto isolado de sub-agent, impedindo que a saída dela polua a conversa principal.
- **K4** Customização pessoal: variantes em `~/.claude/skills/` com nomes diferentes, para não afetar os colegas.
- **S1** Criar slash commands de projeto em `.claude/commands/` para o time inteiro via controle de versão.
- **S2** `context: fork` para isolar da sessão principal skills de saída verbosa (ex.: análise da codebase) ou de contexto exploratório (ex.: brainstorming de alternativas).
- **S3** `allowed-tools` no frontmatter para restringir as tools durante a skill (ex.: só operações de escrita de arquivo, evitando ações destrutivas).
- **S4** `argument-hint` no frontmatter para pedir aos devs os parâmetros obrigatórios quando invocam a skill sem argumentos.
- **S5** Escolher entre skills (sob demanda, workflows de tarefa específica) e CLAUDE.md (padrões universais, sempre carregados).

**Distratores:** `~/.claude/commands/` para o time; comando definido no CLAUDE.md; `.claude/config.json`
(não existe); editar a skill do time em vez de criar variante com outro nome; workflow raro no CLAUDE.md;
skill verbosa sem `context: fork`.

#### 3.3 — Apply path-specific rules for conditional convention loading
`M08` · C2 C5
- **K1** Arquivos em `.claude/rules/` com frontmatter YAML `paths` (padrões glob) para ativação condicional das regras.
- **K2** Regras com escopo de caminho carregam só ao editar arquivos que casam, reduzindo contexto irrelevante e tokens.
- **K3** Vantagem das regras por glob sobre CLAUDE.md de diretório para convenções que atravessam diretórios (ex.: testes espalhados pela codebase).
- **S1** Criar arquivos em `.claude/rules/` com escopo no frontmatter YAML (ex.: `paths: ["terraform/**/*"]`) que só carregam ao editar arquivos que casam.
- **S2** Globs em regras por caminho para aplicar convenções por tipo de arquivo, em qualquer diretório (ex.: `**/*.test.tsx` para todos os testes).
- **S3** Preferir regras por caminho a CLAUDE.md de subdiretório quando a convenção vale para arquivos espalhados pela codebase.

**Distratores:** tudo no CLAUDE.md raiz "para o Claude inferir"; CLAUDE.md por pasta (preso ao diretório);
skill por tipo de código (exige invocação); regra sem `paths` (carrega sempre).

#### 3.4 — Determine when to use plan mode vs direct execution
`M08` · C2 C4
- **K1** Plan mode é feito para tarefas complexas: mudanças em larga escala, várias abordagens válidas, decisões arquiteturais, modificações em vários arquivos.
- **K2** Execução direta serve para mudanças simples e bem delimitadas (ex.: uma checagem de validação numa função).
- **K3** Plan mode permite explorar a codebase e desenhar com segurança antes de se comprometer com mudanças, evitando retrabalho caro.
- **K4** O subagent Explore isola a saída verbosa de descoberta e devolve resumos, preservando o contexto da conversa principal.
- **S1** Plan mode para tarefas com implicações arquiteturais (ex.: reestruturar em microsserviços, migração de biblioteca em 45+ arquivos, escolher entre integrações com requisitos de infraestrutura diferentes).
- **S2** Execução direta para mudanças bem entendidas e de escopo claro (ex.: bug num único arquivo com stack trace claro, condicional de validação de data).
- **S3** Explore em fases de descoberta verbosas, para não esgotar a janela de contexto em tarefas de várias fases.
- **S4** Combinar plan mode para investigar e execução direta para implementar (ex.: planejar a migração da biblioteca e depois executá-la).

**Distratores:** começar direto e "deixar a estrutura emergir"; trocar para plan mode só se complicar
(a complexidade já foi declarada, Q5); direto com instruções detalhadas sem explorar; plan mode para fix trivial.

#### 3.5 — Apply iterative refinement techniques for progressive improvement
`M09` · C2 C4
- **K1** Exemplos concretos de entrada/saída são o jeito mais eficaz de comunicar a transformação esperada quando descrições em prosa são interpretadas de forma inconsistente.
- **K2** Iteração guiada por testes: escrever as suítes primeiro e iterar compartilhando as falhas para guiar a melhoria progressiva.
- **K3** Padrão de entrevista: o Claude pergunta para revelar considerações que o dev talvez não tenha previsto, antes de implementar.
- **K4** Quando mandar todos os problemas numa mensagem só (problemas que interagem) vs corrigi-los em sequência (independentes).
- **S1** Dar 2–3 exemplos concretos de entrada/saída para esclarecer a transformação quando descrições em linguagem natural dão resultados inconsistentes.
- **S2** Escrever, antes da implementação, suítes de teste com comportamento esperado, casos de borda e requisitos de performance, e iterar compartilhando as falhas.
- **S3** Usar a entrevista para levantar considerações de design (ex.: estratégia de invalidação de cache, modos de falha) antes de implementar em domínios desconhecidos.
- **S4** Dar casos de teste específicos, com entrada e saída esperada, para corrigir o tratamento de casos de borda (ex.: valores nulos em scripts de migração).
- **S5** Tratar numa mensagem detalhada problemas cujas correções interagem, e iterar em sequência os independentes.

**Distratores:** prosa mais longa em vez de exemplos; corrigir um a um problemas acoplados; juntar
independentes num pedido só; implementar primeiro e perguntar depois em domínio desconhecido.

#### 3.6 — Integrate Claude Code into CI/CD pipelines
`M09` · C5
- **K1** A flag `-p` (ou `--print`) roda o Claude Code em modo não interativo em pipelines automatizados.
- **K2** As flags `--output-format json` e `--json-schema` para impor saída estruturada no CI.
- **K3** O CLAUDE.md como mecanismo para dar contexto de projeto (padrões de teste, convenções de fixtures, critérios de review) ao Claude Code invocado no CI.
- **K4** Isolamento de contexto de sessão: a mesma sessão que gerou o código revisa as próprias mudanças pior do que uma instância de review independente.
- **S1** Rodar o Claude Code no CI com `-p` para não travar esperando input interativo.
- **S2** `--output-format json` com `--json-schema` para achados estruturados, legíveis por máquina, postados automaticamente como comentários inline no PR.
- **S3** Ao rodar de novo após novos commits, incluir os achados do review anterior e instruir o Claude a reportar só problemas novos ou ainda não resolvidos, evitando comentários duplicados.
- **S4** Dar os arquivos de teste existentes no contexto, para a geração de testes não sugerir cenários já cobertos pela suíte.
- **S5** Documentar no CLAUDE.md padrões de teste, critérios de teste valioso e fixtures disponíveis, para melhorar os testes gerados e reduzir saída de baixo valor.

**Fatos:** `claude -p "<prompt>" --output-format json --json-schema '<schema>'` → o CI lê o JSON e posta
os comentários no PR. **Distratores:** `CLAUDE_HEADLESS=true`, `--batch` (não existem); `< /dev/null`;
regex sobre texto livre; "não repita comentários" sem passar os achados anteriores; revisar na sessão que gerou.

### D4 — Prompt Engineering & Structured Output (20%)

#### 4.1 — Design prompts with explicit criteria to improve precision and reduce false positives
`M02` · C1 C5 C6
- **K1** Critérios explícitos em vez de instruções vagas (ex.: "sinalize comentários só quando o comportamento alegado contradiz o comportamento real do código" vs "verifique se os comentários estão corretos").
- **K2** Instruções gerais como "seja conservador" ou "reporte só achados de alta confiança" não melhoram a precisão tanto quanto critérios categóricos específicos.
- **K3** Impacto dos falsos positivos na confiança dos devs: categorias muito ruidosas minam a confiança nas categorias precisas.
- **S1** Critérios de review específicos que definem o que reportar (bugs, segurança) e o que ignorar (estilo menor, padrões locais), em vez de filtrar por confiança.
- **S2** Desligar temporariamente categorias com muitos falsos positivos para restaurar a confiança dos devs enquanto os prompts delas melhoram.
- **S3** Critérios explícitos de severidade, com exemplos concretos de código para cada nível, para classificação consistente.

**Distratores:** "be conservative"/"only high-confidence"; filtrar por `confidence ≥ 0.8`; segundo modelo
validando cada achado; manter a categoria ruidosa e pedir que os devs a ignorem; severidade só com adjetivos.

#### 4.2 — Apply few-shot prompting to improve output consistency and quality
`M02` · C1 C5 C6
- **K1** Few-shot é a técnica mais eficaz para saída consistente e acionável quando instruções detalhadas sozinhas dão resultados inconsistentes.
- **K2** Few-shot demonstra o tratamento de casos ambíguos (ex.: seleção de tool para pedidos ambíguos, lacunas de cobertura de teste no nível de branch).
- **K3** Few-shot permite ao modelo generalizar o julgamento para padrões novos, em vez de casar só os casos pré-especificados.
- **K4** Few-shot reduz alucinação em extração (ex.: medidas informais, estruturas de documento variadas).
- **S1** Criar 2–4 exemplos direcionados para cenários ambíguos, mostrando o raciocínio de por que uma ação foi escolhida em vez de alternativas plausíveis.
- **S2** Exemplos que demonstram o formato de saída desejado (localização, problema, severidade, correção sugerida), para consistência.
- **S3** Exemplos que distinguem padrões de código aceitáveis de problemas reais, reduzindo falsos positivos sem impedir a generalização.
- **S4** Few-shot para o tratamento de estruturas de documento variadas (citações inline vs bibliografias, seções de metodologia vs detalhes embutidos no texto).
- **S5** Exemplos de extração correta em documentos de formatos variados para resolver extração vazia/nula de campos obrigatórios.

**Distratores:** dezenas de exemplos genéricos; só o caso fácil; mais instrução em prosa; enumerar todos
os casos permitidos (não generaliza); few-shot para compensar descrição de tool mínima (Q2-A).

#### 4.3 — Enforce structured output using tool use and JSON schemas
`M03` (K1/K2 no M01) · C5 C6
- **K1** Tool use (`tool_use`) com JSON schema é a abordagem mais confiável para saída garantidamente conforme ao schema, sem erros de sintaxe JSON.
- **K2** `tool_choice: "auto"` (pode devolver texto em vez de chamar tool) vs `"any"` (tem de chamar uma tool, mas escolhe qual) vs forçado (tem de chamar a tool nomeada).
- **K3** Schemas estritos via tool use eliminam erros de sintaxe, mas não erros semânticos (ex.: itens que não somam o total, valor no campo errado).
- **K4** Desenho de schema: campos obrigatórios vs opcionais; enums com `"other"` + string de detalhe para categorias extensíveis.
- **S1** Definir tools de extração com JSON schema como parâmetros de entrada e extrair os dados estruturados da resposta `tool_use`.
- **S2** `tool_choice: "any"` para garantir saída estruturada quando há vários schemas de extração e o tipo de documento é desconhecido.
- **S3** Forçar uma tool com `tool_choice: {"type": "tool", "name": "extract_metadata"}` para que uma extração específica rode antes das etapas de enriquecimento.
- **S4** Campos opcionais (nullable) quando o documento pode não conter a informação, para o modelo não inventar valores só para preencher campos obrigatórios.
- **S5** Valores de enum como `"unclear"` para casos ambíguos e campos `"other"` + detalhe para categorização extensível.
- **S6** Regras de normalização de formato no prompt, junto com schemas estritos, para lidar com formatação inconsistente na fonte.

```jsonc
// POST /v1/messages (corpo do request)
{
  "model": "claude-...", "max_tokens": 1024,
  "tools": [{
    "name": "extract_metadata",
    "description": "Extrai metadados da fatura. Use antes de qualquer enriquecimento.",
    "strict": true,                                        // ← strict mode: sem erro de sintaxe/schema
    "input_schema": {                                      // ← o schema da SAÍDA desejada
      "type": "object",
      "properties": {
        "vendor":          { "type": "string" },
        "po_number":       { "type": ["string", "null"] }, // ← nullable: pode faltar no documento
        "category":        { "type": "string", "enum": ["utilities", "rent", "other", "unclear"] },
        "category_detail": { "type": ["string", "null"] }  // ← detalhe quando "other"
      },
      "required": ["vendor", "po_number", "category", "category_detail"],
      "additionalProperties": false
    }
  }],
  "tool_choice": { "type": "tool", "name": "extract_metadata" }, // ← AQUI: forçada no 1º turno
  // ou { "type": "any" } (alguma tool) · { "type": "auto" } (pode responder texto)
  "messages": [{ "role": "user", "content": "<documento>" }]
}
// resposta: stop_reason "tool_use"; os dados vêm em content[i].input → validação → sistema downstream
```
**Distratores:** "responda só em JSON" no prompt; regex sobre texto; tudo `required` sem null; enum
fechado sem `other`/`unclear`; achar que o schema garante somas certas; `auto` quando é preciso garantir a chamada.

#### 4.4 — Implement validation, retry, and feedback loops for extraction quality
`M03` · C5 C6
- **K1** Retry com feedback de erro: anexar ao prompt, no retry, os erros de validação específicos para guiar a correção.
- **K2** Limites do retry: é ineficaz quando a informação simplesmente não está no documento-fonte (diferente de erro de formato ou de estrutura).
- **K3** Feedback loop: registrar quais construções de código disparam achados (campo `detected_pattern`) para analisar sistematicamente os padrões de descarte.
- **K4** Erros de validação semântica (valores que não somam, campo no lugar errado) vs erros de sintaxe de schema (eliminados pelo tool use).
- **S1** Requests de follow-up com o documento original, a extração que falhou e os erros de validação específicos, para a autocorreção do modelo.
- **S2** Identificar quando o retry será ineficaz (ex.: a informação só existe num documento externo não fornecido) e quando funciona (descompasso de formato, erro estrutural de saída).
- **S3** Campos `detected_pattern` nos achados estruturados para analisar padrões de falso positivo quando os devs descartam achados.
- **S4** Fluxos de validação com autocorreção: extrair `"calculated_total"` junto de `"stated_total"` para sinalizar discrepâncias e booleanos `"conflict_detected"` para dados inconsistentes na fonte.

**Fatos:** Pydantic ou JSON Schema validam e o erro específico volta no retry. Dado ausente ou externo →
`null` + sinalizar, sem retry. **Distratores:** mesmo prompt ou "try again" genérico; insistir no retry
para dado inexistente; corrigir o total em silêncio; mandar o erro sem o documento.

#### 4.5 — Design efficient batch processing strategies
`M03` · C5 C6
- **K1** Message Batches API: 50% de economia, janela de processamento de até 24 horas, sem SLA de latência garantido.
- **K2** Lote serve para cargas não bloqueantes e tolerantes a latência (relatório noturno, auditoria semanal, geração noturna de testes), não para workflows bloqueantes (checagem pré-merge).
- **K3** A Batch API não suporta tool calling multi-turn num único request (não dá para executar tools no meio do request e devolver resultados).
- **K4** Campos `custom_id` para correlacionar os pares request/response do lote.
- **S1** Casar a API com a latência exigida: síncrona para checagens pré-merge bloqueantes, Batch para análises noturnas/semanais.
- **S2** Calcular a frequência de submissão a partir do SLA (ex.: janelas de 4 h para garantir SLA de 30 h com processamento de até 24 h).
- **S3** Tratar falhas reenviando só os documentos que falharam (pelo `custom_id`), com as modificações adequadas (ex.: dividir em chunks os que estouraram o limite de contexto).
- **S4** Refinar o prompt numa amostra antes de processar grandes volumes, maximizando o sucesso na primeira passada e reduzindo custos de reenvio.

**Fatos:** pior caso = esperar a próxima submissão + 24 h ⇒ intervalo ≤ SLA − 24 h (30 h → até 6 h; 4 h dá
folga). Conclusão por polling. **Distratores:** batch no pre-merge "com polling" ou "com fallback
síncrono"; "síncrono por causa da ordem dos resultados"; reenviar o lote todo; reenviar sem quebrar o
documento grande.

#### 4.6 — Design multi-instance and multi-pass review architectures
`M09` · C2 C5
- **K1** Limite da autorrevisão: o modelo retém o contexto de raciocínio da geração e fica menos propenso a questionar as próprias decisões na mesma sessão.
- **K2** Instâncias de review independentes (sem o raciocínio anterior) pegam problemas sutis melhor que instruções de autorrevisão ou extended thinking.
- **K3** Review multi-pass: passes locais por arquivo + passes de integração entre arquivos, contra diluição de atenção e achados contraditórios.
- **S1** Uma segunda instância independente do Claude revisa o código gerado, sem o contexto de raciocínio do gerador.
- **S2** Dividir reviews grandes em passes focados por arquivo (problemas locais) e passes de integração separados (fluxo de dados entre arquivos).
- **S3** Passes de verificação em que o modelo autodeclara a confiança junto de cada achado, para permitir roteamento calibrado da revisão.

**Fatos:** aqui a confiança por achado é **certa** (§3, desempate 12). **Distratores:** "revise com rigor"
na mesma sessão; extended thinking na mesma sessão; modelo/janela maior num passe; 3 passes com consenso;
exigir PRs menores.

### D5 — Context Management & Reliability (15%)

#### 5.1 — Manage conversation context to preserve critical information across long interactions
`M10` (K4 no M01) · C1 C3 C6
- **K1** Riscos da sumarização progressiva: valores numéricos, percentuais, datas e expectativas declaradas pelo cliente condensados em resumos vagos.
- **K2** Efeito "lost in the middle": modelos processam bem o início e o fim de entradas longas, mas podem omitir achados das seções do meio.
- **K3** Resultados de tools se acumulam no contexto e consomem tokens desproporcionais à relevância (ex.: 40+ campos por consulta de pedido quando 5 importam).
- **K4** A importância de enviar o histórico completo da conversa nos requests seguintes para manter a coerência conversacional.
- **S1** Extrair fatos transacionais (valores, datas, números de pedido, status) para um bloco persistente de "case facts" incluído em todo prompt, fora do histórico resumido.
- **S2** Extrair e persistir dados estruturados por problema (IDs de pedido, valores, status) numa camada de contexto separada em sessões com vários problemas.
- **S3** Aparar saídas verbosas de tools para só os campos relevantes antes que se acumulem (ex.: só os campos relevantes para devolução nas consultas de pedido).
- **S4** Pôr resumos dos achados-chave no início de entradas agregadas e organizar os detalhes com cabeçalhos de seção explícitos, contra efeitos de posição.
- **S5** Exigir que subagents incluam metadados (datas, localização da fonte, contexto metodológico) nas saídas estruturadas, para uma síntese downstream precisa.
- **S6** Fazer agentes upstream devolverem dados estruturados (fatos-chave, citações, scores de relevância) em vez de conteúdo verboso e cadeias de raciocínio quando os downstream têm pouco orçamento de contexto.

**Fatos:** "o bot esquece o que o cliente disse dois turnos atrás" → o código não manda o histórico
completo. **Distratores:** janela ou modelo maior; resumir mais agressivamente; pedir que o cliente
repita; manter os 40 campos "para não perder nada"; achado crítico no meio do documento.

#### 5.2 — Design effective escalation and ambiguity resolution patterns
`M06` · C1
- **K1** Gatilhos adequados de escalonamento: o cliente pede humano, exceções/lacunas de política (não só casos complexos), incapacidade de avançar de forma significativa.
- **K2** Escalar de imediato quando o cliente exige explicitamente vs oferecer resolver quando o problema é simples.
- **K3** Por que escalonamento por sentimento e scores de confiança autodeclarados são proxies pouco confiáveis da complexidade real do caso.
- **K4** Várias correspondências de cliente exigem esclarecimento (pedir identificadores adicionais), não seleção por heurística.
- **S1** Critérios explícitos de escalonamento com exemplos few-shot no system prompt, mostrando quando escalar e quando resolver de forma autônoma.
- **S2** Atender de imediato pedidos explícitos de humano, sem tentar investigar antes.
- **S3** Reconhecer a frustração e oferecer resolução quando o problema está ao alcance do agente, escalando só se o cliente reiterar a preferência.
- **S4** Escalar quando a política é ambígua ou omissa sobre o pedido (ex.: igualar o preço do concorrente quando a política só trata de ajustes no próprio site).
- **S5** Instruir o agente a pedir identificadores adicionais quando as tools devolvem várias correspondências, em vez de escolher por heurística.

**Fatos:** escalonamento descalibrado → critérios + few-shot é o 1º passo (Q3). Frustrado, caso simples,
sem pedir humano → reconhece e oferece resolver; se reiterar → escala. **Distratores:** confiança 1–10
com limiar; sentimento; classificador treinado em tickets; investigar antes de transferir quem pediu
humano; escolher o cliente "mais provável"; decidir por analogia quando a política é omissa.

#### 5.3 — Implement error propagation strategies across multi-agent systems
`M11` · C1 C3 C4
- **K1** Contexto de erro estruturado (tipo de falha, consulta tentada, resultados parciais, alternativas) é o que permite ao coordenador decidir a recuperação com inteligência.
- **K2** Falhas de acesso (timeouts que exigem decisão de retry) vs resultados vazios válidos (consultas bem-sucedidas sem correspondência).
- **K3** Status de erro genéricos ("search unavailable") escondem do coordenador um contexto valioso.
- **K4** Suprimir erros em silêncio (vazio como sucesso) e encerrar o workflow inteiro por uma falha isolada são, ambos, anti-padrões.
- **S1** Devolver contexto de erro estruturado com tipo de falha, o que foi tentado, resultados parciais e alternativas possíveis, para a recuperação pelo coordenador.
- **S2** Distinguir falha de acesso de resultado vazio válido no relato de erro, para o coordenador decidir adequadamente.
- **S3** Subagents com recuperação local para falhas transitórias, propagando só o que não resolvem, com o que foi tentado e os resultados parciais.
- **S4** Saída da síntese com anotações de cobertura: quais achados estão bem sustentados e quais áreas têm lacunas por fontes indisponíveis.

**Fatos:** com erro estruturado o coordenador repete com outra consulta, tenta alternativa ou segue com
o parcial anotando a lacuna (Q8). **Distratores:** backoff e status genérico; timeout virando lista
vazia; exceção que derruba tudo; relatório que não diz o que faltou.

#### 5.4 — Manage context effectively in large codebase exploration
`M10` · C2 C4
- **K1** Degradação de contexto em sessões longas: respostas inconsistentes e citações de "padrões típicos" em vez das classes específicas descobertas antes.
- **K2** Arquivos de scratchpad para persistir achados-chave através de fronteiras de contexto.
- **K3** Delegação a subagents para isolar a saída verbosa de exploração enquanto o agente principal coordena o entendimento de alto nível.
- **K4** Persistência estruturada de estado para recuperar de crash: cada agente exporta o estado para um local conhecido e o coordenador carrega um manifesto ao retomar.
- **S1** Disparar subagents para perguntas específicas (ex.: "achar todos os arquivos de teste", "rastrear as dependências do fluxo de reembolso") enquanto o principal mantém a coordenação de alto nível.
- **S2** Agentes mantêm scratchpads com os achados-chave e os consultam nas perguntas seguintes, contra a degradação de contexto.
- **S3** Resumir os achados de uma fase de exploração antes de disparar os subagents da fase seguinte, injetando os resumos no contexto inicial deles.
- **S4** Recuperação de crash com exportações estruturadas de estado (manifestos) que o coordenador carrega ao retomar e injeta nos prompts dos agentes.
- **S5** Usar `/compact` para reduzir o contexto em explorações longas quando ele se enche de saída verbosa de descoberta.

**Fatos:** `/compact` **substitui** o histórico por um resumo; valores exatos podem se perder, então o que
importa vai antes para o scratchpad. **Distratores:** janela maior; reler a codebase a cada pergunta;
reexplorar tudo após crash; confiar no histórico compactado para valores exatos.

#### 5.5 — Design human review workflows and confidence calibration
`M11` · C6
- **K1** Métricas agregadas de acurácia (ex.: 97% no geral) podem mascarar desempenho ruim em tipos de documento ou campos específicos.
- **K2** Amostragem aleatória estratificada para medir a taxa de erro das extrações de alta confiança e detectar padrões de erro novos.
- **K3** Scores de confiança por campo, calibrados com conjuntos de validação rotulados, para direcionar a atenção da revisão.
- **K4** A importância de validar a acurácia por tipo de documento e segmento de campo antes de automatizar extrações de alta confiança.
- **S1** Amostragem aleatória estratificada das extrações de alta confiança para medir continuamente a taxa de erro e detectar padrões novos.
- **S2** Analisar a acurácia por tipo de documento e por campo, verificando desempenho consistente em todos os segmentos antes de reduzir a revisão humana.
- **S3** O modelo emite scores de confiança por campo; os limiares de revisão são calibrados com conjuntos de validação rotulados.
- **S4** Encaminhar à revisão humana extrações com baixa confiança ou com documentos-fonte ambíguos/contraditórios, priorizando a capacidade limitada dos revisores.

**Fatos:** a amostragem estratificada sorteia **o que passa sem revisão** (alta confiança), por tipo e
campo, para medir o erro invisível. **Não** é "revisar 20/10/5% por faixa de risco". **Distratores:**
confiar nos 97%; limiar arbitrário sem calibração; parar de revisar acima do limiar sem amostrar;
revisar 100%; média das confianças do documento.

#### 5.6 — Preserve information provenance and handle uncertainty in multi-source synthesis
`M11` · C3 C6
- **K1** A atribuição de fonte se perde na sumarização quando os achados são comprimidos sem preservar o mapeamento afirmação→fonte.
- **K2** Mapeamentos estruturados afirmação→fonte que o agente de síntese tem de preservar e mesclar ao combinar achados.
- **K3** Estatísticas conflitantes de fontes confiáveis: anotar o conflito com a atribuição de fonte em vez de escolher um valor arbitrariamente.
- **K4** Dados temporais: exigir datas de publicação/coleta nas saídas estruturadas para que diferenças de época não sejam lidas como contradições.
- **S1** Subagents emitem mapeamentos estruturados afirmação→fonte (URLs, nomes de documento, trechos relevantes) que os agentes downstream preservam na síntese.
- **S2** Relatórios com seções explícitas que separam achados bem estabelecidos de contestados, preservando as caracterizações originais das fontes e o contexto metodológico.
- **S3** Concluir a análise de documentos com os valores conflitantes incluídos e anotados, deixando o coordenador decidir como reconciliar antes da síntese.
- **S4** Subagents incluem datas de publicação ou de coleta nas saídas estruturadas, para a interpretação temporal correta.
- **S5** Apresentar cada tipo de conteúdo de forma adequada na síntese (financeiro em tabelas, notícias em prosa, achados técnicos em listas estruturadas), sem converter tudo para um formato uniforme.

**Distratores:** tirar a média; escolher em silêncio a fonte mais recente; descartar as duas; o analista
de documentos reconciliar sozinho; resumo em prosa sem fontes; formato único para tudo.

## 5. Divergências guia × doc atual

Cada linha vira, na teoria, a caixa `> **Na doc atual [volátil]:**`. Nenhuma questão depende dela.

| Tema | Guia = resposta de prova | Doc atual [volátil] |
|---|---|---|
| `tool_choice` `"any"`/forçado | corretos (2.3, 4.3) | Opus 5.5, Sonnet 5.5, Fable 5.1 e Mythos 5.1 retornam 400; thinking manual também restringe |
| Saída estruturada | `tool_use` + JSON schema (+ `tool_choice`) | também há structured outputs (`output_config.format` no request) |
| Tool que cria subagents | `Task`; `allowedTools` inclui `"Task"` | renomeada `Agent` (alias `Task`); `allowedTools` = auto-aprovação |
| Slash commands | `.claude/commands/` (time) e `~/.claude/commands/` (pessoal) | fundidos em skills; `.claude/commands/` segue funcionando |
| `allowed-tools` (skill) | **restringe** as tools da skill | pré-aprova; quem restringe é `disallowed-tools` |
| `argument-hint` | pede os parâmetros obrigatórios | dica exibida no autocomplete |
| Memória carregada | `/memory` | `/memory` lista e abre; o que carregou no início está em `/context` |
| Edit com âncora não única | Read + Write | âncora mais longa ou `replace_all` |
| Grep / Glob | busca de conteúdo / de caminho | fora do conjunto padrão no macOS, Linux e WSL (busca via Bash) |
| MCP pessoal/experimental | user-level `~/.claude.json` (time: `.mcp.json`) | escopo padrão do `claude mcp add` é `local` (também em `~/.claude.json`) |
| Tools de vários servidores MCP | todas disponíveis ao mesmo tempo | tool search / carga sob demanda é padrão no Claude Code |
| Batch + tools | sem tool calling multi-turn num request | server tools rodam no batch; client tools não |
| Consolidar tools | especializar primeiro; consolidar não é 1º passo | define-tools sugere juntar operações afins (`action`) |
| CLAUDE.md no CI | mecanismo de contexto de projeto | `--bare` pula o CLAUDE.md |
| Fork | `fork_session` (ramo de sessão) | SDK: `fork_session=True`/`forkSession: true` com `resume`; "fork subagent" do Claude Code é outro conceito |

**Erros do material antigo (não repetir):** "`/compact` preserva as mensagens recentes" (ele **substitui**
a conversa por um resumo; a doc recarrega do disco system prompt, CLAUDE.md da raiz, rules sem `paths` e
alguns arquivos recentes [volátil]) · "Streamable HTTP é o único remoto com OAuth" (HTTP e SSE têm OAuth;
e OAuth é out-of-scope) · "`any`/forçado retornam 400" como regra de prova · "confiança autodeclarada é
sempre inútil" · "amostragem estratificada = taxas de revisão por faixa de risco" · TS 2.6, 3.0, 4.7, 4.8,
5.7, 5.8 · vocabulário do "Building Effective Agents"
(routing, voting, evaluator-optimizer) como matéria de prova (no guia, routing e votação são
**distratores**) · "`tool_result` em mensagens `user` separadas faz a API rejeitar" (turnos `user` seguidos
são combinados; o 400 vem de `tool_use` sem `tool_result`).

## 6. Escopo oficial (seção 17)

**Fora do escopo — não cai** e nunca pode decidir uma questão: fine-tuning ou treino de modelos;
autenticação, billing e gestão de conta da API; implementação detalhada de linguagens ou frameworks (além
do necessário para configurar tools e schemas); deploy e hospedagem de MCP servers (infra, rede,
containers); arquitetura interna, treino e pesos do Claude; Constitutional AI, RLHF e safety training;
embeddings e vector databases; computer use; vision; streaming e server-sent events; rate limiting,
quotas e cálculo de preço; OAuth, rotação de API key e protocolos de autenticação; configuração de cloud
providers (AWS, GCP, Azure); benchmarks e comparação de modelos; detalhes de prompt caching (só saber que
existe); contagem de tokens e tokenização.

**Extras da doc atual que o guia não lista (não caem; no máximo 1–3 linhas de contexto, nunca questão):**
- API: adaptive thinking, `effort`, sampling e prefill retornando 400, task budgets, structured outputs,
  `tool_choice: "none"`, `disable_parallel_tool_use`, `stop_reason` `refusal`/`pause_turn`/
  `model_context_window_exceeded`, context editing e compaction da API, memory tool, tool search e
  `defer_loading`, programmatic tool calling, server tools, MCP connector, Tool Runner, Managed Agents.
- MCP: transportes em detalhe, JSON-RPC, sampling/elicitation/roots, `headersHelper`, escopos `local` e `managed`.
- Claude Code: `CLAUDE.local.md`, `AGENTS.md`, auto memory, managed policy, settings e permissões em
  detalhe, modos além de plan, `.claude/agents/`, fork subagent, plugins, routines, `/loop`, flags de CLI
  além de `-p`/`--print`, `--output-format json`, `--json-schema` e `--resume`.
- Padrões: routing/evaluator-optimizer/voting do "Building Effective Agents", evals e LLM-as-judge,
  números voláteis (subagents simultâneos, limites de saída de MCP).
