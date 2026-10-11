# 🎓 Meu Professor Particular

Plataforma de **cursos de programação guiados por IA**: o agente (Claude Code, Codex, Cursor,
Gemini CLI...) atua como **professor particular** — conduz a aula ao vivo no chat, explica um ponto
por vez, tira dúvidas, aplica quizzes e provas, e **salva onde você parou** pra retomar depois.

| # | Curso | Status |
|---|-------|--------|
| 1 | [AWS & Cloud — mega intensivo](AWS/README.md) | ✅ Completo — 19 módulos + simulados CLF-C02/SAA-C03 |
| 2 | [SOLID — design OO (exemplos em C#)](SOLID/README.md) | ✅ Completo — 7 módulos (fundamentos + 5 princípios + capstone) |
| 3 | [Entrevista Angular + .NET — intensivo](Entrevista-Angular-DotNet/README.md) | ✅ Completo — 7 módulos (3 Angular + 4 .NET) + simulado geral |
| 4 | [Claude Certified Architect — preparação para a prova](Claude-Architect/README.md) | ✅ Completo — 11 módulos + 6 bancos por cenário + 5 simulados |

## 🚀 Começando (5 minutos)

1. **Faça um fork** deste repositório (o repo principal fica com progresso zerado — o seu
   progresso será commitado **no seu fork**, e assim você continua de qualquer máquina).
2. Clone o seu fork e abra seu agente de código na pasta (ex.: `claude` no terminal).
3. Inicie a aula de **um destes dois jeitos** (dão no mesmo):
   - **Skill (Claude Code):** digite **`/retomar-curso`** — atalho que já sincroniza, resume e retoma;
   - **Linguagem natural (qualquer agente):** diga **"vamos começar o curso de AWS"** ou
     **"vamos continuar de onde paramos"**.

## 🧰 Comandos/Skills disponíveis

| Comando | O que faz | Quando usar |
|---------|-----------|-------------|
| **`/retomar-curso`** | Detecta o curso, sincroniza seu progresso (`git pull`), resume onde você parou e **retoma a aula exatamente do ponto salvo**. Ao encerrar, commita seu progresso no fork. | Sempre que for **começar ou continuar** a estudar. É o jeito padrão de entrar no curso. Aceita argumento: `/retomar-curso AWS`. |
| **`/revisar`** | Monta uma **mini-prova estilo Anki** amostrando de tudo que você já concluiu, com **repetição espaçada** (as perguntas voltam de tempos em tempos; erradas reaparecem mais cedo). | Quando quiser **revisar e fixar** o que já aprendeu, a qualquer momento. Aceita argumento: `/revisar AWS`. |
| **`/progresso`** | Mostra a **visão geral do avanço**: barra e **% de cada módulo**, **% do curso completo**, o **último beat concluído** (com data) e o **ritmo** (beats por dia). Só leitura — não altera nada. | Quando quiser saber **quanto já fez, quanto falta** ou acompanhar seu ritmo rumo a uma meta. Aceita argumento: `/progresso AWS`. |

Cada comando existe no formato nativo de cada harness (a lógica é uma só — em
`.claude/skills/<comando>/SKILL.md`):

| Harness | Como acionar |
|---------|--------------|
| **Claude Code** | `/retomar-curso`, `/revisar`, `/progresso` (skills nativas) |
| **Gemini CLI** | idem (comandos em `.gemini/commands/`) |
| **Cursor** | idem (comandos em `.cursor/commands/`) |
| **Copilot (VS Code)** | idem (prompts em `.github/prompts/`) |
| **Codex e outros** | Sem comando por repo — **peça em linguagem natural** ("vamos continuar o curso", "quero revisar"); o `AGENTS.md` instrui o agente a seguir o mesmo fluxo. |

> Em **qualquer** harness, a linguagem natural sempre funciona: "vamos continuar o curso de onde
> paramos" ou "me testa no que já aprendi". Os drivers são Python puro, sem dependências.

## 📚 Como funciona um curso

Cada módulo segue o ciclo **teoria → prática real → quiz → prova** (detalhes no README de cada
curso). Você também pode estudar sozinho pelos arquivos `.md` e rodar os quizzes pelo teclado.
O curso de AWS ainda tem **simulados de certificação fiéis ao exame real** (CLF-C02 e SAA-C03,
65 questões, mesmo tempo e corte) e te avisa **quando você está pronto** pra prova de verdade.

## 🧱 Criar seus próprios cursos (expandir além do oficial)

Esta plataforma **não é só de AWS** — dá pra criar curso de qualquer tema (Design Patterns, Go,
Kubernetes, SQL, o que você quiser). Você **não precisa programar nada**: o motor (`engine/`) e as
skills já funcionam para qualquer curso novo, então **basta pedir ao seu agente**, no **seu fork**,
que ele monta tudo no formato-padrão (roteiro de aula ao vivo + teoria + prática + quiz + prova).

**O que informar ao agente** (quanto mais claro, melhor o curso):
- **Tema e nome** do curso (ex.: "Design Patterns").
- **Público/nível** (iniciante? já programa? quer profundidade?).
- **Tamanho**: quantos módulos, ou "você decide o currículo".
- **Estilo**: mais teórico ou mão-na-massa? tem prática executável (código, terminal)?
- **Avaliação**: quer quiz + prova por módulo? simulados de certificação (se o tema tiver)?
- **Idioma** (do texto/aula; padrão: português).
- **Linguagem dos exemplos** (só p/ temas de código): você **não precisa** decidir — se o tema for
  agnóstico (design patterns, algoritmos, SOLID...), o agente vai te avisar e **perguntar em qual
  linguagem escrever os exemplos**; e, depois de pronto, o curso deixa **você (ou qualquer aluno)
  escolher a linguagem ao estudar**, com a escolha salva pra retomar sempre nela.

**Modelo de pedido** (copie e ajuste):

> "Seguindo o formato-padrão do repositório (veja `CLAUDE.md` e `engine/CLAUDE.md`), crie um curso
> novo de **<tema>** para **<seu nível>**. Proponha primeiro o **currículo de módulos** para eu
> aprovar e, se o tema for agnóstico de linguagem, **me pergunte em qual linguagem escrever os
> exemplos**; depois monte cada módulo com `roteiro.json` + `teoria.md` + `pratica.md` + quiz (10
> questões) e prova (12 questões com feedback por alternativa), na pasta `<Nome-do-Curso>/`. Quando
> terminar, me conduza pelo módulo 1."

O agente cria o curso como **conteúdo puro** (sem copiar nem recriar drivers) — o `engine/` e as
skills `/retomar-curso` / `/revisar` passam a funcionar nele automaticamente. Como é o **seu fork**,
você constrói e estuda sem depender do repo principal; se quiser, depois abre um **PR** para
contribuir o curso de volta. Passo a passo técnico em [`engine/CLAUDE.md`](engine/CLAUDE.md).

## 🔄 Seu progresso

- Fica em `<Curso>/.sessions/` e é **commitado no seu fork** (o agente faz isso por você ao
  fim de cada sessão de estudo).
- Outra máquina? `git pull` no fork e "vamos continuar".
- Recomeçar do zero: `python3 engine/reset.py`.

## 🗂️ Estrutura

```
├── README.md            ← você está aqui
├── CLAUDE.md            ← instruções-mestre para os agentes (fonte de verdade)
├── AGENTS.md            ← ponteiro para agentes de outros harnesses
├── .claude/skills/      ← skills do Claude Code (/retomar-curso, /revisar, /progresso)
├── engine/              ← motor compartilhado por TODOS os cursos (drivers Python)
│   └── CLAUDE.md        ← como o motor funciona + como criar um curso novo
├── AWS/                 ← Curso 1 (só conteúdo; README próprio com o passo a passo)
├── SOLID/               ← Curso 2 (só conteúdo; README próprio com o passo a passo)
├── Entrevista-Angular-DotNet/ ← Curso 3 (intensivo de preparação para entrevista)
└── Claude-Architect/    ← Curso 4 (preparação para a certificação CCAR-F)
```

> Cada curso é um diretório na raiz, só com **conteúdo** (roteiros + bancos). O `engine/` serve
> todos — criar um curso novo **não** duplica nem recria nada do motor.
