# Módulo 08 — Configurando o Claude Code: CLAUDE.md, rules, commands/skills, plan mode

> **Task statements:** **3.1** (hierarquia e modularização do CLAUDE.md), **3.2** (slash commands e
> skills), **3.3** (rules por caminho), **3.4** (plan mode × execução direta). Domínio **D3**.
> **Onde cai:** cenário **2 (Code Generation with Claude Code)** é o principal; também **4 (Developer
> Productivity)** e **5 (CI)**, porque o `claude -p` do pipeline lê os mesmos CLAUDE.md, rules e
> skills do repositório.
>
> **Pergunta-mãe:** *onde esta instrução mora e quando ela entra no contexto?* Três eixos decidem
> quase toda questão: **escopo** (só eu × o time, via git × uma pasta), **momento de carga** (sempre
> × ao mexer num arquivo que bate × quando alguém invoca) e **isolamento** (conversa principal ×
> contexto separado, com `context: fork` ou Explore).

> **Pontes.** Tools nativas (Read, Write, Edit, Bash, Grep, Glob): **M05**. Hooks e gates: **M06**.
> CI e iteração: **M09**. `/compact`, scratchpad e sessões: **M10**.

> **Na doc atual [volátil]:** a doc do Claude Code descreve mais coisas que o guia não cobra
> (managed policy, `CLAUDE.local.md`, auto memory, settings e permissões, outros modos, plugins,
> routines). Basta saber que existem; **nenhuma questão do curso depende delas.**

---

## 1. Hierarquia do CLAUDE.md (3.1)

**Fatos de prova**

| Nível | Onde fica | Quem recebe | Vai pelo git? |
|---|---|---|---|
| **User** | `~/.claude/CLAUDE.md` | só aquele usuário, em todos os projetos dele | **não** |
| **Project** | `CLAUDE.md` na raiz **ou** `.claude/CLAUDE.md` | todo mundo que clona o repo (e o CI) | **sim** |
| **Directory** | `CLAUDE.md` num subdiretório | quem trabalha naquela pasta | sim |

- Os níveis **se somam** (são concatenados); um não apaga o outro. O de subdiretório entra quando o
  Claude trabalha com arquivos daquela pasta.
- **User-level é pessoal:** `~/.claude/CLAUDE.md` **não é compartilhado** com os colegas pelo
  controle de versão. Funciona na máquina de quem escreveu, e só nela.
- CLAUDE.md é **contexto**, não enforcement (garantia = hook ou gate, M06).

```text
imobi-portal/                    ← repositório (versionado)
├── CLAUDE.md                    ← PROJECT: "preços usam o tipo Money"; "rode dotnet test"
└── legacy-mls-importer/
    └── CLAUDE.md                ← DIRECTORY: "datas deste importador vêm em dd/MM/yyyy"
~/.claude/CLAUDE.md              ← USER (fora do repo): "explique os diffs em português"
```

**Por quê.** Cada nível responde a "quem precisa ver isso?". Regra do time no nível user vira
"funciona na minha máquina"; preferência pessoal no project polui o contexto de todo mundo.

**Diagnóstico clássico (3.1-S1).** "O dev novo clonou o repo e o Claude gera `throw new` em vez de
`Result<T>`; com os veteranos funciona." A regra está no `~/.claude/CLAUDE.md` dos veteranos →
**mova para o CLAUDE.md do projeto** e commite.

**Anti-padrões que aparecem como alternativa errada**
- "Cada dev copia o `~/.claude/CLAUDE.md` do colega" → manual, deriva, e o CI nunca recebe.
- "Hook que reescreve o código gerado" → over-engineering para um problema de **escopo**.
- "Reescreva a regra em CAIXA ALTA" → a regra nem está sendo carregada.
- "O CLAUDE.md da raiz sobrescreve o da pasta" (ou o contrário) → eles se somam.

**Como cai na prova.** Dev novo, colega ou CI não recebe a convenção que outro recebe → instrução no
nível errado (user em vez de project).

---

## 2. Modularizar: `@import` e `.claude/rules/` por tema (3.1)

**Fatos de prova**
- **`@import`**: uma linha `@caminho/arquivo.md` dentro do CLAUDE.md traz aquele arquivo para o
  contexto **junto com o CLAUDE.md que o referencia** (caminho relativo ao arquivo que importa).
- Padrão do guia (3.1-S2): **import seletivo por pacote**. Os padrões ficam num lugar só, e o
  CLAUDE.md de **cada pacote** importa **só os que se aplicam a ele**; quem escolhe é o mantenedor,
  que conhece o domínio.
