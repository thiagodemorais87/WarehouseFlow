"""Validação estática do frontend (CI).

Verifica, sem subir a aplicação:
1. Sintaxe Jinja2 de todos os templates em frontend/templates.
2. Templates referenciados por extends/include/import existem.
3. Arquivos referenciados como /static/... ou url_for('static', path=...) existem.
4. Sintaxe de cada arquivo JS (node --check), se o Node estiver disponível.

Uso:
    python scripts/ci/check_frontend.py [--require-node]
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError, meta

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
TEMPLATES = FRONTEND / "templates"
STATIC = FRONTEND / "static"

STATIC_HREF = re.compile(r"""["'(]/static/([^"'?#)\s]+)""")
STATIC_URL_FOR = re.compile(
    r"""url_for\(\s*['"]static['"]\s*,\s*path\s*=\s*['"]([^'"]+)['"]"""
)


def check_templates(errors: list[str]) -> int:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    files = sorted(TEMPLATES.rglob("*.html"))
    for path in files:
        rel = path.relative_to(TEMPLATES).as_posix()
        source = path.read_text(encoding="utf-8")
        try:
            ast = env.parse(source, name=rel)
        except TemplateSyntaxError as exc:
            errors.append(f"[jinja] {rel}:{exc.lineno}: {exc.message}")
            continue
        for ref in meta.find_referenced_templates(ast):
            if ref and not (TEMPLATES / ref).is_file():
                errors.append(f"[jinja] {rel}: template referenciado não existe: {ref}")
    return len(files)


def check_static_refs(errors: list[str]) -> int:
    count = 0
    sources = sorted(TEMPLATES.rglob("*.html")) + sorted(STATIC.rglob("*.css"))
    for path in sources:
        text = path.read_text(encoding="utf-8")
        refs = STATIC_HREF.findall(text) + STATIC_URL_FOR.findall(text)
        for ref in refs:
            if "{{" in ref or "{%" in ref:
                continue
            count += 1
            if not (STATIC / ref).is_file():
                rel = path.relative_to(ROOT).as_posix()
                errors.append(f"[static] {rel}: arquivo não encontrado: /static/{ref}")
    return count


def check_js(errors: list[str], require_node: bool) -> int | None:
    node = shutil.which("node")
    if node is None:
        if require_node:
            errors.append("[js] node não encontrado (obrigatório com --require-node)")
        return None
    files = sorted(STATIC.rglob("*.js"))
    for path in files:
        result = subprocess.run(
            [node, "--check", str(path)], capture_output=True, text=True
        )
        if result.returncode != 0:
            rel = path.relative_to(ROOT).as_posix()
            detail = (result.stderr or result.stdout).strip().splitlines()
            errors.append(f"[js] {rel}: {detail[-1] if detail else 'erro de sintaxe'}")
    return len(files)


def main() -> int:
    require_node = "--require-node" in sys.argv[1:]
    errors: list[str] = []

    n_templates = check_templates(errors)
    n_refs = check_static_refs(errors)
    n_js = check_js(errors, require_node)

    print(f"Templates Jinja2 verificados: {n_templates}")
    print(f"Referências /static verificadas: {n_refs}")
    if n_js is None:
        print("Arquivos JS: node não disponível, verificação de sintaxe ignorada")
    else:
        print(f"Arquivos JS verificados (node --check): {n_js}")

    if errors:
        print(f"\n{len(errors)} problema(s) encontrado(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Frontend OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
