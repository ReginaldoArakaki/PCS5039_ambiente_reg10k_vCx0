"""Gera um Markdown determinístico com os objetos-fonte da implementação.

Uso:
    python -m tools.consolidar_codigo
"""
from __future__ import annotations

import hashlib
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "codigo-codex-v0dtb.md"

EXTENSOES = {
    ".css": "css",
    ".html": "html",
    ".ini": "ini",
    ".js": "javascript",
    ".json": "json",
    ".md": "markdown",
    ".mmd": "mermaid",
    ".py": "python",
    ".toml": "toml",
    ".txt": "text",
    ".yaml": "yaml",
    ".yml": "yaml",
}

NOMES_EXATOS = {
    ".gitignore": "gitignore",
    "LICENSE": "text",
    "Makefile": "makefile",
}

PASTAS_IGNORADAS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "saida",
    "venv",
}

# site/index.html é derivado de catalogo/template.html e dos dados do catálogo.
ARQUIVOS_IGNORADOS = {
    SAIDA.relative_to(RAIZ).as_posix(),
    "site/index.html",
}


def _incluido(caminho: Path) -> bool:
    relativo = caminho.relative_to(RAIZ).as_posix()
    if relativo in ARQUIVOS_IGNORADOS:
        return False
    if any(parte in PASTAS_IGNORADAS for parte in caminho.relative_to(RAIZ).parts[:-1]):
        return False
    return caminho.name in NOMES_EXATOS or caminho.suffix.lower() in EXTENSOES


def _linguagem(caminho: Path) -> str:
    return NOMES_EXATOS.get(caminho.name, EXTENSOES.get(caminho.suffix.lower(), "text"))


def _cerca(conteudo: str) -> str:
    """Escolhe uma cerca maior que qualquer sequência de crases do arquivo."""
    maior = 0
    atual = 0
    for caractere in conteudo:
        if caractere == "`":
            atual += 1
            maior = max(maior, atual)
        else:
            atual = 0
    return "`" * max(3, maior + 1)


def arquivos() -> list[Path]:
    return sorted((p for p in RAIZ.rglob("*") if p.is_file() and _incluido(p)),
                  key=lambda p: p.relative_to(RAIZ).as_posix().casefold())


def gerar() -> tuple[int, int, str]:
    selecionados = arquivos()
    partes = [
        "# Código consolidado da implementação Reg10k v0dtb\n",
        "Este documento reúne os objetos-fonte usados pela implementação: código, "
        "configurações, esquemas, cenários, testes e documentação.\n",
        "## Critérios de consolidação\n",
        "- Ordem alfabética determinística por caminho relativo.\n",
        "- Leitura e gravação em UTF-8.\n",
        "- Exclusão de `.git/`, ambientes virtuais, caches, `node_modules/` e `saida/`.\n",
        "- Exclusão de `site/index.html`, pois ele é gerado a partir de `catalogo/template.html`.\n",
        "- Exclusão deste próprio consolidado para impedir auto-inclusão.\n",
        f"- Total de arquivos incluídos: **{len(selecionados)}**.\n",
        "\n## Índice de arquivos\n",
    ]
    partes.extend(f"- `{p.relative_to(RAIZ).as_posix()}`\n" for p in selecionados)

    total_bytes = 0
    digest = hashlib.sha256()
    for caminho in selecionados:
        relativo = caminho.relative_to(RAIZ).as_posix()
        dados = caminho.read_bytes()
        total_bytes += len(dados)
        digest.update(relativo.encode("utf-8") + b"\0" + dados + b"\0")
        conteudo = dados.decode("utf-8-sig")
        cerca = _cerca(conteudo)
        partes.extend([
            "\n---\n",
            f"\n## Arquivo: `{relativo}`\n",
            f"\n{cerca}{_linguagem(caminho)}\n",
            conteudo,
            "" if conteudo.endswith("\n") else "\n",
            f"{cerca}\n",
        ])

    texto = "".join(partes)
    SAIDA.write_text(texto, encoding="utf-8", newline="\n")
    return len(selecionados), total_bytes, digest.hexdigest()


def main() -> None:
    quantidade, bytes_fonte, sha = gerar()
    print(f"{SAIDA.name}: {quantidade} arquivos, {bytes_fonte} bytes-fonte, SHA-256 do conjunto {sha}")


if __name__ == "__main__":
    main()
