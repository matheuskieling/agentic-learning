# Módulo 11 — Confiabilidade: escalonamento, propagação de erro, revisão humana, proveniência, guardrails e evals

> Task statements do blueprint: **5.2** (escalonamento), **5.3** (propagação de erro),
> **5.5** (revisão humana), **5.6** (proveniência). Mais, em nível de arquitetura, **guardrails** e
> **avaliação (evals)**, que atravessam o exame inteiro (o "medir antes de mexer" do espírito da
> prova). Cai com força nos Cenários **1** (suporte), **3** (pesquisa multiagente) e **6** (extração).

A pergunta que amarra o módulo: **como o sistema se comporta quando algo dá errado ou quando ele
não sabe?** Confiável não é "nunca erra": é **escalar na hora certa, não esconder falha, saber de
onde veio cada afirmação, revisar onde o risco está e medir antes de mudar**.

---

## 1. Escalonamento: quando escalar (e quando NÃO)

**Escale de imediato quando:**
- o cliente **pede humano explicitamente** ("quero falar com uma pessoa"). Não tente "só mais uma
  vez" resolver: honre o pedido;
- há **lacuna ou exceção de política** (o caso não está coberto, ou exige exceção que o agente não
  tem autoridade para conceder, ex.: reembolso acima do limite, conta de falecido);
- **não há progresso** após tentativas razoáveis (o agente tentou os caminhos válidos e travou).

**NÃO escale por:**
- **sentimento** alto (cliente irritado, xingando). **Sentimento ≠ complexidade**: cliente furioso
  com cobrança duplicada de 5 dólares → **resolva**; cliente calmíssimo pedindo exceção de política →
  **escale**;
- **confiança autodeclarada** baixa ("tenho 60% de certeza"). Confiança verbal do modelo é **mal
  calibrada**; não é sinal confiável para roteamento;
- **tamanho da conversa** (número de turnos), por si só.

**Por quê.** Os gatilhos certos são **objetivos e verificáveis** (pedido explícito, regra de
política, ausência de progresso). Sentimento e autoconfiança são ruidosos: escalam casos simples
(custo, fila humana lotada) e deixam passar casos complexos ditos com calma.

**Gatilhos críticos em código.** Se a regra é "acima de 500 BRL exige humano", isso é um
**pré-requisito programático** (hook `PreToolUse` que bloqueia `process_refund` e encaminha), não
uma frase no prompt.

**Anti-padrões que aparecem como alternativa errada.** "Treinar um classificador de sentimento para
escalar clientes irritados"; "escalar quando o modelo disser que está pouco confiante"; "escalar
toda conversa com mais de 15 turnos"; "pedir ao modelo para usar o bom senso para decidir quando escalar".

**Como cai na prova.** Cenário 1, quase sempre. Pegadinha: a alternativa de **análise de sentimento**
parece sofisticada e "centrada no cliente". Outra: a de **confiança autodeclarada**, que parece
"o modelo sabe quando não sabe".

---

## 2. Desambiguação e handoff estruturado

**Desambiguação.** Quando a busca retorna **vários clientes** (dois "Maria Souza" no mesmo
CEP), o agente **pede um identificador adicional** (número do pedido, e-mail, últimos dígitos do
documento). **Não chuta** o mais provável nem escolhe o primeiro da lista. Agir sobre o cliente
errado é um incidente de privacidade e financeiro.

**Handoff estruturado.** O humano que recebe o caso **normalmente não vê o transcript** (ou não tem
tempo de lê-lo). O handoff é um **resumo estruturado**:

```json
{
  "cliente": {"id": "C-44817", "verificado": true},
  "problema": "Cobrança duplicada no pedido A-99213",
  "pedido_do_cliente": "Estorno de 184,90 BRL",
  "acoes_tomadas": ["Identidade verificada", "Confirmada captura duplicada no gateway"],
  "motivo_do_escalonamento": "Valor acima do limite de reembolso autônomo (150 BRL)",
  "causa_raiz_provavel": "ERR_DUPLICATE_CAPTURE no gateway",
  "acao_recomendada": "Aprovar estorno integral da 2ª captura",
  "valor": 184.90
}
```

