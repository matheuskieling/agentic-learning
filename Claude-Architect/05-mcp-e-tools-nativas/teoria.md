# Módulo 05 — MCP no Claude Code e no agente + tools nativas

> **Task statements:** **2.4** (integrar servidores MCP ao Claude Code e a workflows de agente) e
> **2.5** (selecionar e aplicar as tools nativas Read, Write, Edit, Bash, Grep, Glob). Domínio **D2 —
> Tool Design & MCP Integration (18%)**, junto com o Módulo 04.
> **Cenários onde cai:** **4 — Developer Productivity** (agente do Agent SDK com tools nativas +
> servidores MCP: o cenário-casa deste módulo), **2 — Code Generation with Claude Code** (`.mcp.json`
> do time, Grep/Glob/Edit no dia a dia) e **1 — Customer Support** (`get_customer`, `lookup_order`...
> são tools MCP customizadas).

No **2.4** a prova cobra **decisões de integração**, não o protocolo: onde configurar (time × pessoal),
como não commitar segredo, o que o agente vê com vários servidores, quando expor **resource**, como
fazer o agente **adotar** a tool MCP e quando **não** escrever servidor próprio. No **2.5**: **qual
tool nativa** usar e **como explorar** um código sem ler tudo de antemão.

> **Na doc atual [volátil]:** o MCP tem muito mais (JSON-RPC, handshake, transportes, OAuth,
> sampling/elicitation, prompts como slash commands, tool search). O guia não lista nada disso, e
> hospedagem de servidor MCP e protocolo de autenticação são **fora do escopo**. Numa alternativa, é distrator.

---

## 1. O mapa mínimo: servidores, tools, resources e o agente

**Fatos de prova.**
- Um **servidor MCP** expõe **tools** (ações/consultas que o **modelo decide** chamar: `create_issue`,
  `process_refund`, `run_query`) e **resources** (conteúdo para **leitura**: catálogos — seção 4).
- Quem conecta é o **host**: o Claude Code (`.mcp.json` / `~/.claude.json`) ou o **seu agente do
  Agent SDK** (servidores na configuração do agente ou o `.mcp.json` do projeto).
- **2.4-K3 — as tools de TODOS os servidores configurados são descobertas na conexão e ficam
  disponíveis AO MESMO TEMPO.** Não existe "servidor ativo": na mesma tarefa o agente lê um ticket
  num servidor e consulta o registro de dispositivos em outro.
- Para o modelo, tool MCP é tool como outra qualquer (nome + descrição + schema): tudo do M04 vale.

