"""Pull real source out of the package, so a page can never quote stale code.

Excerpts are located by name through the AST, not by line number, so they survive
edits above them.
"""

import ast
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def named(relpath: str, name: str, *, inner: str | None = None) -> str:
    """Source of a top-level def/class, or of `inner` nested inside it."""
    src = (ROOT / relpath).read_text()
    tree = ast.parse(src)

    def find(nodes, want):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == want:
                return n
        return None

    node = find(tree.body, name)
    if node is None:
        raise KeyError(f"{name} not found in {relpath}")
    if inner:
        node = find(node.body, inner)
        if node is None:
            raise KeyError(f"{inner} not found inside {name} in {relpath}")

    lines = src.splitlines()[node.lineno - 1: node.end_lineno]
    return textwrap.dedent("\n".join(lines))


def between(relpath: str, first: str, last: str) -> str:
    """Lines from the one containing `first` to the one containing `last`, inclusive.

    Anchored to content rather than to line numbers, which drift silently the
    moment anything above the excerpt changes.
    """
    src = (ROOT / relpath).read_text().splitlines()
    try:
        i = next(k for k, line in enumerate(src) if first in line)
    except StopIteration:
        raise KeyError(f"start anchor not found in {relpath}: {first!r}") from None
    try:
        j = next(k for k in range(i, len(src)) if last in src[k])
    except StopIteration:
        raise KeyError(f"end anchor not found in {relpath} after {first!r}: {last!r}") from None
    return textwrap.dedent("\n".join(src[i: j + 1]))


def xml_element(relpath: str, tag: str, attr: str, value: str) -> str:
    """One element out of a config file, indentation preserved."""
    src = (ROOT / relpath).read_text().splitlines()
    open_pat, close_pat = f"<{tag} ", f"</{tag}>"
    for i, line in enumerate(src):
        if open_pat in line and f'{attr}="{value}"' in line:
            for j in range(i, len(src)):
                if close_pat in src[j]:
                    return textwrap.dedent("\n".join(src[i: j + 1]))
    raise KeyError(f"<{tag} {attr}='{value}'> not found in {relpath}")