- **`.claude/rules/`** (3.1-K4/S3): **arquivos por tema** como alternativa ao CLAUDE.md monolítico:
  `testing.md`, `api-conventions.md`, `deployment.md`. Rule **sem** `paths` carrega **sempre**, como
  o CLAUDE.md; o ganho é **organização e um dono por tema**. Com `paths`, a carga vira condicional
  (seção 4).

```markdown
# Pharmacy API (ASP.NET Core): dispensação de medicamentos

<!-- ← AQUI: import seletivo; o mantenedor sabe que este pacote toca dados de paciente -->
@../../standards/dotnet-api.md
@../../standards/hipaa-logging.md

- Endpoint novo exige teste de integração com WebApplicationFactory.
```
*(arquivo `packages/pharmacy-api/CLAUDE.md`; o de `scheduling-ui` importa só `react-ui.md` e
`accessibility.md`)*

**Por quê.** Um CLAUDE.md de 1.500 linhas dilui a atenção, gera conflito de merge e não tem dono.
Import seletivo dá **fonte única** e **relevância**; rules por tema dão **arquivos focados** com dono.

**Anti-padrões que aparecem como alternativa errada**
- **Copiar** o texto dos padrões para cada pacote → duplica e diverge.
- **Importar todos os padrões no CLAUDE.md raiz** → organiza o arquivo, mas tudo carrega em toda
  sessão. Import **não** é carga sob demanda.
- Padrão que vale sempre virando **skill** → só entra se alguém invocar.
- "Rules carregam quando o Claude acha relevante" → isso descreve skill; rule sem `paths` carrega sempre.

**Como cai na prova.** Monorepo com pacotes de domínios diferentes → `@import` seletivo no CLAUDE.md
de cada pacote. CLAUDE.md gigante, conflito de merge, donos misturados → `.claude/rules/` por tema.

---

## 3. `/memory`: o que está carregado nesta sessão? (3.1)

**Fatos de prova**
- O comando **`/memory`** mostra **quais arquivos de memória** (os CLAUDE.md de cada nível) estão em
  jogo na sessão e permite abri-los para editar.
- É o **primeiro passo** para diagnosticar **comportamento inconsistente entre sessões** ou entre
  devs ("ontem seguiu a convenção, hoje não"; "na minha máquina segue, na do colega não").
- Fluxo: rode `/memory` na sessão que falha (e na que funciona) → compare: falta o arquivo do
  projeto? há um `~/.claude/CLAUDE.md` conflitante? a sessão foi aberta noutra pasta? → só então
  corrija o **lugar** ou o **texto** da instrução.

**Por quê.** Antes de reescrever instruções, confirme que elas **estão sendo carregadas**.

**Anti-padrões que aparecem como alternativa errada**
- Perguntar ao Claude "você leu o CLAUDE.md?" → autodeclaração não é verificação.
- Reescrever a regra com mais ênfase antes de ver o que carregou.
- Trocar de modelo ou reinstalar → não ataca a causa.

**Como cai na prova.** "Comportamento inconsistente entre sessões; qual o primeiro passo?" → `/memory`.

> **Na doc atual [volátil]:** `/memory` lista e abre os arquivos de memória; a doc também sugere
> `/context` para ver o que carregou no início. **Na prova, responda `/memory`.**

---

## 4. Rules por caminho: `paths:` com globs (3.3)

**Fatos de prova**
- Um arquivo em `.claude/rules/` pode ter **frontmatter YAML com `paths`** (lista de **globs**). A
  rule só entra no contexto **quando o Claude trabalha com (lê ou edita) um arquivo que bate**.
- Resultado: menos contexto irrelevante e menos tokens.
- Glob por **tipo de arquivo** ignora o diretório: `**/*.test.tsx`, `**/*Tests.cs` pegam testes
  **em qualquer pasta**, inclusive nas que forem criadas amanhã.
- Para convenção que **atravessa a base** (testes ao lado do código, fixtures em vários serviços),
  **rule com glob vence CLAUDE.md por subdiretório**: o CLAUDE.md de pasta é **preso ao diretório**
  e teria de ser copiado em cada pasta. Convenção de **uma pasta só** continua no CLAUDE.md dela.

```markdown
---
paths:
  - "terraform/**/*"     # ← AQUI: carrega só ao trabalhar com arquivos de Terraform
---
# Convenções de Terraform
- Todo recurso tem as tags `owner` e `cost-center`.
```
*(arquivo `.claude/rules/terraform.md`)*

