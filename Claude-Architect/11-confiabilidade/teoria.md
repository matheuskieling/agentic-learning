# Módulo 11 — Propagação de erro, revisão humana e proveniência

> **TS cobertos:** **5.3** (propagação de erro), **5.5** (revisão humana e calibração de confiança),
> **5.6** (proveniência e incerteza na síntese multifonte), todos os bullets.
> **Onde cai:** Cenários **3** e **6** (principal); **1** e **4**.
> **Pontes:** formato do erro na tool (`isError`, `errorCategory`) → M04 (2.2); escalonamento (5.2)
> → M06; metadados entre agentes → M07 (1.3) e M10 (5.1); verification pass com confiança → M09 (4.6).

A pergunta do módulo: **quando algo falha ou diverge, o sistema mostra isso a quem decide, ou
esconde?** O coordenador só recupera o erro que enxerga em detalhe; o revisor só pega o erro que
alguém mandou olhar; o leitor só confia no que rastreia até a fonte. (Guardrails e evals não têm TS
no guia e ficam fora deste módulo.)

---

## 1. Erro estruturado: o que o coordenador precisa para decidir

**Fatos de prova (5.3-K1, 5.3-S1, 5.3-K3)**
- O subagent que não conclui devolve um **contexto de erro estruturado**: **tipo de falha**, **o que
  foi tentado**, **resultado parcial** e **alternativas possíveis**.
- Com isso o coordenador escolhe: **retentar com a consulta modificada**, **tentar outra fonte** ou
  **seguir com o parcial** e anotar a lacuna.
- **Status genérico** (`"search unavailable"`) **esconde** essas peças: o coordenador não sabe se vale
  retentar, o que já foi feito nem o que já tem.

A saída do subagent (disparado pela tool `Task`) volta como `tool_result` no histórico do coordenador:

```jsonc
// Próximo request do coordenador → POST /v1/messages
{
  "messages": [
    { "role": "assistant", "content": [ { "type": "tool_use", "id": "toolu_07", "name": "Task",
        "input": { "subagent_type": "document-analyzer", "prompt": "Analise os 19 artigos ..." } } ] },
    { "role": "user", "content": [ { "type": "tool_result", "tool_use_id": "toolu_07",
        "content": {                                    // (serializado como texto)
          "status": "partial",
          "completed": [ "...13 análises com fonte..." ],
          "failure": { "type": "transient",                                   // ← AQUI
                       "attempted": "6 artigos, 3 tentativas com backoff (503)",
                       "unresolved_ids": ["PMC-90211", "..."],
                       "alternatives": ["mirror open-access", "versão preprint"] } } } ] }
  ]
}
```

**Por quê.** No hub-and-spoke (1.2), só o coordenador tem a visão do todo: sabe se 13 de 19 artigos
bastam, se outro subagent cobre a lacuna ou se ela vai para o relatório. Sem detalhes, ele chuta.

**Anti-padrões que aparecem como alternativa errada:** "retry com backoff e, esgotado, `search
unavailable`" (o retry local está certo; o status genérico é o defeito; é a B da oficial 8); stack
trace e HTTP cru (detalhe não é contexto de decisão); re-delegar a tarefa inteira a cada falha.

**Como cai na prova.** Cenários 3 e 1: "qual propagação permite recuperação inteligente?". A certa
entrega tipo + tentado + parcial + alternativas.

> **Na doc atual [volátil]:** a tool de subagent se chama `Agent` (antes `Task`). Na prova, `Task`.

---

## 2. Falha de acesso × resultado vazio válido

**Fatos de prova (5.3-K2, 5.3-S2)**

| Situação | Significa | Decisão |
|---|---|---|
| Timeout, 503, sem permissão | **A consulta não rodou** (falha de acesso) | Retry, outra fonte ou lacuna anotada |
| HTTP 200 com **0 resultados** | **Rodou e não achou** (vazio válido) | É achado; não se retenta |

O relatório de erro tem que **distinguir os dois**, senão o coordenador lê "não existe" onde a
verdade é "não sei". Na tool MCP é o `isError` (M04): `{ "isError": true, "content": [...] }` na falha;
`isError: false` com lista vazia no vazio válido.

```csharp
// ERRADO: supressão silenciosa; o timeout vira "nenhuma política encontrada"
catch (TimeoutException) { return new PolicySearchResult(state, Policies: []); }

