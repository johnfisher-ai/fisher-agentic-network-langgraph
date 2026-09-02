"""Build-time syntax highlighting, so no page needs a CDN script.

Two languages, Python and XML. Both emit the same token classes the design
system already defines for SAS and R, so highlighting follows the reader's
theme like everything else.

    sas-c  comment      sas-k  keyword
    sas-p  builtin      sas-s  string       sas-n  number
"""

import html
import re

KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await", "break", "class",
    "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global",
    "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield", "match", "case",
}

BUILTINS = {
    "dict", "list", "set", "tuple", "str", "int", "float", "bool", "bytes", "len", "range",
    "enumerate", "zip", "print", "open", "isinstance", "getattr", "setattr", "hasattr",
    "super", "property", "staticmethod", "classmethod", "Exception", "ValueError",
    "RuntimeError", "TypeError", "KeyError", "FileNotFoundError", "NotImplementedError",
    "self", "cls", "next", "iter", "sorted", "any", "all", "sum", "min", "max", "repr",
}

_PY = re.compile(
    r"""(?P<comment>\#[^\n]*)
      | (?P<string>[rRbBfFuU]{0,2}(?:\"\"\"(?:\\.|[^\\])*?\"\"\"
                                   |'''(?:\\.|[^\\])*?'''
                                   |\"(?:\\.|[^\"\\\n])*\"
                                   |'(?:\\.|[^'\\\n])*'))
      | (?P<decorator>@[A-Za-z_][\w.]*)
      | (?P<number>\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?\b)
      | (?P<word>\b[A-Za-z_]\w*\b)""",
    re.X | re.S,
)


def python(src: str) -> str:
    """Highlight Python. Returns HTML, already escaped."""
    out, last = [], 0
    for m in _PY.finditer(src):
        out.append(html.escape(src[last:m.start()]))
        kind = m.lastgroup
        text = html.escape(m.group())
        if kind == "comment":
            out.append(f'<span class="sas-c">{text}</span>')
        elif kind == "string":
            out.append(f'<span class="sas-s">{text}</span>')
        elif kind == "number":
            out.append(f'<span class="sas-n">{text}</span>')
        elif kind == "decorator":
            out.append(f'<span class="sas-p">{text}</span>')
        elif m.group() in KEYWORDS:
            out.append(f'<span class="sas-k">{text}</span>')
        elif m.group() in BUILTINS:
            out.append(f'<span class="sas-p">{text}</span>')
        else:
            out.append(text)
        last = m.end()
    out.append(html.escape(src[last:]))
    return "".join(out)


_XML = re.compile(
    r"""(?P<comment><!--.*?-->)
      | (?P<cdata><!\[CDATA\[.*?\]\]>)
      | (?P<decl><\?.*?\?>)
      | (?P<tag></?[A-Za-z_][\w.-]*)
      | (?P<close>/?>)
      | (?P<attr>[A-Za-z_][\w.-]*(?=\s*=))
      | (?P<value>"[^"]*"|'[^']*')""",
    re.X | re.S,
)


def xml(src: str) -> str:
    """Highlight XML. CDATA keeps its own colour so config prompts read as data."""
    out, last = [], 0
    for m in _XML.finditer(src):
        out.append(html.escape(src[last:m.start()]))
        kind = m.lastgroup
        text = html.escape(m.group())
        cls = {"comment": "sas-c", "cdata": "sas-s", "decl": "sas-c",
               "tag": "sas-k", "close": "sas-k", "attr": "sas-p", "value": "sas-s"}[kind]
        out.append(f'<span class="{cls}">{text}</span>')
        last = m.end()
    out.append(html.escape(src[last:]))
    return "".join(out)


def block(src: str, lang: str = "python") -> str:
    """A complete <pre class="code"> block."""
    fn = {"python": python, "xml": xml}[lang]
    return f'<pre class="code">{fn(src.strip())}</pre>'


def wrap(src: str, lang: str = "python", *, name: str = "", note: str = "",
         clip: bool = False) -> str:
    """A titled code panel: filename on the left, a note on the right."""
    fn = {"python": python, "xml": xml}[lang]
    head = ""
    if name or note:
        left = f"<code>{html.escape(name)}</code>" if name else ""
        right = f"<span>{html.escape(note)}</span>" if note else ""
        head = f'<div class="head">{left}{right}</div>'
    cls = "code clip" if clip else "code"
    return f'<div class="codewrap">{head}<pre class="{cls}">{fn(src.strip())}</pre></div>'


def collapsed(summary: str, src: str, lang: str = "python", *, name: str = "",
              note: str = "") -> str:
    """The same panel, behind a disclosure triangle. For whole files."""
    inner = wrap(src, lang, name=name, note=note, clip=True)
    return (f'<details class="src"><summary>{html.escape(summary)}</summary>'
            f'{inner}</details>')
