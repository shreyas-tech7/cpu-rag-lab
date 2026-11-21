"""Tiny inline SVG charts. Colors come from CSS variables so the page can theme them."""

from __future__ import annotations

from html import escape

SERIES = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)"]


def bars(title: str, groups: list[str], series: dict[str, list[tuple[float, float, float]]]) -> str:
    """Grouped bars with interval whiskers. series: name -> [(mean, lo, hi) per group]."""
    w, h, left, bottom, top = 640, 260, 44, 40, 28
    n_s = max(1, len(series))
    gw = (w - left - 10) / max(1, len(groups))
    bw = gw * 0.8 / n_s
    y = lambda v: top + (h - top - bottom) * (1 - v)  # noqa: E731 - scale 0..1
    out = [
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}" class="chart">',
        f'<text x="{left}" y="16" class="ct">{escape(title)}</text>',
    ]
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        out.append(
            f'<line x1="{left}" x2="{w - 10}" y1="{y(t):.1f}" y2="{y(t):.1f}" class="grid"/>'
        )
        out.append(
            f'<text x="{left - 6}" y="{y(t) + 4:.1f}" class="ax" text-anchor="end">{t:g}</text>'
        )
    for gi, g in enumerate(groups):
        x0 = left + gi * gw + gw * 0.1
        for si, (name, vals) in enumerate(series.items()):
            mean, lo, hi = vals[gi]
            x = x0 + si * bw
            out.append(
                f'<rect x="{x:.1f}" y="{y(mean):.1f}" width="{bw - 2:.1f}" '
                f'height="{y(0) - y(mean):.1f}" fill="{SERIES[si % 4]}">'
                f"<title>{escape(name)} {escape(g)}: {mean:.3f} [{lo:.3f}, {hi:.3f}]</title></rect>"
            )
            cx = x + (bw - 2) / 2
            out.append(
                f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{y(hi):.1f}" y2="{y(lo):.1f}" class="wh"/>'
            )
        out.append(
            f'<text x="{x0 + gw * 0.4:.1f}" y="{h - bottom + 16}" class="ax" '
            f'text-anchor="middle">{escape(g)}</text>'
        )
    lx = left
    for si, name in enumerate(series):
        out.append(f'<rect x="{lx}" y="{h - 14}" width="10" height="10" fill="{SERIES[si % 4]}"/>')
        out.append(f'<text x="{lx + 14}" y="{h - 5}" class="ax">{escape(name)}</text>')
        lx += 14 + 8 * len(name) + 16
    out.append("</svg>")
    return "\n".join(out)


def scatter(title: str, points: list[tuple[str, float, float, int]], xlabel: str, ylabel: str):
    """points: (label, x, y, series index). x is drawn on a log scale."""
    import math

    w, h, left, bottom, top = 640, 280, 52, 44, 28
    xs = [max(p[1], 1e-3) for p in points] or [1]
    lx0, lx1 = math.floor(math.log10(min(xs))), math.ceil(math.log10(max(xs)))
    if lx0 == lx1:
        lx1 += 1
    sx = lambda v: left + (w - left - 12) * (math.log10(max(v, 1e-3)) - lx0) / (lx1 - lx0)  # noqa: E731
    sy = lambda v: top + (h - top - bottom) * (1 - v)  # noqa: E731
    out = [
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}" class="chart">',
        f'<text x="{left}" y="16" class="ct">{escape(title)}</text>',
    ]
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        out.append(
            f'<line x1="{left}" x2="{w - 12}" y1="{sy(t):.1f}" y2="{sy(t):.1f}" class="grid"/>'
        )
        out.append(
            f'<text x="{left - 6}" y="{sy(t) + 4:.1f}" class="ax" text-anchor="end">{t:g}</text>'
        )
    for e in range(lx0, lx1 + 1):
        out.append(
            f'<text x="{sx(10**e):.1f}" y="{h - bottom + 16}" class="ax" text-anchor="middle">'
            f"{10**e:g}</text>"
        )
    for label, x, yv, s in points:
        out.append(
            f'<circle cx="{sx(x):.1f}" cy="{sy(yv):.1f}" r="4" fill="{SERIES[s % 4]}">'
            f"<title>{escape(label)}: {x:.2f} ms, {yv:.3f}</title></circle>"
        )
    out.append(
        f'<text x="{w / 2:.0f}" y="{h - 8}" class="ax" text-anchor="middle">{escape(xlabel)}</text>'
    )
    out.append(
        f'<text x="12" y="{h / 2:.0f}" class="ax" transform="rotate(-90 12 {h / 2:.0f})" '
        f'text-anchor="middle">{escape(ylabel)}</text>'
    )
    out.append("</svg>")
    return "\n".join(out)
