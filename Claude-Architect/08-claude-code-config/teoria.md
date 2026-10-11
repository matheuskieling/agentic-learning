# Módulo 08 — Configurando o Claude Code: CLAUDE.md, rules, skills, subagents, permissões e tools nativas

> **Domínio D3 (20%)** + o task statement **2.5** do D2 (tools nativas). Cai sobretudo nos cenários
> **2 (Code Generation with Claude Code)** e **4 (Developer Productivity with Claude)**, e aparece no
> **5 (CI)** quando a pergunta é "onde fica essa configuração para valer também no pipeline".
>
> A pergunta-mãe deste módulo é sempre a mesma: **"onde esta instrução/configuração deve morar?"**
> A resposta certa é a que tem o **escopo certo** (quem é afetado), o **custo de contexto certo**
> (carrega só quando precisa) e o **mecanismo certo** (orientação → texto; regra crítica → permissão/hook).

---

## 1. Superfícies: o mesmo motor em todo lugar

**Fato-chave.** CLI, extensões de IDE (VS Code/Cursor, JetBrains), app desktop, web e mobile rodam o
**mesmo motor** do Claude Code. Por isso **CLAUDE.md, settings, skills, subagents, hooks e MCP valem
igual** em todas as superfícies. Configurou no repositório, vale para quem abrir pela IDE, pelo
terminal ou pela web. O `claude -p` do CI (Módulo 09) também é o mesmo motor.

**Por quê.** A configuração mora em **arquivos** (no repo ou em `~/.claude/`), não na interface.

**Anti-padrão (alternativa errada).** "Configurar as regras do time na extensão do VS Code de cada
dev" ou "duplicar o CLAUDE.md para a versão web". Não precisa, porque é o mesmo motor lendo os mesmos arquivos.

**Agendamento [volátil].** Três jeitos de rodar algo "sozinho":
- **Routines (nuvem):** rodam na infra da Anthropic, disparadas por agenda, API ou evento do GitHub,
  **com a sua máquina desligada**.
- **Tarefas agendadas no desktop:** rodam **na sua máquina**: acessam arquivos locais e rede privada.
- **`/loop`:** repetição/polling **dentro da sessão aberta** (morre com a sessão).

**Como cai na prova.** Cenário 4: "o time usa IDEs diferentes; onde colocar as convenções?" A resposta
é o CLAUDE.md do projeto (versionado), não uma configuração por IDE. Agendamento cai como princípio:
precisa rodar com a máquina desligada → nuvem; precisa da rede interna → local.

---

## 2. Hierarquia do CLAUDE.md

**Fato-chave: os níveis, do mais geral ao mais específico.**

| Nível | Onde | Quem vê | Uso típico |
|-------|------|---------|-----------|
| **Managed policy** | caminho do sistema (ex.: `/etc/claude-code/CLAUDE.md`) ou `claudeMd` em managed settings | toda a organização; **não pode ser excluído** | padrões de compliance, segurança |
| **Usuário** | `~/.claude/CLAUDE.md` | só você, em **todos** os projetos | suas preferências pessoais |
| **Projeto** | `./CLAUDE.md` ou `./.claude/CLAUDE.md` | **o time** (versionado no git) | arquitetura, comandos de build/teste, convenções |
| **Local** | `./CLAUDE.local.md` (no `.gitignore`) | só você, **neste** projeto | URL do seu sandbox, seus dados de teste |
| **Subdiretório** | `pasta/CLAUDE.md` | quem trabalha naquela pasta | convenção específica de um módulo |

**Como carregam:**
- Os CLAUDE.md do diretório de trabalho **e de todos os diretórios acima** carregam **no início**.
- Os de **subdiretórios abaixo** carregam **sob demanda**: quando o Claude lê/edita um arquivo daquela pasta.
- Tudo é **concatenado** (não um sobrescreve o outro). O mais próximo de onde você está é lido por
  último; em cada pasta, o `CLAUDE.local.md` vem depois do `CLAUDE.md`.
- CLAUDE.md é **contexto, não enforcement**: o modelo segue com alta probabilidade, não com garantia.