// CERTO: falha de acesso é erro estruturado; vazio só quando a busca rodou
catch (TimeoutException ex)
{
    return PolicySearchResult.AccessFailure(state, failureType: "timeout", retryable: true,
        attempted: $"SearchAsync(state={state})", detail: ex.Message);
}
```

**Por quê.** O vazio falso contamina tudo depois ("o estado X não tem política") sem ninguém
desconfiar. O vazio verdadeiro é achado legítimo e não deve disparar retry.

**Anti-padrões:** `catch → []`; retentar um vazio válido "porque deve ter dado erro"; um só
`status: "no_results"` para os dois casos.

**Como cai.** Cenário 3: "o relatório diz que não há estudos sobre X, mas existem" e os logs mostram
timeouts. Cenário 1: "o pedido não existe" quando o backend caiu.

---

## 3. Recuperação local e os dois anti-padrões opostos

**Fatos de prova (5.3-S3, 5.3-K4)**
- **Recuperação local primeiro:** o subagent trata falhas **transitórias** (retry com backoff) e **só
  propaga o que não resolveu**, com **o que tentou** e o **parcial**. Erro não retentável
  (permissão, negócio) sobe direto, com a categoria.
- **Dois anti-padrões opostos, ambos errados:** (1) **supressão silenciosa**, ou seja, vazio/sucesso
  quando falhou; (2) **abortar o workflow inteiro** por uma falha, jogando fora o trabalho bom.
- O certo: **seguir com o que deu certo, reportar o que falhou com contexto, o coordenador decide.**

Pseudocódigo C#-like (o Agent SDK oficial é Python/TypeScript):

```csharp
for (var attempt = 1; attempt <= 3; attempt++)              // dentro do subagent de garantia
{
    var r = await manufacturerApi.CheckAsync(serial, ct);
    if (r.Ok) return WarrantyResult.Success(r.Data);
    if (!r.IsRetryable) return WarrantyResult.Failure(r.Category, attempted: serial, attempts: attempt);
    await Task.Delay(TimeSpan.FromSeconds(Math.Pow(2, attempt)), ct);
}
return WarrantyResult.Failure("transient", attempted: serial, attempts: 3,
    partial: registrationFromOrder, alternatives: ["data da nota fiscal do pedido"]);
```

**Por quê.** O transitório resolvido no subagent nem chega ao coordenador. Subir cada 503 faz o
coordenador re-delegar tarefas inteiras (custo, latência), e o "o que tentou" evita retry cego.

**Anti-padrões que aparecem como alternativa errada:** "centralizar todo retry no coordenador";
"capturar e devolver lista vazia para o run sempre terminar"; "manter o abort, porque incompleto é
pior que nada"; "escalar para humano a cada falha de subagent".

**Como cai.** Cenário 1 (backend com 503 intermitente), Cenário 4 (agente em 38 repositórios, um
falha), Cenário 3.

---

## 4. Anotações de cobertura na síntese

**Fato de prova (5.3-S4).** A saída da síntese traz **anotações de cobertura**: quais achados estão
**bem sustentados** e quais **áreas têm lacuna por fonte indisponível**. É o destino final do erro
estruturado: a falha não recuperada vira lacuna **declarada**.

```jsonc
// Saída da síntese → coordenador → subagent de relatório
{ "coverage": [
    { "topic": "Custos 2025 por classe de medicamento", "status": "well_supported", "sources": 7 },
    { "topic": "Políticas estaduais de cobertura", "status": "gap",                 // ← AQUI
      "reason": "Portal sem resposta para OR, WA e NV após retry", "impact": "3 de 12 estados" } ] }
