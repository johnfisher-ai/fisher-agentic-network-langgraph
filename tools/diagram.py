"""Flow diagrams as inline SVG.

Same contract as chart.py: the SVG carries no colours of its own, it uses the
classes site.css defines, so a diagram follows the reader's light or dark setting.
"""

from html import escape as esc

W = 780


def _box(x, y, w, h, label, sub=None, cls="node", rx=8):
    """A rounded box with a bold label and an optional second line."""
    out = [f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>']
    if sub:
        out.append(f'<text class="lab bold" x="{x + w / 2}" y="{y + h / 2 - 3}" text-anchor="middle">{esc(label)}</text>')
        out.append(f'<text class="ax" x="{x + w / 2}" y="{y + h / 2 + 12}" text-anchor="middle">{esc(sub)}</text>')
    else:
        out.append(f'<text class="lab bold" x="{x + w / 2}" y="{y + h / 2 + 4}" text-anchor="middle">{esc(label)}</text>')
    return "".join(out)


def _arrow(x1, y1, x2, y2, cls="flow", dash=False):
    d = ' stroke-dasharray="4 3"' if dash else ""
    return f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#ah)"{d}/>'


def network_flow(agents, title, subtitle):
    """One question through the network: fan out, fan in, and the human gate."""
    H = 500
    cx = W / 2
    o = [
        f'<svg class="fig diagram" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="{esc(title)}. {esc(subtitle)}">',
        '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        'markerHeight="6" orient="auto-start-reverse">'
        '<path class="ahead" d="M 0 0 L 10 5 L 0 10 z"/></marker></defs>',
        f'<text class="ttl" x="0" y="16">{esc(title)}</text>',
        f'<text class="sub" x="0" y="33">{esc(subtitle)}</text>',
    ]

    o.append(_box(cx - 70, 52, 140, 30, "a question", cls="node soft"))
    o.append(_arrow(cx, 82, cx, 100))
    o.append(_box(cx - 130, 102, 260, 44, "BROKER", "decides who to consult", cls="node lead"))

    # fan out. Boxes are sized so the row never reaches the annotation gutter.
    n = len(agents)
    bw, gap = 120, 10
    x0 = (W - (n * bw + (n - 1) * gap)) / 2
    ay = 206
    for i, (name, role) in enumerate(agents):
        x = x0 + i * (bw + gap)
        o.append(_arrow(cx, 146, x + bw / 2, ay - 2))
        o.append(_box(x, ay, bw, 46, name, role, cls="node"))
        o.append(_arrow(x + bw / 2, ay + 46, cx, 294))

    o.append(f'<text class="ax" x="{cx}" y="274" text-anchor="middle">'
             'the specialists run in parallel, each returning its fixture</text>')

    o.append(_box(cx - 130, 296, 260, 44, "BROKER", "synthesises, scores risk", cls="node lead"))
    o.append(_arrow(cx, 340, cx, 364))
    o.append(f'<text class="ax" x="{cx + 10}" y="358">risk rule fires?</text>')

    o.append('<path class="flow" d="M 390 364 L 250 364 L 250 424" marker-end="url(#ah)"/>')
    o.append('<text class="ax" x="256" y="380">no</text>')

    o.append('<path class="flow" d="M 390 364 L 530 364 L 530 376" marker-end="url(#ah)"/>')
    o.append('<text class="ax" x="536" y="380">yes</text>')
    o.append(_box(440, 378, 180, 32, "HUMAN APPROVAL", cls="node gate"))
    o.append('<path class="flow" d="M 530 410 L 530 439 L 322 439" marker-end="url(#ah)"/>')
    o.append('<text class="ax" x="530" y="468" text-anchor="middle">'
             'the approved text is returned verbatim</text>')

    o.append(_box(190, 424, 130, 30, "the answer", cls="node soft"))
    o.append("</svg>")
    return "".join(o)


def config_swap(title, subtitle, left, right):
    """Two configs, one graph. left and right are (heading, [rows])."""
    H, colw = 300, 300
    lx, rx = 24, W - colw - 24
    o = [
        f'<svg class="fig diagram" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="{esc(title)}. {esc(subtitle)}">',
        '<defs><marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        'markerHeight="6" orient="auto-start-reverse">'
        '<path class="ahead" d="M 0 0 L 10 5 L 0 10 z"/></marker></defs>',
        f'<text class="ttl" x="0" y="16">{esc(title)}</text>',
        f'<text class="sub" x="0" y="33">{esc(subtitle)}</text>',
    ]
    for x, (head, rows) in ((lx, left), (rx, right)):
        o.append(f'<rect class="node" x="{x}" y="56" width="{colw}" height="{34 + 22 * len(rows)}" rx="8"/>')
        o.append(f'<text class="lab bold" x="{x + 12}" y="78">{esc(head)}</text>')
        for i, r in enumerate(rows):
            o.append(f'<text class="ax" x="{x + 12}" y="{100 + 22 * i}">{esc(r)}</text>')
        o.append(_arrow(x + colw / 2, 56 + 34 + 22 * len(rows) + 4, x + colw / 2, 232, cls="flow"))

    o.append(f'<rect class="node lead" x="{W / 2 - 150}" y="232" width="300" height="44" rx="8"/>')
    o.append(f'<text class="lab bold" x="{W / 2}" y="252" text-anchor="middle">the same graph</text>')
    o.append(f'<text class="ax" x="{W / 2}" y="267" text-anchor="middle">'
             'agentic_network/graph.py, unchanged</text>')
    o.append("</svg>")
    return "".join(o)