**Anti-padrões.** Encaminhar "o transcript completo" como handoff; handoff em texto livre
("cliente com problema de cobrança, ver conversa"); escolher o cliente mais recente quando há
vários matches.

**Como cai na prova.** Cenário 1. Pegadinha: "anexar a transcrição inteira para não perder nada"
soa completo, mas o humano precisa do resumo acionável.

---

## 3. Propagação de erro estruturada

**Fato-chave.** Erro que atravessa camadas (tool → subagent → coordenador) precisa carregar
**contexto para decisão**:

```json
{
  "isError": true,
  "errorCategory": "transient",
  "isRetryable": true,
  "retryAfterSeconds": 30,
  "service": "patent-search-api",
  "attempted_action": "search(query='solid-state battery electrolyte', since=2022)",
  "message": "Timeout após 3 tentativas com backoff",
  "partial_results": [{"id": "US-2023-0142", "title": "..."}],
  "alternatives": ["usar base EPO", "restringir período a 2024"]
}
```

**Regras.**
- **Recuperação local primeiro:** o subagent trata **transitórios** (timeout, 503, rate limit)
  com retry e backoff **dentro dele**; só propaga o que **não resolveu**, com o contexto do que
  tentou.
- **Não aborte o workflow inteiro** por uma etapa: **continue com o parcial, anote a lacuna,
  ofereça alternativa**. Um relatório com "fonte X indisponível; cobertura de patentes incompleta"
  vale mais que nenhum relatório.
- **Vazio ≠ falha.** HTTP 200 com lista vazia = "busca rodou, nada encontrado" (informação útil).
  Timeout/503 = "a busca **não rodou**" (erro). Devolver `[]` quando o backend caiu é **supressão
  silenciosa**: o coordenador conclui "não há patentes" quando na verdade não sabe.
- Categorias e ação: **transitório** → retry/backoff; **validação** → corrigir entrada e tentar de
  novo; **negócio** (política) → explicar ou escalar, não retentar; **permissão** → escalar.

**Anti-padrões.** `"Operation failed"` genérico; `catch { return new List<Result>(); }`; abortar
toda a pesquisa porque um subagent falhou; o coordenador refazer cegamente o retry que o subagent
já fez; retentar erro de negócio.

```csharp
// ERRADO: supressão silenciosa — o coordenador lê "nada encontrado"
catch (HttpRequestException) { return new SearchResult(Items: []); }

// CERTO: erro estruturado que distingue "não rodou" de "rodou e veio vazio"
catch (HttpRequestException ex) when (IsTransient(ex))
{
    return SearchResult.Failure(category: "transient", retryable: true,
        attempted: query, partial: parciais, message: ex.Message);
}
```

**Como cai na prova.** Cenário 3 (subagent de busca com timeout; síntese afirma "não há estudos")
e Cenário 1 (tool de pedido caiu; agente diz ao cliente que o pedido não existe). Pegadinha:
"abortar e reportar falha geral" parece seguro; "retentar indefinidamente" parece resiliente.

---

## 4. Revisão humana: onde colocar o olho humano

**Amostragem estratificada por risco.** Não revise 5% uniforme. Estratifique: por exemplo **20%
dos casos de alto risco, 10% de médio, 5% de baixo** (valores ilustrativos). Ações irreversíveis ou
de alto valor podem exigir revisão de 100%.

**Confiança por campo, calibrada.** Em extração, peça confiança **por campo** (não um número para o
documento inteiro) e **calibre contra um conjunto rotulado**: "quando o modelo diz 0,9 neste
campo, ele acerta 90% das vezes?". Confiança não calibrada **não significa nada** e não deve
rotear revisão. Depois de calibrada, use limiares por campo para mandar à fila humana.

