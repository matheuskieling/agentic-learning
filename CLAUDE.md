# Courses — Plataforma de Cursos

Este repositório é uma **plataforma pessoal de cursos** na área de programação, criada para o
aprendizado do dono do repositório. Cada curso vive em seu próprio diretório na raiz e é
construído de forma incremental, misturando **teoria** e **prática guiada**.

O papel do Claude aqui não é só gerar conteúdo estático: é atuar como **instrutor**. Isso
significa explicar conceitos, propor exercícios, guiar passo a passo execuções reais (ex.:
comandos na AWS, código, configurações) e verificar o entendimento antes de avançar.

## Estrutura

```
courses/
├── CLAUDE.md          ← este arquivo (visão geral da plataforma)
├── AWS/               ← Curso 1: AWS & Cloud (mega intensivo)
│   └── CLAUDE.md      ← contexto e plano do curso de AWS
└── <futuros cursos>/  ← cada curso novo ganha seu próprio diretório + CLAUDE.md
```

**Convenção importante:** todo diretório dentro da raiz tem seu próprio `CLAUDE.md`
descrevendo o que ele contém, o objetivo e como o conteúdo está organizado. O `CLAUDE.md`
de cada diretório é a fonte de verdade sobre aquele escopo — leia-o antes de trabalhar ali.

## Filosofia dos cursos

- **Da base ao avançado.** Começamos pelos fundamentos e subimos até dar plena autonomia.
- **Teoria + prática.** Textos teóricos para entender o "porquê", seguidos de exercícios
  práticos reais para fixar o "como".
- **Aprender fazendo.** Sempre que possível, o aluno executa de verdade (na AWS, no terminal,
  no código) com o Claude guiando cada etapa.
- **Incremental.** O conteúdo cresce conforme avançamos. Nada precisa estar completo de início.

## Como os cursos funcionam — formato padrão (vale para TODOS os cursos)

Este é o formato-padrão da plataforma. **Todo curso novo replica esta estrutura.** A ideia central:
o curso é um **one-on-one com o Claude**, não uma leitura solitária. O Claude conduz a aula ao vivo,
explica um ponto por vez, convida dúvidas, pergunta **"posso continuar?"** e **salva onde paramos**
para retomar depois. Os arquivos `.md` continuam existindo para quem quiser estudar sozinho.

### Estrutura padrão de um curso

```
courses/
├── engine/               ← MOTOR COMPARTILHADO por todos os cursos (Python puro, sem dependências)
│   ├── aula.py           ← driver da AULA ao vivo (lê roteiro.json, salva progresso)
│   ├── session.py        ← driver de QUIZ/PROVA (lê questions.json)
│   ├── revisar.py        ← revisão acumulada com repetição espaçada (estilo Anki)
│   ├── quiz_engine.py    ← motor do quiz no modo solo (teclado)
│   ├── reset.py          ← zera o progresso de um curso
│   └── _common.py        ← resolução de curso/sessão (autodetecção + --curso)
│
└── <Curso>/              ← cada curso é SÓ CONTEÚDO (nenhum driver aqui)
    ├── CLAUDE.md         ← plano do curso + anatomia dos módulos (fonte de verdade)
    ├── README.md         ← como fazer o curso (para o aluno)
    ├── .sessions/        ← progresso do aluno (commitado no fork/branch; zerado na main)
    ├── NN-nome/          ← um diretório por módulo, numerado
    │   ├── roteiro.json  ← ESPINHA da aula ao vivo: "beats" ordenados que o Claude conduz
    │   ├── teoria.md     ← texto teórico (para estudo solo / referência)
    │   └── pratica.md    ← passo a passo da prática guiada
    ├── apps/modulo-NN/   ← questions.json (banco do quiz) + quiz.py (runner solo)
    ├── provas/modulo-NN/ ← prova de fim de módulo (feedback por alternativa)
    └── (extras do curso) ← ex.: AWS tem certificacoes/; outros cursos terão o que fizer sentido
```

Os **drivers vivem só em `engine/`** e são **agnósticos de curso** — descobrem o curso pelo caminho
do conteúdo ou por `--curso <dir>`/autodetecção. Um **curso novo é só conteúdo** (roteiros + bancos):
não se copia nem se recria driver nenhum. Passo a passo técnico de "como criar um curso" em
`engine/CLAUDE.md`; o guia voltado ao aluno (o que pedir ao agente) está em `README.md` na seção
"Criar seus próprios cursos". Ao montar um curso novo, **antes de escrever os módulos**: (a) proponha
o **currículo** para o aluno aprovar; e (b) se o tema for **agnóstico de linguagem** (design patterns,
algoritmos, arquitetura, SOLID...), **avise o aluno** que o curso vai deixá-lo **escolher a linguagem
dos exemplos ao estudar** e **pergunte em qual linguagem-base** escrever os exemplos nos arquivos
(sugira a preferência conhecida do aluno como padrão). Ver a convenção completa em "Cursos que
dependem de linguagem" abaixo.

### Os dois modos de cada módulo

1. **Aula ao vivo (padrão):** o Claude roda `engine/aula.py`, que guarda o **roteiro** (o que ensinar)
   e o **progresso** (onde paramos). O Claude narra cada beat com as próprias palavras, tira dúvidas,
   e só avança (`aula.py next`) quando o aluno confirma. Ao chegar em beats de quiz/prova, dispara o
   `session.py`. O estado persiste → dá para **parar e retomar sempre de onde ficou**.
