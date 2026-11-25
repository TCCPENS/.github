"""Update the organization profile using GitHub's public contributor counts."""
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

CHART = Path(__file__).resolve().parents[1] / "assets/top-contributors.svg"


def render_chart(ordered):
    height = 62 + 36 * max(1, len(ordered))
    rows = []
    peak = max((count for _, count in ordered), default=1)
    label_width = max(140, 36 + 9 * max((len(login) for login, _ in ordered), default=0))
    for index, (login, count) in enumerate(ordered):
        y = 62 + 36 * index
        width = (645 - label_width) * count / max(1, peak)
        rows.append(f'<text x="22" y="{y}">@{escape(login)}</text>'
                    f'<rect x="{label_width}" y="{y-12}" width="{width:.2f}" height="14" rx="4" fill="#7aa2f7"/>'
                    f'<text x="725" y="{y}" text-anchor="end">{count:,}</text>')
    if not ordered:
        rows.append('<text x="22" y="64">No contributors reported yet</text>')
    summary = ", ".join(f"{login}: {count}" for login, count in ordered)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="750" height="{height}" viewBox="0 0 750 {height}" role="img" aria-labelledby="title desc">
<title id="title">Top contributors by commit count</title><desc id="desc">{escape(summary)}</desc>
<rect width="750" height="{height}" rx="7" fill="#1a1b27"/>
<g font-family="system-ui,sans-serif" font-size="15" fill="#c0caf5">
<text x="22" y="30" fill="#70a5fd" font-weight="600">Contributor</text>
<text x="725" y="30" text-anchor="end" fill="#70a5fd" font-weight="600">Commits</text>
{"".join(rows)}</g></svg>
"""


def update_chart(totals):
    ordered = sorted(totals.items(), key=lambda row: (-row[1], row[0].lower()))[:5]
    CHART.write_text(render_chart(ordered), encoding="utf-8")


if __name__ == "__main__":
    totals = Counter()
    for page in json.load(sys.stdin):
        for repo in page:
            if repo["fork"] or repo["visibility"] != "public":
                continue
            endpoint = f'repos/{repo["full_name"]}/contributors?per_page=100'
            result = subprocess.run(
                ["gh", "api", "--paginate", endpoint, "--jq",
                 '.[] | select(.type == "User") | [.login, .contributions] | @tsv'],
                capture_output=True, text=True, check=True,
            )
            for row in result.stdout.splitlines():
                login, count = row.split("\t")
                totals[login] += int(count)
    update_chart(totals)