**Métrica agregada esconde falha por tipo.** 97% de acurácia geral pode esconder **45% em notas
manuscritas** (que são 4% do volume). Sempre **quebre por tipo de documento e por campo**. A
decisão "automatizar 100%" baseada só no agregado é a armadilha clássica.

**Anti-padrões.** Amostra uniforme pequena; usar a confiança autodeclarada crua como gatilho;
"acurácia global de 97% → desligar a revisão humana"; revisar só o que o modelo marcou como
incerto (sem calibração).

**Como cai na prova.** Cenário 6 (extração de faturas, contratos, notas) e Cenário 5 (achados de
review automatizado). Pegadinha: o número agregado alto é apresentado como prova de prontidão.

---

## 5. Proveniência da informação

**Mapa afirmação → fonte.** Cada afirmação da síntese carrega: local da evidência (trecho/página),
URL ou documento, **data de publicação**, tipo de fonte (primária, secundária, opinião). Em
multiagente, os subagents devolvem **conteúdo separado de metadados** para a atribuição sobreviver à
síntese.

```json
{
  "afirmacao": "O mercado de baterias de estado sólido cresceu 38% em 2025",
  "fonte": {"tipo": "relatório setorial", "titulo": "...", "url": "...", "pagina": 14,
            "publicado_em": "2026-02-10", "dados_referentes_a": "2025", "coletado_em": "2026-10-09"},
  "certeza": "fonte_unica"
}
```

**Conflito entre fontes.** Fonte A diz 38%, fonte B diz 24%. **Não escolha um em silêncio, não tire
média.** Anote os dois valores com suas fontes e, se possível, a provável razão (metodologia,
período, escopo).

**Dados temporais.** Registre "dados de", publicação e coleta. 24% (dados de 2024) e 38% (dados de
2025) **não são contradição**: são períodos diferentes. Sem a data, vira um falso conflito (ou uma
falsa "correção").

**Rótulos de certeza e formato.** Rotule cada conclusão: **consolidado** (várias fontes
independentes concordam), **contestado** (fontes divergem), **fonte única**. Preserve ressalvas das
fontes. **Formato conforme o conteúdo:** tabela para dados financeiros/comparativos, cronologia para
eventos, prosa para argumentação.

**Anti-padrões.** Síntese em prosa fluida sem citações; "resolver" conflito pegando a fonte mais
recente ou a média sem dizer; descartar ressalvas para o texto ficar mais assertivo; perder a
fonte no handoff subagent → coordenador.

**Como cai na prova.** Cenário 3, em peso. Pegadinha: "use a fonte mais recente" ou "tire a média
para reconciliar" parecem razoáveis; a resposta é **anotar o conflito com as fontes**.

---

## 6. Guardrails em nível de arquitetura

Guardrail é qualquer controle que **limita o que o sistema pode fazer ou dizer**. Para a prova,
o critério é o mesmo do curso todo: **o que é crítico vai em código determinístico; o prompt é
best-effort**.

| Camada | Exemplo | Determinístico? |
|--------|---------|-----------------|
| Entrada | validar/normalizar input, detectar tentativa de injection em conteúdo externo, mascarar PII | Sim (código) |
| Ação (tools) | `PreToolUse` bloqueia `process_refund` sem identidade verificada ou acima do limite; least privilege nas tools e permissões | Sim |
| Saída | validação de schema + validação semântica (somas, datas), filtros de conteúdo | Sim |
| Comportamento | instruções no system ("não prometa prazos") | Não (probabilístico) |
| Humano | aprovação obrigatória para ação irreversível ou de alto valor | Sim (gate) |

**Princípios.**
- **Defesa em camadas:** prompt orienta, código garante, humano aprova o irreversível.
- **Least privilege:** o agente só tem as tools e permissões de que precisa (um subagent de pesquisa
  não precisa de `process_refund`).
- **Conteúdo externo é dado, não instrução** (páginas web, e-mails, documentos lidos por tools).
- **Falhar fechado** em ação crítica: se a verificação não roda, a ação não acontece.

