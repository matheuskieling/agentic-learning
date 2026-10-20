# Claude-Architect/apps — Quizzes de aula

Só **conteúdo**: os drivers vivem em `engine/` (ver `engine/CLAUDE.md`).

```
apps/modulo-NN/
├── questions.json   ← 15 questões curtas para fixar o módulo (formato em engine/CLAUDE.md)
└── quiz.py          ← runner solo: python3 Claude-Architect/apps/modulo-NN/quiz.py
```

Conduzido pelo Claude: `python3 engine/session.py start Claude-Architect/apps/modulo-NN/questions.json`.
Questões de fixação do conteúdo da aula (podem ser conceituais), em **inglês** como a prova real (a aula segue em PT-BR), com `feedbacks` em todas as alternativas e o campo `ts` (task statement do guia). O formato completo do exame fica nas provas e nos simulados.
