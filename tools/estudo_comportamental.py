"""Gera um conjunto reprodutível de métricas v0dtb para análise/publicação.

Os roteiros são sintéticos e produzem somente registros equivalentes aos do
Hub. A verdade usada para construir a experiência não é entregue ao analisador.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

from hub.comportamento import DIA_MS, analisar_comportamento


def _estado(seq: int, t: int, ocupacao: str) -> dict:
    return {"id": f"est-{seq:07d}", "seq": seq, "t_ms": t, "camada": "ESTADO", "tipo": "ESTADO_SALA",
            "ocupacao": ocupacao, "luz": "APAGADA", "precedencia": "AUTOMATICA", "alertas": []}


def gerar_log(cenario: str, semente: int, dias: int = 30) -> list[dict]:
    rng = random.Random(semente)
    eventos, seq = [], 1
    for dia in range(dias):
        base = dia * DIA_MS
        eventos.append(_estado(seq, base, "VAZIA")); seq += 1
        if cenario == "COBERTURA_BAIXA" and dia % 3:
            eventos.append(_estado(seq, base + 7 * 3_600_000, "DESCONHECIDA")); seq += 1
            continue
        fim_semana = dia % 7 in (5, 6)
        entrada_h = 10 if fim_semana else 8
        saida_h = 20 if fim_semana else 18
        if cenario == "MUDANCA_ROTINA" and dia >= 20:
            entrada_h, saida_h = 12, 22
        jitter = rng.randint(-20, 20) * 60_000
        eventos.append(_estado(seq, base + entrada_h * 3_600_000 + jitter, "OCUPADA")); seq += 1
        eventos.append(_estado(seq, base + saida_h * 3_600_000 + jitter, "VAZIA")); seq += 1
        if cenario == "RETORNOS_CURTOS":
            t = base + 14 * 3_600_000
            eventos.append(_estado(seq, t, "VAZIA")); seq += 1
            eventos.append(_estado(seq, t + 45_000, "OCUPADA")); seq += 1
    return eventos


def executar(sementes: int = 30, dias: int = 30) -> list[dict]:
    linhas = []
    for cenario in ("ROTINA_REGULAR", "MUDANCA_ROTINA", "RETORNOS_CURTOS", "COBERTURA_BAIXA"):
        for semente in range(1, sementes + 1):
            r = analisar_comportamento(gerar_log(cenario, semente, dias), dias * DIA_MS)
            m, sug = r["metricas"], r["sugestao"]
            linhas.append({
                "cenario": cenario, "semente": semente, "dias": dias,
                "algoritmo": "episodios-hub-v1", "metodo_sugestao": sug.get("metodo"),
                **m, "sugestao_estado": sug["estado"],
                "t_atual_ms": sug["valor_atual"], "t_proposto_ms": sug.get("valor_proposto"),
                "beneficio_estimado_ms": sug.get("beneficio_estimado_ms"),
            })
    return linhas


def salvar(saida: Path, sementes: int = 30, dias: int = 30) -> list[dict]:
    linhas = executar(sementes, dias)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "metricas.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=2), encoding="utf-8")
    with (saida / "metricas.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader(); w.writerows(linhas)
    manifesto = {"versao": "v0dtb", "natureza": "SIMULACAO_SINTETICA", "dias": dias,
                 "sementes_por_cenario": sementes, "cenarios": 4, "execucoes": len(linhas),
                 "retencao_dias": 30, "processamento": "HUB"}
    (saida / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return linhas


def main() -> None:
    p = argparse.ArgumentParser(description="Gera métricas longitudinais sintéticas da v0dtb")
    p.add_argument("--sementes", type=int, default=30)
    p.add_argument("--dias", type=int, default=30)
    p.add_argument("--saida", type=Path, default=Path("saida/estudo-comportamental"))
    a = p.parse_args()
    linhas = salvar(a.saida, a.sementes, a.dias)
    print(f"{len(linhas)} execuções gravadas em {a.saida}")


if __name__ == "__main__":
    main()
