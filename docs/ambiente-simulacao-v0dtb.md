# Ambiente de simulação v0dtb Observação comportamental explicável

## Objetivo

A v0dtb é um exercício didático e estatístico para estudar a viabilidade de incorporar inteligência digital futura ao processo Reg10k. O estudo não se limita à iluminação: episódios e perfis são uma base experimental para conveniências preditivas futuras aos moradores.

## Premissas aprovadas

- A ocupação representa pessoa ou animal de grande porte, sem identificação individual ou de espécie.
- O comportamento de espera associado a `T_apagamento` é intencional e pertence à decisão do controlador.
- O processamento comportamental ocorre somente no Hub; plataforma e verdade simulada não participam da derivação.
- O estudo presume consentimento prévio dos moradores; a modelagem do fluxo de consentimento fica fora desta versão.
- Registros e projeções comportamentais têm retenção de 30 dias para o estudo estatístico.
- O sistema pode sugerir configuração, mas não a aplica automaticamente.

## Capacidades

1. Deduplicar e ordenar o log local.
2. Derivar intervalos e episódios de ocupação, incluindo intervalos inconclusivos.
3. Produzir perfil por hora e tipo de dia com cobertura e confiança.
4. Abster-se quando houver menos de 21 dias ou menos de 80% de cobertura.
5. Avaliar candidatos de `T_apagamento` por método contrafactual determinístico.
6. Registrar proposta, benefício estimado e necessidade de aceite.

## Fronteira de confiança

O módulo `hub/comportamento.py` aceita somente as camadas locais `PERCEPCAO`, `DECISAO`, `ATUACAO`, `ESTADO` e `SISTEMA`. Eventos `VERDADE`, `REDE` e `PLATAFORMA` são descartados. A verdade continua disponível apenas ao oráculo de pesquisa para avaliação externa.

## Saídas

Cada execução grava `comportamento.json` ao lado de `eventos.jsonl` e `metricas.json`, contendo intervalos, episódios, perfil horário, sugestão e métricas de cobertura. As projeções identificam a versão do algoritmo e podem ser reconstruídas a partir do log local durante a retenção.

## Métricas iniciais

- cobertura comportamental percentual;
- tempo inconclusivo;
- número de episódios ocupados;
- número de episódios inconclusivos;
- maturidade do perfil;
- benefício estimado da sugestão, sem aplicação automática.

## Limites desta versão

- Não distingue morador e cachorro.
- Não usa aprendizado de máquina.
- Não produz diagnóstico clínico, de segurança ou identificação de rotina individual.
- Não aplica automaticamente preferências.
- Não transfere o perfil comportamental para a plataforma.
