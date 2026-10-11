# Módulo 05 — MCP: arquitetura, transportes, escopos, `.mcp.json`, autenticação

> Domínio **D2 — Design de tools & integração MCP (18%)**. Task statement **2.4**.
> Cenários onde mais cai: **1 (Customer Support)** — tools do agente expostas via MCP —,
> **4 (Developer Productivity)** — servidores MCP no Claude Code do time — e **2 (Code Generation)**.

Ideia central: **MCP (Model Context Protocol)** é um **padrão aberto** para conectar modelos a dados e
tools. Você escreve o servidor **uma vez** e qualquer host compatível (Claude Code, Claude Desktop,
Agent SDK, IDEs...) o usa. A prova cobra três coisas: **como a arquitetura funciona**, **qual
primitiva/transporte/escopo escolher** e **como configurar sem vazar segredo**.

---

## 1. Arquitetura: host, client, server (1:1) e JSON-RPC

**Fato-chave.**
- **Host**: a aplicação com o modelo (ex.: Claude Code). Gerencia as conexões e a segurança.
- **Client**: componente dentro do host; o host roda **um client por server** (conexão **1:1**).
- **Server**: o programa que expõe capacidades (tools, resources, prompts).

Protocolo: **JSON-RPC 2.0** (requests com `id`, responses, notificações sem `id`). Ciclo de vida:

```
client → initialize            (protocolVersion, capabilities, clientInfo)
server → resposta              (protocolVersion, capabilities, serverInfo)
client → notifications/initialized
client → tools/list            (descobre as tools)
client → tools/call            (executa uma tool)
```

Na **inicialização** client e server **negociam versão e capabilities** (o server declara se tem
tools/resources/prompts; o client declara se suporta sampling/elicitation/roots).

```json
{ "jsonrpc": "2.0", "id": 2, "method": "tools/call",
  "params": { "name": "buscar_pedido", "arguments": { "order_id": "PED-123456" } } }
```

Resultado de tool MCP com erro de execução: `"isError": true` no resultado (o modelo vê e raciocina —
mesma lógica de erro estruturado do Módulo 04). Erro de **protocolo** (método inexistente, params
inválidos) é erro JSON-RPC.

No Claude Code, tools MCP aparecem para o modelo com o nome **`mcp__<server>__<tool>`** (é esse nome
que vai em permissões e hooks, ex.: `mcp__github__create_issue`).

**Anti-padrões:** achar que um client fala com vários servers; achar que o modelo "fala MCP" direto
(quem fala é o client do host); pular `initialize` e chamar `tools/call`.

**Como cai na prova.** Pergunta conceitual: "quantos clients o Claude Code cria para 3 servers
configurados?" → **3**. Ou a ordem do handshake (`initialize` → `notifications/initialized` → `tools/list`).

---

## 2. Primitivas: tools, resources, prompts (server) e sampling, elicitation, roots (client)

**Primitivas do server:**

| Primitiva | O que é | Quem controla |
|-----------|---------|---------------|
| **Tools** | funções executáveis com efeito/consulta (`tools/list`, `tools/call`) | o **modelo** decide chamar |
| **Resources** | conteúdo **somente leitura** endereçado por URI (`resources/list`, `resources/read`), catálogo navegável | a **aplicação/usuário** escolhe anexar |
| **Prompts** | templates reutilizáveis (`prompts/list`, `prompts/get`) | o **usuário** invoca |

No Claude Code: resources são referenciados com **`@server:protocolo://caminho`**; prompts viram
**slash commands** `/mcp__<server>__<prompt>`.

**Primitivas do client** (o server pede algo ao host):
- **Sampling**: o server pede **uma completion ao modelo** do host (sem ter API key própria).
- **Elicitation**: o server pede **input ao usuário** no meio da operação (ex.: confirmar, preencher campo).
- **Roots**: o client informa os **limites de URI/filesystem** em que o server pode operar.

**Resource vs. tool — quando usar cada um:**
- **Resource**: dado para **ler/contextualizar** (schema do banco, documentação, catálogo de
  tabelas, arquivos de configuração). Um **catálogo navegável reduz chamadas exploratórias às cegas**
  — o modelo/usuário vê o que existe em vez de "chutar" buscas.
- **Tool**: **ação** ou consulta parametrizada com efeito (criar ticket, executar query, emitir reembolso).

**Anti-padrões:** expor documentação estática como uma tool `get_doc(nome)` que o agente tem que
adivinhar; usar resource para algo com efeito colateral; confundir sampling (server pede ao modelo)
com elicitation (server pede ao usuário); confundir roots com permissões do Claude Code.

