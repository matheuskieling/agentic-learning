# Módulo 09 — Claude Code em CI/CD e refinamento iterativo

> **Domínio D3 (20%)**, task statements **3.5** (refinamento iterativo) e **3.6** (CI/CD). O 3.6 é o
> coração do **cenário 5 (Claude Code for Continuous Integration)**; o 3.5 aparece no **cenário 2
> (Code Generation with Claude Code)**. Batch API e review multi-pass também conversam com o
> **cenário 6** e com o D4 (Módulos 03 e 07).
>
> Duas perguntas-mãe: **"como faço o Claude convergir para o que eu quero?"** (3.5) e **"como rodo o
> Claude sem ninguém olhando, com saída que uma máquina consegue ler, custo limitado e na hora
> certa do pipeline?"** (3.6).

---

## 1. Refinamento iterativo: exemplos concretos batem prosa

**Fato-chave.** Quando o resultado não sai como você quer, a alavanca mais forte é **mostrar**:
**2–3 pares concretos de entrada → saída esperada** comunicam formato, nível de detalhe e casos de
borda melhor que parágrafos de instrução.

```text
Converta as mensagens de commit para o padrão do changelog. Exemplos:

entrada: "fix null ref no calculo de frete qdo cep vazio"
saída:   "- **Frete:** corrigido erro quando o CEP não é informado."

entrada: "feat(api): endpoint GET /pedidos/{id}/rastreio"
saída:   "- **API:** novo endpoint para consultar o rastreio de um pedido."

entrada: "chore: bump deps"
saída:   (omitir: mudança interna, não vai para o changelog)
```

**Por quê.** Prosa é interpretada; exemplo é **imitado**. O terceiro par acima ensina um caso de
borda (omitir) que seria fácil de esquecer na prosa.

**Anti-padrões (alternativas erradas).**
- Reescrever a instrução em prosa "com mais ênfase" pela terceira vez, sem exemplo.
- Um exemplo só (o modelo copia literalmente) ou dez exemplos iguais (não cobre bordas).
- "Use seu bom senso para o formato" → resultado inconsistente.

**Como cai na prova.** Cenário 2: "o Claude gera o formato quase certo, mas varia entre execuções;
qual o próximo passo?" → adicionar 2–3 exemplos concretos de entrada/saída, cobrindo bordas.

---

## 2. TDD e entrevista: dar ao Claude um alvo verificável

**TDD como ciclo de iteração.** **Escreva (ou peça) os testes primeiro**, confirme que **falham**,
peça a implementação, **rode os testes e devolva as falhas** ao Claude até passar. O teste é o
**critério de pronto objetivo**: o Claude itera contra um sinal, não contra a sua impressão.

```text
1. "Escreva testes xUnit para CalculadoraDeFrete cobrindo: CEP vazio → ArgumentException;
    peso 0 → frete mínimo; região Norte → +15%. Não implemente ainda."
2. Rode: dotnet test  → 3 falhas (esperado).
3. "Implemente até os testes passarem. Não altere os testes."
4. Rode, cole as falhas restantes, repita.
```

