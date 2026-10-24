"""v0dtb: projeção comportamental explicável, calculada somente no hub.

O módulo recebe o registro local e deriva episódios e perfis sem consultar a
camada VERDADE, a plataforma, identidades ou posições.  Ele é deliberadamente
determinístico: os mesmos fatos locais produzem a mesma projeção, mesmo quando
o registro é reapresentado fora de ordem ou com duplicatas.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

CAMADAS_LOCAIS = {"PERCEPCAO", "DECISAO", "ATUACAO", "ESTADO", "SISTEMA"}
ESTADOS_OCUPACAO = {"OCUPADA", "VAZIA", "DESCONHECIDA"}
RETENCAO_DIAS = 30
JANELA_MINIMA_DIAS = 21
FAIXA_MS = 60 * 60 * 1000
DIA_MS = 24 * FAIXA_MS
CANDIDATOS_APAGAMENTO_MS = (30_000, 60_000, 90_000, 120_000, 180_000)


def _eventos_locais(eventos: Iterable[dict]) -> list[dict]:
    """Ordena e deduplica o log, descartando tudo que não pertence ao hub."""
    unicos: dict[str, dict] = {}
    for e in eventos:
        if e.get("camada") not in CAMADAS_LOCAIS:
            continue
        chave = str(e.get("id") or f"{e.get('seq')}:{e.get('t_ms')}:{e.get('tipo')}")
        unicos.setdefault(chave, e)
    return sorted(unicos.values(), key=lambda e: (int(e.get("t_ms", 0)), int(e.get("seq", 0)), str(e.get("id", ""))))


def _intervalos_ocupacao(eventos: list[dict], fim_ms: int) -> list[dict]:
    mudancas = [(0, "DESCONHECIDA")]
    for e in eventos:
        if e.get("camada") == "ESTADO" and e.get("tipo") == "ESTADO_SALA" and e.get("ocupacao") in ESTADOS_OCUPACAO:
            par = (int(e["t_ms"]), e["ocupacao"])
            if par[0] == mudancas[-1][0]:
                mudancas[-1] = par
            elif par[1] != mudancas[-1][1]:
                mudancas.append(par)
    saida = []
    for i, (inicio, estado) in enumerate(mudancas):
        fim = mudancas[i + 1][0] if i + 1 < len(mudancas) else fim_ms
        if fim > inicio:
            saida.append({"inicio_ms": inicio, "fim_ms": min(fim, fim_ms), "estado": estado})
    return saida


def _episodios(intervalos: list[dict], eventos: list[dict]) -> list[dict]:
    episodios = []
    estados = [e for e in eventos if e.get("camada") == "ESTADO" and e.get("tipo") == "ESTADO_SALA"]
    for n, it in enumerate(intervalos, 1):
        if it["estado"] == "VAZIA":
            continue
        suporte = [e["id"] for e in estados if it["inicio_ms"] <= int(e["t_ms"]) <= it["fim_ms"]][:8]
        dur = it["fim_ms"] - it["inicio_ms"]
        episodios.append({
            "id": f"EO-{n:05d}",
            "inicio_ms": it["inicio_ms"],
            "fim_ms": it["fim_ms"],
            "duracao_ms": dur,
            "estado": "OCUPADO" if it["estado"] == "OCUPADA" else "INCONCLUSIVO",
            "confianca": 1.0 if it["estado"] == "OCUPADA" else 0.0,
            "evidencias": suporte,
            "algoritmo": "episodios-hub-v1",
        })
    return episodios


def _perfil(intervalos: list[dict], fim_ms: int) -> tuple[list[dict], dict]:
    soma = defaultdict(lambda: {"ocupado_ms": 0, "observavel_ms": 0, "dias": set()})
    for it in intervalos:
        cursor = it["inicio_ms"]
        while cursor < it["fim_ms"]:
            dia = cursor // DIA_MS
            hora = (cursor % DIA_MS) // FAIXA_MS
            limite = min(it["fim_ms"], (dia * DIA_MS) + ((hora + 1) * FAIXA_MS))
            chave = ("FIM_DE_SEMANA" if dia % 7 in (5, 6) else "DIA_UTIL", int(hora))
            if it["estado"] != "DESCONHECIDA":
                soma[chave]["observavel_ms"] += limite - cursor
                soma[chave]["dias"].add(int(dia))
                if it["estado"] == "OCUPADA":
                    soma[chave]["ocupado_ms"] += limite - cursor
            cursor = limite
    dias_totais = max(1, (fim_ms + DIA_MS - 1) // DIA_MS)
    perfil = []
    obs_total = 0
    for (tipo_dia, hora), d in sorted(soma.items()):
        obs = d["observavel_ms"]
        obs_total += obs
        cobertura = obs / (len(d["dias"]) * FAIXA_MS) if d["dias"] else 0
        prob = d["ocupado_ms"] / obs if obs else None
        confianca = min(1.0, len(d["dias"]) / JANELA_MINIMA_DIAS) * cobertura
        perfil.append({
            "tipo_dia": tipo_dia,
            "hora": hora,
            "probabilidade_ocupacao": None if prob is None else round(prob, 4),
            "cobertura": round(cobertura, 4),
            "dias_observados": len(d["dias"]),
            "confianca": round(confianca, 4),
        })
    cobertura_global = obs_total / fim_ms if fim_ms else 0
    resumo = {
        "dias_no_periodo": int(dias_totais),
        "cobertura": round(cobertura_global, 4),
        "janela_minima_dias": JANELA_MINIMA_DIAS,
        "maduro": dias_totais >= JANELA_MINIMA_DIAS and cobertura_global >= 0.8,
    }
    return perfil, resumo


def _sugestao(intervalos: list[dict], atual_ms: int, resumo: dict) -> dict:
    vazios = [x["fim_ms"] - x["inicio_ms"] for x in intervalos if x["estado"] == "VAZIA"]
    if not resumo["maduro"] or not vazios:
        return {
            "estado": "SEM_EVIDENCIA_SUFICIENTE",
            "parametro": "t_apagamento_ms",
            "valor_atual": atual_ms,
            "motivo": "exige ao menos 21 dias e cobertura observável de 80%",
            "aplicacao_automatica": False,
        }
    avaliacoes = []
    for c in CANDIDATOS_APAGAMENTO_MS:
        desperdicio = sum(min(g, c) for g in vazios)
        retornos_antes = sum(1 for g in vazios if g < c)
        # Penaliza fortemente desligamentos em ausências curtas; mantém a regra auditável.
        custo = desperdicio + retornos_antes * 5 * 60_000
        avaliacoes.append({"valor_ms": c, "desperdicio_estimado_ms": desperdicio,
                           "retornos_antes_do_limite": retornos_antes, "custo": custo})
    melhor = min(avaliacoes, key=lambda x: (x["custo"], abs(x["valor_ms"] - atual_ms)))
    estado = "PROPOSTA" if melhor["valor_ms"] != atual_ms else "MANTER"
    return {
        "estado": estado,
        "parametro": "t_apagamento_ms",
        "valor_atual": atual_ms,
        "valor_proposto": melhor["valor_ms"],
        "beneficio_estimado_ms": max(0, sum(min(g, atual_ms) for g in vazios) - melhor["desperdicio_estimado_ms"]),
        "retornos_antes_do_limite": melhor["retornos_antes_do_limite"],
        "metodo": "contrafactual-deterministico-v1",
        "aplicacao_automatica": False,
        "requer_aceite": estado == "PROPOSTA",
    }


def analisar_comportamento(eventos: Iterable[dict], fim_ms: int, t_apagamento_ms: int = 60_000) -> dict:
    """Produz a projeção v0dtb e métricas adequadas a estudos estatísticos."""
    locais = _eventos_locais(eventos)
    intervalos = _intervalos_ocupacao(locais, int(fim_ms))
    episodios = _episodios(intervalos, locais)
    perfil, resumo = _perfil(intervalos, int(fim_ms))
    sugestao = _sugestao(intervalos, int(t_apagamento_ms), resumo)
    inconclusivo = sum(x["fim_ms"] - x["inicio_ms"] for x in intervalos if x["estado"] == "DESCONHECIDA")
    return {
        "versao": "v0dtb",
        "local_processamento": "HUB",
        "semantica_ocupacao": "PESSOA_OU_ANIMAL_GRANDE_PORTE",
        "identifica_ocupante": False,
        "retencao_dias": RETENCAO_DIAS,
        "eventos_locais_considerados": len(locais),
        "intervalos": intervalos,
        "episodios": episodios,
        "perfil_horario": perfil,
        "resumo": resumo,
        "sugestao": sugestao,
        "metricas": {
            "cobertura_comportamental_pct": round(100 * resumo["cobertura"], 2),
            "tempo_inconclusivo_s": round(inconclusivo / 1000, 1),
            "episodios_ocupacao": sum(1 for e in episodios if e["estado"] == "OCUPADO"),
            "episodios_inconclusivos": sum(1 for e in episodios if e["estado"] == "INCONCLUSIVO"),
            "perfil_maduro": resumo["maduro"],
        },
    }
