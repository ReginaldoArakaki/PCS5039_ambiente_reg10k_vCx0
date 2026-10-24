# Requisitos do incremento v0dtb

## Requisitos funcionais

| ID | Requisito | Verificação |
|---|---|---|
| RF-COMPT-01 | O Hub deve derivar episódios de ocupação exclusivamente de registros locais | Teste e inspeção |
| RF-COMPT-02 | Cada episódio deve registrar início, fim, estado, confiança, evidências e versão do algoritmo | Teste de contrato |
| RF-COMPT-03 | O Hub deve produzir perfil por faixa horária e tipo de dia, com cobertura e dias observados | Teste longitudinal |
| RF-COMPT-04 | O perfil deve se abster de afirmar maturidade antes de 21 dias ou com cobertura inferior a 80% | Teste de limiar |
| RF-COMPT-05 | O Hub pode produzir sugestão explicável de `T_apagamento` por avaliação contrafactual | Teste determinístico |
| RF-COMPT-06 | A sugestão não pode alterar a configuração sem aceite posterior explícito | Inspeção e regressão |
| RF-COMPT-07 | O estudo deve exportar métricas em JSON e CSV adequadas à análise estatística | Teste de artefato |
| RF-COMPT-08 | A projeção deve ser reconstruível após duplicação e reordenação do mesmo conjunto de registros | Teste metamórfico |

## Requisitos não funcionais

| ID | Requisito | Meta |
|---|---|---|
| RNF-COMPT-01 | Explicabilidade | Todo episódio e sugestão identifica método e evidências |
| RNF-COMPT-02 | Minimização | Nenhuma identidade, posição ou distinção pessoa/animal no perfil |
| RNF-COMPT-03 | Isolamento | Nenhum evento `VERDADE`, `REDE` ou `PLATAFORMA` participa da derivação |
| RNF-COMPT-04 | Retenção experimental | 30 dias para registro e projeção comportamental |
| RNF-COMPT-05 | Determinismo | Mesmo conjunto de registros produz saída idêntica |
| RNF-COMPT-06 | Compatibilidade | Decisões e atuações da v0dta permanecem inalteradas |

## Invariantes

- **INV-COMPT-01:** `local_processamento = HUB`.
- **INV-COMPT-02:** `identifica_ocupante = false`.
- **INV-COMPT-03:** `retencao_dias = 30`.
- **INV-COMPT-04:** sugestão com estado `PROPOSTA` implica `requer_aceite = true` e `aplicacao_automatica = false`.
- **INV-COMPT-05:** perfil maduro implica `dias_no_periodo >= 21` e `cobertura >= 0,8`.
- **INV-COMPT-06:** replay, duplicação e reordenação não mudam episódios, perfil ou sugestão.

## Dados para publicação

Os resultados são de simulação e devem ser publicados como métricas experimentais, nunca como medição de residências reais. Cada linha deve identificar cenário, semente, janela, algoritmo e parâmetros. A verdade sintética pode ser usada separadamente pelo oráculo para calcular desempenho, mas não integra o perfil gerado pelo Hub.