```markdown
---
paths:
  - "**/*Tests.cs"       # ← AQUI: testes em QUALQUER projeto da solução
---
# Convenções de teste (.NET)
- xUnit + FluentAssertions; nome do método: Metodo_Cenario_Resultado.
- Nada de Thread.Sleep: injete TimeProvider e use FakeTimeProvider.
```
*(arquivo `.claude/rules/testing-dotnet.md`; vale para `src/Scheduling/AppointmentServiceTests.cs`
e para `tests/Pharmacy.Tests/DispenseTests.cs`)*

```csharp
[Fact]
public void Reschedule_WhenSlotIsTaken_ReturnsConflict()
{
    var sut = new AppointmentService(new FakeTimeProvider(), new InMemorySlotRepository(taken: "09:30"));
    sut.Reschedule(appointmentId: 42, newSlot: "09:30").Should().Be(Result.Conflict("slot_taken"));
}
```

**Por quê.** O glob casa pelo **caminho do arquivo**: é automático (ninguém precisa lembrar de
invocar) e barato (só carrega quando é relevante).

**Anti-padrões que aparecem como alternativa errada**
- **CLAUDE.md em cada pasta de testes** → duplicado, diverge, não cobre pasta nova.
- **Tudo no raiz, um cabeçalho por área**, "o Claude infere qual seção vale" → carrega sempre e
  depende de inferência.
- **Skill** para convenção que deve valer sempre que mexer em X → skill é sob demanda.
- **Rule sem `paths`** para convenção de uma área → carrega sempre; não economiza nada.
- **Glob ancorado no diretório errado** (`tests/**/*.cs` com testes ao lado do código em `src/`) →
  a rule nunca carrega para esses arquivos.

**Como cai na prova.** Arquivos de um tipo espalhados → rule com `paths`. "A rule não pega parte
dos arquivos" → leia o glob. "Movemos para rules e o contexto não caiu" → faltou `paths`.

---

## 5. Slash commands: projeto × pessoal (3.2)

**Fatos de prova**
- **`.claude/commands/<nome>.md`** no repositório vira `/<nome>` para **todo o time**: está no
  controle de versão, chega a quem clona ou dá pull, e mudanças passam por code review.
- **`~/.claude/commands/<nome>.md`** é comando **pessoal**: só você, em todos os seus projetos.

```markdown
Gere as notas de release a partir dos PRs mergeados desde a última tag.
Agrupe em Novidades, Correções e Breaking changes, citando o número de cada PR.
Foco deste release: $ARGUMENTS
```
*(arquivo `.claude/commands/release-notes.md` → `/release-notes`, versionado)*

**Por quê.** "Todo dev recebe ao clonar ou dar pull" = versionado no repo. "Só meu" = home do usuário.

**Anti-padrões que aparecem como alternativa errada**
- Distribuir o comando copiando para o `~/.claude/commands/` de cada dev (wiki, script, hook que
  copia) → versões divergem e o dev novo fica sem.
- Descrever o procedimento no **CLAUDE.md** → ele guarda instruções, não define comandos (e carrega
  em toda sessão).

**Como cai na prova.** Comando do time → `.claude/commands/`. Comando só meu → `~/.claude/commands/`.

> **Na doc atual [volátil]:** a doc diz que *custom commands* foram fundidos em skills
> (`.claude/commands/deploy.md` e `.claude/skills/deploy/SKILL.md` criam o mesmo `/deploy`), e
> `.claude/commands/` continua funcionando. **Na prova: comando do time → `.claude/commands/`.**

---

## 6. Skills: `SKILL.md` e o frontmatter que cai (3.2)

**Fatos de prova**
- Skill de projeto: **`.claude/skills/<nome>/SKILL.md`** (versionada). Pessoal:
  **`~/.claude/skills/<nome>/SKILL.md`**. O `SKILL.md` aceita **frontmatter YAML**:

| Campo | O que faz (sentido do guia) | Quando usar |
|---|---|---|
| `context: fork` | roda a skill num **sub-agent isolado**; a saída **não polui** a conversa principal, só o resultado volta | saída verbosa (análise de codebase), contexto exploratório (brainstorm de alternativas) |
| `allowed-tools` | **restringe** as tools que a skill pode usar enquanto roda | skill que só escreve arquivos → limite às tools de escrita para evitar ação destrutiva |
| `argument-hint` | indica o parâmetro esperado e **pede ao dev** quando a skill é invocada **sem argumento** | skill que precisa de ID de ticket, nº de PR, nome de tabela |