Agent SDK (SDK oficial em Python/TypeScript; em C# a ideia seria a mesma):

```ts
const options = {
  mcpServers: {                        // ← AQUI: todos os servidores listados conectam no início da sessão
    "device-registry": { type: "http", url: "https://mcp.registry.internal/mcp",
                         headers: { Authorization: `Bearer ${process.env.REGISTRY_TOKEN}` } },
    "tickets":         { command: "npx", args: ["-y", "<pacote-do-servidor-de-tickets>"] }
  },
  // nativas + MCP (nome mcp__<servidor>__<tool>)
  allowedTools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "mcp__device-registry__*", "mcp__tickets__*"]
};
```

**Ponte com o M04 (TS 2.2).** Falha de tool MCP volta com **`isError: true`** + metadados — é assim
que o agente distingue "falhou" de "consulta válida sem resultado":

```jsonc
// Objeto result devolvido pelo servidor MCP para a chamada da tool (resposta de tools/call)
{
  "content": [ { "type": "text",
                 "text": "{\"errorCategory\":\"transient\",\"isRetryable\":true,\"message\":\"Registry timed out after 5s\"}" } ],
  "isError": true            // ← AQUI: o agente sabe que é FALHA e decide retry/alternativa
}
```

**Por quê.** O host lista as tools de cada servidor ao conectar e entrega todas ao modelo no mesmo
conjunto; o modelo escolhe pela descrição, não por "qual servidor está ligado".

**Anti-padrões que aparecem como alternativa errada.** Tool `select_server` / uma sessão por
servidor / reiniciar ao trocar de servidor; **fundir** os servidores num custom único "para o agente
ver uma lista só"; **roteador** na frente dos servidores; "só o primeiro servidor carrega".

> **Na doc atual [volátil]:** o Claude Code adia o carregamento das *definições* das tools MCP (tool
> search), mas todas continuam disponíveis. **Na prova: tools de todos os servidores ficam
> disponíveis simultaneamente.**

**Como cai na prova.** Cenário 4: design doc propõe "seletor de servidor" para economizar tokens → a
premissa está errada. Cenário 1: pedidos, CRM e logística em servidores diferentes, na mesma conversa.

---

## 2. Onde configurar: project `.mcp.json` × user `~/.claude.json`

**Fatos de prova (2.4-K1, S1, S2).** O guia é **binário**:

| Escopo | Arquivo | Quem recebe | Versionado? | Uso (resposta de prova) |
|--------|---------|-------------|-------------|-------------------------|
| **project** | `.mcp.json` na raiz do repo | todo mundo que clona/puxa | **sim** | tooling **compartilhado do time** |
| **user** | `~/.claude.json` | só você, em todos os seus projetos | não | servidor **pessoal/experimental** |

```jsonc
// <raiz-do-repo>/.mcp.json — versionado; o time inteiro recebe no clone/pull
{
  "mcpServers": {                                         // ← AQUI: nome do servidor → como conectar
    "jira": {
      "command": "npx",
      "args": ["-y", "<pacote-do-servidor-jira-da-comunidade>"],
      "env": { "JIRA_API_TOKEN": "${JIRA_API_TOKEN}" }     // segredo fora do git (seção 3)
    }
  }
}
```

```jsonc
// ~/.claude.json — arquivo do SEU usuário (home), fora do git; servidores na chave mcpServers
{
  "mcpServers": {                                         // ← AQUI: servidores de escopo user
    "lab-vibracao": { "command": "python3", "args": ["/home/ana/mcp-lab/vibration_server.py"] }
  }
}
```

**Por quê.** O `.mcp.json` viaja com o repositório e passa por code review: todos rodam a mesma
definição. O `~/.claude.json` mora na máquina do dev: testar ali não afeta ninguém nem depende de PR.
Quando o experimento virar ferramenta do time, **promova** para o `.mcp.json` via PR.

**Anti-padrões que aparecem como alternativa errada.**
- Servidor do time configurado **um a um** no `~/.claude.json` + "documentar no README como
  adicionar" → o novo membro não recebe e as URLs divergem (mesmo diagnóstico do 3.1).
- Servidor **experimental** direto no `.mcp.json`, "numa branch" ou "por uns dias".
- URL/comando do servidor no **CLAUDE.md** (instrução para o modelo, não configuração de conexão).
- Copiar o `~/.claude.json` de um colega; chave inventada `"experimental": true` no `.mcp.json`.

> **Na doc atual [volátil]:** o `claude mcp add` tem também o escopo `local` (padrão do comando,
> guardado no mesmo `~/.claude.json`) e servidores gerenciados pela organização. **Na prova:
> pessoal/experimental = user-level `~/.claude.json`; time = `.mcp.json`.** Não trate "user" como errado.

**Como cai na prova.** "Dev novo não vê o servidor que o time usa" → mover para o `.mcp.json`.
"Engenheira quer testar um servidor sem afetar os 30 colegas" → `~/.claude.json`.

---

## 3. Segredos: expansão de variável de ambiente no `.mcp.json`

**Fatos de prova (2.4-K2, S1).**
- No `.mcp.json` versionado vai a **referência** `${GITHUB_TOKEN}`; o valor vem do **ambiente de
  quem roda** o Claude Code ou o agente. Cada dev (e o CI) define a variável no próprio ambiente.
- Vale nos campos de conexão (`env`, `headers`, `url`, `command`, `args`); `${VAR:-padrão}` dá default.

```jsonc
// .mcp.json (versionado)
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_TOKEN}" }   // ← AQUI: referência, nunca o token
    }
  }
}
```

```bash
# perfil do shell de cada dev (ou cofre de segredos / secret do CI)
export GITHUB_TOKEN="<token pessoal do dev>"
```

**Por quê.** Segredo commitado vaza pelo histórico, forks e logs; "repo privado" não é cofre. Com a
referência, a config continua **uma só e versionada** e cada pessoa usa a **própria** credencial.

**Sintoma típico.** A config compartilhada funciona para quem tem a variável e falha com erro de
autenticação para quem não tem (ex.: o token dele só existia colado na config antiga).

**Anti-padrões que aparecem como alternativa errada.** Token literal "porque o repo é privado" ou de
um usuário de serviço; tirar o `.mcp.json` do git e distribuir por wiki/chat; "cada dev edita o
arquivo com o próprio token e não commita"; token no CLAUDE.md/system prompt; mover tudo para o
`~/.claude.json` de cada um só para esconder o token (perde o compartilhamento); servidor "wrapper"
que lê um `.env` (over-engineering).

> **Na doc atual [volátil]:** variável sem valor e sem default → o Claude Code mantém `${VAR}` como
> texto e avisa no `claude mcp list`. OAuth e rotação de chave: fora do escopo.

**Como cai na prova.** "Compartilhar o servidor do time sem commitar credencial" → `.mcp.json` com
`${VAR}`. "Funciona para 8 de 12 devs depois da migração" → os outros não definiram a variável.

---

## 4. Resources: catálogos de conteúdo para cortar chamadas exploratórias

**Fatos de prova (2.4-K4, S5).**
- **Resource** = conteúdo exposto para **leitura**; **tool** = **ação** ou consulta parametrizada. O
  in-scope do guia: *"resources for content catalogs, tools for actions"*.
- Exemplos do guia: **resumos de issues**, **hierarquia de documentação**, **schemas de banco**.
- Objetivo: **visibilidade do que existe** sem **chamadas exploratórias** (listar, buscar às cegas,
  chutar nome de tabela/página).

```jsonc
// Catálogo anunciado pelo servidor (resultado de resources/list)
{
  "resources": [                                                    // ← AQUI: o que o agente enxerga antes de agir
    { "uri": "docs://transit-api/index",   "name": "Documentation tree",        "mimeType": "text/markdown" },
    { "uri": "schema://ops-db/tables",     "name": "Operational DB schema",     "mimeType": "application/json" },
    { "uri": "issues://sprint-42/summary", "name": "Open issue summaries",      "mimeType": "text/markdown" }
  ]
}
```

Antes: `search_tables("route")`, `search_tables("trip")`, `run_query(...)` — 12 chamadas antes da
consulta útil. Depois: lê o resource do schema e escreve a consulta certa. (No Claude Code dá para
citar um resource com `@servidor:protocolo://caminho` — contexto.)

**Por quê.** Cada chamada exploratória custa uma volta do loop + tokens; o catálogo encurta o caminho.

**Anti-padrões que aparecem como alternativa errada.**
- Tool `list_tables`/`list_docs` "chamada no início de toda sessão" — parece certo, mas **continua
  sendo chamada exploratória**; o padrão do guia é o resource.
- Colar o schema/documentação inteira no system prompt (gasta contexto sempre, desatualiza).
- Aumentar o limite de chamadas; cache especulativo de buscas.
- Transformar **ações** (`process_refund`, `escalate_to_human`) em resources: o que tem efeito é tool.

**Como cai na prova.** "4–6 buscas no início de cada conversa para descobrir quais políticas
existem" → índice como resource. "Transformar todas as tools em resources" → rejeitar para as ações.

---

## 5. Adoção: descrição detalhada da tool MCP × Grep nativo

**Fatos de prova (2.4-S3).** Se um servidor MCP oferece uma tool **mais capaz** (busca por símbolo em
vários repositórios, índice de código) e o agente continua no **Grep** nativo, a causa provável é a
**descrição** da tool MCP. Correção do guia: **ampliar a descrição**, explicando **capacidades** e
**saídas** — o que cobre que o Grep não cobre, a entrada, o que devolve, quando preferi-la.

```jsonc
// Item de tools/list (é ISTO que o modelo lê para escolher; no MCP o schema se chama inputSchema)
{
  "name": "find_references",
  "description": "Finds references.",        // ← AQUI (antes): perde para o Grep
  "inputSchema": { "type": "object", "properties": { "symbol": { "type": "string" } }, "required": ["symbol"] }
}
```

Depois, mesmo campo `description`: *"Symbol-aware reference search across ALL 14 service repositories
(not only the checked-out one), including generated clients and re-exports. Use it instead of text
search when you need every caller of a function, class or endpoint. Input: fully qualified symbol.
Returns JSON: [{repo, path, line, kind: call|import|reexport, snippet}]. For a literal string such as
a log message, plain text search is enough."*

**Por quê.** A descrição é o principal mecanismo de seleção (TS 2.1); o modelo só "sabe" que a tool
MCP é melhor se a descrição disser.

**Anti-padrões que aparecem como alternativa errada.**
- "**Sempre** use a tool MCP em vez do Grep" no CLAUDE.md/system prompt — rápido e tentador, mas é
  regra absoluta no prompt: não explica capacidades nem **quando** usar, cria a associação forçada
  que o 2.1-K4 condena e desvia até buscas simples de texto.
- **Negar o Grep** (ainda é preciso buscar mensagem de erro, string literal).
- **Hook/roteador** que reescreve toda chamada de Grep para a tool MCP; modelo maior.

**Como cai na prova.** "Em 70% das perguntas 'quem chama X?' o agente usa Grep e perde chamadores em
outros repositórios; a tool MCP diz só 'Finds references'" → reescrever a descrição.

---

## 6. Servidor da comunidade × servidor próprio

**Fatos de prova (2.4-S4).**
- Integração **padrão** (Jira, GitHub, Slack, Postgres) → **servidor MCP existente da comunidade** (ou
  do fornecedor): cobre a API e é mantido por outros, que acompanham as mudanças de versão.
- **Servidor próprio** só para o **workflow específico do time** (regras internas de triagem,
  validador do feed da empresa, registro interno de dispositivos).
- Os dois convivem, conectados ao mesmo tempo (seção 1).

**Por quê.** Construir e manter integração padrão (paginação, campos customizados, mudanças de API)
custa caro e não diferencia nada; o esforço próprio vai para o que só o time tem.

**Anti-padrões que aparecem como alternativa errada.** "Escrever nosso servidor Jira para ter
controle total"; "o agente chama a API REST via Bash/curl"; "um servidor custom único que embrulha
Jira + GitHub + fluxo interno"; culpar descrição ou escopo quando a dor vem de manter o que já existia.

**Como cai na prova.** "Dois engenheiros gastam um dia por semana consertando o servidor Jira que o
time escreveu; o validador interno, também próprio, não dá trabalho" → adotar o da comunidade.

---

## 7. Grep × Glob: conteúdo × caminho

**Fatos de prova (2.5-K1, K2, S1, S2).**

| A pergunta é... | Tool | Exemplos |
|-----------------|------|----------|
| "Onde está **escrito** X?" | **Grep** | chamadores de `ComputeFare(`; a mensagem `"Stop ID not found"`; os `using Transit.Fares;` / imports |
| "Quais arquivos têm **nome/extensão** Y?" | **Glob** | `**/*.test.tsx`, `**/*Controller.cs`, `db/migrations/**/*.sql` |
| "Quero o arquivo inteiro" | **Read** | o handler que o Grep encontrou |
| "Rode isto" | **Bash** | `dotnet test`, `git log`, script de build |

Grep busca **dentro** dos arquivos, independente do nome. Glob casa **caminhos** (`**` = qualquer
profundidade) e não olha conteúdo. Regra: **o que está escrito** → Grep; **como o arquivo se chama /
onde mora** → Glob.

**Anti-padrões que aparecem como alternativa errada.** Glob `**/*checksum*` para achar uma mensagem
de erro; Grep por `toMatchSnapshot` para listar arquivos de teste (perde arquivos de outro estilo — o
critério era o **nome**); Read de diretórios inteiros para "procurar"; Bash `ls -R`/`cat` em massa.

> **Na doc atual [volátil]:** no Claude Code em macOS/Linux/WSL, Glob e Grep ficam fora do conjunto padrão
> e o Claude busca com `find`/`grep` pelo Bash; no Agent SDK, listá-las em `allowedTools` as traz de
> volta. **Na prova: conteúdo = Grep, caminho = Glob.**

**Como cai na prova.** "O agente usou Glob e concluiu que a mensagem não existe no código" → Glob não
olha conteúdo. "Só 9 de 31 arquivos `*.snap.test.ts` foram atualizados" → seleção por nome = Glob.

---

## 8. Read/Write × Edit, e o fallback quando o Edit falha

**Fatos de prova (2.5-K3, K4, S3).**
- **Read** carrega o arquivo **inteiro**; **Write** grava o arquivo **inteiro** (novo ou substituído).
- **Edit** = modificação **pontual** por **texto âncora único**: troca `old_string` por `new_string`;
  o `old_string` precisa aparecer **exatamente uma vez**.

```jsonc
// Bloco tool_use que o modelo emite (response.content[i]) pedindo a tool nativa Edit
{
  "type": "tool_use", "id": "toolu_01A...", "name": "Edit",
  "input": {
    "file_path": "/repo/config/gateway.conf",
    "old_string": "poll_interval_ms = 500",     // ← AQUI: aparece em 9 blocos → Edit falha (não é único)
    "new_string": "poll_interval_ms = 250"
  }
}
```

- **Fallback do guia:** Edit sem âncora única → **Read** do arquivo inteiro → mudar só o bloco certo →
  **Write** do arquivo inteiro.
- Arquivo novo → **Write**; mudança pequena em arquivo existente → **Edit** (diff mínimo, preserva o
  resto); Edit sem âncora única → **Read + Write**.

> **Na doc atual [volátil]:** a doc do Claude Code também descreve ampliar o `old_string` com contexto
> até ficar único, ou `replace_all` para trocar todas. **Na prova, "Edit falhou por texto não único" →
> Read + Write.**

**Anti-padrões que aparecem como alternativa errada.** Repetir o mesmo Edit; `sed -i` pelo Bash
(troca **todas** as ocorrências ou depende de número de linha); Write para toda pequena mudança em
arquivo grande existente (reescreve tudo, pode perder comentários, diff enorme); achar que falhou
"porque o arquivo não foi lido" quando a mensagem diz que há várias ocorrências.

**Como cai na prova.** "O agente reescreve configs de 2.000 linhas com Write e o revisor quer diff
mínimo" → Edit. "Edit falhou: 9 ocorrências; o agente tentou o mesmo Edit 3 vezes" → Read + Write.

---

## 9. Explorar sem ler tudo: incremental e através de wrapper modules

**Fatos de prova (2.5-S4).** Construa o entendimento **incrementalmente**: **Grep** para achar os
**pontos de entrada** (handler, rota, registro de evento, `Main`) → **Read** desses arquivos → seguir
os **imports/chamadas** com Read (e Grep para achar definições). **Não** leia tudo de antemão.

**Fatos de prova (2.5-S5).** Uma função pode ser usada via **módulo wrapper** (fachada, barrel,
reexport) com **outros nomes**; Grep só pelo nome original perde esses usos. Procedimento: (1) **Read**
do wrapper → **lista de todos os nomes exportados**; (2) **Grep de cada nome** no código.

```csharp
// src/Fares/FareFacade.cs — wrapper: expõe a mesma lógica com outros nomes
public static class FareFacade
{
    public static decimal CalculateTripFare(Trip t) => PricingEngine.ComputeFare(t);                          // nome 1
    public static decimal LegacyFare(Trip t, bool peak) => PricingEngine.ComputeFare(t with { Peak = peak }); // nome 2
}
```

Grep `ComputeFare` → 3 arquivos. Read da fachada → `CalculateTripFare`, `LegacyFare` → Grep de cada
→ mais 11 consumidores. Em TypeScript, o barrel: `export { computeFare as calculateTripFare } from "./pricing";`.

**Por quê.** Ler tudo antes enche o contexto e dilui a atenção (M10); seguir o fio desde os pontos de
entrada mantém só o que importa. No wrapper, o nome que os consumidores usam **não é** o original.

**Pontes.** **Bash** serve para **executar** (build, testes, git), não para substituir Grep/Glob/Read.
Para isolar descoberta verbosa: **Explore subagent** (M08, TS 3.4) e subagents (M10, TS 5.4).

**Anti-padrões que aparecem como alternativa errada.** Ler os 240 arquivos de `alarms/` "para não
perder chamadas indiretas"; "ler tudo, mas resumir cada arquivo num scratchpad antes" (continua lendo
tudo); Grep só pelo nome original, ou case-insensitive "mais largo" (não acha alias); Glob por nome
para achar quem usa a função; janela maior/modelo maior.

