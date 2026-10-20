# Módulo 02 — Prompt engineering: critérios explícitos e few-shot

> **Task statements:** **4.1** (critérios explícitos para aumentar a precisão e reduzir falso
> positivo) e **4.2** (few-shot para consistência e qualidade). Domínio **D4 — Prompt Engineering &
> Structured Output (20% da prova)**.
> **Cenários onde cai:** **5** (review de PR em CI com falso positivo), **6** (extração de documentos
> com formatos variados) e **1** (agente de suporte: escalonamento com critérios + few-shot).
>
> Para cada tópico: fato de prova → por quê → anti-padrões que aparecem como alternativa errada →
> como cai. Código de aplicação em C#; prompts e JSON no formato real.

O fio do módulo: **quando a saída é inconsistente ou ruidosa, o primeiro suspeito é o prompt dizer
*o quê* de forma vaga.** A correção proporcional é escrever o critério (4.1) e mostrar exemplos (4.2),
antes de qualquer arquitetura nova.

---

## 1. Critério explícito em vez de instrução vaga (4.1)

**Fatos de prova**
- Instrução vaga gera julgamento inconsistente. O exemplo do guia: *"check that comments are
  accurate"* (vago) × *"flag comments only when claimed behavior contradicts actual code behavior"*
  (explícito).
- O critério explícito diz **o que reportar** (bugs, segurança) e **o que pular** (estilo menor,
  **padrões locais** que o repositório usa de propósito). É isso que reduz falso positivo, e não um
  filtro por confiança.
- Formato que funciona: **reportar / não reportar / fronteira**, com exemplos concretos.

```text
<review_criteria>
REPORT only:
- Bugs: runtime behavior differs from what the PR intends (unawaited Task, null dereference on a
  reachable path, wrong comparison operator).
- Security: user input concatenated into SQL, secrets in source, missing authorization check.
- Comments whose claimed behavior contradicts what the code actually does.
DO NOT REPORT:
- Naming, formatting, `var` vs explicit type, brace style.
- Patterns used consistently in this repository (e.g., Result<T> instead of exceptions).
BOUNDARY:
- MD5 as a file checksum → do not report. MD5 to hash passwords → report as security.
</review_criteria>
```

**Por quê:** o modelo não conhece o *seu* critério de relevância. "Importante" e "relevante" são
interpretados de um jeito diferente a cada chamada. O critério categórico torna o julgamento
**reprodutível** e **auditável**: dá para apontar qual regra gerou cada achado.

**Anti-padrões que aparecem como alternativa errada**
- "Peça para ser mais rigoroso/cuidadoso" (continua vago).
- "Rode 3 vezes e publique só o que aparecer em 2" (votação: suprime bug real intermitente).
- "Segundo modelo para revisar os comentários do primeiro" (arquitetura antes do critério).
- Mover o mesmo texto vago para o CLAUDE.md. No CI, o CLAUDE.md é o lugar certo para os critérios
  (3.6, M09), mas mudar o **lugar** não corrige a **vagueza**.

**Como cai:** cenário 5 ("o bot comenta coisas diferentes no mesmo diff", "metade é estilo");
cenário 6 (extrator que sinaliza anomalias demais). A certa define **o que reportar e o que pular**.

---

## 2. "Be conservative" não melhora a precisão; as três caras da confiança (4.1)

**Fatos de prova**
- *"Be conservative"* e *"only report high-confidence findings"* **não melhoram a precisão** quando
  comparados a critérios categóricos específicos (4.1-K2). Eles mexem em **quanto** o modelo reporta,
  não em **o que** ele considera problema.
- Resultado típico: o volume cai, a **proporção** de falso positivo continua a mesma e alguns
  achados verdadeiros somem junto.

**Por quê:** confiança e relevância são eixos diferentes. O modelo pode estar 95% seguro de que uma
variável tem nome ruim: confiança alta, mas é exatamente o achado que você não queria. E a confiança
que o modelo declara, crua (sem calibrar contra um conjunto rotulado), é mal calibrada.

**As três caras da confiança na prova** (o tema volta em M06, M09 e M11):

