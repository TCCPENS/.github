"""Render the public GitHub overview from paginated repository metadata."""

import json
import sys
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape


def public_repositories(pages):
    repos = {
        repo["id"]: repo
        for page in pages
        for repo in page
        if repo["visibility"] == "public"
    }.values()
    return repos


def top_languages(repos):
    languages = Counter(repo["language"] for repo in repos if repo["language"])
    return sorted(languages.items(), key=lambda item: (-item[1], item[0]))


def card(title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="170" viewBox="0 0 360 170" role="img">
<title>{title}</title><rect width="360" height="170" rx="7" fill="#1a1b27"/>
<g font-family="system-ui,sans-serif" fill="#a9b1d6">
<text x="20" y="32" font-size="18" font-weight="650" fill="#70a5fd">{title}</text>
{body}</g></svg>
"""


def statistics(repos):
    forks = sum(repo["fork"] for repo in repos)
    rows = [("Public repositories", len(repos)), ("Source repositories", len(repos)-forks),
            ("Stars earned", sum(repo["stargazers_count"] for repo in repos)),
            ("Forks received", sum(repo["forks_count"] for repo in repos))]
    percent = round(100 * (len(repos)-forks) / len(repos)) if repos else 0
    body = []
    for i, (label, value) in enumerate(rows):
        y = 61 + 26*i
        body.append(f'<circle cx="23" cy="{y-4}" r="3" fill="#bf91f3"/><text x="35" y="{y}" font-size="13">{label}</text><text x="198" y="{y}" font-size="14" font-weight="600">{value}</text>')
    body.append(f'<circle cx="284" cy="89" r="32" fill="none" stroke="#313650" stroke-width="5"/><circle cx="284" cy="89" r="32" fill="none" stroke="#70a5fd" stroke-width="5" pathLength="100" stroke-dasharray="{percent} 100" transform="rotate(-90 284 89)"/><text x="284" y="95" text-anchor="middle" font-size="18">{percent}%</text><text x="284" y="144" text-anchor="middle" font-size="12">Source repos</text>')
    return card("TCC PENS GitHub Stats", "".join(body))


def languages_card(ranked):
    colors = ["#3572a5", "#a52a22", "#dea584", "#bb9af7", "#9ece6a", "#7dcfff"]
    total = sum(count for _, count in ranked)
    entries = ranked[:5]
    if len(ranked) > 5:
        entries.append(("Other", sum(count for _, count in ranked[5:])))
    body = ['<text x="20" y="54" font-size="12">Primary language by repository count</text>']
    x = 20
    for i, (name, count) in enumerate(entries):
        width = 320 * count / total
        legend_x, y = 20 + 160*(i%2), 103 + 23*(i//2)
        body.append(f'<rect x="{x:.2f}" y="68" width="{width:.2f}" height="8" fill="{colors[i]}"/><circle cx="{legend_x+4}" cy="{y-4}" r="4" fill="{colors[i]}"/><text x="{legend_x+14}" y="{y}" font-size="12">{escape(name)} · {count/total:.0%}</text>')
        x += width
    if not entries:
        body.append('<text x="20" y="103">No languages reported</text>')
    return card("Top Languages", "".join(body))


if __name__ == "__main__":
    assets = Path(__file__).resolve().parents[1] / "assets"
    repos = public_repositories(json.load(sys.stdin))
    (assets / "org-stats.svg").write_text(statistics(repos), encoding="utf-8")
    (assets / "org-languages.svg").write_text(languages_card(top_languages(repos)), encoding="utf-8")
