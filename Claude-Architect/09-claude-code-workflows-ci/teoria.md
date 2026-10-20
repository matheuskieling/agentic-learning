# Módulo 09 — Refinamento iterativo, CI/CD e review multi-instância/multi-pass

> **Task statements:** **3.5** (refinamento iterativo) e **3.6** (Claude Code em CI/CD), domínio
> **D3** (20%); **4.6** (review multi-instância e multi-pass), domínio **D4** (20%).
> **Onde cai:** cenário **5 (Claude Code for Continuous Integration)** é o principal; **2 (Code
> Generation with Claude Code)** para refinamento e auto-revisão; **4 (Developer Productivity)** para
> entrevista e iteração guiada por testes em ferramentas internas.

Duas perguntas-mãe: **"como faço o Claude convergir para o que eu quero?"** (3.5) e **"como rodo o
Claude Code sem ninguém olhando e confio no review que ele produz?"** (3.6 + 4.6). O cenário 5 pede
"feedback acionável" com "poucos falsos positivos": quase toda questão dele mistura saída
estruturada, contexto do projeto e arquitetura de review.

---

## 1. Exemplos concretos quando a prosa falha (3.5)

**Fatos de prova**
- Quando a descrição em prosa é interpretada de forma **inconsistente**, o jeito mais eficaz de
  comunicar a transformação é dar **2–3 exemplos concretos de entrada → saída** (3.5-K1, S1).
- Escolha os exemplos **nos casos que variaram** (abreviação, intervalo aberto, valor ausente).
- Mesmo mecanismo do few-shot (M02, 4.2), aplicado à iteração no Claude Code.

```text
Normalize os telefones para E.164. Exemplos:
entrada: "(51) 99876-5432"  → saída: "+5551998765432"
entrada: "051 3333 4444"    → saída: "+555133334444"
entrada: "ramal 204"        → saída: null   (não é telefone: não invente)
```

**Por quê.** Prosa é **interpretada**; exemplo é **imitado**. "Formato internacional" admite
`+55 51 9...` e `+5551...`; o par entrada/saída elimina a dúvida, inclusive na borda.

**Anti-padrões que aparecem como alternativa errada**
- Reescrever a spec em prosa **mais longa ou mais enfática**: continua sendo interpretada.
- **Votar** entre 3 execuções: escolhe a interpretação mais comum, não a certa, e triplica o custo.
- **JSON schema** para "resolver" a variação: garante **estrutura** (campos, tipos), não a
  **semântica** da transformação; `"2019+"` e `"2019–present"` são strings igualmente válidas.

**Como cai na prova.** Cenário 2: "o formato quase acerta mas varia; um colega propõe uma spec mais
detalhada. Como avaliar?" → rejeitar e dar 2–3 pares cobrindo os casos inconsistentes.

---

## 2. Iteração guiada por testes (3.5)

**Fatos de prova**
- **Escreva a suíte antes da implementação**, cobrindo **comportamento esperado, casos de borda e
  requisitos de performance** (3.5-S2).
- Itere **compartilhando as falhas** dos testes: cada rodada recebe "esperado X, obtido Y" em vez de
  "ainda está errado" (3.5-K2).
- Para corrigir **uma borda específica**, dê **um caso de teste com entrada de exemplo e saída
  esperada** (3.5-S4). Exemplo do guia: valores **null** em script de migração.

```csharp
public class LedgerAggregatorTests          // escrita ANTES de LedgerAggregator existir
{
    [Fact] public void Sums_entries_per_account() { /* esperado */ }
    [Fact] public void Negative_adjustment_reduces_balance() { /* borda */ }
    [Fact] public void Missing_fx_rate_throws() { /* borda: erro explícito, não soma silenciosa */ }

    [Fact] // performance é requisito: entra na suíte desde o início
    public void Aggregates_one_million_entries_under_two_seconds()
    {
        var sw = Stopwatch.StartNew();
        _sut.Aggregate(LedgerFixtures.Entries(1_000_000));
        Assert.True(sw.Elapsed < TimeSpan.FromSeconds(2));
    }
}
```