**Como cai na prova.** "Explicar como um alarme escala num legado de 1.800 arquivos" → incremental.
"Mudou a assinatura de `ComputeFare` e quebraram 11 arquivos que o Grep não mostrou" → wrapper.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| Servidor que o **time inteiro** usa | `.mcp.json` na raiz do repo, versionado |
| Servidor **pessoal/experimental** | `~/.claude.json` (user-level); promover via PR se virar do time |
| Servidor do time exige token | `${VAR}` no `.mcp.json`; cada dev/CI define a variável |
| Config compartilhada falha só para alguns | Variável não definida no ambiente deles |
| Vários servidores | Todas as tools ao mesmo tempo; sem seletor/roteador |
| Chamadas às cegas para descobrir o que existe | Catálogo como **resource** (issues, docs, schema) |
| Ação com efeito | Continua **tool** |
| Agente prefere Grep a uma tool MCP melhor | Ampliar a **descrição** da tool MCP |
| Integração padrão (Jira, GitHub) | Servidor **da comunidade**; custom só para o fluxo do time |
| Procurar **conteúdo** | **Grep** |
| Procurar por **nome/extensão** | **Glob** |
| Criar / substituir arquivo inteiro | **Write** |
| Mudança pontual | **Edit** (âncora única) |
| Edit falhou por âncora não única | **Read + Write** |
| Entender um fluxo | Grep pontos de entrada → Read → seguir imports |
| Função usada via wrapper | Listar nomes exportados → Grep de cada |