**Como cai na prova.** Cenário 4: "o agente faz dezenas de chamadas `search_tables` às cegas para
descobrir o schema do banco". Resposta: **expor o schema/catálogo como resources**. Pegadinha:
"aumentar o limite de chamadas" ou "colocar o schema inteiro no system prompt" (estático, gasta contexto).

---

## 3. Transportes: stdio, Streamable HTTP, SSE (legado)

| Transporte | Onde roda | Notas |
|------------|-----------|-------|
| **stdio** | processo **local** iniciado pelo host | implícito quando há `command`; protocolo no stdin/stdout — **logs vão para stderr** (escrever no stdout corrompe o JSON-RPC) |
| **Streamable HTTP** (`"type": "http"`) | **remoto** | o padrão para servidores remotos; **o único remoto com OAuth** no Claude Code |
| **SSE** (`"type": "sse"`) | remoto | **legado/depreciado**; prefira HTTP |
| [volátil] WebSocket | remoto | confira na doc |

**Pegadinha do `url` sem `type`:** uma entrada com `url` mas **sem `type`** é lida como **stdio**
(sem `command`) e **falha**. Em servidor remoto, **sempre declare `"type": "http"`**.

```json
{ "mcpServers": { "crm": { "url": "https://mcp.crm.exemplo.com/mcp" } } }
```
↑ errado (sem `type`). Certo:
```json
{ "mcpServers": { "crm": { "type": "http", "url": "https://mcp.crm.exemplo.com/mcp" } } }
```

**Como cai na prova.** Cenário 4: "o time adicionou um server remoto no `.mcp.json` com só `url` e
ele não conecta". Resposta: **adicionar `"type": "http"`**. Pegadinha: "trocar para SSE" (legado e
não é a causa) ou "reiniciar com `--debug`" (diagnostica, não corrige).

---

## 4. Escopos de instalação: local, project, user, managed

| Escopo | Visível em | Compartilhado? | Onde fica |
|--------|-----------|----------------|-----------|
| **local** (**padrão**) | **só este projeto**, só você | não | `~/.claude.json` (na entrada do projeto) |
| **project** | este projeto, **todo o time** | **sim, via git** | **`.mcp.json` na raiz** do repo |
| **user** | **todos os seus projetos** | não | `~/.claude.json` |
| **managed** | toda a organização | empurrado pelo admin | arquivo de política gerenciada (`managed-mcp.json`) [volátil: caminhos] |

**Pegadinha:** o escopo **local** do MCP **não é** o `.claude/settings.local.json`. Ele fica em
`~/.claude.json`. (O `settings.local.json` é para *settings* pessoais do projeto, não para servers MCP.)

Mesmo nome em mais de um escopo: **local > project > user** (o mais específico vence).

**Como escolher:**
- Server que **o time inteiro** precisa (ex.: GitHub, Jira do projeto) → **project** (`.mcp.json` versionado).
- Server **pessoal experimental** neste projeto, ou com credencial só sua → **local**.
- Ferramenta **sua em todo projeto** (ex.: seu server de notas) → **user**.
- Governança corporativa (lista permitida/negada de servers) → **managed**.

**Como cai na prova.** Cenário 2/4: "novo dev clona o repo e não tem o server de Jira que o resto do
time usa; cada um configurou com `claude mcp add` sem flags". Causa: o padrão é **local**. Correção:
**`--scope project`** (gera/atualiza o `.mcp.json`) e commitar.

---