Ciclo: "implemente até os testes passarem, sem alterá-los" → `dotnet test` → cole a saída das falhas
→ repita até verde.

A borda do null. "Trate os nulos direito" deixa a decisão aberta (descartar? zero?
`DateTime.MinValue`?). O caso concreto fecha:

```csharp
[Fact]
public void Null_birth_date_is_migrated_as_null_and_row_is_kept()
{
    var legacy = new LegacyCustomerRow(Id: 4471, Name: "Ana Souza", BirthDate: null);
    var migrated = CustomerMigrator.Map(legacy);

    Assert.NotNull(migrated);            // a linha NÃO é descartada
    Assert.Null(migrated.BirthDate);     // não vira DateTime.MinValue
    Assert.True(migrated.NeedsReview);   // sinalizada para o time de dados
}
```

**Por quê.** O teste transforma "certo" em sinal verificável, e a falha diz exatamente o que
corrigir. A performance entra no alvo desde o começo, em vez de aparecer em produção.

**Anti-padrões que aparecem como alternativa errada**
- O Claude implementa e **depois** escreve testes que passam: os testes espelham o código, bugs
  incluídos.
- **Meta de cobertura** (ex.: 90%): mede linhas executadas, não comportamento exigido.
- Requisitos em prosa + "confirme que cada um foi atendido": autoconfirmação não é verificação.
- Feedback informal ("ainda erra nos modelos 2019"); teste de carga manual depois do merge.

**Como cai na prova.** Cenários 2 e 4: "as regressões vieram de bordas e de performance" → suíte
primeiro e iterar com as falhas. "Três tentativas de 'trate os nulos', cada uma diferente" → caso de
teste com entrada e saída esperada.

---

## 3. O padrão entrevista (3.5)

**Fatos de prova**
- **Interview pattern:** o Claude **faz perguntas antes de implementar**, para trazer à tona
  considerações que o dev **não anteciparia** (3.5-K3).
- Gatilho: **domínio desconhecido** para o dev. Exemplos do guia: **estratégia de invalidação de
  cache** e **modos de falha** (3.5-S3).

```text
Preciso adicionar cache às consultas de cotação de câmbio do PricingService e não conheço cache
distribuído. Antes de escrever código, me entreviste: invalidação (quando uma cotação fica velha?
quem precisa do valor exato?), modos de falha (e se o Redis cair? e se o provedor sair do ar?).
Transforme as respostas em requisitos e testes; só então implemente.
```

**Por quê.** Num domínio novo o dev não sabe o que não sabe: a spec que ele escreveria sozinho omite
exatamente essas decisões. As respostas viram requisitos (e testes, §2) **antes** do código.

**Entrevista × plan mode (3.4, M08).** Plan mode explora o **código**; a entrevista extrai
**decisões que não estão no código** (quanto atraso de cotação o negócio tolera?). Num serviço que
nunca teve cache, o código não tem a resposta. Os dois se combinam.

**Anti-padrões que aparecem como alternativa errada**
- "Implemente um cache padrão (TTL de 5 min) e liste as premissas no fim": premissas **depois** do
  código, decididas por default.
- O dev escreve sozinho uma spec detalhada antes: omite o que não antecipou.
- "Plan mode para inferir os requisitos de cache do código": a regra não está no código.

**Como cai na prova.** Cenários 4 e 2: "engenheiro sem experiência em X vai implementar Y; o que
fazer antes do código?" → o Claude o entrevista sobre invalidação e modos de falha.

---

## 4. Uma mensagem só ou em sequência? (3.5)

**Fatos de prova**
- Problemas que **interagem** (a correção de um muda o comportamento do outro) → **uma mensagem
  detalhada** com todos, explicando a interação (3.5-K4, S5).
- Problemas **independentes** → **iteração sequencial**: mudanças pequenas e revisáveis.