**Anti-padrões.** "Adicionar ao prompt, em maiúsculas, NUNCA faça X" como única proteção de regra
financeira; um segundo LLM como único guardrail de algo que uma regra de código resolve; dar todas
as tools a todos os agentes "por flexibilidade".

**Como cai na prova.** Cenário 1 (reembolso, verificação de identidade) e Cenário 5 (CI com
permissões amplas). Pegadinha: a alternativa de prompt reforçado é a mais barata e "parece"
suficiente.

---

## 7. Avaliação (evals): medir antes de mexer

**Conjunto de teste rotulado.** Um conjunto de casos com a **resposta esperada** (ou rubrica),
representativo do tráfego real **e** com casos de borda/adversariais (documentos manuscritos,
pedidos ambíguos, tentativas de injection). Sem ele, "melhorou" é opinião.

**Medir por segmento.** Reporte a métrica **por tipo** (tipo de documento, intenção do cliente,
idioma, campo extraído). O agregado esconde a regressão no segmento pequeno (seção 4).

**Mudanças guiadas por métrica.**
1. Estabeleça a **linha de base** antes de mudar.
2. Mude **uma coisa por vez** (prompt, exemplos, modelo, effort, descrição de tool).
3. Rode o mesmo conjunto e compare **por segmento**; procure regressões, não só o ganho médio.
4. Mantenha o conjunto como **teste de regressão** (rode a cada mudança e ao migrar de modelo).

**Graders.** Prefira checagem **determinística** quando der (campo extraído == esperado, JSON
válido, tool certa chamada). Para julgamento aberto, **LLM-as-judge com rubrica explícita**,
calibrado contra uma amostra julgada por humanos. Avalie também o **comportamento** em agentes: a
tool certa, escalonou quando devia, **não** escalonou quando não devia.

**Anti-padrões.** Ajustar o prompt olhando 3 exemplos à mão e publicar; mudar prompt, modelo e
exemplos ao mesmo tempo; reportar só acurácia global; usar o próprio conjunto de exemplos few-shot
como teste (vazamento).

**Como cai na prova.** Cenário 6 ("como saber se a mudança no prompt melhorou a extração?") e
Cenário 1 ("como validar que o novo critério de escalonamento não piorou?"). Pegadinha:
"testar manualmente alguns casos" é a alternativa rápida e tentadora.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| Cliente pede explicitamente um humano | **Escale de imediato** (com handoff estruturado) |
| Caso exige exceção de política / fora da política | **Escale** |
| Cliente furioso, mas o problema é simples e coberto | **Resolva**; não escale por sentimento |
| Modelo diz "não tenho certeza" | Não use como gatilho; use critérios objetivos |
| Busca retorna vários clientes compatíveis | **Peça identificador** para desambiguar |
| Humano vai assumir o caso | **Resumo estruturado** (cliente, problema, ações, motivo, recomendação, valor) |
| Tool/subagent falha com erro transitório | **Retry local com backoff**; propague só o não resolvido, com contexto |
| Uma etapa falhou num workflow de várias | **Continue com o parcial**, anote a lacuna, ofereça alternativa |
| Backend caiu e o código devolve `[]` | Errado: devolva **erro estruturado** (vazio ≠ falha) |
| Erro de negócio/permissão | Não retente; explique ou escale |
| Precisa decidir o que revisar | **Amostragem estratificada por risco** |
| Quer rotear revisão por confiança | Confiança **por campo, calibrada** contra rotulados |
| Acurácia agregada alta | **Quebre por tipo e campo** antes de decidir |
| Fontes divergem | **Anote os dois valores com as fontes**; não escolha nem faça média |
| Números de períodos diferentes | Registre datas; **não é contradição** |
| Regra crítica (financeira, segurança) | **Código** (hook, validação), não só prompt |
| Vai mudar prompt/modelo | **Linha de base + conjunto rotulado + medir por segmento**, uma mudança por vez |

## Glossário