## 5. O `.mcp.json`: formato, segredos e aprovação

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_TOKEN}" }
    },
    "banco-local": {
      "command": "dotnet",
      "args": ["run", "--project", "tools/DbMcpServer"],
      "env": { "DB_CONN": "${DB_CONN:-Server=localhost;Database=dev}" }
    }
  }
}
```

- Raiz: objeto **`mcpServers`**; cada server com **`type`/`url`/`headers`** (remoto) ou
  **`command`/`args`/`env`** (stdio).
- **Segredos via `${VAR}`** (e `${VAR:-default}`), expandidos do ambiente de cada dev. **Nunca**
  token literal num arquivo versionado. A expansão vale em `command`, `args`, `env`, `url` e `headers`.
- **Aprovação:** servers vindos de `.mcp.json` (escopo project) **pedem aprovação** na sessão
  interativa antes de rodar — proteção contra um repo malicioso executar um processo arbitrário. (Há
  settings para pré-aprovar, ex.: `enableAllProjectMcpServers` / `enabledMcpjsonServers`, e
  `claude mcp reset-project-choices` para refazer as escolhas.) [volátil: nomes]

**Anti-padrões:** commitar `"Authorization": "Bearer ghp_abc123..."`; mandar cada dev "editar o
`.mcp.json` com seu token" (vira commit acidental); desligar aprovação globalmente "para agilizar".

**Como cai na prova.** "Como compartilhar o server do time sem expor credenciais?" → **`.mcp.json`
com `${VAR}`**, cada dev define a variável no seu ambiente.

---

## 6. Autenticação: OAuth via `/mcp`, headers, `headersHelper`

| Mecanismo | Quando |
|-----------|--------|
| **OAuth 2.0 via `/mcp`** | server **remoto HTTP** que suporta OAuth; o dev autentica pelo navegador; token guardado e renovado pelo Claude Code |
| **Token estático em `headers`** | API key / PAT simples (com `${VAR}`) |
| **`headersHelper`** | comando que **gera headers na hora** — credencial de **curta duração** (ex.: token de SSO que expira em 1 h) |
| `env` | credencial para server **stdio** local |

**Anti-padrões:** colar token de curta duração em `headers` (expira e quebra); tentar OAuth em stdio
ou SSE legado; guardar token no prompt/CLAUDE.md.

**Como cai na prova.** "O server interno exige token de SSO que expira a cada hora" → **`headersHelper`**.
"Server remoto com OAuth, o dev precisa logar" → **`/mcp`** e autenticar.

---

## 7. `claude mcp add` e comandos

```bash
# Remoto (Streamable HTTP), compartilhado com o time
claude mcp add --transport http --scope project github https://api.githubcopilot.com/mcp/

# Remoto com header
claude mcp add --transport http crm https://mcp.crm.exemplo.com/mcp \
  --header "Authorization: Bearer ${CRM_TOKEN}"

# Local (stdio): tudo depois de -- é o comando do server
claude mcp add --scope user --env DB_CONN=Server=localhost notas -- dotnet run --project NotasMcp

claude mcp list              # lista
claude mcp get github        # detalhes
claude mcp remove github     # remove
claude mcp add-json nome '{"type":"http","url":"..."}'   # a partir de JSON
```

- `--scope local|project|user` (padrão **local**).
- `--transport stdio|http|sse` (padrão stdio).
- **`--`** separa as opções do `claude` do **comando do server** stdio (sem ele, flags do server
  como `-y` seriam interpretadas pelo `claude`).
- Na sessão: **`/mcp`** mostra status, tools e faz o login OAuth.

---

## 8. Escala: tool search de MCP, limites de saída e um server mínimo em C#

**Tool search de MCP** [volátil]: no Claude Code, quando muitas tools MCP são carregadas, a busca
de tools fica ativa por padrão (controle via `ENABLE_TOOL_SEARCH`) — as definições são carregadas sob
demanda, mantendo o que o modelo vê na decisão pequeno (mesma lógica do Módulo 04).

**Limite de saída** [volátil]: saída de tool MCP gera **aviso acima de ~10k tokens** e é
**truncada em ~25k** (ajustável por `MAX_MCP_OUTPUT_TOKENS`). Correção de arquiteto: o **server**
deve devolver **só os campos relevantes**, paginar e filtrar — não "aumentar o limite" como primeira
resposta.

**Server mínimo em C# (só para reconhecimento)** — SDK oficial `ModelContextProtocol`:

```csharp
using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ModelContextProtocol.Server;

var builder = Host.CreateApplicationBuilder(args);
// stdio: logs precisam ir para stderr (stdout é o canal do JSON-RPC)
builder.Logging.AddConsole(o => o.LogToStandardErrorThreshold = LogLevel.Trace);
builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()
    .WithToolsFromAssembly();
await builder.Build().RunAsync();

