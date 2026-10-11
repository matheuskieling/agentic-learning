# Blueprint do exame CCAR-F — base de conhecimento do curso

Referência condensada do **Claude Certified Architect – Foundations**: domínios, task statements,
fatos-chave e anti-padrões. **Todo conteúdo do curso (teoria, quizzes, provas, simulados) deve ser
coerente com este arquivo.**

> **Fontes:** guias de estudo não oficiais que reconstroem o Exam Guide oficial v1.0 (jul/2026), como
> [dnacenta/claude-certified-architect](https://github.com/dnacenta/claude-certified-architect) e
> [claudecertificationguide.com](https://claudecertificationguide.com/blog/claude-certified-architect-foundations-exam-guide),
> mais a documentação pública da Anthropic. O guia oficial (PDF, Partner Academy) é a autoridade final.
>
> **[volátil]** marca detalhe de versão/modelo/beta que muda rápido. A prova cobra o **princípio**;
> trate o detalhe como "confira na doc atual".

---

## Formato e "espírito" da prova

- 60 questões (múltipla escolha + múltipla resposta), 120 min, corte 720/1000, sem penalidade por chute.
- **4 cenários sorteados de 6**; as questões se penduram no cenário:
  1. **Customer Support Resolution Agent:** Agent SDK, tools MCP, escalonamento.
  2. **Code Generation with Claude Code:** CLAUDE.md, plan mode, slash commands/skills.
  3. **Multi-Agent Research System:** coordenador-subagents, erros, proveniência.
  4. **Developer Productivity with Claude:** tools nativas, servidores MCP, exploração de codebase.
  5. **Claude Code for Continuous Integration:** `-p`, saída estruturada, Batch API, review multi-pass.
  6. **Structured Data Extraction:** JSON schema, tool use, validação com retry.
- **Regras de desempate** que valem para quase toda questão:
  - A **correção mais simples que resolve** vence (descrição melhor de tool antes de classificador de
    roteamento; critério explícito antes de "um segundo modelo para checar o primeiro").
  - **Regra crítica (financeira, segurança, compliance) → código determinístico** (hook, validação,
    pré-requisito). Prompt é probabilístico e só serve para o que pode ser "best-effort".
  - **Medir antes de mexer.** Métrica agregada esconde falha por tipo/segmento.

### Os 10 anti-padrões clássicos (aparecem como alternativas erradas)
1. Encerrar o loop lendo linguagem natural ("terminei") em vez de checar `stop_reason`.
2. Limite arbitrário de iterações como **mecanismo principal** de parada (como *backstop* é ok).
3. Regra de negócio crítica imposta só por prompt (use hooks/código).
4. Escalonar com base em **confiança autodeclarada** pelo modelo (mal calibrada).
5. Escalonar com base em **sentimento** (sentimento ≠ complexidade).
6. Mensagem de erro genérica ("Operation failed") que esconde o diagnóstico.
7. Suprimir erro em silêncio (devolver lista vazia como sucesso quando o backend caiu).
8. Tools demais num agente só (ex.: 18). Diretriz: **4–5 por agente** visíveis na decisão.
9. Auto-revisão na **mesma sessão** que gerou o conteúdo (viés do contexto de raciocínio).
10. Métrica de acurácia agregada que mascara falha por tipo de documento/campo.

---

## D1 — Arquitetura agêntica & orquestração (27%)

### 1.1 Ciclo de vida do loop agêntico
- O loop: Claude recebe prompt + definições de tools → chama tool ou responde → repete até sinalizar fim.
- **Decida pelo `stop_reason`:**
  - `tool_use` → executa a(s) tool(s), devolve `tool_result`, continua.
  - `end_turn` → terminou; apresenta o texto final.
  - `stop_sequence` → bateu numa stop sequence configurada.
  - `max_tokens` → cortou no limite de saída; pode precisar continuar.
  - `pause_turn` → loop de **tool server-side** atingiu o teto de iterações; reenvie a resposta para continuar.
  - `refusal` → recusou por segurança. Vem com **HTTP 200**, então cheque `stop_reason` antes de ler `content`.
  - `model_context_window_exceeded` → encheu a janela antes de `max_tokens`; saída válida, porém truncada.
- `content` pode **misturar texto e `tool_use`**, e trazer **vários `tool_use`** de uma vez (paralelo).
  Ter texto **não** significa que terminou.
- Cada `tool_result` referencia o **`tool_use_id` exato**; todos os resultados vão **numa única
  mensagem `user`**; falha leva `is_error: true` para o modelo raciocinar sobre a recuperação.
- O modelo decide qual tool e quando parar. **Não se codifica árvore de decisão** por fora.
- **Task budget** [volátil, beta]: teto de tokens **visível** ao modelo, que se organiza para caber.
  `max_tokens` é teto **invisível** que corta no meio.
- Quatro formas de construir, da mais simples à mais pronta: **loop manual**, **Tool Runner**
  (SDK roda o loop, você hospeda), **Managed Agents** [beta] (loop + sandbox hospedados) e
  **Claude Agent SDK** (o harness do Claude Code como biblioteca). Escolha a mais simples que atende.

### 1.2 Orquestração multiagente
- **Hub-and-spoke:** um **coordenador** decompõe, delega, **roteia toda comunicação** entre
  subagents, agrega, trata erros dos subagents e redelega quando a síntese tem lacunas.
- Acione **só os subagents que a consulta precisa**. Não passe tudo pelo pipeline inteiro.
- Refinamento iterativo: roda subagents → avalia → identifica lacunas → 2ª rodada direcionada → sintetiza.
- Anti-padrões: decomposição estreita demais (pesquisar "indústrias criativas" e cobrir só artes
  visuais; a correção é decompor de forma mais ampla e checar cobertura explicitamente);
  subagents conversando **diretamente** entre si.

### 1.3 Spawn de subagents e passagem de contexto
- Subagents são criados pela tool **`Agent`** (antes chamada `Task`). O coordenador precisa dela em
  `allowedTools`, e pode restringir a tipos específicos.
- **Contexto do subagent é isolado.** Ele não herda o histórico do coordenador, então tudo o que precisa
  vai **explícito no prompt** (cliente, pedido, problema). "Analise o problema do cliente" falha.
- **Paralelismo:** emitir **vários `Agent` na mesma resposta** do coordenador. Turnos separados = sequencial.
- [volátil] Claude Code: até 20 subagents concorrentes, profundidade 3.
- Agent SDK: `AgentDefinition` configura subagents; mensagens de dentro do subagent trazem
  `parent_tool_use_id` (atribuição).
- **Fork** herda a conversa toda e compartilha o cache de prompt (mais barato); só o resultado final
  volta. Subagent "fresco" serve para tarefa delimitada e bem especificada.
- Passagem estruturada: separe **conteúdo de metadados** (afirmação, evidência, fonte, data) para a
  atribuição sobreviver.

### 1.4 Enforcement de workflow e handoff
- **Programático** (hooks, pré-requisitos) = determinístico → obrigatório quando há consequência
  financeira ou de segurança. **Prompt** = probabilístico, taxa de falha não nula → só best-effort.
- **Handoff para humano** exige **resumo estruturado** (o humano normalmente não vê o transcript):
  cliente, problema, pedido, causa raiz, ações tomadas, ação recomendada, valor.

### 1.5 Hooks (Claude Code / Agent SDK)
- Eventos-chave: `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`,
  `PostToolUseFailure`, `PermissionRequest`, `SubagentStop`, `PreCompact`, `Stop`, `SessionEnd`.
- Tipos: `command` (**exit 0 passa, exit 2 bloqueia**), `http`, `mcp_tool`, `prompt` (uma chamada
  sim/não a LLM), `agent` (multi-turn com tools).
- `PreToolUse` pode devolver `permissionDecision`: `allow` / `deny` / `ask` (+ motivo). É o lugar de
  **bloquear `process_refund` até a verificação de identidade**.
- `PostToolUse` normaliza/limpa/anota resultados (ex.: mascarar PII). `PostToolUseFailure` trata erro de tool.
- Onde configurar: settings de usuário, de projeto (compartilhado), local (gitignored), managed
  policy (organização). Hooks também podem ficar no frontmatter de skill ou de subagent.

### 1.6 Estratégias de decomposição
- **Prompt chaining:** passos fixos e sequenciais, conhecidos de antemão.
- **Decomposição dinâmica/adaptativa:** subtarefas surgem das descobertas (investigação aberta).
- **Review multi-pass de PR grande:** passo 1 analisa **cada arquivo localmente**; passo 2 faz
  **integração entre arquivos** com prompt separado. Evita diluição de atenção, padrão inconsistente
  entre arquivos e bug cross-file perdido.

### 1.7 Gestão de sessão
- `--resume <sessão>` continua uma conversa: bom quando os resultados de tool **ainda valem**.
  Se arquivos/serviços mudaram ou o contexto derivou, **comece do zero com um resumo estruturado**.
- `--fork-session` cria novo ID a partir de uma base comum, então os ramos não se contaminam.
- Ao retomar depois de mudanças, **diga explicitamente o que mudou** (resultados velhos no histórico).
- O que não pode se perder vai para **arquivo/memória**, não para o scrollback.

---

## D2 — Design de tools & integração MCP (18%)

### 2.1 Design da interface da tool
- A **descrição é o critério de seleção** da tool, não documentação decorativa. Boa descrição: propósito e
  quando usar; formato de entrada com exemplo; formato de saída; casos de borda (entrada inválida,
  zero resultados); **como difere das tools parecidas**.
- Definição: `name`, `description`, `input_schema` (JSON Schema com `properties`, `required`);
  descrições por propriedade e `enum` restringem entradas.
- `strict: true` → entradas da tool seguem o schema exatamente. Exige `additionalProperties: false`
  em todo objeto; propriedades opcionais são permitidas (com limite total por request [volátil]);
  só um subconjunto de JSON Schema.
- Anti-padrões: nome/descrição vagos (`search`, "busca coisas"); **tools sobrepostas** com descrições
  quase iguais (causa roteamento errado; renomeie para separar propósitos ou funda as duas).

### 2.2 Respostas de erro estruturadas
- Erro como **objeto estruturado**: `isError`, `errorCategory`, `isRetryable`, descrição,
  `partial_results`, `attempted_action`.
- Categorias:
  - **Transitório** (timeout, indisponível, rate limit): retentável → retry com backoff.
  - **Validação** (formato errado, campo faltando): corrija a entrada e tente de novo.
  - **Negócio** (limite de política, conta congelada): não retentável → explique a política ou escale.
  - **Permissão** (acesso insuficiente, token expirado): não retentável → escale.
- Subagent tenta **recuperação local** de transitórios e só propaga o que não resolveu.
- **Vazio ≠ falha:** 200 com array vazio = "nada encontrado" (informação). Timeout/503 = a busca **não rodou** (erro).
- Anti-padrões: erro genérico; supressão silenciosa; status sem contexto do que foi tentado;
  abortar o workflow inteiro por uma falha (use resultado parcial / alternativa).

### 2.3 Distribuição de tools e `tool_choice`
- **4–5 tools por agente** no momento da decisão. Com 18 tools a seleção degrada → **divida em
  subagents especializados** (coordenador, busca, análise, ação). Melhorar descrições sozinho não basta.
- **Tool search** (`defer_loading`): catálogo grande carregado sob demanda. Use com 10+ tools,
  definições acima de ~10k tokens, ou vários servidores MCP; mantenha 3–5 tools frequentes **não
  deferidas** (pelo menos uma tem que ficar não deferida). Preserva o cache de prompt.
  [volátil] variantes regex e BM25.
  - Conciliação: "4–5 tools" é o que o modelo **vê** na decisão; tool search mantém esse número baixo
    enquanto o catálogo cresce.
- `tool_choice`: `auto` (padrão, pode responder texto) · `any` (obrigado a chamar alguma) ·
  `{"type":"tool","name":...}` (obrigado a chamar aquela) · `none` (só texto, tools continuam
  declaradas). `disable_parallel_tool_use: true` limita a uma chamada por resposta.
- [volátil] Em modelos mais novos (ex.: Fable 5.1, Opus 5.5), `any` e `tool` forçado **retornam 400**.
  Alternativas: `auto` + instrução explícita nomeando a tool + `strict: true`; ou **structured
  outputs** (`output_config.format`) quando o forçar existia só para obter JSON. Modelos anteriores
  aceitam as quatro opções. Suporte é por modelo, então cheque as capabilities.

### 2.4 Configuração de servidores MCP
- MCP = padrão aberto para conectar modelos a dados/tools. **Host** (ex.: Claude Code) roda **um
  client por server** (conexão 1:1). Protocolo **JSON-RPC 2.0**; ciclo
  `initialize` → `notifications/initialized` → `tools/list` → `tools/call`.
- Primitivas do **server**: **tools** (funções executáveis), **resources** (conteúdo somente-leitura,
  catálogo navegável: reduz chamadas exploratórias às cegas), **prompts** (templates).
  Primitivas do **client**: **sampling** (server pede uma completion), **elicitation** (server pede
  input ao usuário), **roots** (limites de URI/filesystem permitidos).
- Transportes: **stdio** (processo local; implícito quando há `command`); **Streamable HTTP**
  (`"http"`, remoto, **o único remoto com OAuth**); **SSE** (legado); [volátil] WebSocket.
  Pegadinha: entrada com `url` mas **sem `type`** é lida como stdio e falha, então sempre declare `type` no remoto.
- **Escopos de instalação:** **local** (padrão; só este projeto, não compartilhado; fica em
  `~/.claude.json`) · **project** (compartilhado via git; **`.mcp.json`** na raiz) · **user** (todos os seus
  projetos; `~/.claude.json`) · **managed** (admin, empurrado para a organização).
  Pegadinha: o escopo "local" do MCP **não é** o `.claude/settings.local.json`.
- `.mcp.json`: objeto `mcpServers`; cada server com `type`/`url`/`headers` ou `command`/`args`/`env`.
  **Segredos via `${VAR}`** (e `${VAR:-default}`), nunca literais no arquivo versionado.
- Servers de projeto (`.mcp.json`) pedem **aprovação** na sessão interativa.
- Autenticação: OAuth via `/mcp` (remoto HTTP); token estático em `headers`; credencial de curta
  duração via `headersHelper`.
- [volátil] No Claude Code, tool search de MCP é padrão (`ENABLE_TOOL_SEARCH`); saída de MCP gera
  aviso acima de ~10k tokens e trunca em ~25k (`MAX_MCP_OUTPUT_TOKENS`).

### 2.5 Tools nativas (Claude Code)
- **Grep** (conteúdo), **Glob** (arquivos por padrão), **Read**, **Write** (criar), **Edit**
  (troca por texto único), **Bash**, **WebSearch/WebFetch**, **Agent** (subagent para trabalho
  delimitado/ruidoso), **Skill**, **NotebookEdit**, **AskUserQuestion**, **ToolSearch**.
- Exploração de codebase: **grep pelos pontos de entrada → lê → segue imports com grep → lê**,
  construindo entendimento aos poucos. Anti-padrão: **ler tudo de antemão** (gasta contexto).
  Para busca volumosa, um subagent **Explore** devolve só a conclusão.
- `Edit` falha se o trecho não é único → leia o arquivo inteiro e reescreva (ou amplie o trecho).

### 2.6 Tools definidas pela Anthropic e server-side
- Declaradas por `type` + `name` (sem schema). **Server-side** (web search, web fetch, code
  execution, tool search) rodam na Anthropic e o resultado volta na **mesma resposta**.
  **Client-side** (bash, text editor, memory) você executa.
- Erro de tool server-side vem **com HTTP 200** e objeto de erro dentro do resultado.
- `pause_turn` = loop server-side bateu no teto; reenvie para continuar.
- Web fetch só busca URLs **já presentes na conversa** (não é crawler).
- **Tool use paralelo:** vários `tool_use` numa mensagem → execute em paralelo, devolva **todos** os
  `tool_result` numa única mensagem `user`; a que falhou também recebe resultado, com `is_error: true`.
- **Programmatic tool calling** [volátil]: Claude chama tools de dentro do sandbox de code execution
  (resultado grande fica fora do contexto).
- **MCP connector** na Messages API: conecta server MCP remoto direto pela API (`mcp_servers` +
  toolset). [volátil] detalhes de beta.
- Trocar o array `tools` entre turnos **invalida o cache**.

---

## D3 — Configuração & workflows do Claude Code (20%)

### 3.0 Superfícies e portabilidade
- CLI, VS Code/Cursor, JetBrains, desktop, web, mobile: **mesmo motor**, então CLAUDE.md, settings,
  skills e MCP valem igual em todas.
- [volátil] Agendamento: *routines* (nuvem, disparo por API/GitHub, máquina desligada), tarefas
  agendadas no desktop (locais, acesso a arquivos/rede privada), `/loop` (polling dentro da sessão).

### 3.1 Hierarquia do CLAUDE.md
- Ordem do geral ao específico: **managed policy** (org) → **usuário** (`~/.claude/CLAUDE.md`,
  pessoal) → **projeto** (`./CLAUDE.md` ou `./.claude/CLAUDE.md`, versionado, do time) →
  **`CLAUDE.local.md`** (pessoal, gitignored) → **subdiretório** (carregado sob demanda quando
  arquivos daquele diretório são lidos).
- `AGENTS.md`: lido se não houver CLAUDE.md (um `CLAUDE.local.md` também conta como "existe CLAUDE.md"); com ambos, **CLAUDE.md vence**; dá para importar com `@AGENTS.md`.
- **`@import`:** caminho relativo ao arquivo que importa; `@~/` = home; profundidade limitada (doc atual: 4 saltos) [volátil].
- **`.claude/rules/`:** regra sem frontmatter carrega no início; com `paths:` (glob) carrega só
  quando arquivos que batem são tocados.
- Auto memory (`MEMORY.md`): primeiras ~200 linhas/25 KB no início da sessão; local da máquina.
- Monorepo: `claudeMdExcludes`, `--add-dir`.

### 3.2 Skills e comandos
- Comandos customizados foram **fundidos em skills**: `.claude/commands/deploy.md` e
  `.claude/skills/deploy/SKILL.md` criam `/deploy`; em conflito, **skill vence**.
- Prioridade: enterprise > pessoal (`~/.claude/skills/`) > projeto (`.claude/skills/`) > plugin
  (namespace `plugin:skill`).
- Frontmatter: `description` (+`when_to_use`) dirige o **auto-carregamento**; `allowed-tools`,
  `disable-model-invocation`, `user-invocable`, `context: fork`, `agent`, `paths`, `model`, `hooks`,
  `argument-hint`. Substituição `$ARGUMENTS`, `$0..$N`. Contexto dinâmico com `` !`cmd` ``.
- `context: fork`: roda a skill num **subagent isolado** (o histórico da conversa não vai; CLAUDE.md carrega, exceto nos subagents Explore/Plan, que não o carregam).
- O corpo da skill **fica na conversa e não é relido**, então escreva instruções permanentes, não passos únicos.
- **Plugins:** pacotes de skills + subagents + hooks + MCP, com namespace.

### 3.3 Regras por caminho
- Convenção que atravessa diretórios (ex.: todos os testes espalhados) → **um arquivo em
  `.claude/rules/` com `paths:` glob**. Cobre diretórios futuros e evita duplicar CLAUDE.md por pasta.

### 3.4 Plan mode vs. execução direta
- Modos de permissão: `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`
  (`--permission-mode` ou Shift+Tab).
- **Plan mode:** explora, desenha a abordagem, pede aprovação, só então edita. Use em mudança
  multi-arquivo, decisão arquitetural, várias abordagens válidas, escopo grande, requisito confuso
  (ex.: migrar biblioteca em 45+ arquivos).
- **Direto:** fix de um arquivo, escopo óbvio, instrução clara (null check, constante, bug com stack trace).
- Subagents nativos: **Explore** e **Plan** (somente leitura), **general-purpose**.
  Customizados em **`.claude/agents/`** (markdown + frontmatter: tools, model, permissões, hooks...).
  O subagent **não escala além do modo de permissão do pai** (se o pai está em `bypassPermissions`/`acceptEdits`/`auto`, o subagent herda o modo; com o pai em `default`/`dontAsk`/`plan`, o subagent pode ter o próprio modo, mas nunca vira bypass).
- **settings.json:** precedência managed > CLI > local (`.claude/settings.local.json`) > projeto (`.claude/settings.json`) > usuário (`~/.claude/settings.json`); listas como `permissions.allow` **se mesclam** entre níveis. Avaliação de permissões: **deny → ask → allow** (um allow nunca abre exceção num deny). Regras tipo `Bash(npm run test *)` (forma antiga equivalente: `Bash(npm run test:*)`).
- `bypassPermissions` não é rotina para tarefa longa/não contida.

### 3.5 Refinamento iterativo
1. **Exemplos concretos:** 2–3 pares entrada/saída batem instrução em prosa.
2. **TDD:** escreva testes que falham, compartilhe as falhas, itere até passar.
3. **Entrevista:** Claude faz perguntas de esclarecimento antes de implementar.
4. **Problemas relacionados** (que interagem) → numa mensagem só; **independentes** → em sequência
  (mudanças revisáveis).

### 3.6 Integração CI/CD
- **`-p` / `--print`** = não interativo. **Sem ele o processo trava esperando input.**
- Flags de CI: `--output-format` (`text`/`json`/`stream-json`), `--json-schema`, `--max-turns`,
  `--allowedTools`/`--disallowedTools`, `--permission-mode`, `--append-system-prompt`,
  [volátil] `--max-budget-usd`, `--bare`, `--no-session-persistence`, `--fallback-model`.
- Integrações gerenciadas: GitHub Actions (`claude-code-action`), GitLab CI/CD, Code Review. `-p` é a
  primitiva para controle total.
- **Batch API:** 50% mais barata, janela de até 24h, sem SLA, resultados **fora de ordem**, então case por
  **`custom_id`**; **não suporta loop multi-turn de tools** dentro de um request. Nada de batch para
  checagem pré-merge/bloqueante.
- **Review em sessão nova**: a sessão que escreveu o código não deve revisá-lo.

---

## D4 — Prompt engineering & saída estruturada (20%)

### 4.1 Critérios explícitos
- "Seja conservador" / "use seu bom senso" → resultado inconsistente. Para cada julgamento: **o que
  conta, o que não conta, exemplos de fronteira**.
- Uma categoria com muito falso positivo **corrói a confiança nas categorias boas**. Desligue a
  ruidosa, refine o critério, religue.

### 4.2 Few-shot
- Use para casos ambíguos, demonstrar formato/raciocínio, reduzir alucinação em extração, casos de borda.
- **2–4 exemplos direcionados**, cada um com entrada, saída **e o raciocínio**; devem ensinar o
  padrão (generalizar), não ser decorados. Varie os exemplos (cubra bordas).

### 4.3 Saída estruturada
- Texto livre pode sair malformado, sem campo, com nome/tipo errado.
- Solução 1: **tool cujo `input_schema` é a saída desejada** (extração via tool use).
  [volátil] Forçar via `tool_choice` vale em modelos anteriores; nos mais novos use `auto` + instrução +
  `strict`, ou a solução 3.
- Solução 2: **`strict: true`** garante conformidade com o schema (`additionalProperties: false` em
  todo objeto; opcionais permitidas, mas contam para um limite. Prefira `required` + nullable).
- Solução 3: **structured outputs** `output_config.format` com `json_schema` (o antigo `output_format`
  de topo está depreciado).
- **Conformidade com schema ≠ correção semântica.** Total com tipo certo pode não bater com os
  itens, então valide em código.
- Padrões de schema: **campo nullable** para dado que pode faltar (evita inventar); enum com
  **"other" + campo de detalhe**; enum **"unclear"** para não chutar.
- Strict **não suporta**: restrições numéricas (`minimum`/`maximum`/`multipleOf`), tamanho de string
  (`minLength`/`maxLength`), restrições de array além de `minItems` 0/1, schemas recursivos, `enum`
  com tipos complexos, `$ref` externo. `pattern` funciona só para regex **simples** (sem
  backreference, lookaround, `\b`, `{n,m}` grandes). `anyOf`/`allOf` com limitações. Usar recurso não
  suportado num schema cru → **400**; os helpers do SDK movem a restrição para a descrição e validam
  localmente. Imponha o resto no seu código.

### 4.4 Loop de validação com retry
- Extrai → valida → devolve **os erros específicos** no prompt → tenta de novo até um limite →
  então falha com erro.
- Validação de schema (campos, tipos, enums, datas) **e** semântica (somas, datas impossíveis,
  contradição entre campos, entidade referenciada que não existe).
- Extraia **valor declarado e valor calculado** para detectar discrepância.
- **Retry não recupera informação que não está na fonte**, então devolva `null`.
- Campo `detected_pattern` ajuda a medir quais padrões geram achados e quais são descartados.

### 4.5 Processamento em lote (Batch API)
- 50% de desconto, até 24h, sem SLA, sem multi-turn num request. Case por `custom_id`.
- Estados: `succeeded`, `errored`, `canceled`, `expired`. Faça poll de `processing_status` até
  `ended`, depois leia os resultados.
- Use em: análise noturna, relatório semanal, processamento em massa. **Não** use em: pré-merge, tempo
  real, passo bloqueante de CI, depuração interativa.
- **Reenvie só os `custom_id` que falharam.** Refine o prompt numa **amostra** antes de rodar volume.

### 4.6 Review multi-pass
- **Viés do contexto de raciocínio:** quem gerou não questiona as próprias decisões, então revise em
  **sessão independente**.
- PR grande: **passo 1 por arquivo** (bugs, estilo, tipos, segurança, prompt consistente) + **passo
  2 de integração** recebendo os achados do passo 1 (fluxo de dados, contratos entre módulos, erro na fronteira).

### 4.7 Thinking, effort e a superfície de request [volátil em boa parte]
- **Adaptive thinking** (`thinking: {"type":"adaptive"}`) substitui `budget_tokens`; nos modelos novos
  `budget_tokens` e parâmetros de sampling (`temperature`, `top_p`, `top_k`) **retornam 400** (em
  alguns modelos, só valores diferentes do padrão).
- `effort` em `output_config` (low/medium/high/xhigh/max) controla quanto o modelo se esforça.
  O **default muda entre modelos** (high em uns, medium em outros): defina explicitamente e
  re-calibre ao migrar de modelo.
- **Prefill do assistant** retorna 400 nos modelos novos → use structured outputs ou instrução no system.
- Ao migrar de modelo: **teste a forma do request**; parâmetros aceitos mudam por modelo.

### 4.8 Prompt caching
- Cache casa **prefixo exato**, na ordem **tools → system → messages**. Qualquer byte diferente no
  prefixo invalida tudo depois dele.
- **Estável primeiro, volátil depois** (timestamp, IDs, a pergunta em si ficam após o último breakpoint).
- Até **4 breakpoints** (`cache_control`). Prefixo abaixo do mínimo do modelo **não cacheia, em silêncio**.
- Escrita custa prêmio (1,25× para 5 min; 2× para 1 h); leitura custa uma fração pequena.
- Verifique com `usage.cache_read_input_tokens`. Se der zero em requests repetidos, algo está invalidando.
- Invalidadores silenciosos: timestamp no system, ordem não determinística de chaves JSON, lista de
  tools que varia por request, ID de sessão/usuário no prefixo, mudar thinking/effort entre requests.

---

## D5 — Gestão de contexto & confiabilidade (15%)

### 5.1 Contexto da conversa
- Janela finita: mensagens, resultados de tool e system consomem tokens; conversa longa degrada.
  [volátil] janelas de 1M em modelos recentes. Janela grande não é de graça (todo token é cobrado a cada
  turno) e o **"lost in the middle"** piora.
- **Resumo perde:** valores exatos, datas, percentuais, IDs, números de pedido, mensagens de erro.
  Correção: bloco persistente de **CASE FACTS** que nunca é resumido.
- Lost in the middle: achados-chave no **começo**, cabeçalhos de seção, nada crítico no meio.
- **Corte a saída das tools:** devolva só os campos relevantes, não os 40.
- Sobrevive ao `/compact`: CLAUDE.md, system prompt, mensagens recentes, memória. Pode se perder:
  detalhes antigos, resultados específicos de tools, números e citações exatas do início.

### 5.2 Padrões de escalonamento
- **Escale de imediato quando:** o cliente **pede humano explicitamente**; há **lacuna/exceção de
  política**; não há progresso após tentativas razoáveis.
- **Não escale por:** sentimento alto, confiança autodeclarada baixa, tamanho da conversa.
- **Sentimento ≠ complexidade:** cliente bravo com cobrança de US$ 5 → resolva. Cliente calmo com
  exceção de política → escale.
- Vários clientes batem na busca → **peça identificador para desambiguar**, não chute.
- Handoff: resumo estruturado (identidade, problema, ações tomadas, motivo do bloqueio, ação recomendada).

### 5.3 Propagação de erro
- Erro estruturado: tipo de falha, serviço, consulta tentada, timeout, resultado parcial,
  alternativas, retentável?, retry-after.
- Não aborte o workflow por uma etapa: **continue com o parcial, anote a lacuna, ofereça alternativa**.
- Subagent: recupera transitório localmente (backoff) e propaga só o que não resolveu, com contexto.

### 5.4 Contexto em codebase grande
- Sinais de degradação: respostas vagas ("padrões típicos") em vez de código específico,
  inconsistência, esquecer descobertas.
- Mitigações: **arquivos de rascunho** (scratchpad) que sobrevivem à compressão; **subagents que
  exploram e devolvem só o resumo**; `/compact` **proativo** com resumo estruturado; estado salvo em
  local conhecido + **manifesto** do coordenador para retomar após crash.

### 5.5 Revisão humana
- **Amostragem estratificada por risco** (ex.: 20% alto, 10% médio, 5% baixo), não uniforme.
- **Confiança por campo**, calibrada contra conjunto rotulado (senão não significa nada).
- 97% de acurácia agregada pode esconder **45% em notas manuscritas**, então quebre por tipo de documento e campo.

### 5.6 Proveniência da informação
- Mapa afirmação → fonte: local da evidência, URL, documento, data de publicação, tipo de fonte.
- **Conflito entre fontes:** anote os valores divergentes com suas fontes. **Não escolha um em silêncio
  nem tire média.**
- Dados temporais: registre "dados de", publicação e coleta. Números de períodos diferentes não são contradição.
- Síntese: rotule certeza (consolidado / contestado / fonte única); preserve ressalvas; formato
  conforme o conteúdo (tabela para financeiro, cronologia para eventos).

### 5.7 Gestão de contexto server-side [volátil nos nomes de beta]
- **Context editing:** limpa resultados antigos de tool/blocos de thinking (`clear_tool_uses`). Bom
  para loop agêntico verboso.
- **Compaction:** resume o contexto anterior num bloco. Bom para trabalho longo que precisa da
  narrativa. **Anexe o `response.content` inteiro**, não só o texto, ou o estado de compaction se perde em silêncio.
- **Memory tool:** arquivos persistentes fora da conversa (você implementa as operações). Bom para
  achados entre sessões.
- Bloco de **case facts** para números que nunca podem ser parafraseados.
- Histórico **append-only**: editar turnos antigos no client pode quebrar blocos de thinking
  preservados (400 no request seguinte).

### 5.8 Limitando e recuperando execuções longas
- **Task budget** (visível, o modelo se organiza) vs. **`max_tokens`** (invisível, corta no meio).
- **Recusa** chega como **HTTP 200** com `stop_reason: "refusal"`. Código que ignora `stop_reason`
  trata como sucesso vazio.