**`@import`.** Dentro do CLAUDE.md, `@caminho/arquivo.md` expande o arquivo no contexto.
- Caminho relativo resolve **a partir do arquivo que importa** (não do diretório de trabalho); `@~/...` = home.
- Imports podem ser recursivos com profundidade máxima pequena (a doc atual diz **4 saltos**).
- Import **organiza**, mas **não economiza contexto**: o importado carrega no início junto.
- Dentro de bloco de código/crase, `@algo` **não** é importado.

```markdown
# CLAUDE.md (raiz do repositório, versionado)
Visão geral do projeto: @README.md
Comandos disponíveis: @docs/comandos.md

## Convenções
- API em ASP.NET Core; toda rota nova precisa de teste de integração.
- Rode `dotnet test` antes de dizer que terminou.

## Preferências pessoais (cada dev mantém o seu, fora do git)
@~/.claude/minhas-preferencias.md
```

**`AGENTS.md`.** O Claude Code lê o `AGENTS.md` **quando não há CLAUDE.md** (nem `CLAUDE.local.md`)
no diretório de trabalho ou acima. **Com ambos, o CLAUDE.md vence** (o AGENTS.md é ignorado por
padrão). Para usar os dois, **importe**: `@AGENTS.md` dentro do CLAUDE.md, uma fonte só para vários agentes.

**Auto memory.** Notas que o **próprio Claude** escreve (aprendizados, correções suas) em
`~/.claude/projects/<projeto>/memory/MEMORY.md` + arquivos por tema. No início da sessão carregam
as **primeiras 200 linhas ou 25 KB** do `MEMORY.md`. É **local da máquina** (não vai para o git,
não é compartilhada com o time).

**Monorepo.**
- `claudeMdExcludes` (em settings) pula CLAUDE.md de outros times por caminho/glob. O managed **não** pode ser excluído.
- `--add-dir ../outro` dá acesso a outro diretório. Por padrão os CLAUDE.md de lá **não** carregam (há variável de ambiente para ligar).

**Por quê.** Cada nível responde "quem precisa ver isso?". Instrução do time no lugar pessoal = o time
não vê; preferência pessoal no arquivo do time = polui o contexto de todo mundo.

**Anti-padrões (alternativas erradas).**
- Convenção do time em `~/.claude/CLAUDE.md` → "funciona na minha máquina", o colega não recebe.
- URL do seu sandbox no `CLAUDE.md` versionado → vai para todos; o lugar é `CLAUDE.local.md`.
- CLAUDE.md gigante (milhares de linhas) com tudo de todas as pastas → diluição e custo; mire em **< 200 linhas**
  e mova o específico para rules com `paths` ou CLAUDE.md de subdiretório.
- Achar que o CLAUDE.md **impede** uma ação. Para bloquear de verdade: `permissions.deny` ou hook `PreToolUse`.

**Como cai na prova.** Cenário 2: "um dev novo não recebe as convenções que o outro recebe" → a
convenção estava no `~/.claude/CLAUDE.md` do veterano; mova para o CLAUDE.md do projeto. Pegadinha:
alternativa que sugere "pedir para cada dev copiar o arquivo".

---

## 3. Regras em `.claude/rules/` e regras por caminho (3.3)

**Fato-chave.** Arquivos `.md` em `.claude/rules/` (busca recursiva) dividem instruções por tema.
- **Sem frontmatter `paths`** → carrega **sempre**, no início (igual ao CLAUDE.md).
- **Com `paths:`** (lista de globs) → carrega **só quando o Claude toca um arquivo que bate** (Read/Write/Edit).

```markdown
---
paths:
  - "**/*Tests.cs"
  - "tests/**/*.cs"
---

# Convenções de teste
- xUnit + FluentAssertions; nome do método: Metodo_Cenario_ResultadoEsperado.
- Nada de Thread.Sleep: use o FakeTimeProvider.
- Um Assert lógico por teste; Arrange/Act/Assert separados por linha em branco.
```
*(arquivo `.claude/rules/testes.md`)*

**Por quê.** Convenções que **atravessam diretórios** (todos os testes, espalhados por 30 projetos)
não cabem num CLAUDE.md de pasta. Um glob cobre **todas as pastas, inclusive as futuras**, e só gasta
contexto quando é relevante.

**Anti-padrões.**
- Copiar o mesmo CLAUDE.md em cada pasta de testes → duplicação, divergência, não cobre pasta nova.
- Pôr tudo no CLAUDE.md raiz → carrega sempre, mesmo quando o Claude está mexendo em CSS.
- Skill para "convenção de teste" → skill é para **tarefa/procedimento** sob demanda; convenção
  que deve valer **sempre que mexer em X** é rule com `paths`.

