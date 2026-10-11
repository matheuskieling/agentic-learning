# Módulo 03 — Saída estruturada, validação com retry e Batch API

> **Domínio:** D4 (task statements **4.3**, **4.4** e **4.5**).
> **Cenários onde mais cai:** 6 (Structured Data Extraction) — quase inteiro — e 5 (Claude Code em CI:
> saída estruturada e Batch API).
>
> Para cada tópico: o fato-chave → o porquê → o anti-padrão que aparece como alternativa errada →
> como cai na prova. Código de aplicação em C#; JSON fica como é.

---

## 1. Por que saída estruturada

**Fato-chave:** texto livre "em formato JSON" pode sair **malformado**, **sem campo**, com **nome
ou tipo errado**, com texto em volta ("Aqui está o JSON: ..."). Num pipeline, isso quebra o parser
ou, pior, passa adiante dado errado.

A API oferece **três caminhos** para obter estrutura confiável:

| # | Caminho | O que garante |
|---|---------|---------------|
| 1 | **Tool cujo `input_schema` é a saída desejada** (extração via tool use) | O modelo preenche o `input` da tool no formato do schema |
| 2 | **`strict: true`** na tool | O `input` segue o schema **exatamente** |
| 3 | **Structured outputs**: `output_config.format` com `json_schema` | A **resposta** (texto) segue o schema |

**Anti-padrões:**
- "Peça 'responda só JSON' e faça parse com regex/try-catch" (frágil).
- "Prefill com `{`" (rejeitado nos modelos novos, Módulo 01).

**Como cai na prova:** cenário 6, como "o parser falha em 4% dos documentos porque o JSON vem com
texto em volta ou campos faltando".

---

## 2. Tool como schema (extração via tool use)

**Fato-chave:** defina uma tool que **não executa nada**; ela existe para que o modelo a "chame"
com os dados extraídos. O `input` do `tool_use` **é** o seu JSON.

```json
{
  "name": "registrar_fatura",
  "description": "Registra os dados extraídos de UMA fatura. Use sempre que receber uma fatura.",
  "strict": true,
  "input_schema": {
    "type": "object",
    "properties": {
      "numero":      { "type": "string" },
      "emissao":     { "type": "string", "format": "date" },
      "vencimento":  { "type": ["string", "null"], "format": "date" },
      "total":       { "type": "number" },
      "categoria":   { "type": "string", "enum": ["servico", "produto", "outro"] },
      "categoria_detalhe": { "type": ["string", "null"] }
    },
    "required": ["numero", "emissao", "vencimento", "total", "categoria", "categoria_detalhe"],
    "additionalProperties": false
  }
}
```

**Como garantir que a tool seja chamada [volátil por modelo]:**
- Em **modelos anteriores**, dava para **forçar** com `tool_choice: {"type": "tool", "name": "registrar_fatura"}`.
- Nos **modelos mais novos**, `tool_choice` `any`/`tool` **retorna 400**. Use `tool_choice: auto` +
  **instrução explícita nomeando a tool** + `strict: true` (e **verifique** que a chamada veio; se não,
  tente de novo), **ou** use structured outputs (seção 3) quando a tool existia só para obter JSON.

**Por quê:** o schema da tool é aplicado pela API, não pela boa vontade do modelo.

**Anti-padrão:** insistir em `tool_choice` forçado num modelo que o rejeita, ou "forçar" com
MAIÚSCULAS no prompt sem checar se a chamada veio.