```markdown
---
name: scaffold-collection
description: Gera o boilerplate de uma nova coleção sazonal (página, estilos, stub de teste).
argument-hint: "[slug-da-colecao]"  # ← AQUI: sem argumento, o dev é lembrado de informar o slug
allowed-tools: Read, Write          # ← AQUI (sentido do guia): só lê e escreve arquivos; sem Bash
context: fork                       # ← AQUI: roda isolada; só o resumo volta para a conversa
---
Crie a coleção $ARGUMENTS seguindo o padrão de src/collections/_template/.
Ao terminar, devolva apenas a lista de arquivos criados.
```
*(arquivo `.claude/skills/scaffold-collection/SKILL.md`)*

- **`context: fork`**: o sub-agent faz o trabalho barulhento (ler 200 arquivos, gerar seis
  alternativas) **no próprio contexto** e devolve o resultado; a conversa principal não recebe a
  transcrição. Ele **não vê o histórico** da conversa, então o `SKILL.md` precisa trazer o que ele
  precisa. `fork` isola **contexto**, não disco nem git.
- **Variante pessoal (3.2-K4):** quer a skill do time do seu jeito? **Copie para
  `~/.claude/skills/` com outro nome** (ex.: `/scaffold-collection-verbose`). Você não altera a
  versão do time e não cria ambiguidade com o nome original.

**Por quê.** Cada campo resolve um problema concreto: poluição de contexto (`context: fork`), ação
destrutiva (`allowed-tools`), invocação incompleta (`argument-hint`).

**Anti-padrões que aparecem como alternativa errada**
- Skill verbosa inline + "rode `/compact` depois" → remedia depois e perde detalhe.
- "Nunca rode comandos destrutivos" no corpo da skill → orientação probabilística; o guia quer
  `allowed-tools` restringindo.
- Editar a skill do time para o seu gosto → afeta todo mundo.
- "Não esqueça o nº do PR" no README ou no CLAUDE.md → é para isso que existe `argument-hint`.

**Como cai na prova.** Saída enorme → `context: fork`; skill destrutiva que só precisava escrever →
`allowed-tools`; invocada sem parâmetro → `argument-hint`; versão própria → `~/.claude/skills/` com
outro nome.

> **Na doc atual [volátil]:** `allowed-tools` **pré-aprova** as tools listadas no turno da skill (quem
> remove tools é `disallowed-tools`), e `argument-hint` é a dica do autocomplete. **Na prova, use o
> sentido do guia:** `allowed-tools` restringe; `argument-hint` pede o parâmetro.

---

## 7. Skill, CLAUDE.md ou rule? (3.2)

**Fatos de prova**

| Mecanismo | Quando entra no contexto | Serve para |
|---|---|---|
| **CLAUDE.md** (e rule sem `paths`) | **sempre** | padrões **universais**: build, convenções gerais, "dado de paciente nunca vai para log" |
| **Rule com `paths`** | ao mexer em arquivo que bate | convenção de um **tipo ou área** de arquivo |
| **Skill / command** | **sob demanda**, quando invocado | **fluxo específico** de uma tarefa (gerar migration, checklist de release) |

**Por quê.** CLAUDE.md custa contexto em **toda** sessão: um procedimento de 90 linhas usado em 5%
das tarefas é desperdício e pode "vazar" para tarefas onde não se aplica. Skill custa zero até ser
chamada, e por isso mesmo **não** serve para regra que precisa valer sempre.

**Anti-padrões que aparecem como alternativa errada**
- Procedimento passo a passo de tarefa ocasional no CLAUDE.md (ou num arquivo importado por ele).
- Padrão universal numa skill → só vale se alguém lembrar de invocar.
- Mudar o procedimento de posição dentro do CLAUDE.md → continua carregado em toda sessão.

**Como cai na prova.** Fluxo ocasional pesando no CLAUDE.md → skill. Padrão universal numa skill →
CLAUDE.md.

---

## 8. Plan mode × execução direta (3.4)

**Fatos de prova**
- **Plan mode**: o Claude **explora a base sem editar**, desenha uma abordagem e só muda arquivos
  depois da sua aprovação. É para tarefas **complexas**: **larga escala**, **várias abordagens
  válidas**, **decisões arquiteturais**, **muitos arquivos**. Exemplos do guia: reestruturar em
  microsserviços; migração de biblioteca que afeta **45+ arquivos**; escolher entre **abordagens de
  integração com requisitos de infraestrutura diferentes**. Valor: explorar e desenhar **antes** de
  se comprometer evita **retrabalho caro**.