**Como cai na prova.** Cenário 2: "os testes ficam ao lado do código em dezenas de pastas; como
aplicar a convenção só quando o Claude edita testes?" → `.claude/rules/` com `paths: ["**/*.test.ts"]`.

---

## 4. Skills e comandos (3.2)

**Fato-chave: comandos foram fundidos em skills.** `.claude/commands/deploy.md` e
`.claude/skills/deploy/SKILL.md` criam o **mesmo** `/deploy`. Se coexistirem com o mesmo nome,
**a skill vence**. A skill acrescenta pasta para arquivos de apoio, frontmatter e **auto-carregamento**.

**Onde ficam e quem vence em colisão de nome:** **enterprise (managed) > pessoal (`~/.claude/skills/`)
> projeto (`.claude/skills/`)**. Skills de **plugin** têm namespace (`/plugin:skill`), então não colidem.

**Frontmatter (o que mais cai):**

| Campo | Efeito |
|-------|--------|
| `description` (+ `when_to_use`) | **critério de auto-carregamento**: o Claude decide carregar pela descrição |
| `disable-model-invocation: true` | só **você** invoca (ex.: `/deploy` não deve disparar sozinho) |
| `user-invocable: false` | some do menu `/`; só o Claude usa (conhecimento de fundo) |
| `allowed-tools` | tools pré-aprovadas **durante o turno** que invocou a skill |
| `context: fork` (+ `agent`) | roda num **subagent isolado**; não vê o histórico da conversa |
| `paths` | limita o auto-carregamento a arquivos que batem com o glob |
| `argument-hint`, `model`, `hooks` | dica de argumento, modelo do turno, hooks enquanto ativa |

**Argumentos:** `$ARGUMENTS` (string inteira), `$0`, `$1`... (posicionais, base 0).
**Contexto dinâmico:** `` !`git diff HEAD` `` roda o comando **antes** e injeta a saída no texto.

```markdown
---
name: revisar-pr
description: Revisa um PR deste repositório contra as convenções do time. Use quando pedirem review de PR.
argument-hint: "[numero-do-pr]"
disable-model-invocation: true
allowed-tools: Bash(gh pr diff *), Bash(gh pr view *), Read, Grep
context: fork
agent: general-purpose
---

Revise o PR #$0.

## Diff
!`gh pr diff $0`

Para cada achado informe: arquivo, linha, severidade (alta/média/baixa) e correção sugerida.
Ignore estilo que o formatter já corrige.
```
*(arquivo `.claude/skills/revisar-pr/SKILL.md`)*

**O corpo não é relido.** Depois de invocada, o texto renderizado da skill entra **uma vez** na
conversa e fica lá; o Claude Code **não relê** o arquivo a cada turno. Consequência: escreva
**instruções permanentes** ("sempre que…", "para cada…"), não passos de uso único que fiquem
obsoletos. (A permissão de `allowed-tools` não persiste; só o texto.)

**`context: fork`** = subagent isolado: bom para tarefa **ruidosa/delimitada** (pesquisa, review)
que devolve só o resultado. O subagent **não vê seu histórico**, então tudo que ele precisa tem que
estar no próprio SKILL.md/argumentos.

**Plugins.** Pacote distribuível de **skills + subagents + hooks + servidores MCP**, com namespace
(`/meu-plugin:revisar`). É a forma de **compartilhar entre repositórios/times**.

**Anti-padrões.**
- `description` vaga ("ajuda com coisas") → nunca auto-carrega, ou carrega na hora errada.
- Skill de efeito colateral (deploy, migração) **sem** `disable-model-invocation: true` → o modelo pode disparar sozinho.
- Esperar que a skill "relembre" um passo porque o arquivo foi editado no meio da sessão → não é relido.
- Usar skill para regra que precisa valer sempre → isso é CLAUDE.md/rule.

**Como cai na prova.** Cenário 2: "o comando `/review` do time deve ficar disponível para todos ao
clonar o repo" → `.claude/skills/review/SKILL.md` (ou `.claude/commands/review.md`) **versionado**,
não em `~/.claude/`. Pegadinha: confundir o escopo pessoal com o do projeto, ou achar que command e skill de mesmo nome "se somam".

---

## 5. settings.json: hierarquia e permissões

**Fato-chave: precedência (maior → menor).**
1. **Managed** (`managed-settings.json`, MDM, console): a organização; **nada abaixo sobrescreve**.
2. **Linha de comando** (`--settings`, flags da sessão).
3. **Local do projeto**: `.claude/settings.local.json` (pessoal, gitignored).
4. **Projeto compartilhado**: `.claude/settings.json` (versionado, o time).
5. **Usuário**: `~/.claude/settings.json` (você, todos os projetos).

Chaves escalares: vence o nível mais alto. **Listas (como `permissions.allow`/`deny`) se mesclam** entre os níveis.

**Permissões: `allow` / `ask` / `deny`.** Avaliação: **deny → ask → allow**; o primeiro que casar
nessa ordem decide. **Allow não abre exceção num deny**, e a especificidade não muda a ordem.

```json
{
  "permissions": {
    "allow": [
      "Bash(dotnet build *)",
      "Bash(dotnet test *)",
      "Bash(npm run test:*)",
      "Read(./src/**)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./secrets/**)",
      "Bash(curl *)",
      "WebFetch"
    ],
    "defaultMode": "default"
  },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [ { "type": "command", "command": ".claude/hooks/bloquear-prod.sh" } ] }
    ]
  }
}
```
*(arquivo `.claude/settings.json`)*

Sintaxe das regras: `Tool` (a tool toda) ou `Tool(especificador)`. Em Bash, ` *` no fim = **prefixo**
(`Bash(dotnet test *)` casa `dotnet test --filter X`); o sufixo `:*` é forma **equivalente**
(`Bash(npm run test:*)`). Atenção ao espaço: `Bash(git diff *)` não casa `git diff-index`.
Caminhos: `Read(./.env)`, `Edit(./src/**)`. Web: `WebFetch(domain:docs.microsoft.com)`.

**Por quê.** Permissão é **enforcement determinístico**: diferente do CLAUDE.md (que o modelo pode
não seguir), um `deny` **impede** a chamada. Regra crítica (segredos, produção) → `deny`/hook.

**Anti-padrões.**
- "Nunca leia o .env" **só no CLAUDE.md** → probabilístico; o certo é `deny: ["Read(./.env)"]`.
- Tentar liberar um comando no `settings.local.json` contra um `deny` do projeto/managed → deny vence sempre.
- Colocar a allowlist do time no `settings.local.json` → não é versionado, o time não recebe.
- `"allow": ["Bash"]` (tudo) para "parar de pedir permissão" → amplo demais; prefira prefixos.

**Como cai na prova.** Cenário 4/5: "o time quer que `dotnet test` rode sem prompt mas que ninguém
consiga ler `secrets/`" → `allow` com prefixo + `deny` de caminho no `.claude/settings.json` versionado.
Pegadinha: alternativa "instruir no CLAUDE.md" (não é garantia) ou "managed" quando a necessidade é só do projeto.

---

## 6. Modos de permissão e plan mode vs. execução direta (3.4)

**Modos** (via `--permission-mode`, `defaultMode` em settings, ou **Shift+Tab** na sessão):

| Modo | Roda sem perguntar | Para quê |
|------|--------------------|----------|
| `default` (Manual) | só leituras | revisar cada ação |
| `acceptEdits` | leituras + edições de arquivo + comandos básicos de FS | iterar em código que você está revisando |
| `plan` | só leitura/exploração; **não edita** até você aprovar o plano | explorar e desenhar antes de mudar |
| `auto` | quase tudo, com um **classificador** revisando as ações | tarefas longas com menos prompts |
| `dontAsk` | só o pré-aprovado; **o resto é negado** (não pergunta) | CI/scripts travados |
| `bypassPermissions` | tudo | **só** container/VM isolado |

**Plan mode.** O Claude **lê, explora, propõe um plano e pede aprovação**; só então edita.
Use quando: **mudança multi-arquivo**, **decisão arquitetural**, **várias abordagens válidas**,
**escopo grande ou requisito confuso** (ex.: migrar a biblioteca de logging em 45+ arquivos;
trocar a estratégia de autenticação).

**Execução direta.** Escopo **óbvio** e **pequeno**: um arquivo, instrução clara, correção conhecida
(null check, renomear constante, bug com stack trace apontando a linha).

**Por quê.** Plan mode custa uma rodada a mais, mas evita retrabalho caro quando a abordagem é
incerta. Em mudança trivial, é só atrito.

**Anti-padrões.**
- Plan mode para trocar uma string num arquivo → overhead sem ganho.
- Execução direta numa migração de 45 arquivos com 3 abordagens possíveis → descobre o problema no arquivo 30.
- `bypassPermissions` "para a tarefa longa andar sozinha" na máquina do dev → não é rotina; use
  `acceptEdits`/allowlist, ou `auto`, e bypass só em ambiente isolado.

**Como cai na prova.** Cenário 2, quase certo: "qual abordagem para esta tarefa?" Leia o tamanho e a
incerteza: **multi-arquivo/arquitetural/ambíguo → plan mode; pontual e claro → direto**.

---

## 7. Subagents: nativos e customizados (3.4)

**Nativos.**
- **Explore**: **somente leitura**, busca e análise de codebase; devolve **só a conclusão** (não as dezenas de arquivos lidos).
- **Plan**: **somente leitura**, pesquisa durante o plan mode.
- Explore e Plan **não carregam o CLAUDE.md** (nem o auto memory): são enxutos de propósito. Se a
  exploração depende de uma convenção do projeto, diga isso no prompt de delegação.
- **general-purpose**: tarefa multi-etapas que precisa **explorar e agir** (todas as tools).

Por que usar: o subagent tem **contexto próprio e isolado**; o ruído (50 arquivos lidos) fica lá
e só o resumo volta, preservando a janela da conversa principal. Ele **não recebe o histórico** da
conversa, então o prompt de delegação precisa ser **explícito**.

**Customizados** em **`.claude/agents/`** (projeto, versionado) ou `~/.claude/agents/` (pessoal).
Markdown + frontmatter. Só `name` e `description` são obrigatórios; a `description` diz **quando
delegar**.

```markdown
---
name: revisor-seguranca
description: Revisa mudanças em busca de vulnerabilidades (injeção, segredos, authz). Use após alterações em controllers ou auth.
tools: Read, Grep, Glob
model: sonnet
permissionMode: default
---

Você é um revisor de segurança de aplicações ASP.NET Core.
Para cada achado informe arquivo, linha, categoria (OWASP), severidade e correção.
Não edite arquivos: apenas reporte.
```
*(arquivo `.claude/agents/revisor-seguranca.md`)*

Campos úteis: `tools` (allowlist: **menor privilégio**), `disallowedTools`, `model`,
`permissionMode`, `skills`, `hooks`, `mcpServers`, `maxTurns`.

**Permissão do pai desce.** Um subagent **não pode escalar** além do modo da conversa principal: se
o pai está em `bypassPermissions`, `acceptEdits` ou `auto`, o subagent herda esse modo e o
`permissionMode` dele é ignorado; e um subagent configurado como `bypassPermissions` **não ganha**
bypass numa sessão em `default`. Se o pai está em `default`, `dontAsk` ou `plan`, o subagent pode usar
o próprio `permissionMode` (ex.: `acceptEdits`), mas **nunca** vira bypass. As regras `deny` também continuam valendo.

**Anti-padrões.**
- Subagent de review com `Write`/`Edit` "por via das dúvidas" → viola menor privilégio.
- Achar que o subagent "lembra" o que foi discutido na conversa → contexto isolado; passe explícito.
- Usar `permissionMode: bypassPermissions` no subagent para "furar" o modo do pai → não funciona.
- Ler 40 arquivos na conversa principal para responder "onde se trata autenticação?" → delegue ao **Explore**.

**Como cai na prova.** Cenário 4: "a exploração do codebase está enchendo o contexto e a sessão
degrada" → **Explore** (ou subagent customizado só-leitura) que devolve resumo. Cenário 2: "o time
quer um revisor padronizado para todos" → `.claude/agents/` versionado com `tools` restritas.

---

## 8. Tools nativas e exploração incremental (2.5)

| Tool | Para quê | Nota de prova |
|------|----------|---------------|
| **Grep** | buscar **conteúdo** (regex) nos arquivos | achar onde algo é usado/definido |
| **Glob** | achar **arquivos por padrão de nome** (`**/*Controller.cs`) | não lê conteúdo |
| **Read** | ler um arquivo | |
| **Write** | **criar**/sobrescrever arquivo inteiro | |
| **Edit** | trocar um trecho **exato e único** (`old_string` → `new_string`) | falha se o trecho não for único |
| **Bash** | rodar comandos (build, teste, git) | sujeito a permissões |
| **WebSearch / WebFetch** | buscar na web / ler uma URL | |
| **Agent** | criar subagent para trabalho delimitado/ruidoso | antiga `Task` |
| **Skill** | invocar uma skill | |
| **NotebookEdit**, **AskUserQuestion**, **ToolSearch** | notebook; perguntar ao usuário; carregar tools sob demanda | |

**Exploração incremental (o padrão que a prova cobra):**
**Grep pelos pontos de entrada → Read do que importa → Grep pelos imports/usos → Read** …
construindo entendimento aos poucos. Para descobrir *quais arquivos existem*, **Glob**; para
*onde está o conteúdo*, **Grep**.

**Edit exige trecho único.** Se `old_string` aparece mais de uma vez (ou não aparece), o Edit
**falha**. Correção: **ampliar o trecho** com contexto ao redor até ficar único, usar `replace_all`
quando a intenção é trocar todas, ou **ler o arquivo e reescrevê-lo** (Write) se a mudança é extensa.

**Anti-padrões.**
- **Ler o repositório inteiro de antemão** "para ter contexto" → gasta a janela e degrada a qualidade.
- Usar **Glob** para achar onde uma função é chamada → Glob não olha conteúdo; é Grep.
- Usar `Bash` com `cat`/`grep` para tudo quando há tools dedicadas → menos controle de permissão e saída pior.
- Repetir o mesmo Edit que falhou por ambiguidade → amplie o trecho.

**Como cai na prova.** Cenário 4: "o dev pergunta como o fluxo de pagamento funciona num repo de
2.000 arquivos" → Grep por `PaymentService`/rota de entrada, lê, segue as dependências com Grep; ou
delega a exploração ao Explore. Pegadinha: "carregar todos os arquivos `.cs` no contexto primeiro".

---

## Tabela de decisão

| Se… | Faça… |
|-----|-------|
| Convenção vale para **todo o time** neste repo | `./CLAUDE.md` (ou `.claude/CLAUDE.md`) versionado |
| Preferência **só sua** em **todos** os projetos | `~/.claude/CLAUDE.md` |
| Preferência **só sua** **neste** projeto (sandbox, dados de teste) | `CLAUDE.local.md` (gitignored) |
| Política de compliance para a **empresa inteira** | managed CLAUDE.md / managed settings |
| Convenção que se aplica a **arquivos espalhados** (todos os testes) | `.claude/rules/x.md` com `paths:` glob |
| Convenção de **um módulo/pasta** específico | CLAUDE.md naquele subdiretório (carrega sob demanda) |
| Repo já tem `AGENTS.md` e você quer CLAUDE.md também | `@AGENTS.md` dentro do CLAUDE.md |
| CLAUDE.md de outros times no monorepo atrapalhando | `claudeMdExcludes` |
| Procedimento reutilizável invocado com `/nome` | skill em `.claude/skills/<nome>/SKILL.md` |
| Skill com efeito colateral (deploy) | `disable-model-invocation: true` |
| Skill ruidosa (pesquisa/review) que deve devolver só o resultado | `context: fork` |
| Compartilhar skills+agents+hooks entre repositórios | **plugin** |
| **Impedir** algo (ler segredo, comando perigoso) | `permissions.deny` (ou hook `PreToolUse`), não CLAUDE.md |
| Liberar comando seguro sem prompt para o time | `permissions.allow` com prefixo no `.claude/settings.json` |
| Mudança multi-arquivo, arquitetural, ambígua | **plan mode** |
| Fix pontual com escopo claro | execução direta |
| Exploração volumosa de codebase | subagent **Explore** (devolve só a conclusão) |
| Revisor padronizado do time | subagent em `.claude/agents/` com `tools` restritas |
| Achar arquivo por nome / achar uso no conteúdo | **Glob** / **Grep** |
| `Edit` falhou por trecho ambíguo | amplie o `old_string` (ou `replace_all`, ou leia e reescreva) |

## Glossário

- **CLAUDE.md**: instruções persistentes carregadas no contexto; orientam, não garantem.
- **`CLAUDE.local.md`**: instruções pessoais de um projeto, fora do git.
- **Managed policy**: configuração imposta pela organização; topo da hierarquia, não excluível.
- **`@import`**: inclusão de outro arquivo dentro do CLAUDE.md; caminho relativo ao arquivo que importa.
- **Rule (`.claude/rules/`)**: arquivo de instruções por tema; com `paths:` carrega só ao tocar arquivos que batem.
- **Auto memory**: `MEMORY.md` escrito pelo Claude; 200 linhas/25 KB no início; local da máquina.
- **Skill**: pacote `SKILL.md` (+ apoio) invocável por `/nome` ou auto-carregado pela `description`.
- **`context: fork`**: executa a skill num subagent isolado.
- **Plugin**: pacote com namespace de skills, subagents, hooks e MCP.
- **Permission mode**: postura da sessão (`default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`).
- **Plan mode**: explora e propõe plano; só edita após aprovação.
- **Subagent**: instância com contexto isolado criada pela tool `Agent`; nativos Explore/Plan/general-purpose.
- **Exploração incremental**: Grep → Read → Grep → Read, em vez de ler tudo de antemão.

## Cola de véspera

- **Mesmo motor** em CLI/IDE/desktop/web: configure **arquivos**, não a interface.
- CLAUDE.md: **managed → usuário → projeto → local → subdiretório (sob demanda)**. Tudo concatena.
- Time = **projeto versionado**. Só você = `~/.claude/` ou `CLAUDE.local.md`.
- `@import` relativo ao arquivo que importa; não economiza contexto. `AGENTS.md` só sem CLAUDE.md; com ambos, CLAUDE.md vence → `@AGENTS.md`.
- `.claude/rules/`: sem `paths` = sempre; **com `paths` = só ao tocar arquivo que bate** → convenção que atravessa pastas.
- Auto memory: 200 linhas/25 KB, **local da máquina**.
- Commands **fundidos** em skills; mesmo nome → **skill vence**. Prioridade: **enterprise > pessoal > projeto**; plugin tem namespace.
- `description` = gatilho de auto-carregamento. `disable-model-invocation` para efeito colateral. `context: fork` = subagent isolado. `$ARGUMENTS`/`$0`. Corpo **não é relido**.
- Settings: **managed > CLI > local > projeto > usuário**; listas se mesclam; **deny → ask → allow**; allow não fura deny.
- `Bash(dotnet test *)` = prefixo; `:*` equivalente. Segredo → `deny: Read(./.env)`, não prompt.
- **Plan mode** = multi-arquivo/arquitetural/ambíguo. **Direto** = pontual e claro. `bypassPermissions` só em ambiente isolado.
- Subagents nativos: **Explore/Plan (só leitura)**, general-purpose. Custom em `.claude/agents/`. **Não escala** o modo do pai.
- Tools: **Grep = conteúdo, Glob = nome de arquivo**. Explore aos poucos. **Edit precisa de trecho único**.

## Perguntas de checagem

1. **Um dev colocou "use xUnit, nunca MSTest" no `~/.claude/CLAUDE.md` e o colega não recebe a regra. Qual a correção?**
   Mover para o `CLAUDE.md` do projeto (versionado). O arquivo do usuário só vale para aquele dev.
2. **Os testes ficam ao lado do código em 40 pastas. Onde pôr a convenção de testes para carregar só quando necessário?**
   Em `.claude/rules/testes.md` com `paths:` glob para os arquivos de teste. Cobre pastas futuras e não gasta contexto à toa.
3. **O projeto tem `allow: ["Bash(git push *)"]` no `settings.local.json` de um dev e `deny: ["Bash(git push *)"]` no `.claude/settings.json`. O push roda?**
   Não. Deny é avaliado primeiro e allow não abre exceção, independentemente do nível.
4. **Migrar o cliente HTTP em 60 arquivos, com duas estratégias possíveis: plan mode ou direto?**
   Plan mode: é multi-arquivo, tem decisão de abordagem e escopo grande. Explore, proponha e aprove antes de editar.
5. **O `Edit` falhou porque `return null;` aparece 7 vezes no arquivo. O que fazer?**
   Ampliar o `old_string` com linhas ao redor até ficar único (ou `replace_all` se a ideia é trocar todas), em vez de repetir a mesma chamada.