**Como cai na prova:** cenário 6 ("migramos de modelo e o `tool_choice` forçado começou a dar
400; qual a alternativa?") → structured outputs ou `auto` + instrução + `strict`.

---

## 3. `strict: true` e `output_config.format`

**`strict: true` (na definição da tool):** o `input` gerado segue o schema **exatamente**.
Exigência: **`additionalProperties: false` em todo objeto**. Propriedades **opcionais são permitidas**,
mas contam para um **limite total por request** [volátil: hoje 24]. **Recomendação:** prefira colocar
tudo em `required` e expressar ausência com **nullable** — fica explícito que o dado "não existe"
(`null`) em vez de simplesmente sumir da saída.

**Structured outputs (`output_config.format`):** a **resposta** do modelo é JSON que segue o schema.

```json
{
  "model": "claude-...",
  "max_tokens": 4096,
  "output_config": {
    "format": {
      "type": "json_schema",
      "schema": { "type": "object", "properties": { "...": {} }, "required": ["..."], "additionalProperties": false }
    }
  },
  "messages": [ { "role": "user", "content": "<fatura>...</fatura> Extraia os dados." } ]
}
```

- O parâmetro de topo antigo **`output_format` está depreciado** → use `output_config.format`.
- Nos SDKs há helpers (ex.: `messages.parse()`) que validam a resposta contra o schema.
- Mesmo com schema, **cheque `stop_reason`**: com `max_tokens` a saída pode vir incompleta; com
  `refusal` pode não seguir o schema.

**Quando usar qual:**
- Quer **só o JSON** da resposta → `output_config.format`.
- O modelo está num **loop de tools** e precisa chamar ações com argumentos válidos → tools com `strict: true`.

**Anti-padrão:** schema sem `additionalProperties: false` (ou sem `strict`) e esperar garantia de formato. Campos opcionais **em si** não são o erro: o cuidado é não estourar o limite de opcionais e não deixar a ausência ambígua (por isso a preferência por `required` + nullable).

**Como cai na prova:** cenários 5 e 6. Enunciado: "precisamos de JSON que sempre valide no
parser do CI" → structured outputs / `strict`.

---

## 4. Schema ≠ semântica; padrões de schema

**Fato-chave:** **conformidade com o schema ≠ correção semântica.** O schema garante que `total`
é número; não garante que `total` = soma dos itens, que `vencimento` é depois de `emissao`, nem que o
CNPJ existe. **Valide em código.**

**Padrões de schema que evitam invenção e chute:**

| Padrão | Para quê | Exemplo |
|--------|----------|---------|
| **Campo nullable** | Dado que pode não existir na fonte → `null` em vez de inventar | `"vencimento": {"type": ["string","null"]}` |
| **Enum com `"other"` + campo de detalhe** | Categoria fora da lista sem forçar uma errada | `categoria: "outro"`, `categoria_detalhe: "locação"` |
| **Enum com `"unclear"`** | Fonte ambígua/ilegível → não chutar | `status_assinatura: "unclear"` |

**Por quê:** se o schema obriga um valor (campo obrigatório não nullable, enum fechado), o modelo
**é forçado a escolher algo**, e inventa. Dar a opção "não existe / outro / não dá para saber" é o
que mantém o dado honesto.

**Anti-padrões:**
- "Strict está ligado, então os dados estão corretos" → só o formato está.
- Campo obrigatório não nullable para dado que muitas vezes falta (gera alucinação).
- Enum fechado sem "other" (força classificação errada).

**Como cai na prova:** cenário 6. "O schema valida 100%, mas a auditoria achou totais que não batem
com os itens" → validação semântica em código. "O modelo inventa a data de vencimento" → nullable.

---

## 5. Limites do strict: o que validar no seu código

**Fato-chave [detalhe volátil]:** o modo strict/structured outputs suporta só um **subconjunto**
de JSON Schema. **Não suportados:**

- **restrições numéricas** (`minimum`, `maximum`, `multipleOf`);
- **tamanho de string** (`minLength`, `maxLength`);
- **restrições de array** além de `minItems` 0 ou 1;
- **schemas recursivos**;
- **`enum` com tipos complexos** e **`$ref` externo**.

Suportado: tipos básicos, `enum` (valores simples), `const`, `$ref` interno, `format` comuns
(`date`, `date-time`, `email`, `uuid`...), `additionalProperties: false`, `anyOf`/`allOf` (com
limitações) e **`pattern` com regex simples** (sem backreference, lookaround, `\b` ou `{n,m}` grandes).

**O que acontece com recurso não suportado:** num **schema cru** enviado à API → **erro 400** (não é
ignorado em silêncio). Os **helpers do SDK** (ex.: `messages.parse()` com modelos tipados) **tiram a
restrição do schema, movem-na para a descrição do campo e validam localmente** a resposta.

**Regra de prova:** o que o strict não suporta, **o seu código valida** (e alimenta o loop de retry,
seção 6). Não espere que a API imponha faixa numérica ou tamanho de string.

```csharp
// Validação do que o schema não garante (C#)
if (fatura.Total < 0) erros.Add("total: não pode ser negativo");
if (fatura.Itens.Sum(i => i.Valor) != fatura.Total)
    erros.Add($"total: {fatura.Total} difere da soma dos itens {fatura.Itens.Sum(i => i.Valor)}");
if (fatura.Vencimento is not null && fatura.Vencimento < fatura.Emissao)
    erros.Add("vencimento: anterior à emissão");
```

**Anti-padrões:** colocar `"minimum": 0` no schema e assumir que a API garante; ao tomar 400 por
recurso não suportado, desligar o strict "para passar" (perde a garantia de formato).

**Como cai na prova:** cenário 6 ("ligamos strict e o request com `minimum`/`maxLength` passou a dar
400" ou "o helper do SDK aceitou o schema, mas a regra de faixa precisa ser garantida") → tirar a
restrição do schema (ou deixar o helper movê-la para a descrição) e **validar em código**.

---

## 6. Loop de validação com retry (task statement 4.4)

**Fato-chave — o ciclo:** **extrai → valida → devolve os erros ESPECÍFICOS no prompt → tenta de
novo até um limite → então falha com erro** (fila de revisão humana/registro do erro).

- Validação de **schema** (campos, tipos, enums, datas) **e semântica** (somas, datas impossíveis,
  contradição entre campos, entidade referenciada que não existe).
- O feedback do retry diz **o quê** e **onde**: "total 1.250,00 difere da soma dos itens
  1.205,00; confira o item 3" — não "está errado, tente de novo".
- **Extraia o valor declarado E o valor calculado** (ex.: `total_declarado` e `soma_itens`) para
  **detectar discrepância** em vez de o modelo "corrigir" em silêncio.
- **Retry não recupera informação que não está na fonte.** Se o dado não existe no documento,
  tentar de novo só produz invenção → o certo é `null` (e, se obrigatório para o negócio, revisão humana).
- Um campo como **`detected_pattern`** (qual padrão/regra gerou o achado) permite **medir** quais
  padrões geram achados úteis e quais são descartados → alimenta o refinamento do prompt.
- Limite de tentativas é **backstop**; depois dele, **falhe explicitamente**, nunca grave o dado inválido.

**Por quê:** erros específicos dão ao modelo o que corrigir; erro genérico produz a mesma resposta.
E retry tem custo: só vale quando a informação **existe** e o erro é corrigível.

**Anti-padrões:**
- Retry genérico ("tente de novo") sem dizer o erro.
- Retry infinito / sem limite.
- Retry para campo que não existe na fonte (gera alucinação).
- Gravar o resultado inválido após esgotar tentativas, ou descartá-lo em silêncio.

**Como cai na prova:** cenário 6. "O retry melhorou pouco: a mensagem de retry é 'JSON inválido,
tente de novo'" → devolver erros específicos. "Mesmo após 3 retries o CNPJ do tomador vem errado;
o documento não traz o CNPJ" → `null` + revisão, não mais retries.

---

## 7. Batch API (task statement 4.5)

**Fato-chave:**
- **50% mais barata**, processamento assíncrono em **até 24h**, **sem SLA** de latência.
- Cada request leva um **`custom_id`**; os resultados chegam **fora de ordem** → **case por
  `custom_id`**, nunca pela posição.
- **Não suporta loop multi-turn de tools dentro de um request**: cada request é uma chamada única
  (se o modelo pedir uma tool, não há quem devolva o resultado dentro do batch).
- Ciclo: cria o batch → faça **poll de `processing_status` até `ended`** → leia os resultados.
- Cada resultado tem um tipo: **`succeeded`**, **`errored`**, **`canceled`**, **`expired`**.

**Por quê:** a Anthropic agenda o trabalho quando há capacidade, por isso o desconto e a ausência de SLA.

**Como cai na prova:** cenário 5 e 6. A pegadinha mais comum é usar batch onde há **alguém esperando**.

---

## 8. Batch: quando usar, quando não, e como operar

| Use Batch para | NÃO use Batch para |
|----------------|--------------------|
| Análise noturna de logs/documentos | Checagem **pré-merge** / passo **bloqueante** de CI |
| Relatório semanal | Atendimento em **tempo real** |
| Processamento em massa de arquivo histórico | **Depuração interativa** |
| Avaliação offline de prompts em grande volume | Fluxos com **loop de tools multi-turn** |

**Operação correta:**
- **Refine o prompt numa amostra** (requests síncronos) **antes** de rodar o volume no batch.
- Ao terminar, **reenvie só os `custom_id` que falharam** (`errored`/`expired`), não o lote inteiro.
- Combine com o **loop de validação**: resultados que não validam entram num novo lote de correção
  (com os erros específicos) ou vão para revisão.

**Anti-padrões:**
- Batch num gate de PR ("50% mais barato!") → o PR pode esperar até 24h.
- Casar resultado pela posição no arquivo.
- Reprocessar tudo porque 2% falhou.
- Rodar 100 mil documentos com um prompt nunca testado.

**Como cai na prova:** cenário 5 ("o time quer cortar custo do review automático de PR usando
Batch API") → não para pré-merge; serve para a varredura noturna. Cenário 6 ("50 mil contratos
históricos para extrair até o fim da semana") → batch, após refinar numa amostra.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| Precisa de JSON confiável da resposta | `output_config.format` (structured outputs) |
| Precisa de argumentos de tool válidos num loop | Tool com `strict: true` (`additionalProperties: false`; prefira `required` + nullable) |
| `tool_choice` forçado dá 400 no modelo novo | `auto` + instrução nomeando a tool + `strict` (verifique a chamada), ou structured outputs |
| Dado pode faltar na fonte | Campo **nullable** |
| Categoria pode não estar na lista | Enum com **"other" + detalhe** |
| Fonte ambígua/ilegível | Enum com **"unclear"** |
| Schema valida mas os números não batem | Validação **semântica em código** |
| Restrição numérica/tamanho de string importante | Valide em código (strict não garante) |
| Validação falhou | Retry com **erros específicos**, até um limite; depois falhe explicitamente |
| Dado não existe na fonte | `null` (+ revisão), não retry |
| Quer detectar inconsistência no documento | Extraia **declarado e calculado** |
| Volume grande, sem pressa | Batch API (50%, até 24h), após refinar numa amostra |
| Alguém espera o resultado (PR, tempo real) | Chamada síncrona, nunca batch |
| Resultados do batch | Case por `custom_id`; reenvie só os que falharam |

## Glossário

- **Structured outputs** — `output_config.format` com `json_schema`: a resposta segue o schema.
- **`strict: true`** — o `input` da tool segue o schema exatamente.
- **Tool como schema** — tool que só existe para receber os dados extraídos.
- **Nullable** — campo que aceita `null` (`["string","null"]`), para dado ausente.
- **"other"/"unclear"** — valores de enum que evitam forçar escolha errada ou chute.
- **Validação semântica** — regras de negócio que o schema não expressa (somas, datas, coerência).
- **Loop de retry** — reenviar com os erros específicos até um limite.
- **`detected_pattern`** — campo que registra qual padrão gerou o achado, para medir utilidade.
- **Batch API** — processamento assíncrono, 50% de desconto, até 24h, sem SLA.
- **`custom_id`** — identificador seu por request no batch; chave para casar resultados.
- **`processing_status: ended`** — o batch terminou; leia os resultados.

## Cola de véspera

- Texto livre falha. **3 caminhos:** tool como schema · **`strict: true`** · **`output_config.format`** (`output_format` de topo está depreciado).
- `strict`: **`additionalProperties: false` em todo objeto**. Opcionais são permitidas (contam para um limite [volátil]); **prefira `required` + nullable**.
- Forçar tool dá **400** nos modelos novos → `auto` + instrução + `strict`, ou structured outputs.
- **Schema ≠ semântica** → valide somas/datas/coerência **em código**.
- **Nullable** (não inventar) · **"other" + detalhe** · **"unclear"** (não chutar).
- Strict **não suporta** faixa numérica, tamanho de string, arrays além de `minItems` 0/1, recursão, `$ref` externo → schema cru dá **400**; helper do SDK move para a descrição e valida local; **seu código valida**. `pattern` simples funciona.
- Retry: **erros específicos**, **limite**, depois **falha explícita**. **Retry não cria dado que não está na fonte** → `null`.
- **Declarado + calculado** para achar discrepância; **`detected_pattern`** para medir.
- **Batch:** 50% · até 24h · sem SLA · fora de ordem → **`custom_id`** · sem multi-turn de tools ·
  poll até `ended` · `succeeded/errored/canceled/expired` · **reenvie só as falhas** · **amostra antes**.
- **Nunca batch** em pré-merge, tempo real, passo bloqueante, depuração interativa.

## Perguntas de checagem

1. **O schema strict valida 100% das saídas, mas totais não batem com os itens. Por quê e o que fazer?**
   Schema garante formato, não semântica. Validar a soma em código e devolver o erro específico no retry.
2. **O modelo inventa a data de vencimento quando ela não existe. Correção de schema?**
   Tornar o campo nullable (e mostrar no few-shot que ausente = `null`).
3. **Por que retry não resolve o CNPJ que não aparece no documento?** Porque retry não recupera
   informação ausente da fonte; só induz invenção. Devolva `null` e encaminhe à revisão.
4. **Pode usar Batch API para o review bloqueante de PR?** Não: até 24h, sem SLA. Batch é para
   trabalho sem espera (noturno, semanal, massa).
5. **Os resultados do batch vieram fora de ordem e 3% falharam. Como proceder?** Casar por
   `custom_id` e reenviar só os `custom_id` com falha.