- **Execução direta**: mudança **simples e bem delimitada**. Exemplos do guia: bug **de um arquivo
  com stack trace claro**; **uma condicional de validação de data**.
- **Combinar** (3.4-S4): **plan mode para investigar e planejar → execução direta para implementar o
  plano aprovado** (ex.: planejar a migração do `Newtonsoft.Json` para o `System.Text.Json`, depois
  executar sem re-planejar cada arquivo).

```text
[plan mode]  explorar callers e dependências → comparar abordagens → plano (arquivos, ordem, riscos)
     │  você revisa e aprova
     ▼
[direto]     implementar o plano → rodar os testes → ajustar
```

**Anti-padrões que aparecem como alternativa errada**
- "Comece direto e deixe a implementação revelar a estrutura" → retrabalho quando a dependência
  aparece tarde.
- "Direto com especificação detalhada de cada arquivo" → presume conhecer a estrutura sem explorar.
- "Comece direto e mude para plan mode **se** complicar" → a complexidade já estava declarada.
- "Plan mode para **tudo**" → overhead em fix de uma linha.
- "Implemente as duas abordagens e compare os diffs" ou "commit a cada arquivo para reverter" →
  aceitam o retrabalho em vez de evitá-lo.

**Como cai na prova.** Cenário 2 quase sempre. A complexidade **já está no enunciado** (muitos
arquivos, arquitetura, duas ou mais abordagens, infraestrutura diferente)? → **plan mode desde o
início**. Dá para descrever o diff numa frase? → **direto**.

---

## 9. Explore subagent: descoberta verbosa fora da conversa principal (3.4)

**Fatos de prova**
- O **Explore** é um subagent nativo, **somente leitura**, para buscar e entender a base. Ele faz a
  descoberta (dezenas de Read e Grep) **no próprio contexto** e devolve **um resumo** à conversa
  principal.
- Uso no guia: **isolar a saída verbosa da fase de descoberta** e **evitar o esgotamento da janela de
  contexto em tarefas de várias fases** (descobrir → planejar → implementar).

```text
Sem Explore: [descoberta: 140 arquivos lidos, 70% da janela] → [plano] → [implementação: janela estoura]
Com Explore: [Explore lê os 140 arquivos no contexto DELE] → resumo de 1 página → [plano] → [implementação]
```

**Por quê.** O que enche a janela é a **saída das ferramentas** (conteúdo de arquivo, resultado de
busca). Num contexto separado, a conversa principal guarda só a conclusão.

**Anti-padrões que aparecem como alternativa errada**
- Ler tudo na conversa principal "para ter o contexto completo".
- "Modelo com janela maior" → adia o problema; a atenção continua diluída.
- Colar a transcrição da descoberta ou guardar o texto bruto num scratchpad e relê-lo → o volume
  volta ao contexto (scratchpad é para **achados-chave**, M10).

**Como cai na prova.** "A sessão esquece decisões depois de uma exploração grande" (causa: descoberta
verbosa no contexto principal) ou "a tarefa de várias fases vai estourar a janela" (correção:
Explore na descoberta). Mesmo princípio do subagent isolado (M07) e do `/compact`/scratchpad (M10).

---

## Tabela de decisão

| Se… | Faça… |
|---|---|
| Convenção do **time** neste repo | CLAUDE.md do projeto (raiz ou `.claude/CLAUDE.md`), versionado |
| Preferência **só sua** / convenção de **uma pasta** | `~/.claude/CLAUDE.md` / `CLAUDE.md` do subdiretório |
| Dev novo ou CI não recebe uma instrução que outro recebe | está no nível **user** → mova para o **project** |
| Comportamento inconsistente entre sessões ou devs | **`/memory`** para ver o que carregou |
| Monorepo: cada pacote precisa de padrões diferentes | `@import` seletivo no CLAUDE.md **de cada pacote** |
| CLAUDE.md monolítico, conflito de merge, donos misturados | `.claude/rules/` por tema (`testing.md`, `api-conventions.md`, `deployment.md`) |
| Convenção para arquivos de um tipo **espalhados** | rule com `paths:` glob (`**/*.test.tsx`) |
| Rules sem efeito no contexto / sem pegar parte dos arquivos | faltou `paths` / glob ancorado em diretório |
| Comando para todo dev / só para você | `.claude/commands/` / `~/.claude/commands/` |
| Skill despeja saída enorme ou brainstorm polui a conversa | `context: fork` |
| Skill só precisa escrever arquivos e fez algo destrutivo | `allowed-tools` restrito à escrita |
| Skill invocada sem o parâmetro obrigatório | `argument-hint` |
| Quer a skill do time do seu jeito | `~/.claude/skills/` **com outro nome** |
| Tarefa grande, arquitetural, multi-arquivo, várias abordagens | **plan mode** |
| Fix de um arquivo com stack trace claro, uma validação | **execução direta** |
| Migração grande | plan mode para investigar → **direto** para implementar |
| Descoberta verbosa enchendo a janela em tarefa de várias fases | **Explore subagent** |