2. **Solo:** o aluno lê os `.md` e roda os quizzes pelo teclado (`quiz.py`, `prova.py`).

O **progresso** (`.sessions/`) é **versionado**: cada aluno commita o próprio progresso no seu
**fork** (ou numa branch própria, ex.: `progresso/<nome>`) e continua **de qualquer máquina** com um
`git pull`. A branch `main` do repositório principal fica sempre com **progresso zerado** — nunca
commitar arquivos de `.sessions/` nela. Para recomeçar, `python3 engine/reset.py` (+ commit).

### Anatomia de um módulo (ciclo aprender → praticar → testar → avaliar)

`roteiro.json` (espinha da aula) · `teoria.md` (o porquê) · `pratica.md` (fazer de verdade) ·
**quiz** da aula (fixar) · **prova** do módulo (avaliar, 70%) · extras de certificação quando houver.
Cada curso detalha isso no seu próprio `CLAUDE.md` (ver `AWS/CLAUDE.md` como referência viva).

### Cursos que dependem de linguagem — preferência salva (convenção da plataforma)

Alguns cursos ensinam algo **agnóstico de linguagem** (design, algoritmos, padrões), mas precisam de
uma linguagem só para os **exemplos** — e essa escolha é **gosto do aluno**, não característica do
curso. Regra da plataforma para esses cursos:

- **Declara-se** no `CLAUDE.md` do curso que ele é *dependente de linguagem* (com a linguagem de
  **referência-base** em que os arquivos estão escritos).
- No **início** (beat `intro` do 1º módulo), o agente **pergunta a linguagem preferida** e salva em
  `<Curso>/.sessions/preferencias.json` → `{ "linguagem": "<nome>" }`. É versionado como o resto do
  progresso (viaja no fork/branch; some no `reset`).
- Em **toda retomada**, o agente **lê** esse arquivo e **conduz os exemplos na linguagem salva**
  (traduzindo ao vivo a partir da referência-base). Se o aluno pedir pra trocar, reescreve o arquivo.
- Os arquivos de conteúdo (`teoria.md`, `pratica.md`, `questions.json`) ficam numa **única
  linguagem-base** — a adaptação é **ao vivo**, na fala do agente; quem estuda solo lê a base.

Cursos **não** dependentes de linguagem (ex.: infra como AWS, ou um curso que é *sobre* uma linguagem
específica) simplesmente não declaram isso e ignoram o mecanismo. Exemplo vivo: `SOLID/CLAUDE.md`.

### Retomar um curso

Para começar/retomar qualquer curso, o aluno usa a skill **`/retomar-curso`**: ela detecta o curso,
dá um breve resumo de onde paramos, oferece uma revisão da última sessão e retoma a aula no ponto
salvo. Para revisão de longo prazo, a skill **`/revisar`** faz uma mini-prova estilo **Anki**
(repetição espaçada) amostrando de todo o conteúdo já concluído. Ambas funcionam em qualquer curso
que siga o formato-padrão. (Definições em `.claude/skills/`.)

Em agentes **sem suporte a skills**, o fluxo é o mesmo feito à mão: `git pull` (se estiver em
fork/branch), `python3 engine/aula.py status` + `current` para resumir onde paramos, e
conduzir a partir do beat atual. Os detalhes estão no `CLAUDE.md` de cada curso.

## Compatibilidade com outros agentes (harness-agnóstico)

Este repositório **não depende do Claude**: qualquer agente de código (Codex, Cursor, Gemini CLI,
Copilot, etc.) consegue conduzir os cursos, porque os drivers são Python puro e as instruções são
arquivos Markdown. Convenções:

- Os **`CLAUDE.md` são a fonte de verdade** das instruções (nome histórico do projeto).
- `AGENTS.md` (raiz e por curso), `GEMINI.md` e `.github/copilot-instructions.md` são **ponteiros**
  que direcionam outros harnesses para o `CLAUDE.md` correspondente — mantenha-os como ponteiros;
  qualquer mudança de convenção vai no `CLAUDE.md`.
- Os comandos (`/retomar-curso`, `/revisar`) têm **uma lógica só** em
  `.claude/skills/<comando>/SKILL.md` e ponteiros no formato de cada harness: `.gemini/commands/`,
  `.cursor/commands/`, `.github/prompts/`. Harnesses sem comando por repo (ex.: Codex) caem no
  fallback do `AGENTS.md` via linguagem natural. Ao alterar uma skill, os ponteiros continuam
  válidos (só referenciam o SKILL.md); ao criar um comando novo, replique os ponteiros nos 3 formatos.

## Cursos

| # | Curso | Diretório | Status |
|---|-------|-----------|--------|
| 1 | AWS & Cloud (mega intensivo) | `AWS/` | ✅ Completo — 19 módulos + simulados CLF-C02/SAA-C03 |
| 2 | SOLID (design OO, exemplos em C#) | `SOLID/` | ✅ Completo — 7 módulos (fundamentos + 5 princípios + capstone) |
| 3 | Entrevista Angular + .NET (intensivo) | `Entrevista-Angular-DotNet/` | ✅ Completo — 7 módulos (3 Angular + 4 .NET) + simulado geral |
| 4 | Claude Certified Architect (preparação CCAR-F, foco em prova) | `Claude-Architect/` | ✅ Completo — 11 módulos + 6 bancos por cenário + 5 simulados (alinhado ao guia oficial v1.0) |
