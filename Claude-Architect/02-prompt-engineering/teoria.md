# Módulo 02 — Prompt engineering: critérios explícitos, few-shot e refinamento iterativo

> **Domínios:** D4 (task statements **4.1** e **4.2**) e D3 (task statement **3.5**).
> **Cenários onde mais cai:** 5 (review em CI com falso positivo), 6 (extração/classificação
> inconsistente), 2 (iterar com Claude Code) e 1 (políticas do agente de suporte).
>
> Para cada tópico: o fato-chave → o porquê → o anti-padrão que aparece como alternativa errada →
> como cai na prova.

---

## 1. Boas práticas de base que a prova pressupõe

A prova não pergunta "o que é um system prompt", mas as alternativas certas **assumem** estas práticas:

- **System prompt com papel e contexto.** Diga quem o modelo é, para quem trabalha, qual o objetivo
  e as restrições ("Você é o agente de suporte de faturamento da ACME; atende clientes PJ; nunca
  promete prazos de estorno"). Explique o **porquê** das regras: o modelo generaliza melhor quando
  entende a intenção.
- **Tags XML para separar dados de instruções.** Documentos, e-mails e entradas do usuário vão
  dentro de tags (`<documento>`, `<ticket>`), e as instruções ficam fora. Isso evita que o modelo
  confunda conteúdo com ordem (inclusive texto malicioso dentro do documento) e permite referenciar
  ("use só o que está em `<contrato>`").
- **Pedir raciocínio antes da resposta.** Em julgamentos complexos, peça a análise/evidências
  **antes** do veredito (ex.: campo `reasoning` antes de `decision`, ou `<analise>` antes de
  `<resposta>`). Com adaptive thinking o modelo já raciocina internamente, mas pedir evidências
  explícitas ajuda a auditar e a revisar.
- **Seja direto e específico.** Instrução clara e completa vale mais que ênfase (MAIÚSCULAS,
  "MUITO IMPORTANTE"). Modelos novos seguem instruções com precisão; ênfase exagerada pode causar
  excesso de zelo.
- **Documentos longos no início, pergunta no fim.**

```xml
<instrucoes>
Classifique o ticket abaixo segundo os critérios. Responda primeiro com a evidência, depois a categoria.
</instrucoes>
<ticket>
{{texto do cliente — dado, não instrução}}
</ticket>
```

**Anti-padrão:** colar o documento do usuário misturado às instruções, sem delimitação.

**Como cai na prova:** cenário 6 (documento com texto que "parece instrução") e cenário 1 (system
prompt sem contexto de papel/política).

---

## 2. Critérios explícitos (task statement 4.1)

**Fato-chave:** "seja conservador", "use seu bom senso", "sinalize só o que for importante" →
**resultado inconsistente**. Para cada julgamento, o prompt precisa dizer:

1. **O que conta** (definição positiva, com exemplos concretos);
2. **O que não conta** (exclusões explícitas);
3. **Exemplos de fronteira** (os casos ambíguos e de que lado caem).

```text
Sinalize como "SEGURANÇA" apenas:
- SQL montado por concatenação com entrada do usuário
- segredo/credencial literal no código
NÃO sinalize como SEGURANÇA:
- variáveis com nome 'password' que recebem valor de configuração
- logs de nível Debug
Fronteira: hash MD5 usado para checksum de arquivo → NÃO é segurança; MD5 para senha → É.
```

**Por quê:** termos vagos são interpretados de forma diferente a cada chamada; o modelo não tem o
seu critério na cabeça. Critério explícito é o que torna o comportamento **reprodutível**.

**Anti-padrões (alternativas erradas típicas):**
- "Peça para o modelo ser mais cuidadoso/conservador" → continua vago.
- "Adicione um segundo modelo para checar o primeiro" → mais complexo; o problema é o critério.
- "Diminua a temperatura" → ataca o sintoma (e é rejeitada nos modelos novos, Módulo 01).
- "Peça uma nota de confiança e filtre abaixo de X" → confiança autodeclarada é mal calibrada.

**Como cai na prova:** cenário 5 (bot de review de PR com comentários inconsistentes) e cenário 6
(classificação de documentos que varia entre execuções). A resposta é **definir o critério**.

---

## 3. Falso positivo corrói a confiança (task statement 4.1)

**Fato-chave:** uma categoria com muitos falsos positivos **faz os usuários ignorarem também as
categorias boas**. A correção em 3 passos:

1. **Desligue** a categoria ruidosa (pare o dano à confiança);
2. **Refine** o critério dela (o que conta / não conta / fronteira) e teste numa amostra;
3. **Religue** quando a precisão estiver aceitável.

**Por quê:** confiança é do **sistema inteiro**. Se 40% dos comentários de "estilo" são ruído, os
desenvolvedores param de ler os de "segurança", que eram bons. **Meça por categoria**, não no agregado.

**Anti-padrões:**
- Manter tudo ligado e "pedir para o modelo errar menos".
- Desligar o bot inteiro (joga fora as categorias que funcionam).
- Olhar só a precisão média (esconde a categoria ruim).

**Como cai na prova:** cenário 5. Enunciado típico: "desenvolvedores começaram a ignorar os
comentários do bot; a análise mostra que a categoria X tem 60% de falso positivo".

---

## 4. Few-shot (task statement 4.2)

**Fato-chave:** exemplos são a ferramenta mais forte para **casos ambíguos, formato, raciocínio e
casos de borda**. Regras:

- **2–4 exemplos direcionados** (não dezenas);
- cada um com **entrada, saída e o raciocínio** (por que essa saída);
- **variados**: cubra os casos de borda e as fronteiras, não 4 versões do caso fácil;
- devem ensinar o **padrão** (generalizar), não ser decorados;
- delimitados (ex.: `<exemplo>`), para não se confundirem com a entrada real.

**Quando usar:**
- casos ambíguos em que a descrição em prosa não basta;
- demonstrar **formato** de saída e **raciocínio** esperado;
- **reduzir alucinação em extração** (mostrar que campo ausente vira `null`, não invenção);
- casos de borda recorrentes que o modelo erra.

**Por quê:** um exemplo mostra de uma vez o formato, o nível de detalhe e a fronteira, coisa que
parágrafos de instrução não conseguem. O raciocínio no exemplo faz o modelo **generalizar** a regra
em vez de copiar a superfície.

**Anti-padrões:**
- Exemplos todos parecidos (o modelo aprende o caso fácil e erra a borda).
- Exemplos sem raciocínio (o modelo copia formato, não critério).
- Dezenas de exemplos "por garantia" (custo, e o modelo pode se prender à superfície).
- Exemplos que contradizem a instrução.

**Como cai na prova:** cenário 6 (extração de formatos variados: notas manuscritas, tabelas,
campos ausentes) e cenário 1 (respostas do agente fora do formato). A alternativa certa costuma
ser "2–4 exemplos variados com raciocínio cobrindo os casos que falham".

---

## 5. Refinamento iterativo: exemplos concretos e TDD (task statement 3.5)

Quatro técnicas para iterar com o Claude (especialmente no Claude Code). As duas primeiras:

1. **Exemplos concretos de entrada/saída.** Quando a descrição em prosa gera resultado errado,
   **2–3 pares entrada → saída esperada** batem mais parágrafos de explicação.
   Ex.: "converta datas" é vago; `"03/04/25" → "2025-04-03"` e `"Abr 3, 2025" → "2025-04-03"` não.
2. **TDD.** Escreva **testes que falham** que expressem o comportamento desejado, compartilhe as
   falhas com o Claude e **itere até passarem**. O teste é um critério objetivo e verificável: o
   Claude sabe quando acabou.

**Por quê:** ambos transformam um requisito subjetivo em um **alvo verificável**.

**Anti-padrões:**
- Reescrever a mesma instrução em prosa cada vez mais longa.
- Pedir "faça e me diga se ficou bom" sem critério de aceite.

**Como cai na prova:** cenário 2 ("o Claude Code implementou a transformação, mas os casos de
borda continuam errados após 3 tentativas de explicar em texto").

---

## 6. Refinamento iterativo: entrevista e agrupamento de problemas (task statement 3.5)

3. **Entrevista.** Para requisito confuso ou com muitas decisões em aberto, peça ao Claude que
   **faça perguntas de esclarecimento antes de implementar** ("antes de codar, me entreviste sobre
   os casos que você não conseguir decidir"). Isso expõe premissas ocultas cedo.
4. **Problemas relacionados × independentes.**
   - **Relacionados** (que interagem, mesma causa, mesmo código) → **numa mensagem só**: o Claude
     vê a interação e evita corrigir um e quebrar o outro.
   - **Independentes** → **em sequência**, um por vez: cada mudança fica pequena e **revisável**,
     e um erro não contamina o outro.

**Anti-padrões:**
- Despejar 6 bugs não relacionados num prompt só (mudança gigante, difícil de revisar).
- Separar em mensagens dois problemas que tocam a mesma função (correções que se atropelam).
- Implementar direto um requisito ambíguo e descobrir as premissas erradas no fim.

**Como cai na prova:** cenário 2. Enunciados: "a especificação tem várias decisões de negócio em
aberto" (→ entrevista); "três bugs: dois no mesmo parser, um no exportador de CSV" (→ os dois do
parser juntos; o do CSV separado).

---

## 7. A escada de soluções: mais simples primeiro

Quando o problema é de **qualidade/consistência de saída**, a prova premia subir a escada **degrau
por degrau**:

1. Instrução clara + contexto + **critério explícito**;
2. **Exemplos** (few-shot / pares concretos);
3. **Estrutura** (schema, Módulo 03) e **validação em código**;
4. Só então: arquitetura extra (segundo modelo, pipeline, classificador).

E **se a regra é crítica** (dinheiro, segurança, compliance), ela **não fica no prompt**: vai para
código (hook/validação), independente do degrau.

**Como cai na prova:** em quase todo cenário. Alternativas que pulam para o degrau 4 sem tentar o
1–2 são distratoras clássicas.

---

## Tabela de decisão

| Se... | Faça... |
|-------|---------|
| Saída inconsistente entre execuções | Critério explícito: o que conta, o que não conta, fronteira |
| Uma categoria tem muito falso positivo e o time ignora o bot | Desligue a categoria, refine o critério, religue |
| Casos ambíguos/borda erram, prosa não resolve | 2–4 exemplos variados com raciocínio |
| Extração inventa campo ausente | Few-shot mostrando `null` + campo nullable no schema |
| Explicações em texto não acertam a transformação | 2–3 pares entrada/saída concretos |
| Precisa de critério de "pronto" verificável | TDD: testes que falham → iterar até passar |
| Requisito confuso, decisões em aberto | Entrevista: Claude pergunta antes de implementar |
| Problemas que interagem | Uma mensagem só |
| Problemas independentes | Em sequência, revisáveis |
| Documento do usuário no prompt | Dentro de tags XML, separado das instruções |
| Julgamento complexo | Pedir evidência/raciocínio antes do veredito |
| Regra crítica | Código (hook/validação), não prompt |

## Glossário

- **Critério explícito** — definição do que conta, do que não conta e dos casos de fronteira.
- **Falso positivo** — sinalizar algo que não deveria; em excesso, corrói a confiança no sistema todo.
- **Few-shot** — exemplos (entrada, saída, raciocínio) no prompt para ensinar um padrão.
- **Caso de fronteira** — exemplo ambíguo que define de que lado da regra ele cai.
- **TDD** — escrever testes que falham antes e iterar até passarem.
- **Entrevista** — o Claude faz perguntas de esclarecimento antes de implementar.
- **Tags XML** — delimitadores (`<documento>`) que separam dados de instruções.

## Cola de véspera

- **Vago ("seja conservador") → inconsistente.** Corrija com **o que conta / o que não conta / fronteira**.
- **Categoria ruidosa → desliga, refina, religa.** Falso positivo corrói a confiança nas boas. Meça **por categoria**.
- **Few-shot: 2–4, variados, com raciocínio,** cobrindo bordas; ensinam padrão, não decoreba.
- **3.5:** pares concretos entrada/saída · **TDD** (testes falhando → iterar) · **entrevista** antes
  de implementar · **relacionados juntos, independentes em sequência**.
- Base: **papel + contexto no system**, **XML separando dados de instruções**, **raciocínio antes do veredito**.
- Escada: **critério → exemplos → schema/validação → arquitetura extra**. Crítico vai para código.
- Distratores: "seja mais cuidadoso", "segundo modelo", "temperatura 0", "filtre por confiança autodeclarada".

## Perguntas de checagem

1. **O bot de review comenta coisas diferentes no mesmo código a cada execução. Primeira correção?**
   Critérios explícitos por categoria: o que conta, o que não conta, exemplos de fronteira.
2. **A categoria "estilo" tem 50% de falso positivo e o time passou a ignorar todo o bot. O que fazer?**
   Desligar "estilo", refinar o critério numa amostra, religar quando a precisão for aceitável.
3. **Quantos exemplos few-shot e com o quê?** 2–4, variados (cobrindo bordas), cada um com entrada, saída e raciocínio.
4. **Dois bugs no mesmo parser e um no exportador. Como pedir ao Claude?** Os dois do parser numa
   mensagem (interagem); o do exportador em sequência, separado.
5. **Por que colocar o e-mail do cliente dentro de `<email>`?** Para separar dado de instrução: o
   modelo não confunde o conteúdo com ordens e você pode referenciá-lo com precisão.