```

**Por quê.** O leitor precisa saber onde confiar e onde falta base; sem a anotação, uma seção com
metade das fontes parece tão sólida quanto as outras.

**Anti-padrões:** omitir a lacuna; aviso genérico "pode estar incompleto" (não diz **onde**); preencher
a lacuna com conhecimento geral ou material de outro sistema; segurar o relatório até tudo voltar.

**Como cai.** Cenários 3 e 4 (dossiê de sistema legado com um MCP server fora do ar).

---

## 5. Métrica agregada esconde segmento: valide por tipo e campo

**Fatos de prova (5.5-K1, 5.5-K4, 5.5-S2)**
- Acurácia **agregada** alta (ex.: 97%) pode esconder desempenho ruim em **tipos de documento** ou
  **campos** específicos.
- **Antes de automatizar** as de alta confiança ou **reduzir a revisão humana**, meça **por tipo de
  documento e por campo**; automatize só o segmento que bate a meta sozinho.

| Segmento | Volume | Acurácia |
|---|---|---|
| Holerites (PDF digital) | 61% | 99,2% |
| Contratos de trabalho | 27% | 97,8% |
| Formulários de dependentes escaneados, campo `dependent_birth_date` | 9% | **78%** |
| Cartas de oferta em espanhol | 3% | 88,5% |
| **Agregado** | 100% | **97,6%** |

**Por quê.** O agregado é dominado pelo volume; o segmento pequeno vai mal sem mexer no número, e o
custo do erro nele (folha errada) não é proporcional ao volume.

**Anti-padrões que aparecem como alternativa errada:** "97% supera a meta, desligue a revisão";
"aumente a amostra uniforme" (mede melhor **o mesmo agregado**); "automatize primeiro os tipos de
maior volume"; "meta mais alta" ou "média móvel de 30 dias" (ainda agregados).

**Como cai.** Cenário 6: "o PM quer desligar a revisão com 98%; avalie" ou "por que a métrica estável
não mostrou o erro que o cliente vê?".

---

## 6. Confiança por campo, calibrada, para rotear revisão humana

**Fatos de prova (5.5-K3, 5.5-S3, 5.5-S4)**
- O modelo emite **confiança por campo** (não um número por documento).
- Os **limiares** são **calibrados com um conjunto de validação rotulado**: por campo, compare a
  confiança com a acurácia real e escolha o limiar que atinge o erro aceitável.
- Vão para **revisão humana**: **confiança baixa** (abaixo do limiar calibrado) **ou** **fonte ambígua
  ou contraditória** (duas datas de admissão no mesmo contrato). E a fila **prioriza a capacidade
  limitada** dos revisores, não a ordem de chegada.

```jsonc
// POST /v1/messages: extração de contrato
{
  "tool_choice": { "type": "tool", "name": "record_contract" },
  "tools": [ { "name": "record_contract", "input_schema": { "type": "object", "properties": {
      "start_date": { "type": "object", "properties": {
          "value":      { "type": ["string", "null"] },
          "confidence": { "type": "number", "minimum": 0, "maximum": 1 } } },   // ← AQUI
      "conflict_detected": { "type": "boolean" } } } } ],
  "messages": [ { "role": "user", "content": "<contrato>...</contrato>" } ]
}
```

O `input` do `tool_use` vai para o roteador: campo abaixo do limiar **ou** `conflict_detected: true`
→ fila de revisão; o resto → folha de pagamento (e entra na amostragem da seção 7).

```csharp
// Calibração de UM campo: sample = conjunto rotulado (IsCorrect conferido por humanos)
double ThresholdFor(IReadOnlyList<LabeledExtraction> sample, double maxError)
{
    foreach (var t in new[] { 0.80, 0.85, 0.90, 0.95, 0.98 })
    {
        var above = sample.Where(e => e.Confidence >= t).ToList();
        if (above.Count >= 200 && above.Count(e => !e.IsCorrect) <= maxError * above.Count)
            return t;                        // abaixo de t → revisão humana
    }
    return double.PositiveInfinity;          // campo não confiável: tudo para revisão
}
```

**Por quê.** O número cru do modelo não é probabilidade confiável; calibrado contra rótulos, passa a
dizer "abaixo de 0,9, neste campo, erramos 6%". Cada campo se comporta de um jeito, daí o limiar
**por campo**. O contraditório vai para humano mesmo com confiança alta.

> **As três caras da confiança (não generalize):**
>
> | Uso | Veredito | TS |
> |---|---|---|
> | Filtrar achados por "só alta confiança" em vez de critério explícito | **Errado** | 4.1 |
> | Escalar atendimento por confiança autodeclarada ou sentimento | **Errado** | 5.2 |
> | Confiança **por campo/achado**, **calibrada** com rotulados, para **rotear revisão** | **Certo** | 5.5, 4.6 |

**Anti-padrões:** score por documento (a média esconde o campo fraco); limiar único "que pareceu bom
em 30 exemplos"; "abandone a confiança e faça amostra uniforme"; mandar tudo para revisão (estoura a
capacidade); fila por ordem de chegada; ignorar o contraditório porque a confiança está alta.

**Como cai.** Cenário 6: "avalie o limiar 0,85 igual para todos os campos"; "ache a falha no fluxo de
revisão".

---

## 7. Amostragem aleatória estratificada das extrações de alta confiança

**Fatos de prova (5.5-K2, 5.5-S1)**
- As extrações **acima do limiar** vão direto ao sistema e **ninguém olha**. Para continuar sabendo
  quanto erram: **amostra aleatória delas, estratificada** (tipo de documento, campo, template, faixa
  de confiança), revisada por humanos.
- Dois objetivos: **medir a taxa de erro contínua** do que é auto-aprovado e **detectar padrões de
  erro novos** (template novo, layout que mudou).

> **Não confunda:** "revisar 20% do alto risco, 10% do médio, 5% do baixo" é outra coisa (taxa de
> revisão por faixa de risco), não a amostragem estratificada do guia. E "revisar só o que o modelo
> marcou como incerto" nunca mede o erro do resto.

**Por quê.** A calibração envelhece: documentos mudam e o modelo pode errar **com confiança alta**,
justamente onde o roteamento é cego. Aleatória para não ter viés; estratificada para o segmento raro
aparecer em número suficiente.

**Anti-padrões:** monitorar só as correções dos revisores (que só veem baixa confiança); amostra
uniforme de tudo; esperar reclamação de cliente; calibrar uma vez e nunca mais medir.

**Como cai.** Cenário 6: "o dashboard mostra 1,2% de erro estável, mas a auditoria achou 18% de
datas erradas com confiança ≥ 0,95; por que ninguém viu?". Nada amostrava as de alta confiança.

---

## 8. Proveniência: mapeamento afirmação → fonte

**Fatos de prova (5.6-K1, 5.6-K2, 5.6-S1)**
- A **atribuição se perde no resumo**: comprimidos em prosa sem **mapeamento afirmação → fonte**, os
  achados mantêm o fato, mas a citação sai errada ou some.
- Subagents emitem **claim-source mappings estruturados**: afirmação + **URL/nome do documento** +
  **trecho relevante** (+ página e datas).
- A síntese **preserva e mescla**: a mesma afirmação de três fontes vira **uma** afirmação com **três**
  fontes, e é isso que a torna "bem estabelecida".

```jsonc
// Saída do subagent de análise → coordenador (tool_result do Task) → prompt da síntese
{ "findings": [ {
    "claim": "Monitoramento remoto reduziu readmissões em 30 dias em IC",
    "sources": [ { "url": "https://.../study-123", "document": "Smith et al., JACC",   // ← AQUI
                   "excerpt": "30-day readmission fell from 24.1% to 19.0%",
                   "page": 6, "published": "2024-03-11", "data_period": "2021-2022" } ] } ] }
