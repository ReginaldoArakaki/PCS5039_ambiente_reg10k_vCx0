# Resultado de referência do estudo comportamental v0dtb

## Desenho experimental

- Simulação sintética, sem dados de residência real.
- Quatro cenários, 30 sementes por cenário e janela de 30 dias.
- Derivação exclusivamente a partir de registros locais do Hub.
- Ocupação agregada: pessoa ou animal de grande porte, sem identificação.
- Sugestões exigem aceite e nunca são aplicadas automaticamente.

## Resultado da execução de referência

| Cenário | Execuções | Cobertura média | Perfis maduros | Propostas |
|---|---:|---:|---:|---:|
| ROTINA_REGULAR | 30 | 100,00% | 30 | 30 |
| MUDANCA_ROTINA | 30 | 100,00% | 30 | 30 |
| RETORNOS_CURTOS | 30 | 100,00% | 30 | 30 |
| COBERTURA_BAIXA | 30 | 52,78% | 0 | 0 |

O resultado confirma o mecanismo de abstenção: as 30 execuções com baixa cobertura ficaram abaixo do limiar de 80% e não geraram perfil maduro nem proposta. Nas demais 90 execuções houve dados suficientes para gerar proposta explicável. Em nenhuma das 120 execuções houve aplicação automática.

## Reprodução

```console
python -m tools.estudo_comportamental
python -m pytest -q
python -m catalogo.validar
```

Os artefatos detalhados são `saida/estudo-comportamental/metricas.json`, `metricas.csv` e `manifesto.json`. O diretório `saida/` é deliberadamente ignorado pelo Git para evitar versionar produtos regeneráveis.

## Interpretação

Este resultado valida o encadeamento técnico e os controles de qualidade dos dados; não demonstra eficácia em uma residência real. Uma publicação deve identificar os dados como sintéticos e relatar cenários, sementes, parâmetros, versão do algoritmo, cobertura e regras de abstenção.
