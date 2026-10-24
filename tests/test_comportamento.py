"""v0dtb: projeção comportamental local, longitudinal e explicável."""
import json

from hub.comportamento import DIA_MS, analisar_comportamento
from tools.estudo_comportamental import executar


def _estado(seq, t, ocupacao):
    return {"id": f"e-{seq}", "seq": seq, "t_ms": t, "camada": "ESTADO", "tipo": "ESTADO_SALA",
            "ocupacao": ocupacao, "luz": "APAGADA", "precedencia": "AUTOMATICA", "alertas": []}


def _trinta_dias():
    eventos, seq = [], 1
    for dia in range(30):
        eventos.append(_estado(seq, dia * DIA_MS, "VAZIA")); seq += 1
        eventos.append(_estado(seq, dia * DIA_MS + 8 * 3_600_000, "OCUPADA")); seq += 1
        eventos.append(_estado(seq, dia * DIA_MS + 18 * 3_600_000, "VAZIA")); seq += 1
    return eventos


def test_perfil_maduro_em_30_dias_e_retencao_fixa():
    r = analisar_comportamento(_trinta_dias(), 30 * DIA_MS)
    assert r["retencao_dias"] == 30
    assert r["local_processamento"] == "HUB"
    assert r["resumo"]["maduro"]
    oito = next(x for x in r["perfil_horario"] if x["tipo_dia"] == "DIA_UTIL" and x["hora"] == 8)
    assert oito["probabilidade_ocupacao"] == 1.0


def test_nao_identifica_pessoa_ou_cachorro_e_nao_usa_verdade():
    eventos = _trinta_dias() + [
        {"id": "verdade", "seq": 999, "t_ms": 0, "camada": "VERDADE", "tipo": "OCUPANTES",
         "presentes": ["morador", "rex"]},
        {"id": "plataforma", "seq": 1000, "t_ms": 0, "camada": "PLATAFORMA", "tipo": "ESTADO_REMOTO"},
    ]
    r = analisar_comportamento(eventos, 30 * DIA_MS)
    texto = json.dumps(r).lower()
    assert not r["identifica_ocupante"]
    assert "morador" not in texto and "rex" not in texto and "verdade" not in texto and "plataforma" not in texto


def test_replay_duplicado_e_fora_de_ordem_e_idempotente():
    eventos = _trinta_dias()
    a = analisar_comportamento(eventos, 30 * DIA_MS)
    b = analisar_comportamento(list(reversed(eventos)) + eventos[:12], 30 * DIA_MS)
    assert a == b


def test_sugestao_nunca_e_aplicada_automaticamente():
    r = analisar_comportamento(_trinta_dias(), 30 * DIA_MS, 60_000)
    assert r["sugestao"]["estado"] in {"PROPOSTA", "MANTER"}
    assert r["sugestao"]["aplicacao_automatica"] is False


def test_janela_curta_abstem_de_sugerir():
    r = analisar_comportamento(_trinta_dias()[:9], 3 * DIA_MS)
    assert r["sugestao"]["estado"] == "SEM_EVIDENCIA_SUFICIENTE"
    assert r["sugestao"]["aplicacao_automatica"] is False


def test_estudo_publicacao_tem_cenarios_sementes_e_metadados():
    linhas = executar(sementes=2, dias=30)
    assert len(linhas) == 8
    assert {x["cenario"] for x in linhas} == {"ROTINA_REGULAR", "MUDANCA_ROTINA", "RETORNOS_CURTOS", "COBERTURA_BAIXA"}
    assert all(x["algoritmo"] == "episodios-hub-v1" for x in linhas)
    assert all(x["dias"] == 30 for x in linhas)