| Uso da confiança do modelo | Veredito | TS |
|---|---|---|
| (a) **Filtrar** achados por confiança **em vez de** definir critério explícito | **Errado** | 4.1 |
| (b) **Escalonar** atendimento por confiança autodeclarada ou sentimento | **Errado** | 5.2 |
| (c) Confiança **por campo/achado**, **calibrada** com conjunto rotulado, para **rotear revisão humana** | **Certo** | 4.6, 5.5 |

O erro em (a) não é a confiança existir; é usá-la **no lugar** do critério. Um review com critério
explícito que também anexa a confiança de cada achado para priorizar revisão é compatível com (c).

**Anti-padrões que aparecem como alternativa errada**
- "Publique só achados com confiança ≥ 0.8" como correção de falso positivo.
- "Reduza a rigidez de todas as categorias por igual" (o mesmo problema, aplicado a tudo).
- O extremo oposto: "confiança do modelo nunca serve" (contradiz 4.6/5.5).

**Como cai:** "confidence threshold" ou "be more conservative" é o distrator mais comum do 4.1.
Também aparece como afirmação a avaliar: "o volume caiu, então a precisão melhorou" (errado).

---

## 3. Falso positivo e a confiança do time: desligar a categoria temporariamente (4.1)

**Fatos de prova**
- Uma categoria com muito falso positivo **mina a confiança nas categorias precisas** (4.1-K3).
  Depois de alguns alarmes falsos, o dev ignora **o bot inteiro**, inclusive os achados de segurança
  que estavam certos.
- A correção do guia (4.1-S2) é **desligar temporariamente** as categorias com muito falso positivo,
  para recuperar a confiança, **enquanto** o prompt delas é melhorado:
  1. **Meça a precisão por categoria**, porque a média esconde a categoria ruidosa.
  2. **Desligue só as ruidosas** e mantenha as precisas no ar.
  3. **Reescreva** o critério delas (reportar / não reportar / fronteira + few-shot de aceitável ×
     problema real, seção 6) e **valide numa amostra** de PRs antigos.
  4. **Religue** quando a precisão medida estiver no nível das outras.

```text
Precisão por categoria (últimos 300 comentários)
security     94%  ← manter
correctness  89%  ← manter
style        41%  ← desligar e reescrever o critério
docs         47%  ← desligar e reescrever o critério
média        71%  ← o número que esconde o problema
```

**Por quê:** a confiança é **do sistema**, não da categoria. Cada falso positivo em `style` ensina o
dev a não ler `security`. Desligar tudo joga fora o que funciona; manter tudo continua queimando a
confiança do time.

**Anti-padrões que aparecem como alternativa errada**
- Desligar o bot inteiro até "todas as categorias chegarem a X%".
- Manter tudo e exibir a confiança ao lado de cada achado "para o dev decidir" (ônus no humano; a
  categoria ruidosa continua no ar). Não confunda com o 4.6-S3: lá a confiança por achado é
  **calibrada** e serve para **rotear a revisão**, o que é certo.
- Religar a categoria depois de só acrescentar "be more careful" (o critério não mudou).

**Ponte:** para descobrir **quais construções de código** geram os achados descartados, registre um
campo `detected_pattern` em cada achado (4.4, M03).

**Como cai:** cenário 5 (bot de PR) e qualquer sistema que gere alertas para humanos (cenário 1:
alertas do agente para supervisores; cenário 6: anomalias para revisores). Enunciado típico: "a
categoria X tem 60% de falso positivo e o time passou a ignorar todos os alertas".

---

## 4. Severidade com exemplos de código por nível (4.1)

**Fatos de prova**
- Para classificar a severidade de forma consistente, defina **cada nível com exemplos concretos de
  código** (4.1-S3). Adjetivos ("crítico = problema grave") não bastam: a mesma omissão vira
  `critical` num PR e `minor` em outro.

