# MaterSphere Silver

MVP demonstrativo para priorizar contatos de agendamento quando uma pessoa idosa pode encontrar barreiras para comparecer à consulta. A aplicação usa somente pacientes e mensagens sintéticas.

## O que funciona

- análise local de mensagens em português com vocabulário explícito;
- score explicado pelos pesos da apresentação: 35 + 30 + 20 + 10 + 5;
- classificação baixo, médio ou alto risco e recomendação operacional;
- fila da sessão e exportação CSV;
- controles de contraste e tamanho de texto;

## Como executar

No PowerShell, com o ambiente virtual do projeto ativado:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Abra `http://localhost:8501` no navegador.

## Limites

O score é uma escala demonstrativa de priorização operacional. Ele não é diagnóstico, não estima probabilidade clínica e não faz contato automático. Um piloto real exigiria governança de dados, validação institucional e revisão humana.
