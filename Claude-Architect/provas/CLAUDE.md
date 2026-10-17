# Claude-Architect/provas — Provas de fim de módulo

Uma prova por módulo, com **20 questões em estilo de cenário** (como o exame) e **feedback por
alternativa** (`feedbacks`). Aprovação: **70%**.

```bash
python3 engine/session.py start Claude-Architect/provas/modulo-NN/questions.json --id prova
python3 engine/session.py answer C --id prova
python3 engine/session.py answer A,D --id prova        # múltipla resposta ("Choose TWO")
python3 Claude-Architect/provas/modulo-NN/prova.py     # modo solo
```

Convenção: `feedbacks` em todas as alternativas, dizendo por que cada errada é tentadora (qual
anti-padrão ela representa). Cerca de 15% das questões são de múltipla resposta.