## Glossário

- **Host** — quem conecta aos servidores MCP: Claude Code ou o seu agente do Agent SDK.
- **Resource** — conteúdo somente leitura do servidor; catálogo (issues, docs, schema).
- **Chamada exploratória** — chamada de tool feita só para descobrir o que existe.
- **Âncora (`old_string`)** — texto que o Edit procura; precisa ser único.
- **Wrapper module** — fachada/barrel que reexporta uma função com outros nomes.

## Cola de véspera

- **Time = `.mcp.json`** (raiz, git). **Pessoal/experimental = `~/.claude.json`**. "User" não é errado.
- **Segredo = `${GITHUB_TOKEN}`**; valor no ambiente de cada dev/CI. Token literal, `.gitignore` + wiki,
  token no CLAUDE.md → errado.
- **Todas as tools de todos os servidores**, descobertas na conexão, **ao mesmo tempo**. Seletor,
  servidor fundido, roteador → errado.
- **Resources = catálogos** (resumos de issues, hierarquia de docs, schema) → menos chamadas
  exploratórias. Tool `list_*` a cada sessão ou tudo no prompt → pior. Ação continua tool.
- **Agente prefere Grep à tool MCP** → descrição com capacidades e saídas. "Always use X" no CLAUDE.md,
  negar Grep, hook roteador → errado.