[McpServerToolType]
public static class PedidoTools
{
    [McpServerTool, Description("Busca UM pedido pelo ID (formato PED-123456). Devolve status e total. Pedido inexistente → found=false.")]
    public static string BuscarPedido([Description("ID no formato PED-123456")] string orderId)
        => $"{{\"found\": true, \"order_id\": \"{orderId}\", \"status\": \"enviado\"}}";
}
```

Repare: o atributo `Description` vira a **description** da tool — as regras do Módulo 04 (descrição =
critério de seleção) valem igual em MCP.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| Todo o time precisa do server | Escopo **project** → `.mcp.json` versionado |
| Só você, só neste projeto | Escopo **local** (padrão) → `~/.claude.json` |
| Você em todos os projetos | Escopo **user** → `~/.claude.json` |
| Organização quer controlar quais servers podem ser usados | **managed** |
| Server remoto não conecta e a entrada só tem `url` | Adicione `"type": "http"` |
| Server remoto com OAuth | Streamable HTTP + login via `/mcp` |
| Token de curta duração | `headersHelper` |
| Token no `.mcp.json` versionado | `${VAR}` / `${VAR:-default}` |
| Agente explora o schema às cegas com muitas chamadas | Exponha como **resources** (catálogo navegável) |
| Ação com efeito colateral | **Tool** |
| Template de instrução reutilizável | **Prompt** (vira slash command) |
| Server precisa de uma completion do modelo | **Sampling** |
| Server precisa de dado/confirmação do usuário | **Elicitation** |
| Limitar onde o server pode mexer no filesystem | **Roots** |
| `claude mcp add` de server stdio com flags próprias | Use `--` antes do comando do server |
| Saída de tool MCP truncada | Server devolve só campos relevantes / pagina |
| Muitas tools MCP | Tool search (sob demanda) |

## Glossário

- **Host / client / server** — aplicação com o modelo / conector 1:1 dentro do host / programa que expõe capacidades.
- **JSON-RPC 2.0** — formato das mensagens MCP (request, response, notificação).
- **`initialize`** — handshake: negocia versão e capabilities; seguido de `notifications/initialized`.
- **Tools / resources / prompts** — ações / conteúdo somente leitura por URI / templates.
- **Sampling / elicitation / roots** — server pede completion ao modelo / input ao usuário / limites de URI.
- **stdio / Streamable HTTP / SSE** — local / remoto padrão (com OAuth) / remoto legado.
- **Escopo local / project / user / managed** — `~/.claude.json` (projeto) / `.mcp.json` / `~/.claude.json` (global) / política da org.
- **`${VAR}`** — expansão de variável de ambiente no `.mcp.json`.
- **`headersHelper`** — comando que gera headers dinâmicos (credencial de curta duração).
- **`mcp__server__tool`** — nome da tool MCP no Claude Code (permissões, hooks).

## Cola de véspera

- **Host** roda **1 client por server** (1:1). **JSON-RPC 2.0**. `initialize` → `notifications/initialized` → `tools/list` → `tools/call`.
- **Server:** tools (ação, o modelo chama) · resources (leitura, URI, catálogo → menos chamadas às cegas) · prompts (templates → slash commands).
- **Client:** sampling (completion ao modelo) · elicitation (input do usuário) · roots (limites de filesystem/URI).
- **Transportes:** stdio (local, `command`, logs no stderr) · **Streamable HTTP** (`"type":"http"`, remoto, **OAuth**) · SSE (legado). **`url` sem `type` = falha** (vira stdio).
- **Escopos:** **local** (padrão, só você, este projeto, `~/.claude.json`) · **project** (`.mcp.json`, git, time) · **user** (`~/.claude.json`, todos os seus projetos) · managed (org). Local ≠ `settings.local.json`. Precedência local > project > user.
- **`.mcp.json`**: `mcpServers` → `type/url/headers` ou `command/args/env`. **Segredo = `${VAR}`**. Servers de projeto pedem **aprovação**.
- **Auth:** OAuth via **`/mcp`** · header estático · **`headersHelper`** (curta duração).
- **CLI:** `claude mcp add [--scope] [--transport http] nome url` · stdio: `claude mcp add nome -- comando args`.
- [volátil] Tool search de MCP ligado por padrão; saída avisa ~10k, trunca ~25k (`MAX_MCP_OUTPUT_TOKENS`) → server devolve menos.

## Perguntas de checagem

1. **O Claude Code tem 4 servers MCP configurados. Quantos clients MCP existem?**
   Quatro — um client por server (1:1), todos dentro do host.
2. **Onde fica um server adicionado com `claude mcp add` sem `--scope`?**
   Escopo local (padrão), em `~/.claude.json` — não em `.claude/settings.local.json` e não no `.mcp.json`.
3. **Uma entrada remota no `.mcp.json` tem só `url` e não conecta. Por quê?**
   Sem `type`, é tratada como stdio; declare `"type": "http"`.
4. **O agente faz dezenas de chamadas para descobrir quais tabelas existem. Qual primitiva resolve?**
   Resources: expor o catálogo/schema como conteúdo navegável somente leitura.
5. **Como compartilhar no git um server que exige token sem expor o token?**
   `.mcp.json` com `"Authorization": "Bearer ${API_TOKEN}"`; cada dev define a variável; ou OAuth via `/mcp` se o server suportar.