- **Escalonamento:** transferir o caso para um humano.
- **Sentimento ≠ complexidade:** emoção do cliente não indica dificuldade do caso.
- **Confiança autodeclarada:** quando o modelo afirma o próprio grau de certeza; mal calibrada.
- **Handoff estruturado:** resumo acionável entregue ao humano no escalonamento.
- **Desambiguação:** pedir identificador quando há múltiplos matches.
- **Erro estruturado:** objeto com categoria, retentável, ação tentada, resultado parcial, alternativas.
- **Recuperação local:** o subagent trata transitórios antes de propagar.
- **Supressão silenciosa:** esconder uma falha como sucesso (ex.: `[]` quando o backend caiu).
- **Amostragem estratificada:** taxas de revisão diferentes por faixa de risco.
- **Calibração:** confiança declarada bate com a taxa de acerto observada.
- **Proveniência:** rastreio de cada afirmação até sua fonte (local, URL, data, tipo).
- **Rótulos de certeza:** consolidado / contestado / fonte única.
- **Guardrail:** controle que limita o que o sistema faz ou diz (entrada, ação, saída, humano).
- **Least privilege:** cada agente com as tools/permissões mínimas necessárias.
- **Eval:** avaliação sistemática contra um conjunto rotulado.
- **Linha de base:** medição antes da mudança, para comparar.
- **LLM-as-judge:** modelo avaliando saídas com rubrica, calibrado contra humanos.

## Cola de véspera

- **Escale já:** pedido explícito de humano · lacuna/exceção de política · sem progresso após tentativas razoáveis.
- **Não escale por:** sentimento · confiança autodeclarada · tamanho da conversa. **Sentimento ≠ complexidade.**
- Vários clientes no match → **peça identificador**. Nunca chute.
- Handoff = **resumo estruturado** (o humano não lê transcript).
- Erro = **objeto estruturado** (categoria, retentável, tentado, parcial, alternativas).
  Subagent **recupera transitório localmente**; **não aborte o workflow**: parcial + lacuna anotada.
- **Vazio ≠ falha.** `[]` com 200 = nada encontrado; timeout = não rodou. Nunca `catch → []`.
- Revisão: **estratificada por risco**; confiança **por campo, calibrada**; **agregado esconde segmento** (97% vs 45% manuscrito).
- Proveniência: **afirmação → fonte + data**; conflito **anotado, nunca resolvido em silêncio nem por média**;
  períodos diferentes não são contradição; rótulos **consolidado/contestado/fonte única**; formato conforme o conteúdo.
- Guardrails: **crítico em código**, prompt é best-effort, humano no irreversível, least privilege, conteúdo externo é dado.
- Evals: **conjunto rotulado**, **por segmento**, **linha de base**, **uma mudança por vez**, regressão contínua.

## Perguntas de checagem

1. **Um cliente calmo pede reembolso de 2.000 BRL de um produto fora da janela de devolução. Um
   cliente furioso reclama de frete cobrado em dobro (12 BRL), coberto pela política. Quem escala?**
   O calmo (exceção de política). O furioso tem um problema simples e coberto: resolva.
2. **A tool de busca de patentes deu timeout e o subagent devolveu lista vazia. O que vai dar
   errado e como corrigir?**
   O coordenador vai concluir "não há patentes". Corrija com erro estruturado (transitório,
   retentável, consulta tentada, parcial) após retry local; a síntese anota a lacuna.
3. **A extração tem 97% de acurácia geral. Pode desligar a revisão humana?**
   Não sem quebrar por tipo de documento e campo: um segmento pode estar em 45%. Depois, revisão
   estratificada por risco e confiança por campo calibrada.
4. **Duas fontes dão 24% e 38% para o mesmo indicador. O que a síntese faz?**
   Verifica as datas de referência (podem ser períodos diferentes). Se for o mesmo período, anota os
   dois valores com as fontes e marca como contestado; não escolhe nem faz média.
5. **O time quer trocar o prompt de extração. Qual o processo mínimo?**
   Linha de base no conjunto rotulado, uma mudança por vez, comparação por segmento (tipo e campo),
   checagem de regressões, conjunto mantido como regressão.