**Entrevista.** Quando o requisito é vago ou o domínio é desconhecido, peça ao Claude que **faça
perguntas de esclarecimento antes de implementar** ("me entreviste sobre este recurso antes de
escrever código"). Ele levanta casos de borda e decisões que você não tinha explicitado.

**Por quê.** Os dois atacam a mesma causa-raiz: **ambiguidade**. TDD transforma "certo" em algo
verificável; a entrevista tira a ambiguidade **antes** de gastar uma rodada de implementação.

**Anti-padrões.**
- "Implemente e me diga se ficou certo" → o Claude afirma que está certo; não há sinal objetivo.
- Deixar o Claude **alterar os testes** para passar → destrói o critério.
- Implementar direto sobre requisito confuso e corrigir na base do "não era isso".

**Como cai na prova.** Cenário 2: "a funcionalidade tem muitas regras de borda e as tentativas
anteriores quebravam casos antigos" → TDD (testes primeiro, iterar com as falhas). "O PO entregou um
requisito de duas linhas para um domínio que o time não conhece" → entrevista antes de implementar.

---

## 3. Problemas relacionados vs. independentes

**Fato-chave.**
- **Relacionados** (que **interagem**: mesma causa, uma correção afeta a outra) → **numa mensagem
  só**, para o Claude ver o todo e não corrigir um quebrando o outro.
- **Independentes** (sem interação) → **em sequência**, um por vez: cada mudança fica pequena,
  **revisável** e fácil de reverter.

**Exemplo.** "O total do pedido arredonda errado **e** o desconto progressivo aplica na ordem
errada", ambos em `CalculadoraDePedido`, com o arredondamento dependendo da ordem: **juntos**.
"Typo na tela de login" e "timeout no relatório de vendas": **separados**.

**Anti-padrões.**
- Despejar 12 problemas sem relação num prompt só → diff gigante, impossível de revisar, e um
  problema contamina o outro.
- Separar problemas acoplados em sessões diferentes → cada correção desfaz a outra.

**Como cai na prova.** Cenário 2: uma lista de bugs com descrição; a pergunta é "como enviar ao
Claude?". Procure pistas de **interação** (mesmo módulo, mesma causa, efeito cruzado).

---

## 4. `-p`: o Claude Code sem ninguém olhando

**Fato-chave.** **`-p` / `--print`** roda o Claude Code de modo **não interativo**: executa o
prompt, imprime o resultado e **sai** (código de saída 0 em sucesso, diferente de 0 em falha).
**Sem `-p`, o processo abre a sessão interativa e fica esperando input: o job de CI trava** até o
timeout.

```bash
claude -p "Explique a causa raiz deste erro de build" < build-error.log
```

- Lê **stdin** (dá para encadear: `gh pr diff 123 | claude -p "..."`).
- É o **mesmo motor**: por padrão carrega CLAUDE.md, settings, skills, `.mcp.json` do diretório,
  como uma sessão interativa. Skills podem ser chamadas no prompt (`claude -p "/revisar-pr 123"`).
- Em `-p` **não há quem responda prompt de permissão**: o que não estiver pré-aprovado é **negado**.
  Por isso CI sempre vem com `--allowedTools` e/ou `--permission-mode`.
- [volátil] `--bare` pula a autodescoberta (hooks, skills, plugins, MCP, CLAUDE.md, auto memory) para
  ter **o mesmo resultado em qualquer máquina**; aí você passa o contexto explicitamente
  (`--append-system-prompt`, `--settings`, `--mcp-config`).

**Anti-padrões.**
- Rodar `claude "revise o PR"` (sem `-p`) no job → trava esperando input.
- Contar com "o Claude vai pedir permissão e alguém aprova" no CI → ninguém aprova; a ação é negada.

**Como cai na prova.** Cenário 5, a questão mais clássica: "o job de CI fica pendurado até o
timeout" → falta `-p`.

---

## 5. Flags de CI e saída estruturada

| Flag | Para quê |
|------|----------|
| `--output-format text \| json \| stream-json` | `json` = um objeto final com `result`, `session_id`, custo e metadados; `stream-json` = um JSON por linha, em tempo real |
| `--json-schema '<schema>'` | (com `--output-format json`) a resposta conforme ao schema vem em **`structured_output`** |
| `--max-turns N` | teto de turnos agênticos: **backstop** de custo/tempo |
| `--allowedTools "Read,Grep,Bash(dotnet test *)"` | pré-aprova tools (sintaxe de regra de permissão); `--disallowedTools` remove |
| `--permission-mode` | postura da sessão: `dontAsk` nega tudo que não foi pré-aprovado (CI travado); `acceptEdits` libera edições; `plan` só analisa |
| `--append-system-prompt "..."` | **acrescenta** instruções ao system prompt padrão (mantém o comportamento do Claude Code); `--system-prompt` substitui tudo |
| [volátil] `--max-budget-usd`, `--bare`, `--no-session-persistence`, `--fallback-model` | teto de gasto, reprodutibilidade, não gravar sessão, modelo reserva |

**Comando completo de review com saída JSON:**

```bash
gh pr diff "$PR_NUMBER" | claude -p \
  "Revise o diff recebido no stdin. Reporte apenas bugs, falhas de segurança e quebras de contrato.
   Não comente estilo que o formatter já corrige." \
  --append-system-prompt "Você é um revisor sênior de C#/.NET. Seja específico: arquivo, linha, problema, correção." \
  --output-format json \
  --json-schema '{
    "type":"object",
    "properties":{
      "findings":{"type":"array","items":{"type":"object",
        "properties":{
          "file":{"type":"string"},
          "line":{"type":"integer"},
          "severity":{"type":"string","enum":["high","medium","low"]},
          "issue":{"type":"string"},
          "suggestion":{"type":"string"}
        },
        "required":["file","line","severity","issue","suggestion"]}}
    },
    "required":["findings"]
  }' \
  --allowedTools "Read,Grep,Glob" \
  --permission-mode dontAsk \
  --max-turns 10 \
  > review.json

# Gate: falha o job se houver achado de severidade alta
jq -e '[.structured_output.findings[] | select(.severity=="high")] | length == 0' review.json
```

Saída (resumida) que o script lê:

```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "num_turns": 6,
  "session_id": "4f1c…",
  "total_cost_usd": 0.19,
  "result": "Encontrei 2 problemas…",
  "structured_output": {
    "findings": [
      { "file": "src/Pedidos/PedidoService.cs", "line": 88, "severity": "high",
        "issue": "Valor do estorno não é validado contra o valor pago.",
        "suggestion": "Validar estorno <= valor pago antes de chamar o gateway." }
    ]
  }
}
```

**Por quê.** Máquina não lê prosa de forma confiável. `--output-format json` + `--json-schema` dá
um contrato para o próximo passo do pipeline (postar comentário, falhar o job, abrir issue).
`--max-turns`/orçamento limitam o pior caso; `--allowedTools` + `dontAsk` aplicam **menor privilégio**.

**Anti-padrões.**
- Fazer *parse* do texto livre com regex ("procurar a palavra CRITICAL") → frágil.
- `--max-turns` como **mecanismo principal** de "pronto" → é **backstop**; o fim normal é o Claude concluir.
- `--allowedTools "Bash"` (tudo) ou `bypassPermissions` num runner com segredos → privilégio demais.
- `--system-prompt` quando só queria acrescentar uma persona → perde o comportamento padrão; use `--append-system-prompt`.
- Conformidade com schema ≠ correção: valide em código o que importa (ex.: o arquivo citado existe no diff).

**Como cai na prova.** Cenário 5: "o pipeline precisa decidir automaticamente se bloqueia o merge
com base no review" → `--output-format json` + `--json-schema` e ler `structured_output`.
"O job às vezes roda 40 turnos e estoura o custo" → `--max-turns` (e teto de orçamento) como backstop.

---

## 6. GitHub Actions e GitLab CI/CD

**GitHub Actions: `anthropics/claude-code-action`.** Roda o Claude Code dentro do workflow.
- **Modo interativo:** sem `prompt`, responde a menções **`@claude`** em issues/PRs.
- **Modo automação:** com `prompt` (texto ou `/skill`), roda no evento (`pull_request`, `schedule`...).
- `claude_args` repassa **qualquer flag da CLI** (`--max-turns`, `--allowedTools`, `--model`, `--append-system-prompt`).
- Credencial em **secret** (`ANTHROPIC_API_KEY`), nunca no YAML. Setup rápido: `/install-github-app`.
- O CLAUDE.md do repositório vale no job (mesmo motor), então mantenha-o **enxuto** (é lido a cada execução).

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize, ready_for_review]