```text
<severity_levels>
CRITICAL — blocks merge. Exploitable or data-corrupting on a normal path.
  var sql = $"SELECT * FROM Invoices WHERE CustomerId = '{request.CustomerId}'";  // SQL injection
  private const string ApiKey = "sk_live_9f2...";                                  // secret in source
HIGH — wrong behavior in production on a common path; no security impact.
  _repo.SaveReadingAsync(reading);         // Task not awaited: exceptions lost, write may not finish
  var c = await _db.Customers.FindAsync(id);
  return c.Email;                          // FindAsync returns null for an unknown id
MEDIUM — correct result, degraded performance or robustness under realistic load.
  foreach (var order in orders)            // N+1: one query per order
      order.Items = await _db.Items.Where(i => i.OrderId == order.Id).ToListAsync();
DO NOT REPORT — style and local conventions.
  var total = items.Sum(i => i.Amount);      // 'var' instead of decimal
  if (reading is null) return Result.Fail(); // repo convention: Result<T> instead of exceptions
</severity_levels>
```

**Por quê:** o exemplo de código ancora o nível. Diante de um caso novo, como
`_ = _mailer.SendInvoiceAsync(invoice);` (um descarte explícito da Task), o modelo compara com os
exemplos ("é o `SaveReadingAsync` não aguardado com outra sintaxe → HIGH") em vez de reinterpretar
um adjetivo a cada execução.

**Anti-padrões que aparecem como alternativa errada**
- Usar uma nota de confiança como severidade.
- Rodar várias vezes e ficar com a severidade mais frequente (votação mascara a falta de critério).
- Reduzir para dois níveis com definições de uma linha (menos níveis, mesma ambiguidade).

**Como cai:** cenário 5, "o mesmo tipo de achado recebe severidades diferentes em PRs diferentes" ou
"achados `blocker` travam o merge e os times reclamam". A certa: **níveis com exemplos de código**.

---

## 5. Few-shot quando as instruções não bastam: formato acionável (4.2)

**Fatos de prova**
- Few-shot é **a técnica mais eficaz** para obter saída **consistentemente formatada e acionável**
  quando **instruções detalhadas sozinhas** produzem resultado inconsistente (4.2-K1). Se o prompt
  já é detalhado e a saída continua variando, **mais prosa não resolve**: mostre exemplos.
- Os exemplos demonstram o **formato exato**: **location, issue, severity, suggested fix** (4.2-S2).
  Um exemplo completo mostra a granularidade da localização (arquivo:linha), o tamanho da descrição
  e o que é um "fix" concreto (código, não "considere refatorar").
- **2–4 exemplos**, delimitados (`<example>`) e separados da entrada real.

Onde os exemplos entram no request que a aplicação de CI monta:

```jsonc
// POST /v1/messages
{
  "model": "<modelo>",
  "max_tokens": 2048,
  "system": "You review C# pull requests for the billing service.\n<review_criteria>...</review_criteria>\n<examples><example><diff>+ _repo.SaveReadingAsync(reading);</diff><finding>{\"location\": \"src/Billing/ReadingService.cs:44\", \"issue\": \"SaveReadingAsync is not awaited; exceptions are lost.\", \"severity\": \"high\", \"suggested_fix\": \"await _repo.SaveReadingAsync(reading);\"}</finding></example> ...</examples>",  // ← AQUI: critérios + few-shot
  "messages": [
    { "role": "user", "content": "<diff>...diff real do PR...</diff>" }  // ← entrada real, fora dos exemplos
  ]
}
```

Cada `finding` vira um **comentário inline no PR** (a aplicação posta via API do GitHub). O few-shot
torna o **conteúdo** de cada campo consistente e acionável. A **garantia** de JSON parseável é papel
do schema: `tool_use` + JSON schema (4.3, M03) ou, no Claude Code em CI, `--output-format json` +
`--json-schema` (3.6, M09). Na prova: "saída não parseável" → schema; "campos inconsistentes, fix
vago" → few-shot.

> **Na doc atual [volátil]:** em alguns modelos recentes, pedir que o modelo preencha um campo
> chamado `reasoning`/`thinking` pode ser recusado; prefira `explanation` ou `evidence`. Não cai na prova.

**Anti-padrões que aparecem como alternativa errada**
- Refinar ainda mais a instrução em prosa (já foi tentado).
- Dividir em duas chamadas (uma acha o problema, outra escreve o fix) para "especializar".
- Janela de contexto maior / mais código do repositório no prompt.
- Exemplos num formato **diferente** do que a instrução pede: o modelo segue o exemplo.