## Glossário

- **User / project / directory level**: `~/.claude/CLAUDE.md` (só você) / raiz ou `.claude/CLAUDE.md`
  (time, via git) / `CLAUDE.md` de subdiretório (aquela pasta).
- **`@import`** (`@caminho`): inclui outro arquivo no CLAUDE.md; relativo ao arquivo que importa.
- **`.claude/rules/`**: instruções por tema; com `paths:` (globs), carregam só para arquivos que batem.
- **`/memory`**: mostra e abre os arquivos de memória carregados na sessão.
- **Slash command**: `.md` em `.claude/commands/` (time) ou `~/.claude/commands/` (pessoal) → `/nome`.
- **Skill**: `SKILL.md` em `.claude/skills/<nome>/` ou `~/.claude/skills/<nome>/`, com frontmatter
  (`context: fork`, `allowed-tools`, `argument-hint`).
- **Plan mode / execução direta**: explorar e planejar sem editar / implementar já.
- **Explore subagent**: subagent nativo só leitura; descoberta verbosa no contexto dele, resumo na
  conversa principal.

## Cola de véspera

- **3 níveis:** user `~/.claude/CLAUDE.md` (só você, **não vai pelo git**) · project (`CLAUDE.md` ou
  `.claude/CLAUDE.md`, time) · directory (pasta). **Somam-se.** Dev novo não recebe → user → project.
- **`/memory`** = primeiro passo para "o que carregou?" e para comportamento inconsistente.
- **`@import`** modulariza; **seletivo por pacote** (o mantenedor escolhe); o importado **carrega
  junto**.
- **`.claude/rules/`** por tema substitui o monolito; **sem `paths` = sempre**; **com `paths` = só ao
  mexer em arquivo que bate**. Glob por tipo (`**/*.test.tsx`) > CLAUDE.md por pasta para convenção
  espalhada.
- Commands: **`.claude/commands/`** (time) × **`~/.claude/commands/`** (pessoal).
- Skills: **`.claude/skills/<nome>/SKILL.md`**; **`context: fork`** isola; **`allowed-tools`**
  restringe (sentido do guia); **`argument-hint`** pede o parâmetro; variante pessoal em
  **`~/.claude/skills/` com outro nome**.
- **Skill = sob demanda, fluxo específico. CLAUDE.md = sempre, padrão universal.**
- **Plan mode:** larga escala, várias abordagens, arquitetura, multi-arquivo. **Direto:** um arquivo
  com stack trace, uma validação. **Combine:** plan para investigar, direto para implementar.
- **Explore:** descoberta verbosa fora da conversa principal; volta o resumo.
- Distratores clássicos: copiar arquivo para cada dev; CAIXA ALTA; CLAUDE.md em cada pasta; tudo no
  raiz "e o Claude infere"; skill para regra universal; `/compact` em vez de isolar; janela maior;
  "comece direto e troque se complicar"; `fork` "protege arquivos".

## Perguntas de checagem

1. **A regra "use `Result<T>`, não exceções" está no `~/.claude/CLAUDE.md` de três veteranos e o dev
   novo não a recebe. Correção?** Mover para o CLAUDE.md do projeto e commitar.
2. **"Ontem o Claude seguiu a convenção de logging, hoje não." Primeiro passo?** `/memory`.
3. **Movemos três seções para `.claude/rules/` e o contexto inicial não mudou. Por quê?** Faltou `paths`.
4. **Testes `*Tests.cs` ao lado do código em 37 projetos: onde fica a convenção?** Rule com
   `paths: ["**/*Tests.cs"]`.
5. **Skill de scaffolding apagou arquivos, mas só precisa criar arquivos. Ajuste?** `allowed-tools`.
6. **Migrar o serializador JSON em 70 arquivos com converters customizados?** Plan mode para
   investigar e decidir; depois execução direta do plano.