| Problema | Interage com | Como enviar |
|---|---|---|
| (1) taxa arredondada antes da conversão de moeda | (2) | juntos, numa mensagem detalhada |
| (2) detecção de duplicidade compara o valor convertido | (1) | juntos, numa mensagem detalhada |
| (3) mensagem de log enganosa; (4) README desatualizado | nenhum | em sequência, um por vez |

**Por quê.** Um a um, problemas acoplados geram correções que se atropelam: corrigir (1) muda o valor
que (2) usa. Já juntar problemas sem relação produz um diff grande e difícil de revisar.

**Anti-padrões que aparecem como alternativa errada**
- Tudo numa mensagem "para economizar turnos" ou "para o PR ficar atômico".
- Separar os acoplados em **sessões diferentes** "para isolar cada correção".
- Agrupar por **aparência** ("os dois são de validação") em vez de por **interação**.
- Seguir um por vez com "não quebre as correções anteriores" no prompt.

**Como cai na prova.** Cenários 2 e 4: lista de bugs com uma pista de interação ("a correção do
arredondamento mudou os totais que a conversão usava"). Em "Choose TWO", as corretas costumam ser as
duas metades: acoplados juntos, independentes em sequência.

---

## 5. `-p` / `--print`: Claude Code não interativo (3.6)

**Fatos de prova**
- **`-p` (ou `--print`)** roda o Claude Code em **modo não interativo**: processa o prompt, imprime o
  resultado em stdout e **sai** (3.6-K1). Exit code 0 em sucesso, diferente de 0 em falha.
- **Sem `-p`**, `claude "..."` abre a **sessão interativa** e espera input; no CI ninguém responde e
  o job **trava** até o timeout do runner (3.6-S1).
- Lê stdin (`gh pr diff 42 | claude -p "..."`). `--output-format` vale para o print mode e **não**
  substitui o `-p`.

```bash
claude "Generate xUnit tests for src/Irrigation/Scheduler.cs"      # trava: espera input
claude -p "Generate xUnit tests for src/Irrigation/Scheduler.cs"   # executa, imprime e sai
```

**Anti-padrões que aparecem como alternativa errada**
- Envolver com `timeout 15m ... || true`: o job fica verde, mas só mata a sessão parada.
- Aumentar o timeout do runner; `--max-turns` (só vale no print mode: sem `-p`, a sessão continua
  interativa e, depois de responder ao prompt inicial, espera o próximo input).
- Pseudo-TTY ou redirecionar stdin (`< /dev/null`): contorno Unix que não tira o Claude Code do modo
  interativo; o mecanismo documentado é o `-p`.
- Variáveis "headless" ou flags `--batch`/`--ci` (não existem).

> **Na doc atual [volátil]:** em `-p` ninguém responde prompt de permissão; o que precisa de
> aprovação e não foi pré-aprovado (`--allowedTools`, `--permission-mode`) é negado. Detalhe de
> permissões não é alvo da prova.

**Como cai na prova.** Cenário 5, com o sintoma disfarçado: "o job não produz nada e é morto aos 90
minutos", "o job ficou verde mas não gerou nenhum teste" → falta `-p`.

---

## 6. Achados estruturados: `--output-format json` + `--json-schema` (3.6)

**Fatos de prova**
- **`--output-format json`** devolve um objeto JSON (resultado + metadados) em vez de texto livre. Com
  **`--json-schema '<schema>'`**, a resposta conforme ao schema vem em **`structured_output`** (3.6-K2).
- Uso do guia: **achados estruturados legíveis por máquina**, postados por um script como
  **comentários inline no PR** (3.6-S2). O mesmo contrato serve a um gate que falha o build.

```bash
gh pr diff "$PR" | claude -p "Review this diff using the review criteria in CLAUDE.md." \
  --output-format json \
  --json-schema '{"type":"object","required":["findings"],"properties":{"findings":{"type":"array",
    "items":{"type":"object","required":["file","line","severity","message"],"properties":{
      "file":{"type":"string"},"line":{"type":"integer"},
      "severity":{"type":"string","enum":["blocker","major","minor"]},"message":{"type":"string"}}}}}}' \
  > review.json
```

O que o `claude -p` escreve em stdout (em `review.json`), resumido:

```jsonc
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "session_id": "9b2e…",
  "result": "Found 1 issue in the diff…",        // texto livre: NÃO parseie
  "structured_output": {
    "findings": [
      {
        "file": "src/Telemetry/SensorMapper.cs",  // ← AQUI: structured_output.findings[0].file
        "line": 57,                               // ← AQUI: structured_output.findings[0].line
        "severity": "major",
        "message": "Soil temperature is read in kelvin but compared with a Celsius threshold."
      }
    ]
  }
}
```

Para onde vai: um passo do pipeline lê `structured_output.findings[]` e posta cada item como
comentário inline no PR (API de review comments do GitHub, com `path` e `line`):

```csharp
var findings = JsonDocument.Parse(File.ReadAllText("review.json"))
    .RootElement.GetProperty("structured_output").GetProperty("findings");
foreach (var f in findings.EnumerateArray())
{
    var (file, line) = (f.GetProperty("file").GetString()!, f.GetProperty("line").GetInt32());
    if (!diff.Touches(file, line)) continue;   // schema válido ≠ achado correto: valide antes
    await github.PostInlineCommentAsync(prNumber, file, line, f.GetProperty("message").GetString()!);
}
```

**Por quê.** Máquina não lê prosa de forma confiável. O schema é um **contrato** para o próximo
passo, e o seu código continua sendo o ponto de controle (valida, formata, posta).

**Anti-padrões que aparecem como alternativa errada**
- **Regex** sobre o texto livre: quebra quando o Claude escreve "line 57 of X" em vez de `X:57`.
- "Responda só JSON, sem crases" no prompt, ou few-shot do formato: reduz, não elimina.
- **Segunda chamada** do Claude para consertar o JSON ou reescrever a prosa: probabilística e cara.
- `stream-json` lendo "a última linha" sem schema: é a mensagem de resultado, com o texto livre.
- Dar `gh`/Bash ao Claude para ele mesmo postar durante o review: some o ponto de validação.

**Como cai na prova.** Cenário 5: "15% dos achados não viram comentário inline porque a localização
vem em formatos diferentes", "o parser do gate quebra em 6% das execuções" → `--output-format json` +
`--json-schema`, lendo `structured_output`.

---

## 7. CLAUDE.md: o contexto do projeto no CI e na geração de testes (3.6)

**Fatos de prova**
- O **CLAUDE.md** do projeto é **o mecanismo** para dar ao Claude Code invocado no CI o contexto do
  projeto: **padrões de teste, convenções de fixtures, critérios de review** (3.6-K3). O `claude -p`
  carrega o CLAUDE.md do repositório como uma sessão local.
- Documente nele **os padrões de teste, o que é um teste valioso e as fixtures disponíveis**:
  melhora os testes gerados e reduz saída de baixo valor (3.6-S5).
- Na geração de testes, coloque **os arquivos de teste existentes no contexto**, para o Claude não
  sugerir cenários que a suíte já cobre (3.6-S4).

```markdown
## Testes (vale para sessões locais e para o CI)
- xUnit + FluentAssertions; um comportamento por teste; nome `Metodo_Cenario_Resultado`.
- Teste valioso: regra de negócio, borda (null, vazio, limite, fuso) ou regressão de bug.
  Não gere: teste de getter/setter, teste que só verifica o mock, cenário que já existe na suíte.
- Fixtures: `FieldFixture` (talhões válidos), `SensorReadingBuilder` (leitura com unidade explícita),
  `FakeClock` (nunca `DateTime.Now`), `SqliteInMemoryFixture`.
## Critérios de review
- Reportar: bug de lógica, conversão de unidade, null não tratado, quebra de contrato, segurança.
- Não reportar: estilo que o formatter corrige, preferência de nome.
```

```bash
claude -p "Generate xUnit tests for the public methods changed in this PR. The existing tests are in
tests/Forecasting.Tests/: read them first and do not propose scenarios they already cover." \
  --output-format json --json-schema "$(cat schemas/generated-tests.json)"
```

**Por quê.** Um lugar só, versionado, vale igual para o dev local e para o job; prompt colado no YAML
diverge entre repositórios e não chega às sessões locais. E o Claude não evita duplicar o que **não
vê**: sem a suíte no contexto, ele "descobre" de novo a borda do ano bissexto já coberta.

**Anti-padrões que aparecem como alternativa errada**
- Critérios na string de prompt de cada pipeline, ou num template só do CI: local e CI divergem.
- Critérios numa **skill** invocada pelo prompt do CI: skill é carga **sob demanda**; critério que
  vale sempre não pode depender de invocação.
- Tratar o CLAUDE.md no CI **só como custo** e encurtá-lo ou removê-lo "para economizar contexto".
- Limitar o número de testes, ou pedir "evite cenários comuns", sem mostrar a suíte existente.
- Contar com memória entre execuções noturnas: cada `claude -p` é sessão nova.

> **Na doc atual [volátil]:** a doc recomenda `--bare` para chamadas scriptadas (e diz que ele pode
> virar o padrão do `-p`); o `--bare` **pula** CLAUDE.md, skills, hooks e `.mcp.json`, e o contexto
> passa a ir por flags. **Na prova, responda: o contexto do projeto no CI vem do CLAUDE.md.**

**Como cai na prova.** "40% dos testes gerados repetem cenários existentes" → testes existentes no
contexto. "Testes de baixo valor que ignoram as fixtures" → padrões, teste valioso e fixtures no
CLAUDE.md. "Critérios divergem entre repositórios e entre CI e local" → CLAUDE.md do projeto.

---

## 8. Re-review após novos commits sem comentário duplicado (3.6)

**Fatos de prova**
- Ao re-rodar o review depois de novos commits, **inclua os achados anteriores no contexto** e
  instrua o Claude a **reportar só problemas novos ou ainda não resolvidos** (3.6-S3).

```bash
claude -p "Review the current PR diff. Findings from the previous run are in prior-findings.json.
Report ONLY new issues or previous issues still unaddressed; do not repeat fixed ones." \
  --output-format json --json-schema "$(cat schemas/rereview.json)"
```

```jsonc
{
  "type": "result",
  "structured_output": {
    "findings": [
      { "status": "still_open", "prior_id": "F-3",   // ← AQUI: structured_output.findings[0].status
        "file": "src/Harvest/YieldEstimator.cs", "line": 112, "message": "Division by zero when area is 0." },
      { "status": "new", "prior_id": null,           // ← AQUI: structured_output.findings[1].status
        "file": "src/Harvest/HarvestWindow.cs", "line": 40, "message": "Uses DateTime.Now, not the clock." }
    ]
  }
}
```

Para onde vai: `still_open` → o script responde na **thread existente** do PR; `new` → comentário
inline novo; achado anterior ausente → a thread pode ser marcada como resolvida.

**Por quê.** Cada execução é uma sessão nova: sem os achados anteriores, o Claude redescobre os
mesmos problemas **com outras palavras** e o PR acumula threads duplicadas.

**Anti-padrões que aparecem como alternativa errada**
- Deduplicar no script por **hash do texto**: o texto muda a cada execução.
- Revisar **só o diff do último commit**: perde problemas ainda abertos e interações com o resto do PR.
- Rodar o review **uma vez só** (ao abrir ou marcar como pronto): commits seguintes ficam sem feedback.

**Como cai na prova.** Cenário 5: "a cada push o bot repete, com outras palavras, comentários já
resolvidos ou já abertos" → achados anteriores no contexto + "só novos ou ainda não resolvidos".

---

## 9. Auto-revisão × instância independente (3.6, 4.6)

**Fatos de prova**
- **Limite da auto-revisão:** o modelo **retém o contexto de raciocínio** da geração e fica menos
  propenso a questionar as próprias decisões **na mesma sessão** (4.6-K1). Por isso a sessão que
  gerou o código revisa pior que uma instância independente (3.6-K4, *session context isolation*).
- **Instâncias independentes** (sem o raciocínio anterior) pegam problemas sutis **melhor que
  instruções de auto-revisão ou extended thinking** (4.6-K2).
- Na prática: uma **segunda instância** revisa o código **sem o raciocínio do gerador** (4.6-S1),
  recebendo só artefatos: diff, ticket/spec, critérios.

```bash
# sessão 1: gera
claude -p "Implement ticket AGRO-311 as described in ticket.md" --allowedTools "Read,Edit,Bash(dotnet test *)"

# sessão 2: revisa (NOVA: sem --resume/--continue da geradora; só artefatos)
git diff origin/main | claude -p "Review this diff against ticket.md and the criteria in CLAUDE.md." \
  --output-format json --json-schema "$(cat schemas/review.json)"
```

**Por quê.** Checklist ("seja crítico") e mais raciocínio (extended thinking) operam **dentro** do
mesmo contexto: o modelo reavalia o código a partir das premissas que produziram o bug. O revisor
independente lê o código como ele é, não como o gerador "acha" que ele é.

**Anti-padrões que aparecem como alternativa errada**
- "Agora revise o que você escreveu" na mesma sessão, mesmo com checklist detalhado.
- Ligar **extended thinking** no passo de auto-revisão.
- **Retomar a sessão geradora com `--resume`** num segundo job: runner limpo **não** é contexto limpo.
- A sessão geradora escreve testes do próprio código e isso vale como review: herdam as premissas.
- "Qualquer review por Claude repete os pontos cegos; só humano serve": o problema é o contexto
  compartilhado, não o modelo.

**Como cai na prova.** Cenários 5 e 2: "o review aprova quase tudo que a mesma sessão gerou", "um
colega numa sessão nova achou o bug em minutos" → instância independente. Proposta de "extended
thinking na auto-revisão" → rejeitar em favor do revisor independente.

---

## 10. Review multi-pass: por arquivo + integração (4.6)

**Fatos de prova**
- Review grande numa passada só sofre **diluição de atenção**: profundidade irregular, bugs óbvios
  perdidos, **achados contraditórios** (4.6-K3).
- Divida em **passes por arquivo** (problemas locais, mesmo critério em todos) + **pass de integração
  separado** para o **fluxo de dados entre arquivos** (4.6-S2). É prompt chaining aplicado a review
  (liga com 1.6, M07).

| Passo | Escopo | Procura |
|---|---|---|
| Por arquivo | um arquivo por vez, mesmo prompt; pode rodar em paralelo | bug local, null, tratamento de erro, segurança |
| Integração | o conjunto, com o mapa das mudanças e os achados locais | contrato produtor/consumidor, unidade ou formato que muda entre arquivos, assinatura alterada sem atualizar chamadores |

Exemplo: o produtor passa a emitir temperatura do solo em **kelvin**; o consumidor, em outro arquivo,
compara com um limiar em **Celsius**. Nenhum pass por arquivo vê o bug; só o de integração.

**Anti-padrões que aparecem como alternativa errada**
- Modelo maior / janela maior "para caber tudo": janela não resolve diluição de atenção.
- Rodar N vezes e manter só os achados de **consenso**: suprime bugs reais pegos de forma intermitente.
- Exigir PRs menores dos devs: empurra o ônus sem melhorar o sistema.
- **Só** passes por arquivo, ou agrupar por módulo sem pass de integração: perde o bug entre arquivos.

**Como cai na prova.** Cenário 5: "PR de 25 arquivos; comentários com profundidade desigual e um bug
de contrato entre produtor e consumidor passou" → por arquivo + integração.

---

## 11. Verification pass com confiança por achado (4.6)

**Fatos de prova**
- Rode um **passo de verificação** em que o modelo **reporta confiança junto a cada achado**, para
  **roteamento calibrado da revisão** (4.6-S3): o confiável vai direto ao PR; o duvidoso, a um humano.
- Os limiares são **calibrados** num **conjunto rotulado** (achados que humanos já marcaram como certos
  ou errados). Liga com 5.5 (M11).

```jsonc
{
  "type": "result",
  "structured_output": {
    "findings": [
      { "file": "src/Irrigation/ValveController.cs", "line": 88,
        "message": "Valve stays open if the moisture sensor returns null.",
        "confidence": 0.93 },   // ← AQUI: structured_output.findings[0].confidence → acima do limiar: posta
      { "file": "src/Irrigation/Schedule.cs", "line": 21,
        "message": "Possible off-by-one in the watering window.",
        "confidence": 0.41 }    // ← AQUI: structured_output.findings[1].confidence → fila dos revisores
    ]
  }
}
```

Nada é descartado: abaixo do limiar calibrado, o achado vai para a fila de triagem humana.

**As três caras da confiança (não generalize nenhuma):**

| Uso da confiança do modelo | Veredito | TS |
|---|---|---|
| Filtrar achados ("só os de alta confiança") no lugar de critérios explícitos do que reportar | errado | 4.1 |
| Escalonar atendimento ao humano por confiança autodeclarada ou por sentimento | errado | 5.2 |
| Confiança **por achado/campo**, **calibrada** com conjunto rotulado, para **rotear revisão humana** | certo | 4.6, 5.5 |

**Anti-padrões que aparecem como alternativa errada**
- "Reporte só o que tiver alta confiança e descarte o resto": filtra em vez de rotear, sem calibração.
- Treinar um classificador sobre comentários antigos antes de tentar isso: over-engineering.
- Consenso entre duas execuções como critério: um falso positivo consistente passa nas duas.
- Uma nota de confiança **única para o review inteiro**: não dá para rotear achado por achado.

**Como cai na prova.** Cenário 5: "os revisores só conseguem triar 20 de 60 achados por semana" →
verification pass com confiança por achado, limiares calibrados, baixa confiança para humanos.

---

## 12. Ponte com o M03: Batch API no CI

- Passo **bloqueante** (review pré-merge, gate de release) → **síncrono** (`claude -p` no job). A
  **Message Batches API** (50% mais barata, até 24 h, **sem SLA**) só para o que tolera latência:
  relatório noturno, auditoria semanal, geração noturna de testes.
- A Batch API **não suporta tool calling multi-turn** num request. Auditoria em que o Claude precisa
  ler arquivos ou rodar comandos via tools no meio da análise **não vai para Batch**, a menos que um
  script **pré-extraia** o conteúdo para um prompt de uma volta só.

---

## Tabela de decisão

| Se… | Faça… | TS |
|---|---|---|
| Prosa interpretada de forma diferente a cada execução | 2–3 pares entrada → saída dos casos que variam | 3.5 |
| Regressões de borda e de performance | suíte primeiro (esperado, bordas, performance); iterar com as falhas | 3.5 |
| Uma borda segue errada (null na migração) | caso de teste com entrada de exemplo e saída esperada | 3.5 |
| Dev em domínio desconhecido | entrevista: Claude pergunta (invalidação, modos de falha) antes | 3.5 |
| Problemas que interagem / independentes | uma mensagem detalhada / em sequência | 3.5 |
| Job de CI trava ou não produz nada | `-p` / `--print` | 3.6 |
| Achados viram comentário inline ou gate | `--output-format json` + `--json-schema` → `structured_output` | 3.6 |
| Padrões de teste, fixtures, critérios de review no CI | CLAUDE.md do projeto | 3.6 |
| Testes gerados de baixo valor / duplicados | CLAUDE.md com teste valioso e fixtures / testes existentes no contexto | 3.6 |
| Re-review duplica comentários | achados anteriores no contexto; só novos ou não resolvidos | 3.6 |
| Review da mesma sessão aprova tudo; proposta de extended thinking | instância independente, sem o raciocínio do gerador | 3.6, 4.6 |
| PR grande: profundidade desigual, contradições, bug entre arquivos | passes por arquivo + pass de integração | 4.6 |
| Achados demais para os revisores | verification pass com confiança por achado, calibrada, para rotear | 4.6 |
| Passo bloqueante × noturno | síncrono × Batch (sem multi-turn de tools) | 4.5 |

## Glossário

- **`-p` / `--print`**: modo não interativo; processa o prompt, imprime e sai.
- **`--output-format json` / `--json-schema`**: saída JSON; a resposta conforme ao schema vem em
  **`structured_output`**.
- **Interview pattern**: o Claude pergunta antes de implementar, para revelar o que o dev não anteciparia.
- **Session context isolation**: quem gerou o código não é quem revisa.
- **Self-review limitation**: o modelo retém o raciocínio da geração e tende a confirmá-lo.
- **Independent review instance**: instância sem o contexto de raciocínio do gerador.
- **Multi-pass review**: passes por arquivo (local) + pass de integração (entre arquivos).
- **Attention dilution**: perda de profundidade e consistência quando um prompt cobre arquivos demais.
- **Verification pass / calibrated review routing**: passo que reporta confiança por achado; limiares
  ajustados num conjunto rotulado decidem o que vai direto e o que vai para humano.

## Cola de véspera

- **Prosa inconsistente → 2–3 exemplos entrada/saída** dos casos que variam (não: prosa maior,
  votação, schema).
- **Suíte antes** (esperado + bordas + **performance**), **compartilhe as falhas**. Borda teimosa →
  **caso de teste com entrada e saída esperada**.
- **Domínio desconhecido → entrevista** (invalidação, modos de falha). Plan mode explora código;
  entrevista extrai requisito.
- **Interagem → uma mensagem detalhada. Independentes → sequência.**
- **CI sem `-p` trava.** `timeout`, TTY, `--max-turns` ou `--output-format` sozinho não resolvem.
- **`--output-format json` + `--json-schema` → `structured_output`** → comentário inline / gate.
- **CLAUDE.md = contexto do projeto no CI** (padrões de teste, fixtures, critérios, teste valioso).
- **Testes existentes no contexto** → sem duplicata. **Achados anteriores no contexto** → só novos ou
  não resolvidos.
- **Quem gerou não revisa.** Instância independente vence checklist e extended thinking na mesma
  sessão; `--resume` da geradora não é independente.
- **PR grande → por arquivo + integração** (não: janela maior, consenso, PR menor).
- **Confiança por achado, calibrada, para rotear** = certo. Filtrar por confiança (4.1) e escalonar por
  confiança/sentimento (5.2) = errado.
- **Bloqueante = síncrono; Batch só para o noturno e sem multi-turn de tools.**

## Perguntas de checagem

1. **O formato varia entre execuções; um colega quer uma spec mais detalhada. O que propor?** 2–3 pares
   entrada → saída cobrindo os casos que variaram.
2. **Um dev que nunca trabalhou com cache vai adicionar um. Primeiro passo?** O Claude o entrevista
   sobre invalidação e modos de falha antes de implementar.
3. **O job de testes foi envolto em `timeout ... || true` e não gera nada. Por quê?** Falta `-p`: a
   sessão interativa espera input; o timeout só a mata.
4. **Onde ficam os critérios de review e as fixtures que o CI deve seguir?** No CLAUDE.md do projeto.
5. **O re-review duplica comentários. Correção?** Achados anteriores no contexto; pedir só os novos ou
   ainda não resolvidos.
6. **Por que extended thinking na auto-revisão não resolve?** Roda no mesmo contexto do gerador; uma
   instância independente é mais eficaz.
7. **Como usar a confiança do modelo num review?** Por achado, num verification pass, calibrada num
   conjunto rotulado, para rotear a revisão humana; nunca para descartar achados no lugar de critérios.