concurrency:                       # um review por PR; push novo cancela o anterior
  group: claude-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    runs-on: ubuntu-latest
    timeout-minutes: 15            # teto de tempo do job
    permissions:
      contents: read
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Revise o PR #${{ github.event.pull_request.number }} deste repositório.
            Siga os critérios de review do CLAUDE.md. Reporte só bugs, segurança e
            quebras de contrato, com arquivo e linha. Poste os achados como comentários no PR.
          claude_args: |
            --max-turns 12
            --allowedTools "Read,Grep,Glob,Bash(gh pr diff *),Bash(gh pr comment *)"
            --append-system-prompt "Você é um revisor sênior de C#/.NET."
```

**GitLab CI/CD** [beta, mantido pelo GitLab]: um job no `.gitlab-ci.yml` instala o Claude Code e
roda `claude -p "..." --permission-mode acceptEdits --allowedTools "..."`; a chave vai como
**variável mascarada** (`ANTHROPIC_API_KEY`); o disparo pode ser manual, por evento de MR ou por
menção `@claude` via webhook. Limite com `--max-turns` e o `timeout` do job.

**Princípio.** As integrações gerenciadas (Action, GitLab, Code Review) são conveniência; **`-p` é a
primitiva** quando você precisa de **controle total** (gate customizado, schema próprio, multi-pass).

**Anti-padrões.** Chave de API literal no YAML; workflow sem `timeout`/`concurrency` (runs empilhados
a cada push); dar `contents: write` + `Bash` irrestrito a um job que só precisa comentar.

**Como cai na prova.** Cenário 5: "onde passar `--max-turns` na Action?" → `claude_args`. "Como
evitar dez reviews simultâneos no mesmo PR?" → `concurrency` com `cancel-in-progress`.

---

## 7. Batch API vs. síncrono no pipeline

**Batch API (Message Batches):** **50% mais barata**, processa em **até 24h**, **sem SLA** de
latência, resultados podem vir **fora de ordem** → **case cada resultado pelo `custom_id`**.
**Não suporta loop multi-turn de tools** dentro de um request (cada request é uma chamada única).
Estados por request: `succeeded`, `errored`, `canceled`, `expired`; faça poll de
`processing_status` até `ended`. **Reenvie só os `custom_id` que falharam.** Refine o prompt numa
**amostra** antes de mandar o volume.

| Use **Batch** | Use **síncrono** (`claude -p` / Messages API) |
|---------------|-----------------------------------------------|
| auditoria noturna de todos os repositórios | **review pré-merge** que bloqueia o PR |
| relatório semanal de dívida técnica | qualquer **gate** do pipeline |
| reclassificar 200 mil tickets antigos | depuração interativa |
| gerar docstrings em massa sem pressa | tarefa que precisa de **loop agêntico com tools** |

**Regra de ouro da prova:** **batch nunca em passo pré-merge/bloqueante.** "Até 24h, sem SLA" é
incompatível com um dev esperando o check ficar verde.

**Anti-padrões.**
- "Trocar o review do PR para Batch API para economizar 50%" → o PR fica bloqueado por horas.
- Casar resultados pela **posição** no arquivo de saída → vêm fora de ordem; use `custom_id`.
- Reenviar o lote inteiro porque 3% falharam → reenvie só os `custom_id` com erro.
- Mandar via batch uma tarefa que precisa de vários turnos de tool use → não é suportado num request.

**Como cai na prova.** Cenário 5: o enunciado oferece "reduzir custo" e lista Batch como opção
para algo bloqueante (pegadinha). Para análise noturna/semanal, Batch é a resposta certa.

---

## 8. Review em sessão nova, multi-pass de PR grande, custos e limites

**Review em sessão nova.** A sessão que **escreveu** o código **não deve revisá-lo**: ela carrega o
raciocínio que levou às decisões e tende a **confirmá-las** (viés do contexto de raciocínio). No CI
isso é natural: o review é um `claude -p` **novo**, sem `--resume`/`--continue` da sessão geradora,
recebendo o diff e os critérios explícitos.

**Multi-pass de PR grande** (ex.: 40 arquivos):
1. **Passo 1, por arquivo:** cada arquivo revisado **isoladamente**, com o **mesmo prompt/critério**
   (bugs, tipos, segurança, padrão do time). Pode rodar em paralelo (matrix de jobs ou várias chamadas `-p`).
2. **Passo 2, integração:** um prompt **separado** recebe os **achados do passo 1** + o mapa das
   mudanças e procura problemas **entre arquivos**: contratos quebrados, fluxo de dados, erro tratado
   de um lado e não do outro.

Por quê: um único prompt com 40 arquivos sofre **diluição de atenção**: achados superficiais,
critério inconsistente entre arquivos, bug cross-file perdido.

**Custos e limites em CI (checklist):**
- `--max-turns` e [volátil] `--max-budget-usd` como **backstop**; `timeout-minutes` no job.
- `concurrency` para não empilhar runs; disparar só nos eventos necessários (ignorar drafts).
- `--allowedTools` mínimo; `--permission-mode dontAsk` em jobs que só analisam.
- CLAUDE.md **enxuto** (é lido em todo run); prompt **específico** (menos turnos).
- Ler `total_cost_usd` do JSON para acompanhar gasto por execução.
- Para o que não é urgente, **Batch** (50% mais barato).
- Segredos em secret/variável mascarada; PRs de fork não recebem secrets no GitHub.

**Anti-padrões.**
- `claude -p --continue` na sessão que gerou o código para "aproveitar o contexto" no review.
- Pedir à mesma sessão "agora revise seu próprio código com olhar crítico".
- Um prompt único para revisar 40 arquivos "para economizar chamadas".
- Resolver custo trocando o gate pré-merge por batch.

**Como cai na prova.** Cenário 5: "o review automatizado aprova quase tudo que o próprio Claude
gerou no job anterior" → review em **sessão nova e independente**. "PR de 50 arquivos com review
superficial e bugs entre módulos passando" → **multi-pass** (por arquivo + integração).

---

## Tabela de decisão

| Se… | Faça… |
|-----|-------|
| O formato da saída varia ou "quase acerta" | 2–3 exemplos concretos entrada → saída (com bordas) |
| Muitas regras de borda / regressões a cada tentativa | TDD: testes primeiro, iterar com as falhas, não alterar os testes |
| Requisito vago ou domínio desconhecido | pedir que o Claude entreviste antes de implementar |
| Problemas que interagem | uma mensagem só |
| Problemas independentes | em sequência, um por vez (revisável) |
| Job de CI trava esperando | faltou `-p` |
| Pipeline precisa ler o resultado | `--output-format json` (+ `--json-schema` → `structured_output`) |
| Quer eventos em tempo real | `--output-format stream-json` |
| Runs longos/caros | `--max-turns` (+ orçamento) como backstop, `timeout`, `concurrency` |
| Job só analisa, não deve mudar nada | `--allowedTools` só leitura + `--permission-mode dontAsk` |
| Acrescentar persona/critério sem perder o padrão | `--append-system-prompt` |
| Review automático em PR no GitHub | `claude-code-action` com `prompt` + `claude_args` |
| Controle total do pipeline | `claude -p` direto |
| Gate pré-merge / bloqueante | **síncrono**, nunca Batch |
| Análise noturna/semanal em volume | **Batch API** (50% mais barata), casar por `custom_id` |
| Parte do lote falhou | reenviar só os `custom_id` com erro |
| Revisar código gerado pelo Claude | sessão **nova** e independente |
| PR grande | multi-pass: por arquivo + integração com os achados |

## Glossário

- **`-p` / `--print`**: modo não interativo; executa, imprime e sai.
- **`--output-format json`**: objeto final com `result`, `session_id`, custo, turnos.
- **`structured_output`**: campo do JSON com a resposta conforme ao `--json-schema`.
- **`stream-json`**: um evento JSON por linha, em tempo real.
- **`--max-turns`**: teto de turnos agênticos (backstop).
- **`--append-system-prompt`**: acrescenta ao system prompt padrão.
- **`dontAsk`**: modo que nega tudo que não foi pré-aprovado; útil em CI.
- **`claude-code-action`**: Action oficial do GitHub; `prompt` + `claude_args`.
- **Batch API**: processamento assíncrono, 50% mais barato, até 24h, sem SLA, `custom_id`.
- **Review multi-pass**: passo por arquivo + passo de integração.
- **Viés do contexto de raciocínio**: tendência de a sessão geradora confirmar as próprias decisões.

## Cola de véspera

- **Exemplos concretos (2–3, com borda) > prosa.** TDD: testes primeiro, devolva as falhas, não mexa nos testes. Requisito vago → **entrevista**.
- **Relacionados → juntos; independentes → em sequência.**
- **CI sem `-p` trava.** Em `-p` ninguém aprova prompt → `--allowedTools`/`--permission-mode`.
- `--output-format json` + `--json-schema` → leia **`structured_output`**. Não faça regex em prosa.
- `--max-turns` = **backstop**, não critério de pronto. `--append-system-prompt` acrescenta; `--system-prompt` substitui.
- `dontAsk` + tools só leitura = job de análise travado e seguro.
- Action: `anthropics/claude-code-action`, `prompt` + **`claude_args`**, chave em secret, `timeout` + `concurrency`. GitLab: job com `claude -p`, variável mascarada.
- **Batch:** 50% off, até 24h, sem SLA, fora de ordem → **`custom_id`**, sem multi-turn de tools, reenvie só as falhas. **Nunca em pré-merge.**
- Review em **sessão nova** (sem `--resume` da geradora). PR grande → **por arquivo + integração**.
- Custo: turnos/orçamento, timeout, concurrency, CLAUDE.md enxuto, tools mínimas, `total_cost_usd`.

## Perguntas de checagem

1. **O job `claude "revise este PR"` fica pendurado até o timeout de 6h. Por quê?**
   Falta `-p`: sem ele o Claude Code abre a sessão interativa e espera input.
2. **Como fazer o pipeline falhar automaticamente quando o review encontra problema grave?**
   `--output-format json --json-schema '<schema com severity>'` e um `jq -e` sobre `.structured_output` que retorna erro se houver `high`.
3. **O time quer usar Batch API no review obrigatório de PR para economizar 50%. Boa ideia?**
   Não: Batch pode levar até 24h, sem SLA, e o review bloqueia o merge. Use síncrono no gate; Batch serve para análise noturna/semanal.
4. **Um job gera código com `claude -p` e o mesmo job continua com `--continue` pedindo "agora revise". O que está errado?**
   Auto-revisão na mesma sessão: o viés do contexto de raciocínio. O review deve ser uma sessão nova, com o diff e critérios explícitos.
5. **Dois bugs: o arredondamento do total e a ordem de aplicação dos descontos, sendo que um depende do outro. Como enviar ao Claude?**
   Numa mensagem só, porque interagem. Bugs independentes iriam em sequência.