- **Jira/GitHub → comunidade**; custom só para workflow do time. **Falha MCP → `isError`** (M04).
- **Grep = conteúdo** (chamadores, mensagens, imports). **Glob = nome/caminho** (`**/*.test.tsx`).
- **Write = inteiro/novo; Edit = pontual, âncora única; Edit não único → Read + Write.**
- **Explorar:** Grep pontos de entrada → Read → seguir imports; nunca ler tudo antes.
- **Wrapper:** Read do wrapper → nomes exportados → Grep de cada. Bash executa; Explore é do M08.

## Perguntas de checagem

1. **O dev novo não vê o servidor de tickets do time. Onde estava e onde deveria estar?**
   No `~/.claude.json` de cada um (não compartilhado); deveria estar no `.mcp.json` do repo.
2. **Engenheira quer testar um servidor experimental sem afetar ninguém. Onde configura?**
   `~/.claude.json` (user-level); se virar ferramenta do time, promove para o `.mcp.json` via PR.
3. **Como compartilhar um servidor que exige token sem commitar o token?**
   `.mcp.json` com `"Bearer ${GITHUB_TOKEN}"`; cada dev/CI define a variável no próprio ambiente.
4. **O agente tem 3 servidores MCP. Quais tools ele pode usar?** As dos três, ao mesmo tempo.
5. **O agente faz 10 buscas para descobrir quais tabelas existem. O que expor?** O schema como resource.
6. **O agente ignora a tool MCP de referências cross-repo e usa Grep. Primeira correção?** Detalhar a
   descrição da tool MCP (capacidades, entrada, saída, quando usar).
7. **Grep ou Glob: (a) todos os `*.spec.ts`; (b) onde é gerada a mensagem "Seat already reserved"?**
   (a) Glob; (b) Grep.
8. **O Edit falhou porque o trecho aparece 7 vezes. Resposta de prova?** Read inteiro + Write.
9. **Função reexportada por um wrapper com dois aliases: como achar todos os usos?** Ler o wrapper,
   listar os nomes exportados e fazer Grep de cada um.