```

**Por quê.** Conteúdo separado de metadados (1.3) sobrevive a cada salto entre agentes; texto corrido
não. Em setor regulado, afirmação sem fonte rastreável não passa em compliance.

**Anti-padrões:** "peça à síntese que cite as fontes" sem estrutura na entrada; resumir cada subagent
num parágrafo; votar citações entre duas execuções; dar `verify_fact` à síntese para re-achar fontes
que já existiam; mesclar guardando só o valor final.

**Como cai.** Cenário 3: "11 de 42 afirmações citam o estudo errado, mas cada uma está em alguma
fonte lida". Cenário 6: mesclar extrações de vários documentos mantendo a origem de cada valor.

---

## 9. Conflitos entre fontes e dados temporais

**Fatos de prova (5.6-K3, 5.6-S3, 5.6-K4, 5.6-S4)**
- **Estatísticas conflitantes de fontes críveis:** **anote o conflito com atribuição**. **Não escolha
  um arbitrariamente** (mais recente, média, "amostra maior").
- **Quem reconcilia:** o subagent de análise **termina a análise** com os valores **incluídos e
  anotados**; o **coordenador** decide como reconciliar **antes** da síntese. O subagent não para no
  meio, não escolhe e não pula o coordenador.
- **Dados temporais:** exija **data de publicação e período de coleta** nas saídas. 11,3% (2019) e
  14,8% (2025) não são contradição; são períodos diferentes.

```jsonc
// Saída do subagent de análise → coordenador
{ "measure": "redução de readmissão em 30 dias",
  "values": [ { "value": "12%", "source": "Estudo A (n=1.840)", "data_period": "2022" },
              { "value": "21%", "source": "Estudo B (n=610)",   "data_period": "2022" } ],
  "conflict": true,                                                          // ← AQUI
  "note": "Mesmo período; A por intenção de tratar, B por protocolo" }