**Como cai:** cenário 5 ("achados sem linha ou com fix genérico, apesar de uma seção de formato
detalhada"); cenário 6 ("o schema já é imposto, mas o conteúdo varia: passos de reprodução às vezes
em lista, às vezes em parágrafo").

---

## 6. Few-shot para casos ambíguos: o porquê, generalização e aceitável × problema real (4.2)

**Fatos de prova**
- Few-shot demonstra o **tratamento de casos ambíguos** (4.2-K2), como **seleção de tool para
  pedidos ambíguos** e **lacunas de cobertura de teste no nível de branch**.
- Crie **2–4 exemplos direcionados** aos casos ambíguos, cada um mostrando **por que** uma ação foi
  escolhida **em vez das alternativas plausíveis** (4.2-S1). O contraste ensina a fronteira.
- Exemplos com o porquê permitem **generalizar o julgamento para padrões novos**, em vez de
  reconhecer só os casos listados (4.2-K3). Uma lista de 60 regras cobre 60 casos; três exemplos bem
  explicados ensinam o critério.
- Exemplos que separam **padrão aceitável** de **problema real** reduzem falso positivo **e**
  generalizam (4.2-S3). Se o prompt só mostra problemas, tudo que se parece com eles vira achado.

**Exemplo 1 — escalonamento no suporte** (cenário 1; o 5.2-S1 pede critérios + few-shot, M06):

```text
<example>
Customer: "My pallet arrived 3 days late and the frozen goods inside thawed. I want the shipping
fee back and the value of the goods."
Action: refund the shipping fee; escalate the goods claim with a handoff summary.
Why not resolve both: policy covers late-delivery fee refunds but is silent on damage to contents.
Why not escalate both: the fee refund is squarely within policy; escalating it lowers resolution.
</example>
```

**Exemplo 2 — lacuna de cobertura por branch** (cenário 5, geração de testes):

```csharp
public decimal CalculateTariff(Reading r)
{
    if (r.Kwh < 0) throw new ArgumentOutOfRangeException(nameof(r));  // branch A
    if (r.Slot.IsPeak) return r.Kwh * PeakRate;                         // branch B
    return r.Kwh * StandardRate;                                         // branch C
}
// Existing test: CalculateTariff_OffPeak_ReturnsStandardRate() → exercises only C
```

```text
<example>
Gap: branches A (negative reading) and B (peak slot) are never exercised. Suggest tests for A and B.
Why not "covered": a function-level test hides untested branches.
Why not a test for C: it duplicates the existing off-peak test.
</example>
```

**Exemplo 3 — aceitável × problema real** (cenário 5):

```csharp
// ACEITÁVEL — não reportar: o host pediu shutdown; encerrar em silêncio é o esperado
catch (OperationCanceledException) when (ct.IsCancellationRequested) { }

// PROBLEMA REAL — reportar (HIGH): a cobrança falhou e ninguém fica sabendo
catch (Exception) { }
```

O exemplo explica *por que* o primeiro é aceitável (engole só o cancelamento que o próprio código
pediu). Diante de `catch (TaskCanceledException) when (ct.IsCancellationRequested)`, que nunca viu,
o modelo aplica o mesmo raciocínio. Uma regra literal "não reporte `OperationCanceledException`" não
cobriria a variação.

**Few-shot não é o 1º passo quando a descrição da tool é mínima:** aí a correção é **reescrever as
descrições** (2.1, Q2 oficial, M04). Few-shot de seleção de tool é a resposta quando as descrições
já são boas e o **pedido** é genuinamente ambíguo.

**Anti-padrões que aparecem como alternativa errada**
- 15–20 exemplos, "um por tipo de pedido": mais custo, e o modelo se prende à superfície.
- Exemplos do caso mais frequente ou do caso fácil, em vez dos casos que **falham**.
- Exemplos só com a resposta final, sem o porquê (o modelo copia o formato, não o critério).
- Exemplos só de problemas, sem o "parecido, mas aceitável".
- Classificador por palavra-chave antes de tentar exemplos (over-engineering).

**Como cai:** cenário 1 ("decisões inconsistentes em pedidos ambíguos"; "quais DUAS características
tornam os exemplos eficazes?"); cenário 5 ("a função tem teste, mas um branch não"; "trocar os
exemplos por uma lista de 60 padrões proibidos: boa ideia?").

---

## 7. Few-shot em extração: formatos variados, campos vazios e alucinação (4.2)

**Fatos de prova**
- Few-shot **reduz alucinação em extração** (4.2-K4), por exemplo com **medidas informais** ("uns
  20 quilos", "do tamanho de um micro-ondas") e **estruturas de documento variadas**.
- Use exemplos que demonstrem estruturas diferentes (4.2-S4): **citação inline × bibliografia no
  fim**; **metodologia numa seção própria × detalhes diluídos no texto**.
- Quando um campo **obrigatório volta vazio/nulo** em documentos que **têm** a informação, só que num
  formato que o prompt nunca mostrou, **acrescente exemplos de extração correta desses formatos**
  (4.2-S5).

```text
<example>
<document>...As shown by Moreira et al. (2022), outages fall 18%... [sem seção Methods; na
introdução:] "we interviewed 340 field technicians between March and May 2023"...</document>
<output>{"citations": [{"author": "Moreira et al.", "year": 2022, "style": "inline"}],
"method": "interviews", "sample_size": 340}</output>
</example>
<example>
<document>...outages fall 18% [14]... Methods: survey of 1,120 households... References:
[14] Moreira, L. et al. 2022.</document>
<output>{"citations": [{"author": "Moreira, L. et al.", "year": 2022, "style": "numbered"}],
"method": "survey", "sample_size": 1120}</output>
</example>
```

Medida informal: o exemplo mostra como **registrar o que foi dito**, sem inventar precisão.

```jsonc
// saída da extração → gravada na tabela de sinistros (claims)
{
  "package_weight": { "value": 20, "unit": "kg", "approximate": true, "source_text": "uns 20 quilos" },
  "package_dimensions": null,   // ← AQUI: "do tamanho de um micro-ondas" não vira 45×30×30
  "dimensions_source_text": "do tamanho de um micro-ondas"
}
```

**Três situações que a prova separa:**

| Sintoma | Causa | Correção |
|---|---|---|
| Campo nulo, mas o dado **está** no documento em outra estrutura (tabela do anexo, bloco de assinatura) | O prompt nunca mostrou essa estrutura | **Few-shot** com esses formatos (4.2-S5) |
| Modelo **inventa** valor quando o dado **não existe** | Campo obrigatório "força" um valor | Campo **nullable** (4.3, M03) **+** exemplo com `null` |
| Dado ausente da fonte; retry após retry | Informação não está no documento | Retry **não** resolve (4.4, M03); `null` + rotear |

**Anti-padrões que aparecem como alternativa errada**
- Tornar o campo **não-nulo** "para forçar o modelo a achar" (convida a inventar).
- "Não alucine" / "procure com mais atenção" (vago).
- Exigir que os autores dos documentos sigam um template único (ônus em humanos que você não controla).
- Pré-processamento por regex para cada formato (over-engineering antes do few-shot).

**Como cai:** cenário 6 ("o campo obrigatório vem nulo em 18% dos documentos; a revisão manual acha
o valor no anexo"); relatórios com citações em estilos diferentes; cenário 1 (agente extraindo peso
e dimensões de mensagens informais).

---

## 8. A escada de correções

1. **Critério explícito** (reportar / pular / fronteira; severidade com exemplos de código).
2. **Few-shot** (2–4 exemplos direcionados, com o porquê, o aceitável e o formato completo).
3. **Estrutura e validação**: `tool_use` + JSON schema, campos nullable, validação em código (M03).
4. Só então **arquitetura extra** (segundo modelo, classificador, pipeline novo).

Exceções: regra crítica (dinheiro, identidade, compliance) vai para **código** desde o início
(hook/gate, M06). Descrição de tool mínima → reescreva a descrição (M04). PR grande com atenção
diluída → passes por arquivo + passe de integração (M09). Os "2–3 pares entrada/saída" para guiar o
Claude Code numa transformação são o refinamento iterativo do 3.5, no M09.

---

## Tabela de decisão

| Se o enunciado mostra... | A resposta tende a ser... | Distrator típico |
|---|---|---|
| Saída inconsistente, muito estilo/padrão local | Critério explícito: reportar / pular / fronteira | "Mais rigor", votação, confiança ≥ X |
| "Be conservative" já tentado; volume caiu, FP não | Critério categórico | Subir o limiar de confiança |
| Uma categoria ruidosa e o time ignorando tudo | Medir por categoria; desligar a ruidosa; reescrever; religar | Desligar o bot; exibir confiança |
| Mesma falha com severidades diferentes | Níveis com exemplos de código | Severidade por votação |
| Instruções detalhadas, conteúdo/formato variando | Few-shot com location, issue, severity, fix | Mais prosa; duas chamadas |
| Saída não parseável para automação | Schema (`tool_use` / `--json-schema`) | Só few-shot |
| Casos ambíguos decididos de forma inconsistente | 2–4 exemplos com o porquê vs alternativas | 20 exemplos; classificador |
| Lista de regras falha em caso novo | Poucos exemplos com o porquê | Ampliar a lista |
| Falso positivo em padrões aceitáveis | Few-shot de aceitável × problema real | Só exemplos de problemas |
| Campo nulo com o dado presente em outro formato | Few-shot com esses formatos | Tornar o campo não-nulo |
| Valor inventado quando o dado não existe | Nullable + exemplo com `null` | Retry; "não alucine" |

## Glossário

- **Critério explícito** — definição categórica do que reportar, do que pular e da fronteira.
- **Padrão local** — convenção que o repositório usa de propósito (ex.: `Result<T>`); não é achado.
- **Falso positivo (FP)** — achado que não deveria existir; em excesso numa categoria, derruba a
  confiança nas outras.
- **Few-shot** — 2–4 exemplos no prompt (entrada → saída + porquê) que ensinam formato e julgamento.
- **Lacuna de cobertura por branch** — função "com teste" em que algum ramo nunca é executado.

## Cola de véspera

- **Vago → inconsistente.** Corrija com **reportar (bugs, segurança) / pular (estilo, padrões
  locais) / fronteira**, não com filtro de confiança.
- **"Be conservative" / "only high-confidence" não melhoram a precisão**: mudam o volume, não o quê.
- **Três caras da confiança:** filtrar em vez de critério = errado (4.1) · escalonar por confiança ou
  sentimento = errado (5.2) · por campo/achado, **calibrada** com conjunto rotulado, para **rotear
  revisão** = certo (4.6/5.5).
- **Categoria ruidosa mina as precisas.** Meça por categoria → **desligue temporariamente** a
  ruidosa → reescreva + valide → religue.
- **Severidade:** cada nível com **exemplo de código**.
- **Few-shot = técnica mais eficaz** quando instruções detalhadas não dão consistência. Formato
  completo: **location, issue, severity, suggested fix**.
- **2–4 exemplos nos casos ambíguos**, com o **porquê vs alternativas plausíveis** → generaliza.
- Inclua o **aceitável parecido** (reduz FP) e as **estruturas variadas** (inline × bibliografia;
  metodologia em seção × diluída).
- **Nulo com o dado presente** → few-shot dos formatos. **Dado ausente** → nullable + `null`, sem retry.
- Escada: critério → few-shot → schema/validação → arquitetura. Regra crítica → código.

## Perguntas de checagem

1. **O prompt diz "check that error handling is adequate" e os achados variam a cada execução. O que
   mudar?** Critério explícito: o que reportar (ex.: exceção capturada e descartada num caminho de
   escrita), o que pular, fronteira.
2. **O time acrescentou "only report findings you are highly confident about". O volume caiu 40%,
   mas o percentual de FP não mudou. Por quê?** A instrução mexe no volume, não no critério.
3. **A seção de formato é detalhada, mas metade dos achados vem sem linha ou com "consider
   refactoring". Próximo passo?** 2–4 exemplos completos (location, issue, severity, suggested fix).
4. **Um campo obrigatório volta nulo em 18% dos contratos, e o valor está numa tabela do anexo. O
   que fazer?** Few-shot com extração correta desse formato (não tornar o campo não-nulo).