```

**Por quê.** Escolher esconde uma incerteza real; a média cria um número que nenhuma fonte publicou.
Quem tem a visão do todo para decidir é o coordenador.

**Anti-padrões:** "use a fonte mais recente"; "tire a média"; "pare e pergunte ao usuário"; "mande
direto para a síntese"; "descarte fontes com mais de N anos"; "mantenha o flag por precaução" quando
os períodos diferem.

**Como cai.** Cenários 3 e 6: duas fontes críveis divergem → anotar; flag de conflito em 31% dos
casos, quase todos entre anos diferentes → campos de data.

---

## 10. O relatório: consolidado × contestado e formato por tipo de conteúdo

**Fatos de prova (5.6-S2, 5.6-S5)**
- **Seções explícitas** separando **achados bem estabelecidos** (fontes concordam) de **contestados**
  (divergem, cada valor com sua fonte).
- **Preserve as caracterizações originais e o contexto metodológico**: "preliminar", "n=48", "só
  salário-base". Não normalize para um tom neutro e assertivo.
- **Renderize por tipo:** **financeiro em tabela**, **notícias em prosa**, **achados técnicos em lista
  estruturada**, em vez de um formato uniforme.

**Por quê.** Misturar consenso e disputa faz um número contestado parecer fato. E cada conteúdo tem um
formato legível: 9 classes × 6 trimestres viram uma tabela, não 54 bullets.

**Anti-padrões:** "tudo em bullets uniformes, para consistência"; "um valor por item, fontes no
rodapé"; "tire as ressalvas para ficar assertivo"; "padronize a terminologia das fontes".

**Como cai.** Cenário 3 ("ache a falha": prompt do relatório força formato uniforme); Cenário 6
(benchmark com pesquisas divergentes; escolha DUAS: consolidado × contestado + qualificadores).

---

## Tabela de decisão

| Se... | Faça... |
|---|---|
| Subagent falhou e o coordenador vai decidir | Erro estruturado: **tipo, tentado, parcial, alternativas** |
| "Retry e, esgotado, `search unavailable`" | Rejeite o status genérico |
| Timeout/503 × HTTP 200 com zero | **Falha de acesso** (decidir retry) × **vazio válido** (achado) |
| Falha transitória no subagent | **Retry local**; propague só o não resolvido, com tentado + parcial |
| Uma etapa falhou num workflow longo | **Siga com o resto** e reporte; nem suprimir, nem abortar |
| Fonte indisponível na síntese | **Anotação de cobertura** (bem sustentado × lacuna) |
| Agregado alto, querem reduzir revisão | **Por tipo de documento e campo**; automatize só o segmento que bate a meta |
| Rotear revisão por confiança | **Por campo**, limiar **calibrado** em conjunto **rotulado** |
| Fonte ambígua/contraditória; revisores limitados | **Revisão humana** e fila **priorizada** |
| Alta confiança vai direto ao sistema | **Amostra aleatória estratificada delas**: erro contínuo + padrões novos |
| Síntese perde citações | **Claim-source mappings**; a síntese **preserva e mescla** |
| Fontes críveis divergem | **Anote com atribuição**; análise termina, **coordenador reconcilia** |
| "Conflito" entre anos diferentes | **Datas de publicação/coleta** nas saídas |
| Relatório final | **Consolidado × contestado**, ressalvas preservadas, **tabela/prosa/lista** |

## Glossário

- **Contexto de erro estruturado:** tipo de falha + tentado + parcial + alternativas.
- **Falha de acesso × vazio válido:** a consulta não rodou × rodou e não achou nada.
- **Supressão silenciosa:** devolver falha como sucesso (vazio).
- **Recuperação local:** o subagent resolve os transitórios antes de propagar.
- **Coverage annotation:** marca o bem sustentado e a lacuna por fonte indisponível.
- **Field-level confidence:** score do modelo por campo extraído.
- **Calibração:** limiar ajustado comparando confiança e acerto num conjunto de validação rotulado.
- **Amostragem aleatória estratificada:** sorteio por estrato no conjunto de alta confiança.
- **Claim-source mapping:** afirmação → URL/documento + trecho (+ página, datas).
- **Bem estabelecido × contestado:** fontes concordam × divergem.

## Cola de véspera

- Erro = **tipo + tentado + parcial + alternativas**; status genérico **esconde contexto**.
- **Falha de acesso ≠ vazio válido.** Timeout → decisão de retry; HTTP 200 com zero → achado.
- **Supressão silenciosa** e **abortar tudo**: **ambos** errados. Siga com o resto, reporte a falha.
- Subagent **recupera transitório localmente**; propaga o resto **com o que tentou e o parcial**.
- Síntese com **anotações de cobertura**.
- **Agregado esconde segmento**: valide **por tipo e campo** antes de automatizar ou reduzir revisão.
- **Confiança por campo calibrada em rotulados** roteia revisão (certo). Errado: escalar por
  confiança/sentimento (5.2) e filtrar achados por confiança (4.1).
- Para humano: **baixa confiança** ou **fonte ambígua/contraditória**; **priorize** os revisores.
- **Amostra aleatória estratificada das de ALTA confiança** → erro contínuo + padrões novos.
  (Não é "20/10/5% por risco".)
- **Claim-source mappings** emitidos pelos subagents, **preservados e mesclados** na síntese.
- Conflito → **anotar com atribuição**; análise termina; **coordenador reconcilia** antes da síntese.
- **Datas de publicação/coleta**: diferença temporal não é contradição.
- Relatório: **consolidado × contestado**, ressalvas e método preservados; **financeiro = tabela,
  notícias = prosa, técnico = lista estruturada**.

## Perguntas de checagem

1. **13 de 19 artigos analisados; 6 falharam com 503 após retry. O que o subagent devolve?**
   Os 13 + tipo de falha + o que tentou + alternativas. Nem `"analysis failed"`, nem os 13 como se
   fossem tudo.
2. **"Nenhuma política publicada" para 4 estados; 3 existem. Logs: 3 requests sem resposta, 1 HTTP 200
   vazio. Causa raiz?** Falha de acesso reportada como vazio válido.
3. **Hoje uma falha aborta o run; um colega propõe `catch` devolvendo lista vazia.** Ambos são
   anti-padrão: siga com o resto, reporte a falha com contexto, anote a lacuna.
4. **98,6% nas de alta confiança; o PM quer desligar a revisão.** Exija acurácia por tipo e campo;
   automatize só os segmentos que batem a meta sozinhos.
5. **Como saber se as de alta confiança continuam boas?** Amostra aleatória estratificada delas,
   revisada por humanos.
6. **Limiar 0,85 igual para 22 campos, "bom em 30 contratos"; há 1.200 rotulados.** Calibre por campo
   no conjunto rotulado; não abandone o roteamento por confiança.
7. **Fontes críveis dão 12% e 21% (mesmo período).** O subagent termina a análise com os dois valores
   anotados; o coordenador reconcilia antes da síntese.
8. **O relatório força tudo em bullets de 25 palavras.** Tabela para custos, prosa para notícias,
   lista estruturada para achados técnicos; consolidado × contestado.
